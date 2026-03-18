"""
User model — all SQL operations for the users table.
No business logic. Just data access.
"""
from utils.db import get_db


def create_user(username: str, email: str, password_hash: str) -> int:
    """Insert a new user and return the user ID."""
    with get_db() as (conn, cur):
        cur.execute(
            """
            INSERT INTO users (username, email, password_hash, created_at)
            VALUES (%s, %s, %s, NOW())
            RETURNING id
            """,
            (username, email, password_hash),
        )
        return cur.fetchone()[0]


def find_by_email(email: str):
    """Return (id, password_hash) for the given email, or None."""
    with get_db() as (conn, cur):
        cur.execute(
            "SELECT id, password_hash FROM users WHERE email = %s",
            (email,),
        )
        return cur.fetchone()


def find_by_id(user_id: int):
    """Return (id, username, email) for the given user ID, or None."""
    with get_db() as (conn, cur):
        cur.execute(
            "SELECT id, username, email FROM users WHERE id = %s",
            (user_id,),
        )
        return cur.fetchone()
