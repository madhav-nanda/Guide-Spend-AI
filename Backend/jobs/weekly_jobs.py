"""
Background job: Generate weekly reports for all users.
Safe to run via cron, scheduler, or manual trigger.
Idempotent — re-running updates existing reports, never duplicates.

Now uses the generalized time-range engine (writes to time_range_reports).

Usage (cron / CLI):
    from jobs.weekly_jobs import generate_all_users_weekly_reports
    generate_all_users_weekly_reports()

Recommended schedule: Monday 02:00 UTC (captures complete prior week)
"""
from models import time_range_report as report_model
from services import insights_service
from utils.logger import get_logger

log = get_logger("jobs.weekly_reports")


def generate_all_users_weekly_reports():
    """
    Iterate all users who have transactions and generate
    a weekly report for each (all-accounts aggregate).
    Failures for one user do not block others.

    Returns:
        { "generated": int, "errors": int }
    """
    log.info("Starting weekly report generation job")

    # Single query — no N+1
    user_ids = report_model.find_distinct_user_ids()
    log.info(
        f"Found {len(user_ids)} users with transactions",
        extra={"context": {"user_count": len(user_ids)}},
    )

    success_count = 0
    error_count = 0

    for uid in user_ids:
        try:
            report = insights_service.get_time_range_report(
                user_id=uid,
                range_type="week",
                account_id=None,
                offset=0,
            )
            log.info(
                "Weekly report generated for user",
                extra={"context": {
                    "user_id": uid,
                    "total_spent": report["total_spent"],
                    "total_income": report["total_income"],
                    "volatility_score": report["volatility_score"],
                }},
            )
            success_count += 1
        except Exception as e:
            log.error(
                f"Weekly report failed for user {uid}: {e}",
                extra={"context": {"user_id": uid}},
                exc_info=True,
            )
            error_count += 1

    log.info(
        "Weekly report generation job finished",
        extra={"context": {
            "generated": success_count,
            "errors": error_count,
            "total_users": len(user_ids),
        }},
    )

    return {"generated": success_count, "errors": error_count}
