"""
HealthScore model — SQL operations for health_scores table.

Handles:
  * Fetching raw financial metrics (income, spending, volatility)
  * Querying cached health scores
  * Upserting computed scores
"""
import json
import math
from utils.db import get_db


# ──────────────────────────────────────────────
# Row Mapping
# ──────────────────────────────────────────────

def _row_to_dict(row) -> dict:
    """Convert a health_scores row to dict."""
    return {
        "id": row[0],
        "user_id": row[1],
        "account_id": row[2],
        "as_of_date": str(row[3]),
        "analysis_window_days": row[4],
        "health_score": row[5],
        "savings_ratio": float(row[6]) if row[6] else 0.0,
        "volatility_score": float(row[7]) if row[7] else 0.0,
        "recurring_burden": float(row[8]) if row[8] else 0.0,
        "cash_buffer_days": float(row[9]) if row[9] else 0.0,
        "component_scores": row[10] if isinstance(row[10], dict) else {},
        "explanation_json": row[11] if isinstance(row[11], dict) else {},
        "created_at": str(row[12]),
        "updated_at": str(row[13]),
    }


_SELECT_COLS = """
    id, user_id, account_id, as_of_date, analysis_window_days,
    health_score, savings_ratio, volatility_score, recurring_burden,
    cash_buffer_days, component_scores, explanation_json,
    created_at, updated_at
"""


# ──────────────────────────────────────────────
# Data Queries for Score Computation
# ──────────────────────────────────────────────

def fetch_total_income(user_id: int, account_id: str,
                       window_days: int = 90) -> float:
    """Total income (positive amounts) over the analysis window."""
    acct_clause, acct_params = _account_filter(account_id)

    with get_db() as (conn, cur):
        cur.execute(
            f"""
            SELECT COALESCE(SUM(amount), 0)
            FROM transactions
            WHERE user_id = %s
              AND amount > 0
              AND date >= CURRENT_DATE - INTERVAL '{int(window_days)} days'
              {acct_clause}
            """,
            [user_id] + acct_params,
        )
        return float(cur.fetchone()[0])


def fetch_total_spending(user_id: int, account_id: str,
                         window_days: int = 90) -> float:
    """Total spending (absolute value of negative amounts) over the window.
    Excludes transfers."""
    acct_clause, acct_params = _account_filter(account_id)

    with get_db() as (conn, cur):
        cur.execute(
            f"""
            SELECT COALESCE(SUM(ABS(amount)), 0)
            FROM transactions
            WHERE user_id = %s
              AND amount < 0
              AND date >= CURRENT_DATE - INTERVAL '{int(window_days)} days'
              AND COALESCE(category, '') NOT ILIKE '%%transfer%%'
              {acct_clause}
            """,
            [user_id] + acct_params,
        )
        return float(cur.fetchone()[0])


def fetch_daily_spending_stddev(user_id: int, account_id: str,
                                 window_days: int = 90) -> float:
    """Standard deviation of daily spending totals over the window.
    Returns the coefficient of variation (stddev/mean) as a 0-1 ratio."""
    acct_clause, acct_params = _account_filter(account_id)

    with get_db() as (conn, cur):
        cur.execute(
            f"""
            SELECT date, COALESCE(SUM(ABS(amount)), 0) AS daily_total
            FROM transactions
            WHERE user_id = %s
              AND amount < 0
              AND date >= CURRENT_DATE - INTERVAL '{int(window_days)} days'
              AND COALESCE(category, '') NOT ILIKE '%%transfer%%'
              {acct_clause}
            GROUP BY date
            ORDER BY date
            """,
            [user_id] + acct_params,
        )
        rows = cur.fetchall()

    if len(rows) < 2:
        return 0.0

    daily_totals = [float(r[1]) for r in rows]
    mean = sum(daily_totals) / len(daily_totals)
    if mean == 0:
        return 0.0

    variance = sum((x - mean) ** 2 for x in daily_totals) / len(daily_totals)
    stddev = math.sqrt(variance)
    cv = stddev / mean  # coefficient of variation (0-∞, typically 0-2)
    return round(min(cv, 2.0), 4)  # cap at 2.0


