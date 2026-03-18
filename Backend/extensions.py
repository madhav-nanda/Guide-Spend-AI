"""
Extension initialization — JWT and Plaid client.
Created once, imported wherever needed.
"""
import plaid
from plaid.api import plaid_api
from flask_jwt_extended import JWTManager
from config import Config

# ── JWT ──
jwt = JWTManager()

# ── Plaid Client ──
_plaid_env_map = {
    "sandbox": plaid.Environment.Sandbox,
    "production": plaid.Environment.Production,
}


def create_plaid_client():
    """Build and return a configured Plaid API client."""
    plaid_config = plaid.Configuration(
        host=_plaid_env_map.get(Config.PLAID_ENV, plaid.Environment.Sandbox),
        api_key={
            "clientId": Config.PLAID_CLIENT_ID,
            "secret": Config.PLAID_SECRET,
        },
    )
    api_client = plaid.ApiClient(plaid_config)
    return plaid_api.PlaidApi(api_client)
