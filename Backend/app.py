"""
Application factory.
This is the ONLY file that knows about Flask setup.
It wires together: config, extensions, routes, error handlers, and startup hooks.
"""
import os
from flask import Flask
from flask_cors import CORS
from config import Config
from extensions import jwt, create_plaid_client
from routes import register_blueprints
from utils.db import init_pool, close_pool
from utils.encryption import init_fernet
from utils.errors import register_error_handlers
from utils.logger import get_logger
from services import plaid_service

log = get_logger("app")


def create_app() -> Flask:
    """Build and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # ── CORS — allow deployed frontend + localhost for dev ──
    allowed_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    CORS(app, origins=allowed_origins, supports_credentials=True)
    jwt.init_app(app)

    # ── Infrastructure ──
    init_pool()
    init_fernet()

    # ── Plaid client → inject into service layer ──
    plaid_client = create_plaid_client()
    plaid_service.init_plaid_client(plaid_client)

    # ── Blueprints ──
    register_blueprints(app)

    # ── Error handlers ──
    register_error_handlers(app)

    # ── Shutdown hook ──
    import atexit
    atexit.register(close_pool)

    log.info("Application initialized", extra={"context": {"env": Config.PLAID_ENV}})
    return app


# ── Module-level app for gunicorn: `gunicorn app:app` ──
app = create_app()

# ── Entry point (local dev only — production uses gunicorn) ──
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)), debug=True)
