"""
Plaid service — all Plaid API interactions and banking logic.
Handles link tokens, token exchange, account fetching, and transaction sync.
No HTTP concepts. Pure business orchestration.
"""
import json
import plaid
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.transactions_sync_request import TransactionsSyncRequest
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.item_remove_request import ItemRemoveRequest
from plaid.model.products import Products
from plaid.model.country_code import CountryCode

from models import plaid_item as item_model
from models import transaction as txn_model
from utils.encryption import encrypt_token, decrypt_token
from utils.errors import NotFoundError, PlaidError, ValidationError
from utils.logger import get_logger

log = get_logger("plaid_service")

# ── Plaid client (initialized by extensions.py) ──
_plaid_client = None


def init_plaid_client(client):
    """Set the Plaid API client. Called once at startup."""
    global _plaid_client
    _plaid_client = client


# ═══════════════════════════════════════════════════
# Link Token
# ═══════════════════════════════════════════════════

def create_link_token(user_id: int) -> str:
    """Generate a Plaid Link token for the frontend widget."""
    try:
        req = LinkTokenCreateRequest(
            products=[Products("transactions")],
            client_name="GuideSpend AI",
            country_codes=[CountryCode("US")],
            language="en",
            user=LinkTokenCreateRequestUser(client_user_id=str(user_id)),
        )
        resp = _plaid_client.link_token_create(req)
        log.info("Link token created", extra={"context": {"user_id": user_id}})
        return resp["link_token"]

    except plaid.ApiException as e:
        _raise_plaid_error(e, "create_link_token")


# ═══════════════════════════════════════════════════
# Token Exchange
# ═══════════════════════════════════════════════════

def exchange_public_token(user_id: int, public_token: str,
                          institution_id: str, institution_name: str) -> dict:
    """Exchange a Plaid public_token for an access_token and store it securely."""
    if not public_token:
        raise ValidationError("public_token is required")

    try:
        exchange_req = ItemPublicTokenExchangeRequest(public_token=public_token)
        exchange_resp = _plaid_client.item_public_token_exchange(exchange_req)
    except plaid.ApiException as e:
        _raise_plaid_error(e, "exchange_token")

    access_token = exchange_resp["access_token"]
    item_id = exchange_resp["item_id"]

    encrypted = encrypt_token(access_token)

    item_model.upsert(
        user_id=user_id,
        encrypted_token=encrypted,
        item_id=item_id,
        institution_id=institution_id,
        institution_name=institution_name,
    )

    log.info(
        "Token exchanged and stored",
        extra={"context": {"user_id": user_id, "item_id": item_id, "institution": institution_name}},
    )

    return {
        "message": "Bank account linked successfully",
        "item_id": item_id,
        "institution_name": institution_name,
    }


# ═══════════════════════════════════════════════════
# Accounts
# ═══════════════════════════════════════════════════

def get_accounts(user_id: int) -> list:
    """Fetch all linked bank accounts with real-time balances from Plaid."""
    items = item_model.find_tokens_for_accounts(user_id)

    if not items:
        return []

    all_accounts = []

    for encrypted_token, item_id, institution_name in items:
        access_token = decrypt_token(encrypted_token)

        try:
            req = AccountsGetRequest(access_token=access_token)
            resp = _plaid_client.accounts_get(req)

            for acct in resp["accounts"]:
                all_accounts.append({
                    "item_id": item_id,
                    "institution_name": institution_name,
                    "account_id": acct["account_id"],
                    "name": acct["name"],
                    "official_name": acct.get("official_name", ""),
                    "type": str(acct["type"]),
                    "subtype": str(acct.get("subtype", "")),
                    "mask": acct.get("mask", ""),
                    "current_balance": acct["balances"]["current"],
                    "available_balance": acct["balances"].get("available"),
                    "currency": acct["balances"].get("iso_currency_code", "USD"),
                })

        except plaid.ApiException as e:
            error_body = json.loads(e.body)
            all_accounts.append({
                "item_id": item_id,
                "institution_name": institution_name,
                "error": error_body.get("error_message", "Failed to fetch accounts"),
            })

    log.info(
        "Accounts fetched",
        extra={"context": {"user_id": user_id, "count": len(all_accounts)}},
    )
    return all_accounts


# ═══════════════════════════════════════════════════
# Transaction Sync
# ═══════════════════════════════════════════════════

