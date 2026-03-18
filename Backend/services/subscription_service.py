"""
Subscription detection service — deterministic recurring payment detection.

Algorithm:
  1. Fetch expenses from last N days
  2. Group by normalized merchant_key
  3. For each group with >= 3 transactions:
     a. Compute date gaps between consecutive transactions
     b. Match gaps to cadence templates (weekly/biweekly/monthly/quarterly)
     c. Compute amount statistics (mean, stddev, tolerance)
     d. Compute confidence score based on cadence fit, amount stability, sample size
     e. Predict next expected date
  4. Upsert results into recurring_merchants

Design: deterministic, explainable, idempotent. No ML.
"""
import math
import time
from datetime import date, timedelta
from collections import defaultdict

from models import recurring_merchant as rm_model
from utils.merchant_normalization import normalize_merchant
from utils.errors import ValidationError, DatabaseError
from utils.logger import get_logger

log = get_logger("subscription_service")

# ═══════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════

LOOKBACK_DAYS = 180
MIN_SAMPLE_WEEKLY = 4
MIN_SAMPLE_DEFAULT = 3

# Cadence templates: (name, target_days, tolerance_days)
CADENCE_TEMPLATES = [
    ("weekly",    7,   2),
    ("biweekly",  14,  3),
    ("monthly",   30,  5),
    ("quarterly", 90,  10),
]


# ═══════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════

def detect_subscriptions(user_id: int, account_id: str = "all") -> dict:
    """
    Run the full subscription detection pipeline for a user.

    Returns:
        { "detected": int, "updated": int, "skipped": int, "elapsed_ms": float }
    """
    t0 = time.monotonic()
    account_id = account_id if account_id and account_id != "all" else "all"

    log.info("Starting subscription detection",
             extra={"context": {"user_id": user_id, "account_id": account_id}})

    # ── Step 1: Fetch candidate transactions ──
    txns = rm_model.fetch_expense_transactions(user_id, account_id, LOOKBACK_DAYS)

    if not txns:
        log.info("No expense transactions found",
                 extra={"context": {"user_id": user_id}})
        return {"detected": 0, "updated": 0, "skipped": 0, "elapsed_ms": 0}

    # ── Step 2: Group by normalized merchant key ──
    merchant_groups = _group_by_merchant(txns)

    # ── Step 3: Analyze each group ──
    detected = 0
    updated = 0
    skipped = 0
    active_keys = []

    for merchant_key, group_data in merchant_groups.items():
        result = _analyze_merchant_group(
            merchant_key=merchant_key,
            display_name=group_data["display_name"],
            transactions=group_data["transactions"],
        )

        if result is None:
            skipped += 1
            continue

        active_keys.append(merchant_key)

        # ── Step 4: Upsert ──
        try:
            rm_model.upsert(
                user_id=user_id,
                account_id=account_id,
                merchant_key=result["merchant_key"],
                merchant_display_name=result["merchant_display_name"],
                cadence=result["cadence"],
                avg_amount=result["avg_amount"],
                amount_stddev=result["amount_stddev"],
                amount_tolerance=result["amount_tolerance"],
                last_charge_date=result["last_charge_date"],
                next_expected_date=result["next_expected_date"],
                confidence_score=result["confidence_score"],
                sample_size=result["sample_size"],
                last_n_transactions=result["last_n_transactions"],
                explanation_json=result["explanation_json"],
            )
            detected += 1
            updated += 1
        except Exception as e:
            log.error(f"Upsert failed for {merchant_key}: {e}",
                      extra={"context": {"user_id": user_id}})
            skipped += 1

    # ── Cleanup stale entries ──
    if active_keys:
        try:
            rm_model.delete_stale(user_id, account_id, active_keys)
        except Exception:
            pass  # Non-fatal

    elapsed_ms = round((time.monotonic() - t0) * 1000, 1)

    log.info("Subscription detection complete",
             extra={"context": {
                 "user_id": user_id,
                 "detected": detected,
                 "updated": updated,
                 "skipped": skipped,
                 "elapsed_ms": elapsed_ms,
             }})

    return {
        "detected": detected,
        "updated": updated,
        "skipped": skipped,
        "elapsed_ms": elapsed_ms,
    }


