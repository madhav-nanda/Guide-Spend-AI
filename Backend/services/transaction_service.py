"""
Transaction service — CRUD operations and pagination.
Orchestrates model calls with validation.
"""
from models import transaction as txn_model
from config import Config
from utils.errors import ValidationError, NotFoundError
from utils.logger import get_logger

log = get_logger("transaction_service")


def add_manual_transaction(user_id: int, data: dict) -> dict:
    """
    Create a manually-entered transaction.
    Validates required fields.
    """
    amount = data.get("amount")
    category = data.get("category")
    description = data.get("description")
    date = data.get("date")

    if amount is None or not date:
        raise ValidationError("amount and date are required")

    txn_id = txn_model.create_manual(
        user_id=user_id,
        amount=amount,
        category=category or "Uncategorized",
        description=description or "",
        date=date,
    )

    log.info("Manual transaction created", extra={"context": {"user_id": user_id, "txn_id": txn_id}})
    return {"message": "Transaction added successfully", "id": txn_id}


def get_transactions(user_id: int, account_id: str = None,
                     page: int = None, per_page: int = None) -> dict:
    """
    Retrieve paginated transactions, optionally filtered by account.
    Returns { transactions: [...], pagination: {...} }.
    """
    page = page or Config.DEFAULT_PAGE
    per_page = per_page or Config.DEFAULT_PER_PAGE
    per_page = min(per_page, Config.MAX_PER_PAGE)

    result = txn_model.find_paginated(
        user_id=user_id,
        account_id=account_id,
        page=page,
        per_page=per_page,
    )

    log.info(
        "Transactions fetched",
        extra={"context": {
            "user_id": user_id,
            "account_id": account_id,
            "page": page,
            "total": result["pagination"]["total"],
        }},
    )
    return result


def delete_transaction(user_id: int, transaction_id: int) -> dict:
    """Delete a transaction by ID. Verifies ownership via user_id."""
    rows_deleted = txn_model.delete_by_id(user_id, transaction_id)

    if rows_deleted == 0:
        raise NotFoundError("Transaction not found")

    log.info("Transaction deleted", extra={"context": {"user_id": user_id, "txn_id": transaction_id}})
    return {"message": "Transaction deleted successfully"}
