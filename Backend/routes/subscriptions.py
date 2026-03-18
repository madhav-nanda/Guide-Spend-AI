"""
Subscription routes — /v1/subscriptions
Recurring payment detection endpoints.

Thin handlers: validate input, delegate to service, return JSON.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from services import subscription_service
from utils.errors import ValidationError
from utils.logger import get_logger

subscriptions_bp = Blueprint("subscriptions", __name__, url_prefix="/v1/subscriptions")
log = get_logger("routes.subscriptions")


@subscriptions_bp.route("", methods=["GET"])
@jwt_required()
def list_subscriptions():
    """
    List detected recurring merchants / subscriptions.

    Query params:
        account_id      (optional): plaid_account_id filter
        min_confidence  (optional): minimum confidence 0–100 (default 0)
    """
    try:
        user_id = int(get_jwt_identity())
    except (ValueError, TypeError):
        raise ValidationError("Invalid user identity in token")

    account_id = request.args.get("account_id", "all")
    min_confidence = request.args.get("min_confidence", 0, type=float)

    if not (0 <= min_confidence <= 100):
        raise ValidationError("min_confidence must be between 0 and 100")

    results = subscription_service.get_subscriptions(
        user_id=user_id,
        account_id=account_id,
        min_confidence=min_confidence,
    )

    return jsonify({"subscriptions": results, "count": len(results)})


@subscriptions_bp.route("/<int:sub_id>", methods=["GET"])
@jwt_required()
def get_subscription(sub_id):
    """Return full details for a single subscription."""
    try:
        user_id = int(get_jwt_identity())
    except (ValueError, TypeError):
        raise ValidationError("Invalid user identity in token")

    result = subscription_service.get_subscription_detail(sub_id, user_id)
    return jsonify(result)


@subscriptions_bp.route("/recompute", methods=["POST"])
@jwt_required()
def recompute_subscriptions():
    """
    Trigger subscription detection recompute for the current user.
    Returns detection stats.
    """
    try:
        user_id = int(get_jwt_identity())
    except (ValueError, TypeError):
        raise ValidationError("Invalid user identity in token")

    account_id = request.args.get("account_id", "all")

    log.info("Recompute requested",
             extra={"context": {"user_id": user_id, "account_id": account_id}})

    try:
        stats = subscription_service.detect_subscriptions(
            user_id=user_id,
            account_id=account_id,
        )
    except Exception as e:
        log.exception("Subscription recompute failed",
                      extra={"context": {"user_id": user_id}})
        raise

    return jsonify(stats)