def sync_transactions(user_id: int) -> dict:
    """
    Cursor-based incremental sync from Plaid.
    Fetches account names, tags every transaction with
    plaid_account_id + institution_name + account_name.
    """
    items = item_model.find_by_user(user_id)

    if not items:
        raise NotFoundError("No linked bank accounts found. Connect a bank first.")

    total_added = 0
    total_modified = 0
    total_removed = 0

    for plaid_item_db_id, encrypted_token, saved_cursor, inst_name, item_id_str in items:
        access_token = decrypt_token(encrypted_token)

        # ── Build account_id → account_name map ──
        account_name_map = _fetch_account_name_map(access_token)

        cursor = saved_cursor or ""
        has_more = True

        while has_more:
            try:
                resp = _plaid_client.transactions_sync(
                    TransactionsSyncRequest(access_token=access_token, cursor=cursor)
                )
            except plaid.ApiException as e:
                _raise_plaid_error(e, "sync_transactions")

            # ── ADDED ──
            for txn in resp["added"]:
                parsed = _parse_plaid_txn(txn, inst_name, account_name_map)
                txn_model.upsert_plaid_transaction(user_id=user_id, **parsed)
                total_added += 1

            # ── MODIFIED ──
            for txn in resp["modified"]:
                parsed = _parse_plaid_txn(txn, inst_name, account_name_map)
                txn_model.update_plaid_transaction(user_id=user_id, **parsed)
                total_modified += 1

            # ── REMOVED ──
            for txn in resp["removed"]:
                txn_model.delete_by_plaid_id(user_id, txn["transaction_id"])
                total_removed += 1

            cursor = resp["next_cursor"]
            has_more = resp["has_more"]

        # ── Persist cursor for next incremental sync ──
        item_model.update_cursor(plaid_item_db_id, cursor)

    log.info(
        "Transaction sync complete",
        extra={"context": {
            "user_id": user_id,
            "added": total_added,
            "modified": total_modified,
            "removed": total_removed,
        }},
    )

    return {
        "message": "Transactions synced successfully",
        "added": total_added,
        "modified": total_modified,
        "removed": total_removed,
    }


# ═══════════════════════════════════════════════════
# Disconnect
# ═══════════════════════════════════════════════════

def disconnect_item(user_id: int, item_id: str) -> dict:
    """
    Disconnect a linked bank:
    1. Verify ownership
    2. Get account IDs for targeted transaction deletion
    3. Revoke Plaid access token
    4. Delete related transactions (only this item's)
    5. Delete the plaid_item record
    """
    row = item_model.find_by_item_id_and_user(item_id, user_id)
    if not row:
        raise NotFoundError("Linked account not found")

    _, encrypted_token = row
    access_token = decrypt_token(encrypted_token)

    # ── Step 1: Get account IDs for targeted deletion ──
    account_ids = []
    try:
        req = AccountsGetRequest(access_token=access_token)
        resp = _plaid_client.accounts_get(req)
        account_ids = [a["account_id"] for a in resp["accounts"]]
    except plaid.ApiException:
        log.warning("Could not fetch accounts for disconnect — will skip transaction cleanup",
                     extra={"context": {"item_id": item_id}})

    # ── Step 2: Revoke with Plaid ──
    try:
        _plaid_client.item_remove(ItemRemoveRequest(access_token=access_token))
    except plaid.ApiException:
        pass  # Item may already be invalid

    # ── Step 3: Delete only this item's transactions ──
    removed_txns = txn_model.delete_by_account_ids(user_id, account_ids)

    # ── Step 4: Delete the plaid_item record ──
    item_model.delete_by_item_id_and_user(item_id, user_id)

    log.info(
        "Account disconnected",
        extra={"context": {"user_id": user_id, "item_id": item_id, "txns_removed": removed_txns}},
    )

    return {
        "message": "Bank account disconnected successfully",
        "transactions_removed": removed_txns,
    }


# ═══════════════════════════════════════════════════
# Private Helpers
# ═══════════════════════════════════════════════════

def _fetch_account_name_map(access_token: str) -> dict:
    """Fetch {account_id: account_name} from Plaid for a given access token."""
    try:
        req = AccountsGetRequest(access_token=access_token)
        resp = _plaid_client.accounts_get(req)
        return {a["account_id"]: a["name"] for a in resp["accounts"]}
    except plaid.ApiException:
        return {}


def _parse_plaid_txn(txn, institution_name: str, account_name_map: dict) -> dict:
    """Normalize a raw Plaid transaction object into our DB columns."""
    plaid_account_id = txn["account_id"]

    category = "Uncategorized"
    if txn.get("personal_finance_category"):
        category = txn["personal_finance_category"]["primary"]
    elif txn.get("category"):
        category = txn["category"][0]

    return {
        "amount": -txn["amount"],  # Plaid flips sign
        "category": category,
        "description": txn.get("name", ""),
        "date": str(txn["date"]),
        "plaid_transaction_id": txn["transaction_id"],
        "plaid_account_id": plaid_account_id,
        "institution_name": institution_name,
        "account_name": account_name_map.get(plaid_account_id, ""),
    }


def _raise_plaid_error(api_exception, operation: str):
    """Parse a Plaid ApiException and raise our PlaidError."""
    try:
        body = json.loads(api_exception.body)
        msg = body.get("error_message", "Plaid API error")
    except Exception:
        msg = "Plaid API error"

    log.error(f"Plaid error in {operation}: {msg}")
    raise PlaidError(msg)
