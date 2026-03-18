"""
Financial Health Score service — enterprise-grade scoring engine.

Computes a composite Financial Health Score (0-100) from four metrics:
  1. Savings Ratio        (weight 30%) — income vs. spending discipline
  2. Spending Volatility  (weight 20%) — consistency of spending behavior
  3. Recurring Burden     (weight 20%) — subscription load vs. income
  4. Cash Buffer Days     (weight 30%) — runway based on current balance

Algorithm: deterministic, explainable, idempotent. No ML.
Caching: returns same-day cached result if available.
Edge cases: safe defaults for zero income, new accounts, missing data.
"""
import time
from datetime import date

from models import health_score as hs_model
from utils.errors import ValidationError
from utils.logger import get_logger

log = get_logger("health_score_service")

# ═══════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════

VALID_WINDOWS = (30, 60, 90)
MIN_TRANSACTIONS = 5  # Minimum data points for meaningful score

WEIGHTS = {
    "savings":       0.30,
    "volatility":    0.20,
    "subscriptions": 0.20,
    "cash_buffer":   0.30,
}


# ═══════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════

def get_health_score(user_id: int, account_id: str = "all",
                     window_days: int = 90,
                     current_balance: float = None) -> dict:
    """
    Compute (or return cached) the Financial Health Score.

    Args:
        user_id: Authenticated user
        account_id: plaid_account_id or "all"
        window_days: Analysis window (30, 60, or 90 days)
        current_balance: Real-time balance from Plaid (optional)

    Returns:
        Full health score dict matching the API response spec.
    """
    if window_days not in VALID_WINDOWS:
        raise ValidationError(f"window_days must be one of {VALID_WINDOWS}")

    account_id = account_id if account_id and account_id != "all" else "all"
    today_str = str(date.today())

    # ── Try cache first ──
    try:
        cached = hs_model.find_score(user_id, account_id, today_str, window_days)
        if cached:
            log.info("Returning cached health score",
                     extra={"context": {"user_id": user_id, "score": cached["health_score"]}})
            return _format_response(cached)
    except Exception:
        log.warning("Cache lookup failed, recomputing",
                    extra={"context": {"user_id": user_id}})

    # ── Compute fresh score ──
    t0 = time.monotonic()

    # 1. Fetch raw metrics
    total_income = hs_model.fetch_total_income(user_id, account_id, window_days)
    total_spending = hs_model.fetch_total_spending(user_id, account_id, window_days)
    volatility_cv = hs_model.fetch_daily_spending_stddev(user_id, account_id, window_days)
    monthly_recurring = hs_model.fetch_monthly_recurring_total(user_id, account_id)
    daily_spend_avg = hs_model.fetch_daily_spending_avg(user_id, account_id, min(window_days, 30))
    txn_count = hs_model.fetch_transaction_count(user_id, account_id, window_days)

    balance = current_balance if current_balance is not None else 0.0

    # 2. Compute derived metrics
    savings_ratio = _compute_savings_ratio(total_income, total_spending)
    monthly_income = total_income / max(window_days / 30, 1)
    recurring_burden = _compute_recurring_burden(monthly_recurring, monthly_income)
    cash_buffer_days = _compute_cash_buffer_days(balance, daily_spend_avg)

    # 3. Compute component scores (each 0-100)
    savings_score = _score_savings_ratio(savings_ratio)
    volatility_score = _score_volatility(volatility_cv)
    subscription_score = _score_recurring_burden(recurring_burden)
    buffer_score = _score_cash_buffer(cash_buffer_days)

    # 4. Weighted final score
    raw_score = (
        WEIGHTS["savings"] * savings_score
        + WEIGHTS["volatility"] * volatility_score
        + WEIGHTS["subscriptions"] * subscription_score
        + WEIGHTS["cash_buffer"] * buffer_score
    )
    health_score = int(round(max(0, min(100, raw_score))))

    # 5. Insufficient data check
    has_enough_data = txn_count >= MIN_TRANSACTIONS

    # 6. Build component scores dict
    component_scores = {
        "savings": round(savings_score),
        "volatility": round(volatility_score),
        "subscriptions": round(subscription_score),
        "cash_buffer": round(buffer_score),
    }

    # 7. Build explanation
    explanation = _build_explanation(
        health_score=health_score,
        savings_ratio=savings_ratio,
        savings_score=savings_score,
        volatility_cv=volatility_cv,
        volatility_score=volatility_score,
        recurring_burden=recurring_burden,
        subscription_score=subscription_score,
        cash_buffer_days=cash_buffer_days,
        buffer_score=buffer_score,
        has_enough_data=has_enough_data,
        window_days=window_days,
    )

    # 8. Persist
    try:
        hs_model.upsert_score(
            user_id=user_id,
            account_id=account_id,
            as_of_date=today_str,
            analysis_window_days=window_days,
            health_score=health_score,
            savings_ratio=round(savings_ratio, 4),
            volatility_score=round(volatility_cv, 4),
            recurring_burden=round(recurring_burden, 4),
            cash_buffer_days=round(cash_buffer_days, 2),
            component_scores=component_scores,
            explanation_json=explanation,
        )
    except Exception:
        log.warning("Failed to persist health score, returning computed result",
                    extra={"context": {"user_id": user_id}})

    elapsed = round((time.monotonic() - t0) * 1000, 1)

    log.info("Health score computed",
             extra={"context": {
                 "user_id": user_id,
                 "health_score": health_score,
                 "window_days": window_days,
                 "elapsed_ms": elapsed,
             }})

    return {
        "health_score": health_score,
        "analysis_period": f"Last {window_days} days",
        "as_of_date": today_str,
        "has_enough_data": has_enough_data,
        "metrics": {
            "savings_ratio": round(savings_ratio, 4),
            "cash_buffer_days": round(cash_buffer_days, 1),
            "recurring_burden": round(recurring_burden, 4),
            "spending_volatility": round(volatility_cv, 4),
        },
        "component_scores": component_scores,
        "explanation": explanation,
    }


