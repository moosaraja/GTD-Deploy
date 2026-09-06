# db.py
# Database helper for the GTD app
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import closing
import os   # add this at the very top, with the other imports

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "gtd_app",
    "user": "postgres",
    "password": os.environ.get("GTD_DB_PASSWORD", ""),   
}

def fetch_all(sql, params=()):
    """Run a SELECT, return all rows as a list of dicts."""
    with closing(psycopg2.connect(**DB_CONFIG)) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]


def fetch_one(sql, params=()):
    """Run a SELECT, return one row as a dict (or None)."""
    with closing(psycopg2.connect(**DB_CONFIG)) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            return dict(row) if row else None


def execute(sql, params=()):
    """Run an INSERT / UPDATE / DELETE. Returns affected row count."""
    with closing(psycopg2.connect(**DB_CONFIG)) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rowcount = cur.rowcount
        conn.commit()
        return rowcount

def execute_returning(sql, params=()):
    """Run INSERT/UPDATE ... RETURNING; returns the new row as a dict."""
    with closing(psycopg2.connect(**DB_CONFIG)) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
        conn.commit()
        return dict(row) if row else None