"""
TimeRangeReport model — SQL operations for the time_range_reports table.

Handles:
  • Generic date-range aggregation (week, month, rolling, custom)
  • Cached report lookup / idempotent upsert
  • Previous-period comparison data

Architecture note:
  All aggregation runs inside a single get_db() context (5 queries,
  1 connection) to avoid N+1. The composite index on
  transactions(user_id, date) accelerates every range scan.
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
    """Convert a raw DB row tuple to a clean dictionary."""
    return {
        "id": row[0],
        "user_id": row[1],
        "account_id": row[2],
        "start_date": str(row[3]),
        "end_date": str(row[4]),
        "granularity": row[5],
        "total_spent": float(row[6]) if row[6] else 0.0,
        "total_income": float(row[7]) if row[7] else 0.0,
        "net_change": float(row[8]) if row[8] else 0.0,
        "top_merchants": row[9] if isinstance(row[9], list) else [],
        "top_categories": row[10] if isinstance(row[10], list) else [],
        "volatility_score": float(row[11]) if row[11] is not None else 0.0,
        "period_change": float(row[12]) if row[12] is not None else 0.0,
        "explanation": row[13] if isinstance(row[13], dict) else {},
        "created_at": str(row[14]),
    }


_SELECT_COLS = """
    id, user_id, account_id, start_date, end_date, granularity,
    total_spent, total_income, net_change,
    top_merchants, top_categories, volatility_score,
    period_change, explanation_json, created_at
"""


# ──────────────────────────────────────────────
# Aggregation (read-only, single connection)
# ──────────────────────────────────────────────

def aggregate_range_data(user_id: int, account_id: str,
                         start_date: str, end_date: str,
                         prev_start: str, prev_end: str) -> dict:
    """
    Run all aggregation queries for an arbitrary date range
    within a single DB connection.

    Returns:
        {
            "total_spent": float,
            "total_income": float,
            "net_change": float,
            "prev_period_spent": float,
            "top_merchants": [{"name": str, "amount": float}, ...],
            "top_categories": [{"name": str, "amount": float}, ...],
            "daily_spending": {"YYYY-MM-DD": float, ...},
            "transaction_count": int,
        }
    """
    acct_clause, acct_params = _account_filter(account_id)

    with get_db() as (conn, cur):
        # ── 1. Current period totals ──
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
            [user_id, start_date, end_date] + acct_params,
        )
        row = cur.fetchone()
        total_spent, total_income, net_change, txn_count = row

        # ── 2. Previous period total spending (for comparison) ──
        cur.execute(
            f"""
            SELECT COALESCE(SUM(ABS(amount)), 0)
            FROM transactions
            WHERE user_id = %s AND date >= %s AND date <= %s AND amount < 0
            {acct_clause}
            """,
            [user_id, prev_start, prev_end] + acct_params,
        )
        prev_period_spent = cur.fetchone()[0]

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
            [user_id, start_date, end_date] + acct_params,
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
            [user_id, start_date, end_date] + acct_params,
        )
        top_categories = [
            {"name": r[0], "amount": float(r[1])}
            for r in cur.fetchall()
        ]

        # ── 5. Daily spending totals (for volatility) ──
        cur.execute(
            f"""
            SELECT date, COALESCE(SUM(ABS(amount)), 0) AS daily_total
            FROM transactions
            WHERE user_id = %s AND date >= %s AND date <= %s AND amount < 0
            {acct_clause}
            GROUP BY date
            ORDER BY date
            """,
            [user_id, start_date, end_date] + acct_params,
        )
        daily_spending = {
            str(r[0]): float(r[1])
            for r in cur.fetchall()
        }

    return {
        "total_spent": float(total_spent),
        "total_income": float(total_income),
        "net_change": float(net_change),
        "prev_period_spent": float(prev_period_spent),
        "top_merchants": top_merchants,
        "top_categories": top_categories,
        "daily_spending": daily_spending,
        "transaction_count": txn_count,
    }


# ──────────────────────────────────────────────
# Report CRUD
# ──────────────────────────────────────────────

def find_report(user_id: int, account_id: str,
                start_date: str, end_date: str):
    """Find a cached report by user + account + date range. Returns dict or None."""
    with get_db() as (conn, cur):
        cur.execute(
            f"""
            SELECT {_SELECT_COLS}
            FROM time_range_reports
            WHERE user_id = %s AND account_id = %s
                  AND start_date = %s AND end_date = %s
            """,
            (user_id, account_id, start_date, end_date),
        )
        row = cur.fetchone()

    return _row_to_dict(row) if row else None


def upsert_report(user_id: int, account_id: str,
                  start_date: str, end_date: str, granularity: str,
                  total_spent: float, total_income: float,
                  net_change: float, top_merchants: list,
                  top_categories: list, volatility_score: float,
                  period_change: float,
                  explanation_json: dict) -> int:
    """
    Insert or update a time-range report (idempotent).
    Uses ON CONFLICT on (user_id, account_id, start_date, end_date).
    Returns the report ID.
    """
    with get_db() as (conn, cur):
        cur.execute(
            """
            INSERT INTO time_range_reports
                (user_id, account_id, start_date, end_date, granularity,
                 total_spent, total_income, net_change,
                 top_merchants, top_categories,
                 volatility_score, period_change,
                 explanation_json, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT ON CONSTRAINT uq_time_range_reports_user_dates
            DO UPDATE SET
                granularity      = EXCLUDED.granularity,
                total_spent      = EXCLUDED.total_spent,
                total_income     = EXCLUDED.total_income,
                net_change       = EXCLUDED.net_change,
                top_merchants    = EXCLUDED.top_merchants,
                top_categories   = EXCLUDED.top_categories,
                volatility_score = EXCLUDED.volatility_score,
                period_change    = EXCLUDED.period_change,
                explanation_json = EXCLUDED.explanation_json,
                created_at       = NOW()
            RETURNING id
            """,
            (user_id, account_id, start_date, end_date, granularity,
             total_spent, total_income, net_change,
             json.dumps(top_merchants), json.dumps(top_categories),
             volatility_score, period_change,
             json.dumps(explanation_json)),
        )
        return cur.fetchone()[0]


def find_distinct_user_ids() -> list:
    """Return all user IDs that have at least one transaction. Used by batch jobs."""
    with get_db() as (conn, cur):
        cur.execute("SELECT DISTINCT user_id FROM transactions")
        return [row[0] for row in cur.fetchall()]
