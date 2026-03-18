"""
Transaction model — all SQL operations for the transactions table.
Supports manual + Plaid-sourced transactions with multi-account metadata.
"""
from utils.db import get_db


def create_manual(user_id: int, amount: float, category: str,
                  description: str, date: str) -> int:
    """Insert a manually-created transaction and return its ID."""
    with get_db() as (conn, cur):
        cur.execute(
            """
            INSERT INTO transactions
            (user_id, amount, category, description, date, source, created_at)
            VALUES (%s, %s, %s, %s, %s, 'manual', NOW())
            RETURNING id
            """,
            (user_id, amount, category, description, date),
        )
        return cur.fetchone()[0]


def upsert_plaid_transaction(
    user_id: int,
    amount: float,
    category: str,
    description: str,
    date: str,
    plaid_transaction_id: str,
    plaid_account_id: str,
    institution_name: str,
    account_name: str,
):
    """Insert or update a Plaid-sourced transaction (idempotent via plaid_transaction_id)."""
    with get_db() as (conn, cur):
        cur.execute(
            """
            INSERT INTO transactions
            (user_id, amount, category, description, date,
             plaid_transaction_id, source, plaid_account_id,
             institution_name, account_name, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, 'plaid', %s, %s, %s, NOW())
            ON CONFLICT (plaid_transaction_id) DO UPDATE SET
                amount = EXCLUDED.amount,
                category = EXCLUDED.category,
                description = EXCLUDED.description,
                date = EXCLUDED.date,
                plaid_account_id = EXCLUDED.plaid_account_id,
                institution_name = EXCLUDED.institution_name,
                account_name = EXCLUDED.account_name
            """,
            (user_id, amount, category, description, date,
             plaid_transaction_id, plaid_account_id,
             institution_name, account_name),
        )


def update_plaid_transaction(
    user_id: int,
    plaid_transaction_id: str,
    amount: float,
    category: str,
    description: str,
    date: str,
    plaid_account_id: str,
    institution_name: str,
    account_name: str,
):
    """Update a modified Plaid transaction."""
    with get_db() as (conn, cur):
        cur.execute(
            """
            UPDATE transactions
            SET amount = %s, category = %s, description = %s, date = %s,
                plaid_account_id = %s, institution_name = %s, account_name = %s
            WHERE plaid_transaction_id = %s AND user_id = %s
            """,
            (amount, category, description, date,
             plaid_account_id, institution_name, account_name,
             plaid_transaction_id, user_id),
        )


def delete_by_plaid_id(user_id: int, plaid_transaction_id: str):
    """Delete a single transaction by its Plaid ID."""
    with get_db() as (conn, cur):
        cur.execute(
            "DELETE FROM transactions WHERE plaid_transaction_id = %s AND user_id = %s",
            (plaid_transaction_id, user_id),
        )


def delete_by_id(user_id: int, transaction_id: int) -> int:
    """Delete a transaction by its internal ID. Returns rows affected."""
    with get_db() as (conn, cur):
        cur.execute(
            "DELETE FROM transactions WHERE id = %s AND user_id = %s",
            (transaction_id, user_id),
        )
        return cur.rowcount


def delete_by_account_ids(user_id: int, account_ids: list) -> int:
    """Delete all Plaid transactions belonging to the given account IDs. Returns rows deleted."""
    if not account_ids:
        return 0
    placeholders = ",".join(["%s"] * len(account_ids))
    with get_db() as (conn, cur):
        cur.execute(
            f"""
            DELETE FROM transactions
            WHERE user_id = %s AND source = 'plaid'
            AND plaid_account_id IN ({placeholders})
            """,
            [user_id] + account_ids,
        )
        return cur.rowcount


def find_paginated(user_id: int, account_id: str = None,
                   page: int = 1, per_page: int = 50) -> dict:
    """
    Return paginated transactions with metadata.
    Optionally filter by plaid_account_id.

    Returns:
        {
            "transactions": [...],
            "pagination": { "page", "per_page", "total", "total_pages" }
        }
    """
    offset = (page - 1) * per_page

    with get_db() as (conn, cur):
        # ── Count total matching rows ──
        if account_id:
            cur.execute(
                "SELECT COUNT(*) FROM transactions WHERE user_id = %s AND plaid_account_id = %s",
                (user_id, account_id),
            )
        else:
            cur.execute(
                "SELECT COUNT(*) FROM transactions WHERE user_id = %s",
                (user_id,),
            )
        total = cur.fetchone()[0]

        # ── Fetch the page ──
        if account_id:
            cur.execute(
                """
                SELECT id, amount, category, description, date, created_at,
                       plaid_transaction_id, source, plaid_account_id,
                       institution_name, account_name
                FROM transactions
                WHERE user_id = %s AND plaid_account_id = %s
                ORDER BY date DESC, id DESC
                LIMIT %s OFFSET %s
                """,
                (user_id, account_id, per_page, offset),
            )
        else:
            cur.execute(
                """
                SELECT id, amount, category, description, date, created_at,
                       plaid_transaction_id, source, plaid_account_id,
                       institution_name, account_name
                FROM transactions
                WHERE user_id = %s
                ORDER BY date DESC, id DESC
                LIMIT %s OFFSET %s
                """,
                (user_id, per_page, offset),
            )

        rows = cur.fetchall()

    transactions = []
    for row in rows:
        transactions.append({
            "id": row[0],
            "amount": float(row[1]),
            "category": row[2],
            "description": row[3],
            "date": str(row[4]),
            "created_at": str(row[5]),
            "plaid_transaction_id": row[6],
            "source": row[7] or "manual",
            "plaid_account_id": row[8],
            "institution_name": row[9],
            "account_name": row[10],
        })

    total_pages = max(1, -(-total // per_page))  # Ceiling division

    return {
        "transactions": transactions,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
        },
    }
