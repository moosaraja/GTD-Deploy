The Process Decision Tree
Project Structure
Item Status Flow


i need this in a good different way. its not yet fixed. Or may be you can give me good corrected format
The existing format is not looking good

--- Attached File: ReadMe.md ---
# 🎯 GTD Web App

A full-stack **Getting Things Done (GTD)** task management application built with
**Python (Flask)** and **PostgreSQL**, faithfully implementing David Allen's
*Mastering Workflow* — from capturing "stuff" to the Weekly Review.

Multi-user with admin controls, dark mode, and a clean gradient UI.

> **Author & Developer:** [Moosa Raja](https://github.com/moosaraja)

## ✨ Features

### 🔄 The Complete GTD Workflow

| Phase | Feature | What it does |
|-------|---------|--------------|
| **Collect** | 📥 Inbox | Capture anything that has your attention — get it out of your head |
| **Process** | ⚙️ Decision wizard | One item at a time: *"What is it? Is it actionable?"* |
| **Organize** | 📋 Projects & Lists | Next Actions, Calendar, Waiting For, Someday/Maybe, Reference, Trash |
| **Do** | 📍 Context filters | *"I'm at @home with 30 min — what can I do right now?"* |
| **Review** | 🔍 Weekly dashboard | Inbox status, overdue items, stuck projects, loose ends, waiting-for follow-ups |

### ⚙️ The Process Decision Tree (Text Edition)

Process every inbox item **top-down**, one at a time — never put it back.

| # | Question | Yes → Do this | No → Next question |
|---|----------|---------------|---------------------|
| 1 | **Is it actionable?**  | **Trash** / **Someday/Maybe** / **Reference** | → **2** |
| 2 | **Can you do it in < 2 min?** | **Do it now** ✅ | → **3** |
| 3 | **Should you delegate it?** | **Waiting For** 🤝 | → **4** |
| 4 | **Does it have a specific date/time?** | **Calendar** 📅 | → **5** |
| 5 | **Is it a multi-step outcome?** | **Project** 📋 + **Next Action** ➡ | **Next Action** ➡ + **@context** |

> **Golden rule:** Once processed, the item **never returns to the Inbox**.
    
### 👤 Multi-User System

- **Open registration** — new users get 6 default contexts auto-seeded (@office, @home, @computer, @phone, @errands, @anywhere)
- **Password hashing** — never stored in plain text (Werkzeug / PBKDF2)
- **Full data isolation** — every query is scoped to the logged-in user; users can never see or touch each other's items (even by guessing URLs)
- **Admin panel** — admins can:
  - ⛔ Deactivate / ✅ Reactivate accounts (instant logout for disabled users)
  - ▲ Promote / ▼ Demote admins
  - 🗑 Delete a user **and** all their data (with confirmation)
  - 🛡 Self-protection: you cannot deactivate/demote/delete yourself

### 🎨 UI Extras

- 🌙 **Dark mode** toggle with persistent preference (localStorage)
- ✏️ **Edit & move** any item between lists, change context/project/dates
- 🔥 Empty Trash (permanently delete, per user)
- Active-page highlighting in the navigation bar
- Gradient design system: login, register, and all inner pages

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, Flask |
| Database | PostgreSQL |
| Templating | Jinja2 |
| Frontend | HTML5, CSS3, vanilla JavaScript |
| Security | Werkzeug password hashing, signed Flask sessions |
| Auth | Session-based with `before_request` login wall |

---

## 📁 Project Structure

| Path | Purpose |
|------|---------|
| `app.py` | Flask application — all routes & business logic |
| `db.py` | PostgreSQL helpers (`fetch_all`, `fetch_one`, `execute`) |
| `schema.sql` | Core tables: `items`, `projects`, `contexts` |
| `schema_users.sql` | Multi-user upgrade: `users` table + `user_id` FKs |
| `create_admin.py` | One-time script to bootstrap the first admin |
| `requirements.txt` | Python dependencies |
| `templates/` | Jinja2 templates (see below) |
| &nbsp;&nbsp;`├── base.html` | Shared layout, navbar, dark-mode toggle |
| &nbsp;&nbsp;`├── login.html` / `register.html` | Auth pages |
| &nbsp;&nbsp;`├── inbox.html` | **Collect** phase |
| &nbsp;&nbsp;`├── process.html` | **Process** phase (decision wizard) |
| &nbsp;&nbsp;`├── list.html` | Generic list (all statuses + context filter) |
| &nbsp;&nbsp;`├── projects.html` | Projects with outcomes & actions |
| &nbsp;&nbsp;`├── review.html` | **Weekly Review** dashboard |
| &nbsp;&nbsp;`├── edit.html` | Edit / move item form |
| &nbsp;&nbsp;`└── admin.html` | Admin user-management panel |



---

## 🗄 Database Schema

### Tables

| Table | Purpose | Key columns |
|-------|---------|-------------|
| `users` | Accounts | username, password_hash, is_admin, is_active |
| `items` | Every piece of "stuff" | title, notes, **status**, project_id, context_id, due_date, due_time, delegated_to, user_id |
| `projects` | Multi-step outcomes | name, outcome, status (active/completed), user_id |
| `contexts` | @where/@how labels | name, user_id (unique per user) |

### 🗄 Item Status Flow

| From Status | Trigger / Action | To Status |
|-------------|------------------|-----------|
| `inbox` | Process → Actionable, < 2 min | `done` |
| `inbox` | Process → Actionable, delegate | `waiting_for` |
| `inbox` | Process → Actionable, specific date | `scheduled` |
| `inbox` | Process → Actionable, anytime | `next_action` |
| `inbox` | Process → Actionable, multi-step | `next_action` + `project` |
| `inbox` | Process → Incubate | `someday_maybe` |
| `inbox` | Process → Reference | `reference` |
| `inbox` | Process → Trash | `trash` |
| `next_action` | Complete | `done` |
| `next_action` | Set due date/time | `scheduled` |
| `next_action` | Delegate | `waiting_for` |
| `next_action` | Defer indefinitely | `someday_maybe` |
| `scheduled` | Date arrives / Reschedule | `next_action` |
| `waiting_for` | Returned / Followed up | `next_action` |
| `someday_maybe` | Promote to active | `next_action` |
| `trash` | **Empty Trash** | *permanently deleted* |

> **Rule:** Items flow **forward only** — they never return to `inbox` once processed.


  
---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 14+ running locally

### 1. Clone & set up environment

bash
git clone https://github.com/moosaraja/GTD.git
cd GTD
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt


### 2. Create the database

bash
psql -U postgres

sql
CREATE DATABASE gtd_app;
\c gtd_app
\i 'schema_final.sql'

### 3. Configure credentials

Set the database password as an environment variable (recommended):

bash
setx GTD_DB_PASSWORD "your-postgres-password"


> Close and reopen the terminal after `setx`.

### 4. Create the first admin

bash
python create_admin.py


### 5. Run

bash
python app.py

Open **http://127.0.0.1:955** — log in with your admin account. 🎉

---

## 📖 Usage (the GTD way)

1. **Collect** — dump everything into the Inbox as it comes to mind
2. **Process** — open the Process page daily; decide each item top-down, never back into the inbox
3. **Organize** — keep Next Actions contextual (@phone, @office), track delegated work in Waiting For
4. **Do** — filter lists by context, time, and energy
5. **Review** — run the Weekly Review dashboard: process inbox, plan stuck projects, chase Waiting For, clear loose ends

---

## 🔒 Security Notes

- Passwords are hashed (PBKDF2 via Werkzeug) — never stored or logged in plain text
- All data queries enforce ownership (`user_id`) server-side — including updates, deletes, and URL-accessed items
- DB credentials live in environment variables, not in source code
- Session cookies are signed with a secret key to prevent tampering

---

## 🔮 Roadmap

- [ ] Recurring tasks (weekly reviews, bills)
- [ ] Global search across all lists
- [ ] "Today" view (calendar + due next actions)
- [ ] Email-to-inbox capture
- [ ] REST API for mobile clients
- [ ] Per-user theme preference in DB

---

## 🙏 Acknowledgments

- Workflow based on *Getting Things Done* by **David Allen** — [gettingthingsdone.com](https://gettingthingsdone.com)
- Built as a hands-on full-stack learning project

---

## 👤 Author

**Moosa Raja** — a.k.a. [@moosaraja](https://github.com/moosaraja)

Designed, developed, and maintained the full application:
Flask backend, PostgreSQL schema, GTD workflow engine,
multi-user auth with admin controls, and the UI.


## 📄 License

MIT — feel free to use, learn, and adapt.


MIT License

Copyright (c) 2025 Moosa Raja

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.