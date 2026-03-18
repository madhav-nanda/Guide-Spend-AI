"""
WeeklyReport model — all SQL operations for the weekly_reports table.
Handles aggregation queries and report persistence.

Architecture note:
  All aggregation runs inside a single get_db() context to avoid
  N+1 queries. Five queries share one connection from the pool.
"""
import json
from utils.db import get_db


# ──────────────────────────────────────────────
# Private Helpers
# ──────────────────────────────────────────────

def _account_filter(account_id: str):
    """Build optional account filter clause and params for transactions table."""
    if account_id and account_id != "all":
        return " AND plaid_account_id = %s", [account_id]
    return "", []


def _row_to_dict(row) -> dict:
    """Convert a raw DB row tuple to a clean dictionary."""
    return {
        "id": row[0],
        "user_id": row[1],
        "account_id": row[2],
        "week_start": str(row[3]),
        "week_end": str(row[4]),
        "total_spent": float(row[5]) if row[5] else 0.0,
        "total_income": float(row[6]) if row[6] else 0.0,
        "net_change": float(row[7]) if row[7] else 0.0,
        "top_merchants": row[8] if isinstance(row[8], list) else [],
        "top_categories": row[9] if isinstance(row[9], list) else [],
        "week_over_week_change": float(row[10]) if row[10] is not None else None,
        "volatility_score": float(row[11]) if row[11] is not None else 0.0,
        "explanation": row[12] if isinstance(row[12], dict) else {},
        "created_at": str(row[13]),
        "updated_at": str(row[14]),
    }


# ──────────────────────────────────────────────
# Aggregation (read-only, single connection)
# ──────────────────────────────────────────────

def aggregate_week_data(user_id: int, account_id: str,
                        week_start: str, week_end: str,
                        prev_week_start: str, prev_week_end: str) -> dict:
    """
    Run all aggregation queries for a week within a single DB connection.

    Returns:
        {
            "total_spent": float,
            "total_income": float,
            "net_change": float,
            "prev_week_spent": float,
            "top_merchants": [{"name": str, "amount": float}, ...],
            "top_categories": [{"name": str, "amount": float}, ...],
            "daily_spending": {"YYYY-MM-DD": float, ...},
            "transaction_count": int,
        }
    """
    acct_clause, acct_params = _account_filter(account_id)

    with get_db() as (conn, cur):
        # ── 1. Current week totals ──
        cur.execute(
            f"""
            SELECT
                COALESCE(SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END), 0),
                COALESCE(SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END), 0),
                COALESCE(SUM(amount), 0),
                COUNT(*)
            FROM transactions
            WHERE user_id = %s AND date >= %s AND date <= %s
            {acct_clause}
            """,
            [user_id, week_start, week_end] + acct_params,
        )
        row = cur.fetchone()
        total_spent = row[0]
        total_income = row[1]
        net_change = row[2]
        txn_count = row[3]

        # ── 2. Previous week total spending (for WoW comparison) ──
        cur.execute(
            f"""
            SELECT COALESCE(SUM(ABS(amount)), 0)
            FROM transactions
            WHERE user_id = %s AND date >= %s AND date <= %s AND amount < 0
            {acct_clause}
            """,
            [user_id, prev_week_start, prev_week_end] + acct_params,
        )
        prev_week_spent = cur.fetchone()[0]

        # ── 3. Top 5 merchants by spend ──
        cur.execute(
            f"""
            SELECT description, ROUND(SUM(ABS(amount))::numeric, 2) AS total
            FROM transactions
            WHERE user_id = %s AND date >= %s AND date <= %s AND amount < 0
            {acct_clause}
            GROUP BY description
            ORDER BY total DESC
            LIMIT 5
            """,
            [user_id, week_start, week_end] + acct_params,
        )
        top_merchants = [
            {"name": r[0], "amount": float(r[1])}
            for r in cur.fetchall()
        ]

        # ── 4. Top 5 categories by spend ──
        cur.execute(
            f"""
            SELECT category, ROUND(SUM(ABS(amount))::numeric, 2) AS total
            FROM transactions
            WHERE user_id = %s AND date >= %s AND date <= %s AND amount < 0
            {acct_clause}
            GROUP BY category
            ORDER BY total DESC
            LIMIT 5
            """,
            [user_id, week_start, week_end] + acct_params,
        )
        top_categories = [
            {"name": r[0], "amount": float(r[1])}
            for r in cur.fetchall()
        ]

        # ── 5. Daily spending totals (for volatility calculation) ──
        cur.execute(
            f"""
            SELECT date, COALESCE(SUM(ABS(amount)), 0) AS daily_total
            FROM transactions
            WHERE user_id = %s AND date >= %s AND date <= %s AND amount < 0
            {acct_clause}
            GROUP BY date
            ORDER BY date
            """,
            [user_id, week_start, week_end] + acct_params,
        )
        daily_spending = {
            str(r[0]): float(r[1])
            for r in cur.fetchall()
        }

    return {
        "total_spent": float(total_spent),
        "total_income": float(total_income),
        "net_change": float(net_change),
        "prev_week_spent": float(prev_week_spent),
        "top_merchants": top_merchants,
        "top_categories": top_categories,
        "daily_spending": daily_spending,
        "transaction_count": txn_count,
    }


