"""
Centralized error handling.
Custom exceptions map to HTTP status codes.
Flask error handlers catch them and return consistent JSON responses.
"""
from flask import jsonify
from utils.logger import get_logger

log = get_logger("errors")


# ──────────────────────────────────────────────
# Custom Exception Hierarchy
# ──────────────────────────────────────────────

class AppError(Exception):
    """Base application error. All custom errors inherit from this."""
    status_code = 500
    message = "Internal server error"

    def __init__(self, message=None, status_code=None, context=None):
        self.message = message or self.__class__.message
        self.status_code = status_code or self.__class__.status_code
        self.context = context or {}
        super().__init__(self.message)


class ValidationError(AppError):
    """Raised when request data fails validation."""
    status_code = 400
    message = "Validation error"


class AuthenticationError(AppError):
    """Raised when credentials are invalid."""
    status_code = 401
    message = "Invalid credentials"


class NotFoundError(AppError):
    """Raised when a requested resource does not exist."""
    status_code = 404
    message = "Resource not found"


class ConflictError(AppError):
    """Raised when a resource already exists (e.g., duplicate email)."""
    status_code = 409
    message = "Resource already exists"


class PlaidError(AppError):
    """Raised when a Plaid API call fails."""
    status_code = 502
    message = "Banking service error"


class DatabaseError(AppError):
    """Raised when a database operation fails unexpectedly."""
    status_code = 500
    message = "Database error"


# ──────────────────────────────────────────────
# Flask Error Handler Registration
# ──────────────────────────────────────────────

def register_error_handlers(app):
    """Register centralized error handlers on the Flask app."""

    @app.errorhandler(AppError)
    def handle_app_error(error):
        log.error(
            error.message,
            extra={"context": {"status": error.status_code, **error.context}},
        )
        response = {"error": error.message}
        return jsonify(response), error.status_code

    @app.errorhandler(404)
    def handle_404(error):
        return jsonify({"error": "Endpoint not found"}), 404

    @app.errorhandler(405)
    def handle_405(error):
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(500)
    def handle_500(error):
        log.error("Unhandled server error", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500
