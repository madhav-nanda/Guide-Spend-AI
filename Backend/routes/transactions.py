"""
Transaction routes — /transactions
Thin handlers with pagination support.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from services import transaction_service

transactions_bp = Blueprint("transactions", __name__)


@transactions_bp.route("/transactions", methods=["POST"])
@jwt_required()
def add_transaction():
    user_id = int(get_jwt_identity())
    result = transaction_service.add_manual_transaction(user_id, request.json)
    return jsonify(result), 201


@transactions_bp.route("/transactions", methods=["GET"])
@jwt_required()
def get_transactions():
    user_id = int(get_jwt_identity())

    # ── Parse query parameters ──
    account_id = request.args.get("account_id")
    page = request.args.get("page", type=int)
    per_page = request.args.get("per_page", type=int)

    result = transaction_service.get_transactions(
        user_id=user_id,
        account_id=account_id,
        page=page,
        per_page=per_page,
    )
    return jsonify(result)


@transactions_bp.route("/transactions/<int:transaction_id>", methods=["DELETE"])
@jwt_required()
def delete_transaction(transaction_id):
    user_id = int(get_jwt_identity())
    result = transaction_service.delete_transaction(user_id, transaction_id)
    return jsonify(result)