def get_subscriptions(user_id: int, account_id: str = "all",
                      min_confidence: float = 0) -> list:
    """Return detected subscriptions for a user."""
    account_id = account_id if account_id and account_id != "all" else "all"
    return rm_model.find_by_user(user_id, account_id, min_confidence)


def get_subscription_detail(recurring_id: int, user_id: int) -> dict:
    """Return a single subscription with full explanation."""
    result = rm_model.find_by_id(recurring_id, user_id)
    if not result:
        from utils.errors import NotFoundError
        raise NotFoundError("Subscription not found")
    return result


# ═══════════════════════════════════════════════════
# Grouping
# ═══════════════════════════════════════════════════

def _group_by_merchant(txns: list) -> dict:
    """Group transactions by normalized merchant key."""
    groups = defaultdict(lambda: {"display_name": "", "transactions": []})

    for t in txns:
        norm = normalize_merchant(t["description"])
        key = norm["merchant_key"]
        groups[key]["display_name"] = norm["merchant_display_name"]
        groups[key]["transactions"].append(t)

    return dict(groups)


# ═══════════════════════════════════════════════════
# Analysis
# ═══════════════════════════════════════════════════

def _analyze_merchant_group(merchant_key: str, display_name: str,
                             transactions: list) -> dict | None:
    """
    Analyze a group of transactions for a single merchant.
    Returns a detection result dict, or None if not recurring.
    """
    if len(transactions) < MIN_SAMPLE_DEFAULT:
        return None

    # Sort by date
    txns = sorted(transactions, key=lambda t: t["date"])

    # ── Date gap analysis ──
    dates = [date.fromisoformat(t["date"]) for t in txns]
    gaps = [(dates[i+1] - dates[i]).days for i in range(len(dates) - 1)]

    if not gaps:
        return None

    # ── Find best cadence match ──
    best_cadence = _detect_cadence(gaps)
    if best_cadence is None:
        return None

    cadence_name, target_days, tolerance_days = best_cadence["template"]
    match_rate = best_cadence["match_rate"]

    # Enforce minimum sample size per cadence type
    min_sample = MIN_SAMPLE_WEEKLY if cadence_name in ("weekly", "biweekly") else MIN_SAMPLE_DEFAULT
    if len(txns) < min_sample:
        return None

    # ── Amount analysis ──
    amounts = [t["amount"] for t in txns]
    avg_amount = sum(amounts) / len(amounts)
    if len(amounts) > 1:
        variance = sum((a - avg_amount) ** 2 for a in amounts) / len(amounts)
        stddev = math.sqrt(variance)
    else:
        stddev = 0.0

    tolerance = max(stddev * 2, avg_amount * 0.05, 1.0)

    # ── Confidence score ──
    confidence = _compute_confidence(
        match_rate=match_rate,
        sample_size=len(txns),
        stddev=stddev,
        avg_amount=avg_amount,
        cadence_name=cadence_name,
    )

    if confidence < 30:
        return None

    # ── Next expected date ──
    last_date = dates[-1]
    next_expected = last_date + timedelta(days=target_days)

    # ── Last N transactions (compact for UI) ──
    last_n = [
        {"date": t["date"], "amount": round(t["amount"], 2), "txn_id": t["id"]}
        for t in txns[-10:]
    ]

    # ── Explanation ──
    explanation = {
        "merchant_key": merchant_key,
        "cadence_detected": cadence_name,
        "cadence_evidence": {
            "date_gaps_days": gaps[-10:],  # Last 10 gaps
            "target_gap_days": target_days,
            "tolerance_days": tolerance_days,
            "gap_match_rate": round(match_rate, 3),
        },
        "amount_evidence": {
            "mean": round(avg_amount, 2),
            "stddev": round(stddev, 2),
            "tolerance": round(tolerance, 2),
            "min": round(min(amounts), 2),
            "max": round(max(amounts), 2),
        },
        "sample_size": len(txns),
        "rule_out_notes": [],
        "confidence_rationale": _confidence_rationale(confidence, match_rate, len(txns), stddev, avg_amount),
    }

    return {
        "merchant_key": merchant_key,
        "merchant_display_name": display_name,
        "cadence": cadence_name,
        "avg_amount": round(avg_amount, 2),
        "amount_stddev": round(stddev, 2),
        "amount_tolerance": round(tolerance, 2),
        "last_charge_date": last_date,
        "next_expected_date": next_expected,
        "confidence_score": round(confidence, 2),
        "sample_size": len(txns),
        "last_n_transactions": last_n,
        "explanation_json": explanation,
    }


