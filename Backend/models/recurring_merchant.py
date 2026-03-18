"""
RecurringMerchant model — SQL operations for subscription detection.

Handles:
  * Fetching candidate transactions for analysis
  * Upserting detected recurring merchants
  * Querying detected subscriptions for API responses
"""
import json
from utils.db import get_db


# ──────────────────────────────────────────────
# Private Helpers
# ──────────────────────────────────────────────

def _account_filter(account_id: str):
    """Build optional plaid_account_id clause and params."""
    if account_id and account_id != "all":
        return " AND plaid_account_id = %s", [account_id]
    return "", []


def _row_to_dict(row) -> dict:
    """Convert a recurring_merchants row to dict."""
    return {
        "id": row[0],
        "user_id": row[1],
        "account_id": row[2],
        "merchant_key": row[3],
        "merchant_display_name": row[4],
        "cadence": row[5],
        "avg_amount": float(row[6]) if row[6] else 0.0,
        "amount_stddev": float(row[7]) if row[7] else 0.0,
        "amount_tolerance": float(row[8]) if row[8] else 0.0,
        "last_charge_date": str(row[9]) if row[9] else None,
        "next_expected_date": str(row[10]) if row[10] else None,
        "confidence_score": float(row[11]) if row[11] else 0.0,
        "sample_size": row[12],
        "last_n_transactions": row[13] if isinstance(row[13], list) else [],
        "explanation_json": row[14] if isinstance(row[14], dict) else {},
        "created_at": str(row[15]),
        "updated_at": str(row[16]),
    }


_SELECT_COLS = """
    id, user_id, account_id, merchant_key, merchant_display_name,
    cadence, avg_amount, amount_stddev, amount_tolerance,
    last_charge_date, next_expected_date, confidence_score,
    sample_size, last_n_transactions, explanation_json,
    created_at, updated_at
"""


# ──────────────────────────────────────────────
# Transaction queries for detection
# ──────────────────────────────────────────────

def fetch_expense_transactions(user_id: int, account_id: str,
                                lookback_days: int = 180) -> list:
    """
    Fetch expense transactions for subscription detection.
    Returns list of dicts with id, description, amount, date, category.
    Only expenses (amount < 0), excludes transfers.
    """
    acct_clause, acct_params = _account_filter(account_id)

    with get_db() as (conn, cur):
        cur.execute(
            f"""
            SELECT id, description, ABS(amount) as amount, date, category
            FROM transactions
            WHERE user_id = %s
              AND amount < 0
              AND date >= CURRENT_DATE - INTERVAL '{int(lookback_days)} days'
              AND COALESCE(category, '') NOT ILIKE '%%transfer%%'
              {acct_clause}
            ORDER BY description, date
            """,
            [user_id] + acct_params,
        )
        rows = cur.fetchall()

    return [
        {
            "id": r[0],
            "description": r[1],
            "amount": float(r[2]),
            "date": str(r[3]),
            "category": r[4],
        }
        for r in rows
    ]


# ──────────────────────────────────────────────
# CRUD
# ──────────────────────────────────────────────

