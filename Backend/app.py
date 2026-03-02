from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity
)
import psycopg2
import bcrypt
import os
import time
import json
from dotenv import load_dotenv
from cryptography.fernet import Fernet

import plaid
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.transactions_sync_request import TransactionsSyncRequest
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.item_remove_request import ItemRemoveRequest
from plaid.model.products import Products
from plaid.model.country_code import CountryCode

load_dotenv()

app = Flask(__name__)
CORS(app)

app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET")
jwt = JWTManager(app)

# ---------------------
# Plaid Client Setup
# ---------------------
PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID")
PLAID_SECRET = os.getenv("PLAID_SECRET")
PLAID_ENV = os.getenv("PLAID_ENV", "sandbox")

plaid_env_map = {
    "sandbox": plaid.Environment.Sandbox,
    "production": plaid.Environment.Production,
}

plaid_config = plaid.Configuration(
    host=plaid_env_map.get(PLAID_ENV, plaid.Environment.Sandbox),
    api_key={
        "clientId": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
    }
)
api_client = plaid.ApiClient(plaid_config)
plaid_client = plaid_api.PlaidApi(api_client)

# ---------------------
# Encryption Helpers
# ---------------------
FERNET_KEY = os.getenv("PLAID_ENCRYPTION_KEY")
fernet = Fernet(FERNET_KEY.encode()) if FERNET_KEY else None


def encrypt_token(token):
    """Encrypt an access token before storing in DB."""
    return fernet.encrypt(token.encode()).decode()


def decrypt_token(encrypted_token):
    """Decrypt an access token retrieved from DB."""
    return fernet.decrypt(encrypted_token.encode()).decode()


def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        sslmode="require"
    )


@app.route("/")
def home():
    return jsonify({"message": "AI Banking Backend Running"})


@app.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data["username"]
    email = data["email"]
    password = data["password"]

    hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO users (username, email, password_hash, created_at) VALUES (%s, %s, %s, NOW())",
            (username, email, hashed_pw.decode("utf-8"))
        )
        conn.commit()
        return jsonify({"message": "User registered successfully"})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cur.close()
        conn.close()


@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data["email"]
    password = data["password"]

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, password_hash FROM users WHERE email = %s", (email,))
    user = cur.fetchone()

    cur.close()
    conn.close()

    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    user_id, stored_hash = user

    if bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8")):
        access_token = create_access_token(identity=str(user_id))
        return jsonify({"access_token": access_token})

    return jsonify({"error": "Invalid credentials"}), 401


@app.route("/protected", methods=["GET"])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify({"logged_in_as": current_user})
@app.route("/transactions", methods=["POST"])
@jwt_required()
def add_transaction():
    user_id = get_jwt_identity()
    data = request.json

    amount = data["amount"]
    category = data["category"]
    description = data["description"]
    date = data["date"]

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            INSERT INTO transactions 
            (user_id, amount, category, description, date, created_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
            """,
            (int(user_id), amount, category, description, date)
        )
        conn.commit()
        return jsonify({"message": "Transaction added successfully"})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cur.close()
        conn.close()
@app.route("/transactions", methods=["GET"])
@jwt_required()
def get_transactions():
    user_id = get_jwt_identity()
    account_id = request.args.get("account_id")  # Optional filter

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        if account_id:
            cur.execute(
                """
                SELECT id, amount, category, description, date, created_at,
                       plaid_transaction_id, source, plaid_account_id,
                       institution_name, account_name
                FROM transactions
                WHERE user_id = %s AND plaid_account_id = %s
                ORDER BY date DESC
                """,
                (int(user_id), account_id)
            )
        else:
            cur.execute(
                """
                SELECT id, amount, category, description, date, created_at,
                       plaid_transaction_id, source, plaid_account_id,
                       institution_name, account_name
                FROM transactions
                WHERE user_id = %s
                ORDER BY date DESC
                """,
                (int(user_id),)
            )

        rows = cur.fetchall()

        transactions = []
        for row in rows:
            transactions.append({
                "id": row[0],
                "amount": float(row[1]),
                "category": row[2],
                "description": row[3],
                "date": str(row[4]),
                "created_at": str(row[5]),
                "plaid_transaction_id": row[6],
                "source": row[7] or "manual",
                "plaid_account_id": row[8],
                "institution_name": row[9],
                "account_name": row[10]
            })

        return jsonify(transactions)

    except Exception as e:
        return jsonify({"error": str(e)}), 400

    finally:
        cur.close()
        conn.close()

@app.route("/transactions/<int:transaction_id>", methods=["DELETE"])
@jwt_required()
def delete_transaction(transaction_id):
    user_id = get_jwt_identity()

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            DELETE FROM transactions
            WHERE id = %s AND user_id = %s
            """,
            (transaction_id, int(user_id))
        )

        conn.commit()

        if cur.rowcount == 0:
            return jsonify({"error": "Transaction not found"}), 404

        return jsonify({"message": "Transaction deleted successfully"})

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400

    finally:
        cur.close()
        conn.close()


