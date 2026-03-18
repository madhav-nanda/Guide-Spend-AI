"""
Cash flow forecast service — deterministic daily-balance projection.

Algorithm:
  For each day in [today..today+horizon]:
    balance = prev_balance
              + expected_income(day)
              - expected_spend(day)
              - subscriptions_due(day)

  Track min_projected_balance throughout the horizon.

Risk score (0–100):
  - High risk (70–100): min_projected_balance < 0  (overdraft likely)
  - Medium risk (40–69): min_projected_balance < threshold ($50)
  - Low risk (0–39): healthy projected balance
  - Volatility factor adds up to 15 points

Design: deterministic, explainable, idempotent. No ML.
"""
import time
from datetime import date, timedelta

from models import cashflow_forecast as cf_model
from models import recurring_merchant as rm_model
from utils.errors import ValidationError
from utils.logger import get_logger

log = get_logger("cashflow_service")

# ═══════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════

VALID_HORIZONS = (7, 14, 30)
OVERDRAFT_THRESHOLD = 50.0     # Balance below this = medium risk
LOOKBACK_SPEND_DAYS = 30       # Days to average daily spending
LOOKBACK_INCOME_DAYS = 60      # Days to average daily income
MIN_CONFIDENCE_FOR_SUBS = 50   # Min subscription confidence for projection


# ═══════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════

def get_forecast(user_id: int, account_id: str = "all",
                 horizon_days: int = 7,
                 starting_balance: float = None) -> dict:
    """
    Generate (or return cached) a cash flow forecast.

    Args:
        user_id: Authenticated user
        account_id: plaid_account_id or "all"
        horizon_days: 7, 14, or 30
        starting_balance: Current balance (from Plaid); None = use 0

    Returns:
        Full forecast dict matching the cashflow_forecasts schema.
    """
    if horizon_days not in VALID_HORIZONS:
        raise ValidationError(f"horizon_days must be one of {VALID_HORIZONS}")

    account_id = account_id if account_id and account_id != "all" else "all"
    today_str = str(date.today())

    # ── Try cache first ──
    try:
        cached = cf_model.find_forecast(user_id, account_id, today_str, horizon_days)
        if cached:
            log.info("Returning cached forecast",
                     extra={"context": {"user_id": user_id, "horizon": horizon_days}})
            return cached
    except Exception:
        log.warning("Cache lookup failed, regenerating",
                    extra={"context": {"user_id": user_id}})

    # ── Compute fresh forecast ──
    t0 = time.monotonic()

    balance = starting_balance if starting_balance is not None else 0.0
    daily_spend = cf_model.fetch_daily_spending_avg(
        user_id, account_id, LOOKBACK_SPEND_DAYS
    )
    daily_income = cf_model.fetch_daily_income_avg(
        user_id, account_id, LOOKBACK_INCOME_DAYS
    )
    volatility = cf_model.fetch_spend_volatility(
        user_id, account_id, LOOKBACK_SPEND_DAYS
    )

    # ── Fetch upcoming subscriptions ──
    upcoming_subs = _get_subscription_schedule(
        user_id, account_id, horizon_days
    )
    # Build a day→total_subs map
    sub_by_day = {}
    for sub in upcoming_subs:
        sub_by_day.setdefault(sub["expected_date"], 0)
        sub_by_day[sub["expected_date"]] += sub["amount"]

    # ── Project day by day ──
    projected = []
    running_balance = balance
    min_balance = balance
    min_balance_date = today_str

    for day_offset in range(horizon_days):
        d = date.today() + timedelta(days=day_offset)
        d_str = str(d)

        # Income for this day
        income_today = daily_income

        # Spending for this day (baseline + subscriptions)
        subs_today = sub_by_day.get(d_str, 0)
        spend_today = daily_spend + subs_today

        running_balance = running_balance + income_today - spend_today

        projected.append({
            "date": d_str,
            "projected_balance": round(running_balance, 2),
            "income": round(income_today, 2),
            "spend": round(spend_today, 2),
            "subscriptions": round(subs_today, 2),
        })

        if running_balance < min_balance:
            min_balance = running_balance
            min_balance_date = d_str

    end_balance = running_balance

    # ── Compute risk score ──
    risk_score = _compute_risk_score(min_balance, volatility)

    # ── Build explanation ──
    risk_level = (
        "high" if risk_score >= 70
        else "medium" if risk_score >= 40
        else "low"
    )

    drivers = {
        "daily_spend_avg": round(daily_spend, 2),
        "daily_income_avg": round(daily_income, 2),
        "volatility": round(volatility, 2),
        "upcoming_subscriptions": upcoming_subs,
        "subscription_total": round(sum(s["amount"] for s in upcoming_subs), 2),
    }

    explanation = {
        "risk_level": risk_level,
        "min_balance_date": min_balance_date,
        "summary": _build_summary(
            risk_level, min_balance, end_balance, daily_spend,
            upcoming_subs, horizon_days
        ),
        "risk_rationale": _risk_rationale(risk_score, min_balance, volatility),
    }

    # ── Persist ──
    try:
        cf_model.upsert_forecast(
            user_id=user_id,
            account_id=account_id,
            as_of_date=today_str,
            horizon_days=horizon_days,
            starting_balance=round(balance, 2),
            projected_end_balance=round(end_balance, 2),
            min_projected_balance=round(min_balance, 2),
            risk_score=round(risk_score, 2),
            projected_daily_balances=projected,
            drivers_json=drivers,
            explanation_json=explanation,
        )
    except Exception:
        log.warning("Failed to persist forecast, returning computed result",
                    extra={"context": {"user_id": user_id}})

    elapsed = round((time.monotonic() - t0) * 1000, 1)

    log.info("Forecast computed",
             extra={"context": {
                 "user_id": user_id,
                 "horizon": horizon_days,
                 "risk_score": round(risk_score, 2),
                 "elapsed_ms": elapsed,
             }})

    return {
        "user_id": user_id,
        "account_id": account_id,
        "as_of_date": today_str,
        "horizon_days": horizon_days,
        "starting_balance": round(balance, 2),
        "projected_end_balance": round(end_balance, 2),
        "min_projected_balance": round(min_balance, 2),
        "risk_score": round(risk_score, 2),
        "projected_daily_balances": projected,
        "drivers_json": drivers,
        "explanation_json": explanation,
    }


