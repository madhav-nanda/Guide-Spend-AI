"""
Insights service — generalized financial intelligence engine.

Supports arbitrary time ranges: week, month, rolling (N-day), and custom.
Deterministic, idempotent, and future-proof for AI enrichment.

Architecture decisions:
  • All aggregation pushed to SQL (models layer) — zero N+1.
  • Volatility uses Coefficient of Variation (CV) normalized to 0–100.
  • Explanations are deterministic template strings — an AI layer can
    replace _build_explanation() later without touching any other code.
  • Date math lives exclusively here (not in routes, not in frontend).
  • Cache key = (user_id, account_id, start_date, end_date).
    Same range requested twice → cache hit, regardless of granularity label.
  • Old weekly_reports table is untouched; the /v1/insights/weekly/latest
    endpoint still works for backwards compatibility. New code writes to
    time_range_reports exclusively.
"""
from datetime import date, timedelta
import math
import time

from models import time_range_report as report_model
from utils.errors import ValidationError, DatabaseError
from utils.logger import get_logger

log = get_logger("insights_service")

MAX_RANGE_DAYS = 365


# ═══════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════

def get_time_range_report(user_id: int, range_type: str,
                          account_id: str = None, offset: int = 0,
                          days: int = None, start: str = None,
                          end: str = None) -> dict:
    """
    Unified entry point for all time-range insight requests.

    Resolves the date range, checks the cache, generates if needed.

    Args:
        user_id:    Authenticated user
        range_type: "week" | "month" | "rolling" | "custom"
        account_id: plaid_account_id or None / "all"
        offset:     For week/month — 0 = current, -1 = previous, etc.
        days:       For rolling — how many days back (7, 30, 90)
        start/end:  For custom — "YYYY-MM-DD" strings
    """
    t0 = time.monotonic()
    account_id = _normalize_account_id(account_id)

    # ── Resolve date boundaries ──
    start_date, end_date, granularity = _resolve_range(
        range_type, offset=offset, days=days, start=start, end=end
    )

    # ── Check cache ──
    try:
        cached = report_model.find_report(
            user_id, account_id, str(start_date), str(end_date)
        )
    except Exception as e:
        # Cache lookup failure is non-fatal — log and continue to generate fresh.
        # Common cause: schema drift (e.g., missing period_change column).
        log.warning(
            f"Cache lookup failed (will regenerate): {e}",
            extra={"context": {"user_id": user_id}},
        )
        cached = None

    if cached:
        elapsed_ms = round((time.monotonic() - t0) * 1000, 1)
        log.info(
            "Cache hit",
            extra={"context": {
                "user_id": user_id,
                "account_id": account_id,
                "start": str(start_date),
                "end": str(end_date),
                "granularity": granularity,
                "elapsed_ms": elapsed_ms,
            }},
        )
        return _format_response(cached, granularity)

    # ── Generate fresh ──
    return generate_time_range_report(
        user_id, account_id, start_date, end_date, granularity, t0
    )


def generate_time_range_report(user_id: int, account_id: str,
                                start_date, end_date,
                                granularity: str = "range",
                                t0: float = None) -> dict:
    """
    Generate (or regenerate) a time-range report.
    Idempotent — safe to call repeatedly; uses upsert.

    Pipeline:
      1. Compute comparison period (same-length window before start_date)
      2. Aggregate transactions via SQL (5 queries, 1 connection)
      3. Compute derived metrics (period comparison, volatility)
      4. Build deterministic explanation
      5. Upsert to time_range_reports
      6. Return structured response
    """
    if t0 is None:
        t0 = time.monotonic()

    account_id = _normalize_account_id(account_id)
    start_str = str(start_date)
    end_str = str(end_date)

    # ── Previous period of same length ──
    range_days = (end_date - start_date).days + 1
    prev_end = start_date - timedelta(days=1)
    prev_start = prev_end - timedelta(days=range_days - 1)

    log.info(
        "Generating report",
        extra={"context": {
            "user_id": user_id,
            "account_id": account_id,
            "start": start_str,
            "end": end_str,
            "granularity": granularity,
            "range_days": range_days,
        }},
    )

    # ── Step 1: Aggregate (5 queries, 1 connection) ──
    try:
        data = report_model.aggregate_range_data(
            user_id=user_id,
            account_id=account_id,
            start_date=start_str,
            end_date=end_str,
            prev_start=str(prev_start),
            prev_end=str(prev_end),
        )
    except Exception as e:
        log.error(
            f"Aggregation failed: {e}",
            extra={"context": {"user_id": user_id}},
            exc_info=True,
        )
        raise DatabaseError("Failed to aggregate transaction data")

    # ── Step 2: Period-over-period change ──
    period_change = _compute_period_change(
        data["total_spent"], data["prev_period_spent"]
    )

    # ── Step 3: Volatility ──
    volatility = _compute_volatility(
        data["daily_spending"], start_date, end_date
    )

    # ── Step 4: Explanation ──
    period_label = _period_label(granularity, range_days)
    explanation = _build_explanation(
        total_spent=data["total_spent"],
        total_income=data["total_income"],
        net_change=data["net_change"],
        top_merchants=data["top_merchants"],
        top_categories=data["top_categories"],
        period_change=period_change,
        volatility=volatility,
        txn_count=data["transaction_count"],
        period_label=period_label,
    )

    # ── Step 5: Upsert ──
    try:
        report_id = report_model.upsert_report(
            user_id=user_id,
            account_id=account_id,
            start_date=start_str,
            end_date=end_str,
            granularity=granularity,
            total_spent=data["total_spent"],
            total_income=data["total_income"],
            net_change=data["net_change"],
            top_merchants=data["top_merchants"],
            top_categories=data["top_categories"],
            volatility_score=volatility,
            period_change=period_change,
            explanation_json=explanation,
        )
    except Exception as e:
        log.error(
            f"Upsert failed: {e}",
            extra={"context": {"user_id": user_id}},
            exc_info=True,
        )
        raise DatabaseError("Failed to save report")

    elapsed_ms = round((time.monotonic() - t0) * 1000, 1)
    log.info(
        "Report generated",
        extra={"context": {
            "user_id": user_id,
            "report_id": report_id,
            "total_spent": data["total_spent"],
            "volatility": volatility,
            "elapsed_ms": elapsed_ms,
        }},
    )

    # ── Step 6: Response ──
    return {
        "start_date": start_str,
        "end_date": end_str,
        "granularity": granularity,
        "total_spent": round(data["total_spent"], 2),
        "total_income": round(data["total_income"], 2),
        "net_change": round(data["net_change"], 2),
        "top_merchants": data["top_merchants"],
        "top_categories": data["top_categories"],
        "period_change": period_change,
        "volatility_score": volatility,
        "explanation": explanation,
    }