# ===================================
# Plaid Integration Endpoints
# ===================================

@app.route("/plaid/create_link_token", methods=["POST"])
@jwt_required()
def create_link_token():
    """Generate a Plaid Link token for the frontend to open the Plaid widget."""
    user_id = get_jwt_identity()

    try:
        link_request = LinkTokenCreateRequest(
            products=[Products("transactions")],
            client_name="AI Banking Platform",
            country_codes=[CountryCode("US")],
            language="en",
            user=LinkTokenCreateRequestUser(client_user_id=str(user_id))
        )

        response = plaid_client.link_token_create(link_request)
        return jsonify({"link_token": response["link_token"]})

    except plaid.ApiException as e:
        error_response = json.loads(e.body)
        return jsonify({"error": error_response.get("error_message", "Plaid error")}), 400


@app.route("/plaid/exchange_token", methods=["POST"])
@jwt_required()
def exchange_token():
    """Exchange a Plaid public_token for an access_token and store it securely."""
    user_id = get_jwt_identity()
    data = request.json
    public_token = data.get("public_token")
    institution_id = data.get("institution_id", "")
    institution_name = data.get("institution_name", "")

    if not public_token:
        return jsonify({"error": "public_token is required"}), 400

    try:
        # Exchange public token for access token
        exchange_request = ItemPublicTokenExchangeRequest(public_token=public_token)
        exchange_response = plaid_client.item_public_token_exchange(exchange_request)

        access_token = exchange_response["access_token"]
        item_id = exchange_response["item_id"]

        # Encrypt the access token before storing
        encrypted_token = encrypt_token(access_token)

        conn = get_db_connection()
        cur = conn.cursor()

        try:
            # Check if user already has this item linked
            cur.execute("SELECT id FROM plaid_items WHERE item_id = %s", (item_id,))
            existing = cur.fetchone()

            if existing:
                # Update existing item
                cur.execute(
                    """
                    UPDATE plaid_items
                    SET access_token = %s, institution_id = %s, institution_name = %s, updated_at = NOW()
                    WHERE item_id = %s
                    """,
                    (encrypted_token, institution_id, institution_name, item_id)
                )
            else:
                # Insert new item
                cur.execute(
                    """
                    INSERT INTO plaid_items
                    (user_id, access_token, item_id, institution_id, institution_name, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                    """,
                    (int(user_id), encrypted_token, item_id, institution_id, institution_name)
                )

            conn.commit()
            return jsonify({
                "message": "Bank account linked successfully",
                "item_id": item_id,
                "institution_name": institution_name
            })

        except Exception as e:
            conn.rollback()
            return jsonify({"error": str(e)}), 400
        finally:
            cur.close()
            conn.close()

    except plaid.ApiException as e:
        error_response = json.loads(e.body)
        return jsonify({"error": error_response.get("error_message", "Plaid error")}), 400


