"""
Background job: Pre-compute cash flow forecasts for all users.
Safe to run via cron, scheduler, or manual trigger.
Idempotent — re-running updates existing forecasts for today.

Usage (cron / CLI):
    from jobs.cashflow_jobs import generate_all_users_forecasts
    generate_all_users_forecasts()

Recommended schedule: Daily at 04:00 UTC (after subscription detection)
"""
from models import cashflow_forecast as cf_model
from services import cashflow_service
from utils.logger import get_logger

log = get_logger("jobs.cashflow_forecasts")

DEFAULT_HORIZONS = [7, 14]


def generate_all_users_forecasts(horizons=None):
    """
    Iterate all users with transactions and generate cashflow forecasts.
    Failures for one user do not block others.

    Args:
        horizons: list of horizon_days to compute (default [7, 14])

    Returns:
        { "processed": int, "errors": int, "forecasts_generated": int }
    """
    horizons = horizons or DEFAULT_HORIZONS
    log.info("Starting cashflow forecast job",
             extra={"context": {"horizons": horizons}})

    user_ids = cf_model.find_distinct_user_ids()
    log.info(
        f"Found {len(user_ids)} users with transactions",
        extra={"context": {"user_count": len(user_ids)}},
    )

    processed = 0
    errors = 0
    forecasts_generated = 0

    for uid in user_ids:
        user_ok = True
        for horizon in horizons:
            try:
                cashflow_service.get_forecast(
                    user_id=uid,
                    account_id="all",
                    horizon_days=horizon,
                    starting_balance=None,  # Will use 0; real balance comes from frontend
                )
                forecasts_generated += 1
            except Exception as e:
                log.error(
                    f"Forecast failed for user {uid}, horizon {horizon}: {e}",
                    extra={"context": {"user_id": uid, "horizon": horizon}},
                    exc_info=True,
                )
                errors += 1
                user_ok = False

        if user_ok:
            processed += 1

    log.info(
        "Cashflow forecast job finished",
        extra={"context": {
            "processed": processed,
            "errors": errors,
            "forecasts_generated": forecasts_generated,
            "total_users": len(user_ids),
        }},
    )

    return {
        "processed": processed,
        "errors": errors,
        "forecasts_generated": forecasts_generated,
    }