def upsert(user_id: int, account_id: str, merchant_key: str,
           merchant_display_name: str, cadence: str,
           avg_amount: float, amount_stddev: float, amount_tolerance: float,
           last_charge_date, next_expected_date,
           confidence_score: float, sample_size: int,
           last_n_transactions: list, explanation_json: dict) -> int:
    """Upsert a detected recurring merchant. Returns ID."""
    with get_db() as (conn, cur):
        cur.execute(
            """
            INSERT INTO recurring_merchants
                (user_id, account_id, merchant_key, merchant_display_name,
                 cadence, avg_amount, amount_stddev, amount_tolerance,
                 last_charge_date, next_expected_date,
                 confidence_score, sample_size,
                 last_n_transactions, explanation_json,
                 created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            ON CONFLICT ON CONSTRAINT uq_recurring_merchants_user_merchant
            DO UPDATE SET
                merchant_display_name = EXCLUDED.merchant_display_name,
                avg_amount            = EXCLUDED.avg_amount,
                amount_stddev         = EXCLUDED.amount_stddev,
                amount_tolerance      = EXCLUDED.amount_tolerance,
                last_charge_date      = EXCLUDED.last_charge_date,
                next_expected_date    = EXCLUDED.next_expected_date,
                confidence_score      = EXCLUDED.confidence_score,
                sample_size           = EXCLUDED.sample_size,
                last_n_transactions   = EXCLUDED.last_n_transactions,
                explanation_json      = EXCLUDED.explanation_json,
                updated_at            = NOW()
            RETURNING id
            """,
            (user_id, account_id, merchant_key, merchant_display_name,
             cadence, avg_amount, amount_stddev, amount_tolerance,
             str(last_charge_date) if last_charge_date else None,
             str(next_expected_date) if next_expected_date else None,
             confidence_score, sample_size,
             json.dumps(last_n_transactions), json.dumps(explanation_json)),
        )
        return cur.fetchone()[0]


def find_by_user(user_id: int, account_id: str = "all",
                 min_confidence: float = 0) -> list:
    """Find all recurring merchants for a user, optionally filtered."""
    acct_clause = ""
    params = [user_id, min_confidence]

    if account_id and account_id != "all":
        acct_clause = " AND account_id = %s"
        params.append(account_id)

    with get_db() as (conn, cur):
        cur.execute(
            f"""
            SELECT {_SELECT_COLS}
            FROM recurring_merchants
            WHERE user_id = %s AND confidence_score >= %s
            {acct_clause}
            ORDER BY next_expected_date ASC NULLS LAST,
                     confidence_score DESC
            """,
            params,
        )
        return [_row_to_dict(r) for r in cur.fetchall()]


def find_by_id(recurring_id: int, user_id: int):
    """Find a single recurring merchant by ID, with ownership check."""
    with get_db() as (conn, cur):
        cur.execute(
            f"""
            SELECT {_SELECT_COLS}
            FROM recurring_merchants
            WHERE id = %s AND user_id = %s
            """,
            (recurring_id, user_id),
        )
        row = cur.fetchone()
    return _row_to_dict(row) if row else None


def find_upcoming_in_horizon(user_id: int, account_id: str,
                              horizon_days: int, min_confidence: float = 50) -> list:
    """Find subscriptions expected within a date horizon (for cashflow)."""
    acct_clause, acct_params = ("", [])
    if account_id and account_id != "all":
        acct_clause = " AND account_id = %s"
        acct_params = [account_id]

    with get_db() as (conn, cur):
        cur.execute(
            f"""
            SELECT merchant_display_name, cadence, avg_amount, next_expected_date
            FROM recurring_merchants
            WHERE user_id = %s
              AND confidence_score >= %s
              AND next_expected_date IS NOT NULL
              AND next_expected_date >= CURRENT_DATE
              AND next_expected_date <= CURRENT_DATE + %s
              {acct_clause}
            ORDER BY next_expected_date
            """,
            [user_id, min_confidence, horizon_days] + acct_params,
        )
        return [
            {
                "merchant": r[0],
                "cadence": r[1],
                "amount": float(r[2]),
                "expected_date": str(r[3]),
            }
            for r in cur.fetchall()
        ]


def delete_stale(user_id: int, account_id: str, active_keys: list) -> int:
    """Remove recurring merchants that are no longer detected."""
    if not active_keys:
        return 0
    placeholders = ",".join(["%s"] * len(active_keys))
    with get_db() as (conn, cur):
        cur.execute(
            f"""
            DELETE FROM recurring_merchants
            WHERE user_id = %s AND account_id = %s
              AND merchant_key NOT IN ({placeholders})
            """,
            [user_id, account_id] + active_keys,
        )
        return cur.rowcount


def find_distinct_user_ids() -> list:
    """All user IDs that have transactions. Used by batch jobs."""
    with get_db() as (conn, cur):
        cur.execute("SELECT DISTINCT user_id FROM transactions")
        return [row[0] for row in cur.fetchall()]
