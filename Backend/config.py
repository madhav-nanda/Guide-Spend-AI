"""
Centralized configuration loaded from environment variables.
Single source of truth for all settings across the application.
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration."""

    # ── Flask ──
    SECRET_KEY = os.getenv("JWT_SECRET", "change-me-in-production")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET", "change-me-in-production")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)

    # ── Database (Supabase PostgreSQL) ──
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = int(os.getenv("DB_PORT", 5432))
    DB_NAME = os.getenv("DB_NAME", "postgres")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_SSLMODE = "require"

    # Connection pool sizing
    DB_POOL_MIN = int(os.getenv("DB_POOL_MIN", 2))
    DB_POOL_MAX = int(os.getenv("DB_POOL_MAX", 10))

    # ── Plaid ──
    PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID")
    PLAID_SECRET = os.getenv("PLAID_SECRET")
    PLAID_ENV = os.getenv("PLAID_ENV", "sandbox")

    # ── Encryption ──
    PLAID_ENCRYPTION_KEY = os.getenv("PLAID_ENCRYPTION_KEY")

    # ── Pagination defaults ──
    DEFAULT_PAGE = 1
    DEFAULT_PER_PAGE = 50
    MAX_PER_PAGE = 200
