"""
Database connection pool using psycopg2.pool.
Provides a context manager for safe acquire/release of connections.
"""
from contextlib import contextmanager
from psycopg2 import pool
from config import Config
from utils.logger import get_logger

log = get_logger("db")

_pool = None


def init_pool():
    """Initialize the connection pool. Called once at app startup."""
    global _pool
    if _pool is not None:
        return

    log.info(
        "Initializing DB connection pool",
        extra={"context": {"host": Config.DB_HOST, "min": Config.DB_POOL_MIN, "max": Config.DB_POOL_MAX}},
    )
    _pool = pool.ThreadedConnectionPool(
        minconn=Config.DB_POOL_MIN,
        maxconn=Config.DB_POOL_MAX,
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        database=Config.DB_NAME,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        sslmode=Config.DB_SSLMODE,
    )


def close_pool():
    """Close all connections in the pool. Called at app shutdown."""
    global _pool
    if _pool:
        _pool.closeall()
        _pool = None
        log.info("DB connection pool closed")


@contextmanager
def get_db():
    """
    Context manager that yields (conn, cur).
    Auto-commits on success, rolls back on exception,
    and always returns the connection to the pool.

    Usage:
        with get_db() as (conn, cur):
            cur.execute("SELECT 1")
            rows = cur.fetchall()
    """
    conn = _pool.getconn()
    cur = conn.cursor()
    try:
        yield conn, cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        _pool.putconn(conn)
