"""
PlaidItem model — all SQL operations for the plaid_items table.
Handles linked bank account records with encrypted access tokens.
"""
from utils.db import get_db


def find_by_user(user_id: int) -> list:
    """Return all plaid items for a user: [(id, access_token, cursor, institution_name, item_id), ...]"""
    with get_db() as (conn, cur):
        cur.execute(
            """
            SELECT id, access_token, cursor, institution_name, item_id
            FROM plaid_items
            WHERE user_id = %s
            ORDER BY created_at DESC
            """,
            (user_id,),
        )
        return cur.fetchall()


def find_by_item_id(item_id: str):
    """Return (id, user_id, access_token) for a given plaid item_id, or None."""
    with get_db() as (conn, cur):
        cur.execute(
            "SELECT id, user_id, access_token FROM plaid_items WHERE item_id = %s",
            (item_id,),
        )
        return cur.fetchone()


def find_by_item_id_and_user(item_id: str, user_id: int):
    """Return (id, access_token) if item belongs to user, or None."""
    with get_db() as (conn, cur):
        cur.execute(
            "SELECT id, access_token FROM plaid_items WHERE item_id = %s AND user_id = %s",
            (item_id, user_id),
        )
        return cur.fetchone()


def upsert(user_id: int, encrypted_token: str, item_id: str,
           institution_id: str, institution_name: str):
    """Insert or update a plaid item (idempotent by item_id)."""
    with get_db() as (conn, cur):
        cur.execute("SELECT id FROM plaid_items WHERE item_id = %s", (item_id,))
        existing = cur.fetchone()

        if existing:
            cur.execute(
                """
                UPDATE plaid_items
                SET access_token = %s, institution_id = %s,
                    institution_name = %s, updated_at = NOW()
                WHERE item_id = %s
                """,
                (encrypted_token, institution_id, institution_name, item_id),
            )
        else:
            cur.execute(
                """
                INSERT INTO plaid_items
                (user_id, access_token, item_id, institution_id,
                 institution_name, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                """,
                (user_id, encrypted_token, item_id,
                 institution_id, institution_name),
            )


def update_cursor(plaid_item_db_id: int, cursor: str):
    """Save the latest sync cursor for incremental transaction fetching."""
    with get_db() as (conn, cur):
        cur.execute(
            "UPDATE plaid_items SET cursor = %s, updated_at = NOW() WHERE id = %s",
            (cursor, plaid_item_db_id),
        )


def delete_by_item_id_and_user(item_id: str, user_id: int) -> int:
    """Delete a plaid item record. Returns rows affected."""
    with get_db() as (conn, cur):
        cur.execute(
            "DELETE FROM plaid_items WHERE item_id = %s AND user_id = %s",
            (item_id, user_id),
        )
        return cur.rowcount


def find_tokens_for_accounts(user_id: int) -> list:
    """Return [(access_token, item_id, institution_name), ...] for a user."""
    with get_db() as (conn, cur):
        cur.execute(
            "SELECT access_token, item_id, institution_name FROM plaid_items WHERE user_id = %s",
            (user_id,),
        )
        return cur.fetchall()
