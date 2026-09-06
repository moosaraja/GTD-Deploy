# app.py
# GTD Web App - entry point
from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
import db
import os

app = Flask(__name__)
#app.secret_key = "c486102bef6787d20a4c73f30bfbfde38795fb9e7a6a165dbe67e6e730dee51b"   # sessions
app.secret_key = os.environ.get("GTD_SECRET_KEY", "dev-only-fallback-key")


# ---------- AUTH: current user + decorators ----------
def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    return db.fetch_one(
        "SELECT * FROM users WHERE id = %s AND is_active = TRUE", (uid,))

def uid():
    """Shortcut: id of the logged-in user."""
    return session["user_id"]


@app.context_processor
def inject_user():
    """Makes current_user available in every template (navbar)."""
    return {"current_user": current_user()}


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user():
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        u = current_user()
        if not u:
            return redirect(url_for("login"))
        if not u["is_admin"]:
            flash("Admins only.")
            return redirect(url_for("inbox"))
        return f(*args, **kwargs)
    return wrapper

@app.before_request
def require_login():
    """Every page requires login, except these."""
    open_pages = {"login", "register", "static"}
    if request.endpoint not in open_pages and not current_user():
        return redirect(url_for("login"))


# ---------- AUTH routes ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        if not username or len(password) < 6:
            flash("Username required, password min 6 characters.")
        elif password != confirm:
            flash("Passwords do not match.")
        elif db.fetch_one("SELECT id FROM users WHERE username = %s", (username,)):
            flash("Username already taken.")
        else:
            user = db.execute_returning(
                "INSERT INTO users (username, password_hash) "
                "VALUES (%s, %s) RETURNING id",
                (username, generate_password_hash(password)),
            )
            # seed this user's own default contexts
            for name in ["@office", "@home", "@computer",
                         "@phone", "@errands", "@anywhere"]:
                db.execute(
                    "INSERT INTO contexts (name, user_id) VALUES (%s, %s)",
                    (name, user["id"]))
            session["user_id"] = user["id"]
            flash("Welcome to GTD! 🎉")
            return redirect(url_for("inbox"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = db.fetch_one(
            "SELECT * FROM users WHERE username = %s", (username,))
        if user and check_password_hash(user["password_hash"], password):
            if not user["is_active"]:
                flash("Account disabled. Contact an admin.")
            else:
                session["user_id"] = user["id"]
                return redirect(url_for("inbox"))
        else:
            flash("Wrong username or password.")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------- Home ----------
@app.route("/")
def home():
    return redirect(url_for("inbox"))


# ---------- INBOX: "Collect" phase ----------
@app.route("/inbox")
def inbox():
    items = db.fetch_all(
        "SELECT * FROM items WHERE status = 'inbox' AND user_id = %s "
        "ORDER BY created_at DESC",
        (uid(),))
    return render_template("inbox.html", items=items, count=len(items))


@app.route("/inbox/add", methods=["POST"])
def inbox_add():
    """Stuff -> "IN" tray."""
    title = request.form.get("title", "").strip()
    notes = request.form.get("notes", "").strip()
    if title:  # ignore empty submissions
        db.execute(
            "INSERT INTO items (title, notes, status, user_id) "
            "VALUES (%s, %s, 'inbox', %s)",
            (title, notes or None, uid()),
        )
    return redirect(url_for("inbox"))


@app.route("/inbox/trash/<int:item_id>", methods=["POST"])
def inbox_trash(item_id):
    """Workflow: Eliminate -> Trash (soft delete, keeps history)."""
    db.execute(
        "UPDATE items SET status = 'trash', updated_at = CURRENT_TIMESTAMP "
        "WHERE id = %s AND status = 'inbox' AND user_id = %s",
        (item_id, uid()),
    )
    return redirect(url_for("inbox"))

# ---------- PROCESS: "What is it? Is it actionable?" ----------
@app.route("/process")
def process():
    """Show ONE inbox item at a time (oldest first) for processing."""
    item = db.fetch_one(
        "SELECT * FROM items WHERE status = 'inbox' AND user_id = %s "
        "ORDER BY created_at ASC LIMIT 1",
        (uid(),))
    remaining = db.fetch_one(
        "SELECT COUNT(*) AS c FROM items "
        "WHERE status = 'inbox' AND user_id = %s",
        (uid(),))
    count = remaining["c"] if remaining else 0
    contexts = db.fetch_all(
        "SELECT * FROM contexts WHERE user_id = %s ORDER BY name",
        (uid(),))
    return render_template("process.html", item=item, count=count,
                           contexts=contexts)


def _move(item_id, new_status, extra_sql="", params=()):
    """Helper: move an item to a new status, then return where you came from."""
    db.execute(
        "UPDATE items SET status = %s, updated_at = CURRENT_TIMESTAMP"
        + extra_sql + " WHERE id = %s AND user_id = %s",
        (new_status, *params, item_id, uid()),
    )
    return redirect(request.referrer or url_for("process"))


# --- NO branch: not actionable ---
@app.route("/process/<int:item_id>/trash", methods=["POST"])
def process_trash(item_id):
    return _move(item_id, "trash")


@app.route("/process/<int:item_id>/someday", methods=["POST"])
def process_someday(item_id):
    return _move(item_id, "someday_maybe")


@app.route("/process/<int:item_id>/reference", methods=["POST"])
def process_reference(item_id):
    return _move(item_id, "reference")


# --- YES branch: simple decisions ---
@app.route("/process/<int:item_id>/done", methods=["POST"])
def process_done(item_id):
    """'Do it' — takes less than 2 minutes."""
    return _move(item_id, "done", 
                 ", completed_at = CURRENT_TIMESTAMP")


@app.route("/process/<int:item_id>/next", methods=["POST"])
def process_next(item_id):
    """'Defer it' — as soon as I can -> Next Actions list (with context)."""
    context_id = request.form.get("context_id", type=int)
    if context_id:
        return _move(item_id, "next_action",
                     ", context_id = %s", (context_id,))
    return _move(item_id, "next_action")

# --- YES branch: decisions that need extra info ---
@app.route("/process/<int:item_id>/delegate", methods=["POST"])
def process_delegate(item_id):
    """'Delegate it' -> Waiting For (tracked on a person)."""
    who = request.form.get("delegated_to", "").strip() or "Unknown"
    return _move(item_id, "waiting_for",
                 ", delegated_to = %s", (who,))


@app.route("/process/<int:item_id>/schedule", methods=["POST"])
def process_schedule(item_id):
    """'Defer it' to a specific day/time -> Calendar."""
    due_date = request.form.get("due_date", "").strip() or None
    due_time = request.form.get("due_time", "").strip() or None
    return _move(item_id, "scheduled",
                 ", due_date = %s, due_time = %s", (due_date, due_time))


@app.route("/process/<int:item_id>/project", methods=["POST"])
def process_project(item_id):
    """Multi-step? -> Create Project; item becomes its first Next Action."""
    name = request.form.get("project_name", "").strip() or "Untitled Project"
    project = db.execute_returning(
        "INSERT INTO projects (name, user_id) VALUES (%s, %s) RETURNING id",
        (name, uid()),
    )
    return _move(item_id, "next_action",
                 ", project_id = %s", (project["id"],))

# ---------- LISTS: view items by status ----------
VALID_STATUSES = ["inbox", "next_action", "scheduled", "waiting_for",
                  "someday_maybe", "reference", "done", "trash"]

LIST_TITLES = {
    "next_action":  "➡ Next Actions",
    "scheduled":    "📅 Scheduled (Calendar)",
    "waiting_for":  "🤝 Waiting For",
    "someday_maybe": "☁ Someday / Maybe",
    "reference":    "📁 Reference",
    "done":         "✅ Completed",
    "trash":        "🗑 Trash",
}


@app.route("/list/<status>")
def list_view(status):
    if status not in VALID_STATUSES:
        return "Not found", 404
    context_id = request.args.get("context", type=int)
    contexts = db.fetch_all(
        "SELECT * FROM contexts WHERE user_id = %s ORDER BY name",
        (uid(),))
    sql = ("SELECT i.*, p.name AS project_name, c.name AS context_name "
           "FROM items i "
           "LEFT JOIN projects p ON i.project_id = p.id "
           "LEFT JOIN contexts c ON i.context_id = c.id "
           "WHERE i.status = %s AND i.user_id = %s")
    params = [status, uid()]
    if context_id:
        sql += " AND i.context_id = %s"
        params.append(context_id)
    sql += " ORDER BY i.created_at DESC"
    items = db.fetch_all(sql, tuple(params))
    return render_template("list.html", items=items, status=status,
                           title=LIST_TITLES.get(status, status.title()),
                           contexts=contexts, active_context=context_id)


@app.route("/items/<int:item_id>/done", methods=["POST"])
def item_done(item_id):
    """Mark an item done from any list ('Do' phase)."""
    return _move(item_id, "done", ", completed_at = CURRENT_TIMESTAMP")


@app.route("/items/<int:item_id>/restore", methods=["POST"])
def item_restore(item_id):
    """Pull an item out of Trash back to Inbox."""
    return _move(item_id, "inbox")

@app.route("/items/<int:item_id>/set_context", methods=["POST"])
def item_set_context(item_id):
    """Assign/change a context from any list page."""
    context_id = request.form.get("context_id", type=int)
    db.execute(
        "UPDATE items SET context_id = %s, updated_at = CURRENT_TIMESTAMP "
        "WHERE id = %s AND user_id = %s",
        (context_id, item_id, uid()),
    )
    return redirect(request.referrer or url_for("inbox"))


# ---------- REVIEW: weekly review dashboard ----------
@app.route("/review")
def review():
    today = date.today()

    # 1. Inbox still to process
    inbox_row = db.fetch_one(
        "SELECT COUNT(*) AS c FROM items "
        "WHERE status = 'inbox' AND user_id = %s",
        (uid(),))
    inbox_count = inbox_row["c"] if inbox_row else 0

    # 2. Calendar (overdue first)
    upcoming = db.fetch_all(
        "SELECT * FROM items WHERE status = 'scheduled' "
        "AND due_date IS NOT NULL AND user_id = %s "
        "ORDER BY due_date, due_time NULLS LAST",
        (uid(),))

    # 3. Stuck projects: mine, active, no open actions
    stuck = db.fetch_all(
        "SELECT p.* FROM projects p WHERE p.status = 'active' "
        "AND p.user_id = %s "
        "AND NOT EXISTS (SELECT 1 FROM items i WHERE i.project_id = p.id "
        "AND i.status IN ('next_action','scheduled','waiting_for'))",
        (uid(),))

    # 4. Stale next actions
    stale = db.fetch_all(
        "SELECT * FROM items WHERE status = 'next_action' AND user_id = %s "
        "ORDER BY updated_at ASC LIMIT 5",
        (uid(),))

    # 5. Waiting For
    waiting = db.fetch_all(
        "SELECT * FROM items WHERE status = 'waiting_for' AND user_id = %s "
        "ORDER BY created_at ASC",
        (uid(),))

    # 6. Overview counts
    counts = db.fetch_all(
        "SELECT status, COUNT(*) AS c FROM items "
        "WHERE user_id = %s GROUP BY status",
        (uid(),))

    return render_template("review.html", today=today,
                           inbox_count=inbox_count, upcoming=upcoming,
                           stuck=stuck, stale=stale, waiting=waiting,
                           counts=counts, titles=LIST_TITLES)

# ---------- PROJECTS: "What's the successful outcome?" ----------
@app.route("/projects")
def projects_view():
    """All MY active projects, each with its next actions."""
    projects = db.fetch_all(
        "SELECT * FROM projects WHERE status = 'active' AND user_id = %s "
        "ORDER BY created_at DESC",
        (uid(),))
    items = db.fetch_all(
        "SELECT * FROM items WHERE project_id IS NOT NULL AND user_id = %s "
        "AND status IN ('next_action','scheduled','waiting_for') "
        "ORDER BY created_at ASC",
        (uid(),))
    by_project = {}
    for it in items:
        by_project.setdefault(it["project_id"], []).append(it)
    return render_template("projects.html",
                           projects=projects, items_by_project=by_project)


@app.route("/projects/add", methods=["POST"])
def project_add():
    name = request.form.get("name", "").strip()
    outcome = request.form.get("outcome", "").strip()
    if name:
        db.execute(
            "INSERT INTO projects (name, outcome, user_id) VALUES (%s, %s, %s)",
            (name, outcome or None, uid()),
        )
    return redirect(url_for("projects_view"))


@app.route("/projects/<int:project_id>/complete", methods=["POST"])
def project_complete(project_id):
    db.execute(
        "UPDATE projects SET status = 'completed', "
        "completed_at = CURRENT_TIMESTAMP "
        "WHERE id = %s AND user_id = %s",
        (project_id, uid()),
    )
    return redirect(url_for("projects_view"))


@app.route("/projects/<int:project_id>/add_action", methods=["POST"])
def project_add_action(project_id):
    """Add a next action — only if the project belongs to me."""
    title = request.form.get("title", "").strip()
    project = db.fetch_one(
        "SELECT id FROM projects WHERE id = %s AND user_id = %s",
        (project_id, uid()))
    if title and project:
        db.execute(
            "INSERT INTO items (title, status, project_id, user_id) "
            "VALUES (%s, 'next_action', %s, %s)",
            (title, project_id, uid()),
        )
    return redirect(url_for("projects_view"))

# ---------- EDIT & MOVE: fix or relocate any item ----------
@app.route("/items/<int:item_id>/edit", methods=["GET"])
def item_edit(item_id):
    """Show the edit form — only for MY items."""
    item = db.fetch_one(
        "SELECT * FROM items WHERE id = %s AND user_id = %s",
        (item_id, uid()))
    if not item:
        return "Not found", 404
    contexts = db.fetch_all(
        "SELECT * FROM contexts WHERE user_id = %s ORDER BY name",
        (uid(),))
    projects = db.fetch_all(
        "SELECT * FROM projects WHERE status = 'active' AND user_id = %s "
        "ORDER BY name",
        (uid(),))
    return render_template("edit.html", item=item,
                           contexts=contexts, projects=projects)


@app.route("/items/<int:item_id>/edit", methods=["POST"])
def item_update(item_id):
    """Save edits — only if the item is mine."""
    title = request.form.get("title", "").strip()
    notes = request.form.get("notes", "").strip() or None
    status = request.form.get("status", "inbox")
    project_id = request.form.get("project_id", type=int)
    context_id = request.form.get("context_id", type=int)
    due_date = request.form.get("due_date", "").strip() or None
    due_time = request.form.get("due_time", "").strip() or None
    delegated_to = request.form.get("delegated_to", "").strip() or None

    if not title or status not in VALID_STATUSES:
        return redirect(request.referrer or url_for("inbox"))

    if status == "done":
        db.execute(
            "UPDATE items SET title=%s, notes=%s, status=%s, project_id=%s, "
            "context_id=%s, due_date=%s, due_time=%s, delegated_to=%s, "
            "completed_at=CURRENT_TIMESTAMP, updated_at=CURRENT_TIMESTAMP "
            "WHERE id=%s AND user_id=%s",
            (title, notes, status, project_id, context_id, due_date,
             due_time, delegated_to, item_id, uid()))
    else:
        db.execute(
            "UPDATE items SET title=%s, notes=%s, status=%s, project_id=%s, "
            "context_id=%s, due_date=%s, due_time=%s, delegated_to=%s, "
            "completed_at=NULL, updated_at=CURRENT_TIMESTAMP "
            "WHERE id=%s AND user_id=%s",
            (title, notes, status, project_id, context_id, due_date,
             due_time, delegated_to, item_id, uid()))

    return redirect(url_for("list_view", status=status))


@app.route("/trash/empty", methods=["POST"])
def trash_empty():
    """Permanently delete THIS user's trash only."""
    db.execute(
        "DELETE FROM items WHERE status = 'trash' AND user_id = %s",
        (uid(),))
    return redirect(url_for("list_view", status="trash"))

# ---------- ADMIN: manage users ----------
@app.route("/admin")
@admin_required
def admin_panel():
    users = db.fetch_all(
        "SELECT u.id, u.username, u.is_admin, u.is_active, u.created_at, "
        "COUNT(i.id) AS item_count "
        "FROM users u LEFT JOIN items i ON i.user_id = u.id "
        "GROUP BY u.id ORDER BY u.created_at")
    return render_template("admin.html", users=users)


@app.route("/admin/<int:user_id>/toggle_active", methods=["POST"])
@admin_required
def admin_toggle_active(user_id):
    if user_id == uid():
        flash("You cannot deactivate yourself.")
        return redirect(url_for("admin_panel"))
    db.execute(
        "UPDATE users SET is_active = NOT is_active WHERE id = %s",
        (user_id,))
    return redirect(url_for("admin_panel"))


@app.route("/admin/<int:user_id>/toggle_admin", methods=["POST"])
@admin_required
def admin_toggle_admin(user_id):
    if user_id == uid():
        flash("You cannot change your own admin role.")
        return redirect(url_for("admin_panel"))
    db.execute(
        "UPDATE users SET is_admin = NOT is_admin WHERE id = %s",
        (user_id,))
    return redirect(url_for("admin_panel"))


@app.route("/admin/<int:user_id>/delete", methods=["POST"])
@admin_required
def admin_delete(user_id):
    if user_id == uid():
        flash("You cannot delete yourself.")
        return redirect(url_for("admin_panel"))
    # delete their data first (foreign key safety), then the user
    db.execute("DELETE FROM items WHERE user_id = %s", (user_id,))
    db.execute("DELETE FROM projects WHERE user_id = %s", (user_id,))
    db.execute("DELETE FROM contexts WHERE user_id = %s", (user_id,))
    db.execute("DELETE FROM users WHERE id = %s", (user_id,))
    flash("User and all their data deleted.")
    return redirect(url_for("admin_panel"))

if __name__ == "__main__":
    app.run(debug=True, port=955)