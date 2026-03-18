"""
Structured JSON logging for production observability.
Every log line is machine-parseable with consistent fields.
"""
import logging
import json
import sys
import traceback
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    """Outputs each log record as a single JSON line."""

    def format(self, record):
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Attach extra context if provided (e.g., user_id, endpoint, item_id)
        if hasattr(record, "context") and record.context:
            log_entry["context"] = record.context

        # Attach exception info if present
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info),
            }

        return json.dumps(log_entry, default=str)


def get_logger(name: str) -> logging.Logger:
    """Create a logger with JSON formatting for the given module name."""
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False

    return logger