@app.route("/plaid/sync_transactions", methods=["POST"])
@jwt_required()
def sync_transactions():
    """Fetch transactions from Plaid using cursor-based sync and store them with account-level detail."""
    user_id = get_jwt_identity()

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Get all linked Plaid items for this user
        cur.execute(
            "SELECT id, access_token, cursor, institution_name FROM plaid_items WHERE user_id = %s",
            (int(user_id),)
        )
        items = cur.fetchall()

        if not items:
            return jsonify({"error": "No linked bank accounts found. Connect a bank first."}), 404

        total_added = 0
        total_modified = 0
        total_removed = 0

        for item_row in items:
            plaid_item_id, encrypted_token, saved_cursor, inst_name = item_row
            access_token = decrypt_token(encrypted_token)

            # ── Fetch account names for this item so we can tag each transaction ──
            account_name_map = {}
            try:
                acct_req = AccountsGetRequest(access_token=access_token)
                acct_resp = plaid_client.accounts_get(acct_req)
                for acct in acct_resp["accounts"]:
                    account_name_map[acct["account_id"]] = acct["name"]
            except plaid.ApiException:
                pass  # If accounts fetch fails, we'll use empty names

            cursor = saved_cursor or ""
            has_more = True

            while has_more:
                sync_request = TransactionsSyncRequest(
                    access_token=access_token,
                    cursor=cursor
                )

                try:
                    response = plaid_client.transactions_sync(sync_request)
                except plaid.ApiException as e:
                    error_response = json.loads(e.body)
                    return jsonify({"error": error_response.get("error_message", "Plaid sync error")}), 400

                # Process ADDED transactions
                for txn in response["added"]:
                    plaid_txn_id = txn["transaction_id"]
                    plaid_account_id = txn["account_id"]
                    amount = -txn["amount"]  # Plaid uses negative for income, we flip
                    category = txn["personal_finance_category"]["primary"] if txn.get("personal_finance_category") else (txn["category"][0] if txn.get("category") else "Uncategorized")
                    description = txn.get("name", "")
                    date = str(txn["date"])
                    acct_name = account_name_map.get(plaid_account_id, "")

                    # Upsert: insert or update on conflict
                    cur.execute(
                        """
                        INSERT INTO transactions
                        (user_id, amount, category, description, date,
                         plaid_transaction_id, source, plaid_account_id,
                         institution_name, account_name, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, 'plaid', %s, %s, %s, NOW())
                        ON CONFLICT (plaid_transaction_id) DO UPDATE SET
                            amount = EXCLUDED.amount,
                            category = EXCLUDED.category,
                            description = EXCLUDED.description,
                            date = EXCLUDED.date,
                            plaid_account_id = EXCLUDED.plaid_account_id,
                            institution_name = EXCLUDED.institution_name,
                            account_name = EXCLUDED.account_name
                        """,
                        (int(user_id), amount, category, description, date,
                         plaid_txn_id, plaid_account_id, inst_name, acct_name)
                    )
                    total_added += 1

                # Process MODIFIED transactions
                for txn in response["modified"]:
                    plaid_txn_id = txn["transaction_id"]
                    plaid_account_id = txn["account_id"]
                    amount = -txn["amount"]
                    category = txn["personal_finance_category"]["primary"] if txn.get("personal_finance_category") else (txn["category"][0] if txn.get("category") else "Uncategorized")
                    description = txn.get("name", "")
                    date = str(txn["date"])
                    acct_name = account_name_map.get(plaid_account_id, "")

                    cur.execute(
                        """
                        UPDATE transactions
                        SET amount = %s, category = %s, description = %s, date = %s,
                            plaid_account_id = %s, institution_name = %s, account_name = %s
                        WHERE plaid_transaction_id = %s AND user_id = %s
                        """,
                        (amount, category, description, date,
                         plaid_account_id, inst_name, acct_name,
                         plaid_txn_id, int(user_id))
                    )
                    total_modified += 1

                # Process REMOVED transactions
                for txn in response["removed"]:
                    plaid_txn_id = txn["transaction_id"]
                    cur.execute(
                        "DELETE FROM transactions WHERE plaid_transaction_id = %s AND user_id = %s",
                        (plaid_txn_id, int(user_id))
                    )
                    total_removed += 1

                cursor = response["next_cursor"]
                has_more = response["has_more"]

            # Save the latest cursor for this item
            cur.execute(
                "UPDATE plaid_items SET cursor = %s, updated_at = NOW() WHERE id = %s",
                (cursor, plaid_item_id)
            )

        conn.commit()

        return jsonify({
            "message": "Transactions synced successfully",
            "added": total_added,
            "modified": total_modified,
            "removed": total_removed
        })

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()