# ═══════════════════════════════════════════════════
# Metric Computation
# ═══════════════════════════════════════════════════

def _compute_savings_ratio(total_income: float, total_spending: float) -> float:
    """Savings Ratio = (income - spending) / income. Safe for zero income."""
    if total_income <= 0:
        return -1.0 if total_spending > 0 else 0.0
    return (total_income - total_spending) / total_income


def _compute_recurring_burden(monthly_recurring: float,
                                monthly_income: float) -> float:
    """Recurring Burden = monthly subscriptions / monthly income."""
    if monthly_income <= 0:
        return 1.0 if monthly_recurring > 0 else 0.0
    return monthly_recurring / monthly_income


def _compute_cash_buffer_days(balance: float,
                                daily_spend_avg: float) -> float:
    """Cash Buffer Days = current balance / avg daily spend."""
    if daily_spend_avg <= 0:
        return 999.0 if balance > 0 else 0.0
    return balance / daily_spend_avg


# ═══════════════════════════════════════════════════
# Component Scoring (each returns 0-100)
# ═══════════════════════════════════════════════════

def _score_savings_ratio(ratio: float) -> float:
    """
    Score savings ratio on a 0-100 scale.
      >= 30%  → 100
      20-30%  → 80
      10-20%  → 60
      0-10%   → 40
      negative → 10
    Smooth interpolation within bands.
    """
    if ratio >= 0.30:
        return 100
    elif ratio >= 0.20:
        return 80 + (ratio - 0.20) / 0.10 * 20
    elif ratio >= 0.10:
        return 60 + (ratio - 0.10) / 0.10 * 20
    elif ratio >= 0:
        return 40 + ratio / 0.10 * 20
    else:
        # Negative savings: scale from 10 (barely negative) to 0 (very negative)
        return max(0, 10 + ratio * 20)


def _score_volatility(cv: float) -> float:
    """
    Score spending volatility (coefficient of variation).
    Lower volatility = better.
      CV 0.0   → 100
      CV 0.3   → 75
      CV 0.6   → 50
      CV 1.0   → 25
      CV 1.5+  → 5
    Linear interpolation.
    """
    if cv <= 0:
        return 100
    elif cv <= 0.3:
        return 100 - (cv / 0.3) * 25
    elif cv <= 0.6:
        return 75 - ((cv - 0.3) / 0.3) * 25
    elif cv <= 1.0:
        return 50 - ((cv - 0.6) / 0.4) * 25
    elif cv <= 1.5:
        return 25 - ((cv - 1.0) / 0.5) * 20
    else:
        return 5


def _score_recurring_burden(burden: float) -> float:
    """
    Score recurring subscription burden.
      <5%   → 100
      5-10% → 80
      10-20% → 60
      20-30% → 40
      >30%  → 20
    Smooth interpolation.
    """
    if burden < 0.05:
        return 100
    elif burden < 0.10:
        return 80 + (0.10 - burden) / 0.05 * 20
    elif burden < 0.20:
        return 60 + (0.20 - burden) / 0.10 * 20
    elif burden < 0.30:
        return 40 + (0.30 - burden) / 0.10 * 20
    else:
        return max(10, 20 - (burden - 0.30) / 0.20 * 10)