# ──────────────────────────────────────────────
# Report CRUD
# ──────────────────────────────────────────────

def find_report(user_id: int, account_id: str, week_start: str):
    """Find an existing weekly report by user + account + week. Returns dict or None."""
    with get_db() as (conn, cur):
        cur.execute(
            """
            SELECT id, user_id, account_id, week_start, week_end,
                   total_spent, total_income, net_change,
                   top_merchants, top_categories,
                   week_over_week_change, volatility_score,
                   explanation_json, created_at, updated_at
            FROM weekly_reports
            WHERE user_id = %s AND account_id = %s AND week_start = %s
            """,
            (user_id, account_id, week_start),
        )
        row = cur.fetchone()

    if not row:
        return None
    return _row_to_dict(row)


def find_latest(user_id: int, account_id: str):
    """Find the most recent weekly report for a user + account. Returns dict or None."""
    with get_db() as (conn, cur):
        cur.execute(
            """
            SELECT id, user_id, account_id, week_start, week_end,
                   total_spent, total_income, net_change,
                   top_merchants, top_categories,
                   week_over_week_change, volatility_score,
                   explanation_json, created_at, updated_at
            FROM weekly_reports
            WHERE user_id = %s AND account_id = %s
            ORDER BY week_start DESC
            LIMIT 1
            """,
            (user_id, account_id),
        )
        row = cur.fetchone()

    if not row:
        return None
    return _row_to_dict(row)


def upsert_report(user_id: int, account_id: str, week_start: str,
                  week_end: str, total_spent: float, total_income: float,
                  net_change: float, top_merchants: list, top_categories: list,
                  week_over_week_change: float, volatility_score: float,
                  explanation_json: dict) -> int:
    """
    Insert or update a weekly report (idempotent).
    Uses ON CONFLICT on the (user_id, account_id, week_start) unique constraint.
    Returns the report ID.
    """
    with get_db() as (conn, cur):
        cur.execute(
            """
            INSERT INTO weekly_reports
                (user_id, account_id, week_start, week_end,
                 total_spent, total_income, net_change,
                 top_merchants, top_categories,
                 week_over_week_change, volatility_score,
                 explanation_json, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            ON CONFLICT ON CONSTRAINT uq_weekly_reports_user_account_week
            DO UPDATE SET
                week_end              = EXCLUDED.week_end,
                total_spent           = EXCLUDED.total_spent,
                total_income          = EXCLUDED.total_income,
                net_change            = EXCLUDED.net_change,
                top_merchants         = EXCLUDED.top_merchants,
                top_categories        = EXCLUDED.top_categories,
                week_over_week_change = EXCLUDED.week_over_week_change,
                volatility_score      = EXCLUDED.volatility_score,
                explanation_json      = EXCLUDED.explanation_json,
                updated_at            = NOW()
            RETURNING id
            """,
            (user_id, account_id, week_start, week_end,
             total_spent, total_income, net_change,
             json.dumps(top_merchants), json.dumps(top_categories),
             week_over_week_change, volatility_score,
             json.dumps(explanation_json)),
        )
        return cur.fetchone()[0]


def find_distinct_user_ids() -> list:
    """Return all user IDs that have at least one transaction. Used by batch jobs."""
    with get_db() as (conn, cur):
        cur.execute("SELECT DISTINCT user_id FROM transactions")
        return [row[0] for row in cur.fetchall()]