# ═══════════════════════════════════════════════════
# Cadence Detection
# ═══════════════════════════════════════════════════

def _detect_cadence(gaps: list) -> dict | None:
    """
    Match date gaps against cadence templates.
    Returns the best matching template, or None.
    """
    best = None

    for template in CADENCE_TEMPLATES:
        name, target, tol = template
        matches = sum(1 for g in gaps if abs(g - target) <= tol)
        rate = matches / len(gaps)

        if rate >= 0.6 and (best is None or rate > best["match_rate"]):
            best = {"template": template, "match_rate": rate, "matches": matches}

    return best


# ═══════════════════════════════════════════════════
# Confidence Scoring
# ═══════════════════════════════════════════════════

def _compute_confidence(match_rate: float, sample_size: int,
                         stddev: float, avg_amount: float,
                         cadence_name: str) -> float:
    """
    Compute confidence score (0–100) based on evidence.

    Components (weighted):
      - Cadence fit (40%): How well gaps match the template
      - Sample size (25%): More data = higher confidence
      - Amount stability (25%): Low variance = higher confidence
      - Cadence bonus (10%): Monthly/weekly more common = slight boost
    """
    # Cadence fit: 0.6 → 0, 1.0 → 40
    cadence_score = min(40, max(0, (match_rate - 0.6) / 0.4 * 40))

    # Sample size: 3 → 5, 6 → 15, 12+ → 25
    sample_score = min(25, max(0, (sample_size - 2) / 10 * 25))

    # Amount stability: CV (coefficient of variation)
    if avg_amount > 0 and stddev > 0:
        cv = stddev / avg_amount
        # CV 0 → 25, CV 0.5+ → 0
        amount_score = min(25, max(0, (0.5 - cv) / 0.5 * 25))
    else:
        amount_score = 25  # Zero variance = perfect

    # Cadence bonus
    cadence_bonus = {"monthly": 10, "weekly": 8, "biweekly": 7, "quarterly": 5}.get(cadence_name, 3)

    total = cadence_score + sample_score + amount_score + cadence_bonus
    return min(100, max(0, total))


def _confidence_rationale(confidence: float, match_rate: float,
                           sample_size: int, stddev: float,
                           avg_amount: float) -> str:
    """Human-readable explanation of confidence score."""
    parts = []

    if match_rate >= 0.9:
        parts.append("Very consistent payment schedule")
    elif match_rate >= 0.75:
        parts.append("Mostly consistent payment schedule")
    else:
        parts.append("Somewhat irregular payment schedule")

    if sample_size >= 6:
        parts.append(f"with strong history ({sample_size} charges)")
    else:
        parts.append(f"with limited history ({sample_size} charges)")

    if avg_amount > 0:
        cv = stddev / avg_amount if avg_amount > 0 else 0
        if cv < 0.05:
            parts.append("and very stable amounts")
        elif cv < 0.2:
            parts.append("and fairly stable amounts")
        else:
            parts.append("but variable amounts")

    return ". ".join(parts) + "."
