# create_admin.py - run: python create_admin.py
import getpass
from werkzeug.security import generate_password_hash
import db

username = input("Admin username: ").strip()
password = getpass.getpass("Password: ")

if db.fetch_one("SELECT id FROM users WHERE username = %s", (username,)):
    print("That username already exists.")
else:
    db.execute(
        "INSERT INTO users (username, password_hash, is_admin) "
        "VALUES (%s, %s, TRUE)",
        (username, generate_password_hash(password)),
    )
    print(f"Admin '{username}' created. ✅")