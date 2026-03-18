"""
Background job: Sync transactions for all users.
Can be invoked by a cron scheduler, Celery task, or manual trigger.
Iterates over every user's plaid_items and runs incremental sync.
"""
from models import plaid_item as item_model
from services import plaid_service
from utils.db import get_db
from utils.logger import get_logger

log = get_logger("jobs.sync_transactions")


def sync_all_users():
    """
    Fetch all distinct user IDs that have linked Plaid items
    and run a transaction sync for each.
    Designed for scheduled background execution.
    """
    log.info("Starting bulk transaction sync job")

    with get_db() as (conn, cur):
        cur.execute("SELECT DISTINCT user_id FROM plaid_items")
        user_rows = cur.fetchall()

    user_ids = [row[0] for row in user_rows]
    log.info(f"Found {len(user_ids)} users with linked accounts")

    success_count = 0
    error_count = 0

    for uid in user_ids:
        try:
            result = plaid_service.sync_transactions(uid)
            log.info(
                "User sync complete",
                extra={"context": {"user_id": uid, **result}},
            )
            success_count += 1
        except Exception as e:
            log.error(
                f"Sync failed for user {uid}: {e}",
                extra={"context": {"user_id": uid}},
            )
            error_count += 1

    log.info(
        "Bulk sync job finished",
        extra={"context": {"success": success_count, "errors": error_count}},
    )

    return {"synced": success_count, "errors": error_count}
