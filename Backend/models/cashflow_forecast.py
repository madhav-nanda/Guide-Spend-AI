"""
CashflowForecast model — SQL operations for cashflow_forecasts table.

Handles:
  * Fetching recent spending/income data for projections
  * Upserting computed forecasts
  * Querying cached forecasts
"""
import json
from utils.db import get_db


def _row_to_dict(row) -> dict:
    """Convert a cashflow_forecasts row to dict."""
    return {
        "id": row[0],
        "user_id": row[1],
        "account_id": row[2],
        "as_of_date": str(row[3]),
        "horizon_days": row[4],
        "starting_balance": float(row[5]) if row[5] else 0.0,
        "projected_end_balance": float(row[6]) if row[6] else 0.0,
        "min_projected_balance": float(row[7]) if row[7] else 0.0,
        "risk_score": float(row[8]) if row[8] else 0.0,
        "projected_daily_balances": row[9] if isinstance(row[9], list) else [],
        "drivers_json": row[10] if isinstance(row[10], dict) else {},
        "explanation_json": row[11] if isinstance(row[11], dict) else {},
        "created_at": str(row[12]),
    }


_SELECT_COLS = """
    id, user_id, account_id, as_of_date, horizon_days,
    starting_balance, projected_end_balance, min_projected_balance,
    risk_score, projected_daily_balances, drivers_json,
    explanation_json, created_at
"""


# ──────────────────────────────────────────────
# Data queries for forecast computation
# ──────────────────────────────────────────────

def fetch_daily_spending_avg(user_id: int, account_id: str,
                              lookback_days: int = 30) -> float:
    """Average daily spending over the lookback period (excludes transfers)."""
    acct_clause, acct_params = _account_filter(account_id)

    with get_db() as (conn, cur):
        cur.execute(
            f"""
            SELECT COALESCE(SUM(ABS(amount)), 0)
            FROM transactions
            WHERE user_id = %s
              AND amount < 0
              AND date >= CURRENT_DATE - INTERVAL '{int(lookback_days)} days'
              AND COALESCE(category, '') NOT ILIKE '%%transfer%%'
              {acct_clause}
            """,
            [user_id] + acct_params,
        )
        total = float(cur.fetchone()[0])

    return round(total / max(lookback_days, 1), 2)


def fetch_daily_income_avg(user_id: int, account_id: str,
                            lookback_days: int = 60) -> float:
    """Average daily income over the lookback period."""
    acct_clause, acct_params = _account_filter(account_id)

    with get_db() as (conn, cur):
        cur.execute(
            f"""
            SELECT COALESCE(SUM(amount), 0)
            FROM transactions
            WHERE user_id = %s
              AND amount > 0
              AND date >= CURRENT_DATE - INTERVAL '{int(lookback_days)} days'
              {acct_clause}
            """,
            [user_id] + acct_params,
        )
        total = float(cur.fetchone()[0])

    return round(total / max(lookback_days, 1), 2)


def fetch_spend_volatility(user_id: int, account_id: str,
                            lookback_days: int = 30) -> float:
    """Coefficient of variation for daily spending (0-100 scale)."""
    acct_clause, acct_params = _account_filter(account_id)

    with get_db() as (conn, cur):
        cur.execute(
            f"""
            SELECT date, COALESCE(SUM(ABS(amount)), 0) as daily_total
            FROM transactions
            WHERE user_id = %s
              AND amount < 0
              AND date >= CURRENT_DATE - INTERVAL '{int(lookback_days)} days'
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

    import math
    variance = sum((x - mean) ** 2 for x in daily_totals) / len(daily_totals)
    cv = (math.sqrt(variance) / mean) * 100
    return round(min(cv, 100.0), 2)


# ──────────────────────────────────────────────
# CRUD
# ──────────────────────────────────────────────

def find_forecast(user_id: int, account_id: str,
                   as_of_date: str, horizon_days: int):
    """Find a cached forecast. Returns dict or None."""
    with get_db() as (conn, cur):
        cur.execute(
            f"""
            SELECT {_SELECT_COLS}
            FROM cashflow_forecasts
            WHERE user_id = %s AND account_id = %s
              AND as_of_date = %s AND horizon_days = %s
            """,
            (user_id, account_id, as_of_date, horizon_days),
        )
        row = cur.fetchone()
    return _row_to_dict(row) if row else None


def upsert_forecast(user_id: int, account_id: str, as_of_date: str,
                     horizon_days: int, starting_balance: float,
                     projected_end_balance: float, min_projected_balance: float,
                     risk_score: float, projected_daily_balances: list,
                     drivers_json: dict, explanation_json: dict) -> int:
    """Upsert a cashflow forecast. Returns ID."""
    with get_db() as (conn, cur):
        cur.execute(
            """
            INSERT INTO cashflow_forecasts
                (user_id, account_id, as_of_date, horizon_days,
                 starting_balance, projected_end_balance, min_projected_balance,
                 risk_score, projected_daily_balances, drivers_json,
                 explanation_json, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT ON CONSTRAINT uq_cashflow_user_date_horizon
            DO UPDATE SET
                starting_balance         = EXCLUDED.starting_balance,
                projected_end_balance    = EXCLUDED.projected_end_balance,
                min_projected_balance    = EXCLUDED.min_projected_balance,
                risk_score               = EXCLUDED.risk_score,
                projected_daily_balances = EXCLUDED.projected_daily_balances,
                drivers_json             = EXCLUDED.drivers_json,
                explanation_json         = EXCLUDED.explanation_json,
                created_at               = NOW()
            RETURNING id
            """,
            (user_id, account_id, as_of_date, horizon_days,
             starting_balance, projected_end_balance, min_projected_balance,
             risk_score, json.dumps(projected_daily_balances),
             json.dumps(drivers_json), json.dumps(explanation_json)),
        )
        return cur.fetchone()[0]


def find_distinct_user_ids() -> list:
    """All user IDs with transactions. For batch jobs."""
    with get_db() as (conn, cur):
        cur.execute("SELECT DISTINCT user_id FROM transactions")
        return [row[0] for row in cur.fetchall()]


# ──────────────────────────────────────────────
# Private Helpers
# ──────────────────────────────────────────────

def _account_filter(account_id: str):
    if account_id and account_id != "all":
        return " AND plaid_account_id = %s", [account_id]
    return "", []