def fetch_daily_spending_avg(user_id: int, account_id: str,
                              window_days: int = 30) -> float:
    """Average daily spending over the lookback period."""
    acct_clause, acct_params = _account_filter(account_id)

    with get_db() as (conn, cur):
        cur.execute(
            f"""
            SELECT COALESCE(SUM(ABS(amount)), 0)
            FROM transactions
            WHERE user_id = %s
              AND amount < 0
              AND date >= CURRENT_DATE - INTERVAL '{int(window_days)} days'
              AND COALESCE(category, '') NOT ILIKE '%%transfer%%'
              {acct_clause}
            """,
            [user_id] + acct_params,
        )
        total = float(cur.fetchone()[0])

    return round(total / max(window_days, 1), 2)


def fetch_monthly_recurring_total(user_id: int, account_id: str) -> float:
    """Sum of avg_amount from detected recurring merchants, normalized to monthly.
    Uses the recurring_merchants table from the subscription engine."""
    acct_clause = ""
    acct_params = []
    if account_id and account_id != "all":
        acct_clause = " AND account_id = %s"
        acct_params = [account_id]

    with get_db() as (conn, cur):
        cur.execute(
            f"""
            SELECT cadence, avg_amount
            FROM recurring_merchants
            WHERE user_id = %s
              AND confidence_score >= 40
              {acct_clause}
            """,
            [user_id] + acct_params,
        )
        rows = cur.fetchall()

    monthly_total = 0.0
    for cadence, avg_amount in rows:
        amt = float(avg_amount) if avg_amount else 0.0
        if cadence == "weekly":
            monthly_total += amt * 4.33
        elif cadence == "biweekly":
            monthly_total += amt * 2.17
        elif cadence == "monthly":
            monthly_total += amt
        elif cadence == "quarterly":
            monthly_total += amt / 3.0
        else:
            monthly_total += amt  # assume monthly

    return round(monthly_total, 2)


def fetch_transaction_count(user_id: int, account_id: str,
                             window_days: int = 90) -> int:
    """Count of transactions in the analysis window."""
    acct_clause, acct_params = _account_filter(account_id)

    with get_db() as (conn, cur):
        cur.execute(
            f"""
            SELECT COUNT(*)
            FROM transactions
            WHERE user_id = %s
              AND date >= CURRENT_DATE - INTERVAL '{int(window_days)} days'
              {acct_clause}
            """,
            [user_id] + acct_params,
        )
        return cur.fetchone()[0]


# ──────────────────────────────────────────────
# CRUD
# ──────────────────────────────────────────────

def find_score(user_id: int, account_id: str,
               as_of_date: str, window_days: int):
    """Find a cached health score. Returns dict or None."""
    with get_db() as (conn, cur):
        cur.execute(
            f"""
            SELECT {_SELECT_COLS}
            FROM health_scores
            WHERE user_id = %s AND account_id = %s
              AND as_of_date = %s AND analysis_window_days = %s
            """,
            (user_id, account_id, as_of_date, window_days),
        )
        row = cur.fetchone()
    return _row_to_dict(row) if row else None


def upsert_score(user_id: int, account_id: str, as_of_date: str,
                  analysis_window_days: int, health_score: int,
                  savings_ratio: float, volatility_score: float,
                  recurring_burden: float, cash_buffer_days: float,
                  component_scores: dict, explanation_json: dict) -> int:
    """Upsert a health score. Returns ID."""
    with get_db() as (conn, cur):
        cur.execute(
            """
            INSERT INTO health_scores
                (user_id, account_id, as_of_date, analysis_window_days,
                 health_score, savings_ratio, volatility_score,
                 recurring_burden, cash_buffer_days,
                 component_scores, explanation_json,
                 created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            ON CONFLICT ON CONSTRAINT uq_health_score_user_date_window
            DO UPDATE SET
                health_score       = EXCLUDED.health_score,
                savings_ratio      = EXCLUDED.savings_ratio,
                volatility_score   = EXCLUDED.volatility_score,
                recurring_burden   = EXCLUDED.recurring_burden,
                cash_buffer_days   = EXCLUDED.cash_buffer_days,
                component_scores   = EXCLUDED.component_scores,
                explanation_json   = EXCLUDED.explanation_json,
                updated_at         = NOW()
            RETURNING id
            """,
            (user_id, account_id, as_of_date, analysis_window_days,
             health_score, savings_ratio, volatility_score,
             recurring_burden, cash_buffer_days,
             json.dumps(component_scores), json.dumps(explanation_json)),
        )
        return cur.fetchone()[0]


# ──────────────────────────────────────────────
# Private Helpers
# ──────────────────────────────────────────────

def _account_filter(account_id: str):
    if account_id and account_id != "all":
        return " AND plaid_account_id = %s", [account_id]
    return "", []