# ═══════════════════════════════════════════════════
# Legacy wrapper (keeps /v1/insights/weekly/latest working)
# ═══════════════════════════════════════════════════

def get_or_generate_latest(user_id: int, account_id: str = None) -> dict:
    """Backward-compatible wrapper: returns current week report."""
    result = get_time_range_report(
        user_id=user_id,
        range_type="week",
        account_id=account_id,
        offset=0,
    )
    # Reshape to match the old response format expected by
    # any client still using /v1/insights/weekly/latest
    return {
        "week_start": result["start_date"],
        "week_end": result["end_date"],
        "total_spent": result["total_spent"],
        "total_income": result["total_income"],
        "net_change": result["net_change"],
        "top_merchants": result["top_merchants"],
        "top_categories": result["top_categories"],
        "week_over_week_change": result["period_change"],
        "volatility_score": result["volatility_score"],
        "explanation": result["explanation"],
    }


# ═══════════════════════════════════════════════════
# Date Range Resolution
# ═══════════════════════════════════════════════════

def _resolve_range(range_type: str, offset: int = 0,
                   days: int = None, start: str = None,
                   end: str = None):
    """
    Convert human parameters into (start_date, end_date, granularity).
    All date math lives here — nowhere else.
    """
    today = date.today()

    if range_type == "week":
        return _resolve_week(today, offset)

    if range_type == "month":
        return _resolve_month(today, offset)

    if range_type == "rolling":
        return _resolve_rolling(today, days)

    if range_type == "custom":
        return _resolve_custom(today, start, end)

    raise ValidationError(
        f"Invalid type '{range_type}'. Must be: week, month, rolling, custom"
    )


def _resolve_week(today, offset):
    """offset 0 = current week (Mon–Sun), -1 = last week, etc."""
    offset = int(offset or 0)
    monday = today - timedelta(days=today.weekday())
    monday += timedelta(weeks=offset)
    sunday = monday + timedelta(days=6)

    if monday > today:
        raise ValidationError("Cannot request future weeks")

    return monday, sunday, "week"


def _resolve_month(today, offset):
    """offset 0 = current month (1st–last), -1 = last month, etc."""
    offset = int(offset or 0)
    year = today.year
    month = today.month + offset

    # Handle year rollover
    while month < 1:
        month += 12
        year -= 1
    while month > 12:
        month -= 12
        year += 1

    first_day = date(year, month, 1)
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)

    if first_day > today:
        raise ValidationError("Cannot request future months")

    return first_day, last_day, "month"


def _resolve_rolling(today, days):
    """Last N days ending today."""
    if not days or int(days) <= 0:
        raise ValidationError("'days' must be a positive integer")

    days = int(days)
    if days > MAX_RANGE_DAYS:
        raise ValidationError(f"Rolling range cannot exceed {MAX_RANGE_DAYS} days")

    start_date = today - timedelta(days=days - 1)
    return start_date, today, "rolling"


