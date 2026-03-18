"""
Health Score routes — /v1/health-score
Financial Health Score computation endpoint.

Thin handler: validate input, delegate to service, return JSON.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from services import health_score_service
from utils.errors import ValidationError
from utils.logger import get_logger

health_score_bp = Blueprint("health_score", __name__, url_prefix="/v1/health-score")
log = get_logger("routes.health_score")


@health_score_bp.route("", methods=["GET"])
@jwt_required()
def get_health_score():
    """
    Compute or return cached Financial Health Score.

    Query params:
        account_id       (optional): plaid_account_id filter (default "all")
        window_days      (optional): 30 | 60 | 90 (default 90)
        current_balance  (optional): real-time balance from frontend
    """
    try:
        user_id = int(get_jwt_identity())
    except (ValueError, TypeError):
        raise ValidationError("Invalid user identity in token")

    account_id = request.args.get("account_id", "all")
    window_days = request.args.get("window_days", 90, type=int)
    current_balance = request.args.get("current_balance", None, type=float)

    log.debug("Health score request",
              extra={"context": {
                  "user_id": user_id,
                  "account_id": account_id,
                  "window_days": window_days,
              }})

    try:
        result = health_score_service.get_health_score(
            user_id=user_id,
            account_id=account_id,
            window_days=window_days,
            current_balance=current_balance,
        )
    except ValidationError:
        raise
    except Exception as e:
        log.exception("Health score computation failed",
                      extra={"context": {"user_id": user_id}})
        raise

    return jsonify(result)
