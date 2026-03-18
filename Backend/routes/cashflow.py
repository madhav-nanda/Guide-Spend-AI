"""
Cash flow forecast routes — /v1/cashflow
Deterministic balance projection + overdraft risk endpoints.

Thin handlers: validate input, delegate to service, return JSON.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from services import cashflow_service
from utils.errors import ValidationError
from utils.logger import get_logger

cashflow_bp = Blueprint("cashflow", __name__, url_prefix="/v1/cashflow")
log = get_logger("routes.cashflow")


@cashflow_bp.route("/forecast", methods=["GET"])
@jwt_required()
def get_forecast():
    """
    Get a cash flow forecast for the authenticated user.

    Query params:
        account_id       (optional): plaid_account_id filter (default "all")
        horizon_days     (optional): 7 | 14 | 30 (default 7)
        starting_balance (optional): current balance in dollars
    """
    try:
        user_id = int(get_jwt_identity())
    except (ValueError, TypeError):
        raise ValidationError("Invalid user identity in token")

    account_id = request.args.get("account_id", "all")
    horizon_days = request.args.get("horizon_days", 7, type=int)
    starting_balance = request.args.get("starting_balance", None, type=float)

    log.debug("Forecast request",
              extra={"context": {
                  "user_id": user_id,
                  "account_id": account_id,
                  "horizon_days": horizon_days,
                  "starting_balance": starting_balance,
              }})

    try:
        result = cashflow_service.get_forecast(
            user_id=user_id,
            account_id=account_id,
            horizon_days=horizon_days,
            starting_balance=starting_balance,
        )
    except ValidationError:
        raise
    except Exception as e:
        log.exception("Forecast computation failed",
                      extra={"context": {"user_id": user_id}})
        raise

    return jsonify(result)