def _resolve_custom(today, start_str, end_str):
    """Custom date range from explicit start/end strings."""
    if not start_str or not end_str:
        raise ValidationError("Custom range requires 'start' and 'end' parameters")

    try:
        start_date = date.fromisoformat(start_str)
        end_date = date.fromisoformat(end_str)
    except (ValueError, TypeError):
        raise ValidationError("Invalid date format. Use YYYY-MM-DD")

    if start_date > end_date:
        raise ValidationError("'start' must be before or equal to 'end'")

    if end_date > today:
        raise ValidationError("End date cannot be in the future")

    range_days = (end_date - start_date).days + 1
    if range_days > MAX_RANGE_DAYS:
        raise ValidationError(f"Custom range cannot exceed {MAX_RANGE_DAYS} days")

    return start_date, end_date, "custom"


# ═══════════════════════════════════════════════════
# Computation Helpers
# ═══════════════════════════════════════════════════

def _normalize_account_id(account_id):
    """Normalize empty/None account_id to 'all'."""
    return account_id if account_id and account_id != "all" else "all"


def _compute_period_change(current_spent: float, prev_spent: float) -> float:
    """
    Period-over-period spending change as a percentage.
    Safe divide: 0/0 → 0.0, X/0 → 100.0.
    """
    if prev_spent == 0:
        return 0.0 if current_spent == 0 else 100.0
    change = ((current_spent - prev_spent) / prev_spent) * 100
    return round(change, 2)


def _compute_volatility(daily_spending: dict, start_date, end_date) -> float:
    """
    Spending volatility as a normalized 0–100 score.
    CV = std_dev / mean × 100, capped at 100.
    Zero-fills every day in the range.
    """
    daily_totals = []
    current = start_date
    while current <= end_date:
        daily_totals.append(daily_spending.get(str(current), 0.0))
        current += timedelta(days=1)

    if len(daily_totals) < 2:
        return 0.0

    mean = sum(daily_totals) / len(daily_totals)
    if mean == 0:
        return 0.0

    variance = sum((x - mean) ** 2 for x in daily_totals) / len(daily_totals)
    std_dev = math.sqrt(variance)
    cv = (std_dev / mean) * 100
    return round(min(cv, 100.0), 2)


def _period_label(granularity: str, range_days: int) -> str:
    """Human-readable label for the period type."""
    labels = {
        "week": "this week",
        "month": "this month",
        "rolling": f"the last {range_days} days",
        "custom": f"the selected {range_days}-day period",
    }
    return labels.get(granularity, f"this {range_days}-day period")


# ═══════════════════════════════════════════════════
# Explanation Builder
# ═══════════════════════════════════════════════════

def _build_explanation(total_spent, total_income, net_change,
                       top_merchants, top_categories,
                       period_change, volatility, txn_count,
                       period_label) -> dict:
    """
    Deterministic, human-readable explanation JSON.
    Future AI hook point — replace this function to add LLM summaries.
    """
    # ── Summary ──
    if total_spent == 0 and total_income == 0:
        summary = f"No transactions recorded for {period_label}."
    elif net_change >= 0:
        summary = (
            f"You earned ${total_income:,.2f} and spent ${total_spent:,.2f} "
            f"across {txn_count} transactions {period_label}, "
            f"netting +${net_change:,.2f}."
        )
    else:
        summary = (
            f"You earned ${total_income:,.2f} and spent ${total_spent:,.2f} "
            f"across {txn_count} transactions {period_label}, "
            f"netting -${abs(net_change):,.2f}."
        )

    # ── Biggest merchant ──
    if top_merchants:
        m = top_merchants[0]
        biggest_merchant = f"{m['name']} (${m['amount']:,.2f})"
    else:
        biggest_merchant = "No spending recorded"

    # ── Largest category ──
    if top_categories:
        c = top_categories[0]
        largest_category = f"{c['name']} (${c['amount']:,.2f})"
    else:
        largest_category = "No spending recorded"

    # ── Spending change ──
    if total_spent == 0 and period_change == 0:
        spending_change = "No spending to compare."
    elif period_change == 0:
        spending_change = "Spending is flat compared to the previous period."
    elif period_change > 0:
        spending_change = f"Spending is up {period_change:.1f}% vs. the previous period."
    else:
        spending_change = f"Spending is down {abs(period_change):.1f}% vs. the previous period."

    # ── Volatility level ──
    if volatility <= 30:
        volatility_level = "low"
    elif volatility <= 60:
        volatility_level = "medium"
    else:
        volatility_level = "high"

    return {
        "summary": summary,
        "biggest_merchant": biggest_merchant,
        "largest_category": largest_category,
        "spending_change": spending_change,
        "volatility_level": volatility_level,
    }


# ═══════════════════════════════════════════════════
# Response Formatting
# ═══════════════════════════════════════════════════

def _format_response(report: dict, granularity: str) -> dict:
    """Format a cached report dict into the API response shape."""
    return {
        "start_date": report["start_date"],
        "end_date": report["end_date"],
        "granularity": granularity,
        "total_spent": report["total_spent"],
        "total_income": report["total_income"],
        "net_change": report["net_change"],
        "top_merchants": report["top_merchants"],
        "top_categories": report["top_categories"],
        "period_change": report.get("period_change", 0.0),
        "volatility_score": report["volatility_score"],
        "explanation": report["explanation"],
    }
