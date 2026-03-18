"""
Background job: Detect subscriptions for all users.
Safe to run via cron, scheduler, or manual trigger.
Idempotent — re-running updates existing records, never duplicates.

Usage (cron / CLI):
    from jobs.subscription_jobs import detect_all_users_subscriptions
    detect_all_users_subscriptions()

Recommended schedule: Daily at 03:00 UTC
"""
from models import recurring_merchant as rm_model
from services import subscription_service
from utils.logger import get_logger

log = get_logger("jobs.subscription_detection")


def detect_all_users_subscriptions():
    """
    Iterate all users with transactions and run subscription detection.
    Failures for one user do not block others.

    Returns:
        { "processed": int, "errors": int, "total_detected": int }
    """
    log.info("Starting subscription detection job")

    user_ids = rm_model.find_distinct_user_ids()
    log.info(
        f"Found {len(user_ids)} users with transactions",
        extra={"context": {"user_count": len(user_ids)}},
    )

    processed = 0
    errors = 0
    total_detected = 0

    for uid in user_ids:
        try:
            stats = subscription_service.detect_subscriptions(
                user_id=uid,
                account_id="all",
            )
            log.info(
                "Subscriptions detected for user",
                extra={"context": {
                    "user_id": uid,
                    "detected": stats["detected"],
                    "elapsed_ms": stats["elapsed_ms"],
                }},
            )
            processed += 1
            total_detected += stats["detected"]
        except Exception as e:
            log.error(
                f"Subscription detection failed for user {uid}: {e}",
                extra={"context": {"user_id": uid}},
                exc_info=True,
            )
            errors += 1

    log.info(
        "Subscription detection job finished",
        extra={"context": {
            "processed": processed,
            "errors": errors,
            "total_detected": total_detected,
            "total_users": len(user_ids),
        }},
    )

    return {
        "processed": processed,
        "errors": errors,
        "total_detected": total_detected,
    }