def _score_cash_buffer(buffer_days: float) -> float:
    """
    Score cash buffer days.
      >90 days  → 100
      60-90     → 80
      30-60     → 60
      15-30     → 40
      <15       → 20
    Smooth interpolation.
    """
    if buffer_days >= 90:
        return 100
    elif buffer_days >= 60:
        return 80 + (buffer_days - 60) / 30 * 20
    elif buffer_days >= 30:
        return 60 + (buffer_days - 30) / 30 * 20
    elif buffer_days >= 15:
        return 40 + (buffer_days - 15) / 15 * 20
    elif buffer_days > 0:
        return 20 + buffer_days / 15 * 20
    else:
        return 5


# ═══════════════════════════════════════════════════
# Explanation Generator
# ═══════════════════════════════════════════════════

def _build_explanation(health_score: int, savings_ratio: float,
                       savings_score: float, volatility_cv: float,
                       volatility_score: float, recurring_burden: float,
                       subscription_score: float, cash_buffer_days: float,
                       buffer_score: float, has_enough_data: bool,
                       window_days: int) -> dict:
    """Build human-readable explanation with strengths, risks, and suggestions."""

    # ── Overall summary ──
    if health_score >= 80:
        summary = "Your financial health is excellent. You demonstrate strong financial discipline."
    elif health_score >= 70:
        summary = "Your financial health is good. You're on a solid financial footing."
    elif health_score >= 55:
        summary = "Your financial health is fair. There are areas where you could improve."
    elif health_score >= 40:
        summary = "Your financial health needs attention. Consider the suggestions below."
    else:
        summary = "Your financial health is at risk. Immediate action is recommended."

    if not has_enough_data:
        summary += " Note: Limited transaction data available — score may improve with more history."

    # ── Strengths ──
    strengths = []
    if savings_score >= 70:
        pct = max(0, savings_ratio * 100)
        strengths.append(f"You maintain a healthy savings rate of {pct:.0f}%.")
    if volatility_score >= 70:
        strengths.append("Your spending patterns are consistent and predictable.")
    if subscription_score >= 70:
        strengths.append("Your recurring subscription costs are well-controlled.")
    if buffer_score >= 70:
        strengths.append(f"You have a solid cash buffer of {cash_buffer_days:.0f} days of spending.")

    if not strengths:
        strengths.append("Building financial awareness is a great first step.")

    # ── Risks ──
    risks = []
    if savings_score < 40:
        if savings_ratio < 0:
            risks.append("You are spending more than you earn — your savings rate is negative.")
        else:
            risks.append(f"Your savings rate of {max(0, savings_ratio * 100):.0f}% is below the recommended 20%.")
    if volatility_score < 40:
        risks.append("Your spending varies significantly from day to day, which makes budgeting harder.")
    if subscription_score < 40:
        pct = recurring_burden * 100
        risks.append(f"Subscription costs consume {pct:.0f}% of your income — above the recommended 10%.")
    if buffer_score < 40:
        if cash_buffer_days < 1:
            risks.append("You have very little cash buffer for unexpected expenses.")
        else:
            risks.append(f"Your cash buffer of {cash_buffer_days:.0f} days is below the recommended 30 days.")

    # ── Suggestions ──
    suggestions = []
    if savings_score < 70:
        suggestions.append("Aim to save at least 20% of your income each month.")
    if volatility_score < 60:
        suggestions.append("Try setting a daily spending limit to reduce spending swings.")
    if subscription_score < 60:
        suggestions.append("Review your recurring subscriptions and cancel unused services.")
    if buffer_score < 60:
        suggestions.append("Build an emergency fund covering at least 30 days of expenses.")
    if not suggestions:
        suggestions.append("Keep up the great work! Consider increasing your savings target.")

    return {
        "summary": summary,
        "strengths": strengths,
        "risks": risks,
        "suggestions": suggestions,
    }


# ═══════════════════════════════════════════════════
# Response Formatter (for cached results)
# ═══════════════════════════════════════════════════

def _format_response(cached: dict) -> dict:
    """Format a cached health_scores row into the API response shape."""
    return {
        "health_score": cached["health_score"],
        "analysis_period": f"Last {cached['analysis_window_days']} days",
        "as_of_date": cached["as_of_date"],
        "has_enough_data": True,  # If it was cached, it was valid
        "metrics": {
            "savings_ratio": cached["savings_ratio"],
            "cash_buffer_days": cached["cash_buffer_days"],
            "recurring_burden": cached["recurring_burden"],
            "spending_volatility": cached["volatility_score"],
        },
        "component_scores": cached["component_scores"],
        "explanation": cached["explanation_json"],
    }