@app.route("/plaid/accounts", methods=["GET"])
@jwt_required()
def get_plaid_accounts():
    """List all linked bank accounts and their balances for the authenticated user."""
    user_id = get_jwt_identity()

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            "SELECT access_token, item_id, institution_name FROM plaid_items WHERE user_id = %s",
            (int(user_id),)
        )
        items = cur.fetchall()

        if not items:
            return jsonify({"accounts": [], "message": "No linked bank accounts"})

        all_accounts = []

        for encrypted_token, item_id, institution_name in items:
            access_token = decrypt_token(encrypted_token)

            try:
                accounts_request = AccountsGetRequest(access_token=access_token)
                response = plaid_client.accounts_get(accounts_request)

                for account in response["accounts"]:
                    all_accounts.append({
                        "item_id": item_id,
                        "institution_name": institution_name,
                        "account_id": account["account_id"],
                        "name": account["name"],
                        "official_name": account.get("official_name", ""),
                        "type": str(account["type"]),
                        "subtype": str(account.get("subtype", "")),
                        "mask": account.get("mask", ""),
                        "current_balance": account["balances"]["current"],
                        "available_balance": account["balances"].get("available"),
                        "currency": account["balances"].get("iso_currency_code", "USD")
                    })

            except plaid.ApiException as e:
                error_response = json.loads(e.body)
                all_accounts.append({
                    "item_id": item_id,
                    "institution_name": institution_name,
                    "error": error_response.get("error_message", "Failed to fetch accounts")
                })

        return jsonify({"accounts": all_accounts})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()


@app.route("/plaid/disconnect/<item_id>", methods=["DELETE"])
@jwt_required()
def disconnect_plaid(item_id):
    """Revoke Plaid access and remove only this specific linked bank item and its transactions."""
    user_id = get_jwt_identity()

    if not item_id:
        return jsonify({"error": "item_id is required"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Get the access token for this item (ownership check)
        cur.execute(
            "SELECT access_token FROM plaid_items WHERE item_id = %s AND user_id = %s",
            (item_id, int(user_id))
        )
        row = cur.fetchone()

        if not row:
            return jsonify({"error": "Linked account not found"}), 404

        encrypted_token = row[0]
        access_token = decrypt_token(encrypted_token)

        # ── Step 1: Get account IDs belonging to this item ──
        account_ids = []
        try:
            acct_req = AccountsGetRequest(access_token=access_token)
            acct_resp = plaid_client.accounts_get(acct_req)
            account_ids = [a["account_id"] for a in acct_resp["accounts"]]
        except plaid.ApiException:
            pass  # If fetch fails, fall back to deleting by item association

        # ── Step 2: Revoke the access token with Plaid ──
        try:
            remove_request = ItemRemoveRequest(access_token=access_token)
            plaid_client.item_remove(remove_request)
        except plaid.ApiException:
            pass  # Item may already be invalid; continue cleanup

        # ── Step 3: Delete ONLY transactions belonging to this item's accounts ──
        removed_txns = 0
        if account_ids:
            placeholders = ",".join(["%s"] * len(account_ids))
            cur.execute(
                f"""
                DELETE FROM transactions
                WHERE user_id = %s AND source = 'plaid'
                AND plaid_account_id IN ({placeholders})
                """,
                [int(user_id)] + account_ids
            )
            removed_txns = cur.rowcount
        else:
            # Fallback: if we couldn't fetch accounts, remove nothing extra
            # (transactions without account_id mapping are orphaned already)
            pass

        # ── Step 4: Delete the plaid item record ──
        cur.execute(
            "DELETE FROM plaid_items WHERE item_id = %s AND user_id = %s",
            (item_id, int(user_id))
        )

        conn.commit()

        return jsonify({
            "message": "Bank account disconnected successfully",
            "transactions_removed": removed_txns
        })

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    app.run(debug=True)