# ═══════════════════════════════════════════════════
# Risk Score
# ═══════════════════════════════════════════════════

def _compute_risk_score(min_balance: float, volatility: float) -> float:
    """
    Compute overdraft risk score (0–100).

    Components:
      - Balance risk (0–85): Based on min projected balance
      - Volatility bonus (0–15): Higher volatility = higher risk
    """
    # Balance risk
    if min_balance < 0:
        # Negative balance → 70–85 range based on severity
        severity = min(abs(min_balance) / 500, 1.0)  # normalize to 500
        balance_risk = 70 + severity * 15
    elif min_balance < OVERDRAFT_THRESHOLD:
        # Close to zero → 40–70 range
        closeness = 1 - (min_balance / OVERDRAFT_THRESHOLD)
        balance_risk = 40 + closeness * 30
    elif min_balance < 200:
        # Moderate buffer → 15–40 range
        balance_risk = 15 + (1 - min_balance / 200) * 25
    else:
        # Healthy → 0–15 range
        balance_risk = max(0, 15 - min_balance / 100)

    # Volatility bonus (0–15)
    vol_bonus = min(15, volatility / 100 * 15)

    return min(100, max(0, balance_risk + vol_bonus))


# ═══════════════════════════════════════════════════
# Subscription Schedule
# ═══════════════════════════════════════════════════

def _get_subscription_schedule(user_id: int, account_id: str,
                                horizon_days: int) -> list:
    """
    Get upcoming subscription charges within the forecast horizon.
    Returns list of { merchant, amount, expected_date, cadence }.
    """
    try:
        return rm_model.find_upcoming_in_horizon(
            user_id=user_id,
            account_id=account_id,
            horizon_days=horizon_days,
            min_confidence=MIN_CONFIDENCE_FOR_SUBS,
        )
    except Exception:
        log.warning("Could not fetch subscriptions for forecast",
                    extra={"context": {"user_id": user_id}})
        return []


# ═══════════════════════════════════════════════════
# Explanation Builders
# ═══════════════════════════════════════════════════

def _build_summary(risk_level: str, min_balance: float, end_balance: float,
                   daily_spend: float, upcoming_subs: list,
                   horizon_days: int) -> str:
    """Build a human-readable forecast summary."""
    parts = []

    if risk_level == "high":
        parts.append(
            f"Your projected balance may drop below zero within the next "
            f"{horizon_days} days."
        )
    elif risk_level == "medium":
        parts.append(
            f"Your balance is projected to get low (under ${OVERDRAFT_THRESHOLD:.0f}) "
            f"within the next {horizon_days} days."
        )
    else:
        parts.append(
            f"Your cash flow looks healthy over the next {horizon_days} days."
        )

    parts.append(
        f"Based on your recent spending of ~${daily_spend:.0f}/day."
    )

    if upcoming_subs:
        total_subs = sum(s["amount"] for s in upcoming_subs)
        parts.append(
            f"{len(upcoming_subs)} upcoming subscription charge(s) "
            f"totaling ${total_subs:.2f} are factored in."
        )

    return " ".join(parts)


def _risk_rationale(risk_score: float, min_balance: float,
                    volatility: float) -> str:
    """Human-readable explanation of the risk score."""
    parts = []

    if min_balance < 0:
        parts.append(f"Projected overdraft of ${abs(min_balance):.2f}")
    elif min_balance < OVERDRAFT_THRESHOLD:
        parts.append(f"Balance may drop to ${min_balance:.2f}")
    else:
        parts.append(f"Lowest projected balance is ${min_balance:.2f}")

    if volatility > 60:
        parts.append("with high spending variability")
    elif volatility > 30:
        parts.append("with moderate spending variability")
    else:
        parts.append("with stable spending patterns")

    return ". ".join(parts) + "."
