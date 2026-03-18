"""
Plaid routes — /plaid/*
Thin handlers for bank linking, account listing, sync, and disconnect.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from services import plaid_service

plaid_bp = Blueprint("plaid", __name__)


@plaid_bp.route("/create_link_token", methods=["POST"])
@jwt_required()
def create_link_token():
    user_id = int(get_jwt_identity())
    link_token = plaid_service.create_link_token(user_id)
    return jsonify({"link_token": link_token})


@plaid_bp.route("/exchange_token", methods=["POST"])
@jwt_required()
def exchange_token():
    user_id = int(get_jwt_identity())
    data = request.json
    result = plaid_service.exchange_public_token(
        user_id=user_id,
        public_token=data.get("public_token"),
        institution_id=data.get("institution_id", ""),
        institution_name=data.get("institution_name", ""),
    )
    return jsonify(result)


@plaid_bp.route("/sync_transactions", methods=["POST"])
@jwt_required()
def sync_transactions():
    user_id = int(get_jwt_identity())
    result = plaid_service.sync_transactions(user_id)
    return jsonify(result)


@plaid_bp.route("/accounts", methods=["GET"])
@jwt_required()
def get_accounts():
    user_id = int(get_jwt_identity())
    accounts = plaid_service.get_accounts(user_id)
    return jsonify({"accounts": accounts})


@plaid_bp.route("/disconnect/<item_id>", methods=["DELETE"])
@jwt_required()
def disconnect(item_id):
    user_id = int(get_jwt_identity())
    result = plaid_service.disconnect_item(user_id, item_id)
    return jsonify(result)
