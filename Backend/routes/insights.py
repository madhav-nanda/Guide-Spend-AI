"""
Insights routes — /v1/insights
Financial intelligence endpoints.

Thin handlers: validate input, delegate to service, return JSON.
No business logic lives here.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from services import insights_service
from utils.errors import ValidationError
from utils.logger import get_logger

insights_bp = Blueprint("insights", __name__, url_prefix="/v1/insights")
log = get_logger("routes.insights")


# ──────────────────────────────────────────────
# New unified endpoint
# ──────────────────────────────────────────────

@insights_bp.route("/time-range", methods=["GET"])
@jwt_required()
def get_time_range():
    """
    Unified time-range insights endpoint.

    Query params:
        type       (required): week | month | rolling | custom
        offset     (optional): integer offset for week/month (0 = current, -1 = previous)
        days       (optional): integer for rolling (7, 30, 90)
        start      (optional): YYYY-MM-DD for custom
        end        (optional): YYYY-MM-DD for custom
        account_id (optional): plaid_account_id filter

    Examples:
        ?type=week&offset=0
        ?type=week&offset=-1
        ?type=month&offset=0
        ?type=rolling&days=30
        ?type=custom&start=2026-01-01&end=2026-01-31
        ?type=week&offset=-2&account_id=abc123
    """
    # ── Safe identity parsing ──
    try:
        user_id = int(get_jwt_identity())
    except (ValueError, TypeError):
        raise ValidationError("Invalid user identity in token")

    range_type = request.args.get("type", "week")
    offset = request.args.get("offset", 0, type=int)
    days = request.args.get("days", type=int)
    start = request.args.get("start")
    end = request.args.get("end")
    account_id = request.args.get("account_id")

    # ── Debug logging for every request ──
    log.info(
        "Time range request",
        extra={"context": {
            "user_id": user_id,
            "type": range_type,
            "offset": offset,
            "days": days,
            "start": start,
            "end": end,
            "account_id": account_id,
        }},
    )

    try:
        report = insights_service.get_time_range_report(
            user_id=user_id,
            range_type=range_type,
            account_id=account_id,
            offset=offset,
            days=days,
            start=start,
            end=end,
        )
    except Exception as e:
        # AppError subclasses (ValidationError, DatabaseError) will be
        # re-raised and caught by Flask's error handler for proper
        # HTTP status codes. Any unexpected exception gets logged with
        # a full stack trace before re-raising.
        log.exception(
            "Time range insights failed",
            extra={"context": {
                "user_id": user_id,
                "type": range_type,
                "offset": offset,
                "account_id": account_id,
            }},
        )
        raise

    return jsonify(report)


# ──────────────────────────────────────────────
# Legacy endpoint (backward compatible)
# ──────────────────────────────────────────────

@insights_bp.route("/weekly/latest", methods=["GET"])
@jwt_required()
def get_weekly_latest():
    """
    Return the latest weekly report for the authenticated user.
    Kept for backward compatibility — delegates to the generalized engine.
    """
    try:
        user_id = int(get_jwt_identity())
    except (ValueError, TypeError):
        raise ValidationError("Invalid user identity in token")

    account_id = request.args.get("account_id")

    try:
        report = insights_service.get_or_generate_latest(user_id, account_id)
    except Exception as e:
        log.exception(
            "Weekly insights failed",
            extra={"context": {"user_id": user_id, "account_id": account_id}},
        )
        raise

    return jsonify(report)
