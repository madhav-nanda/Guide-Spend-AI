"""
Authentication service — password hashing, credential verification, JWT creation.
No HTTP or Flask request objects here. Pure business logic.
"""
import bcrypt
from flask_jwt_extended import create_access_token

from models import user as user_model
from utils.errors import AuthenticationError, ConflictError, ValidationError
from utils.logger import get_logger

log = get_logger("auth_service")


def register_user(username: str, email: str, password: str) -> dict:
    """
    Register a new user.
    Raises ConflictError if email already exists.
    Returns {"user_id": int, "message": str}.
    """
    if not username or not email or not password:
        raise ValidationError("username, email, and password are required")

    if len(password) < 6:
        raise ValidationError("Password must be at least 6 characters")

    # Hash the password
    hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    try:
        user_id = user_model.create_user(username, email, hashed_pw.decode("utf-8"))
    except Exception as e:
        err_msg = str(e)
        if "duplicate key" in err_msg or "unique constraint" in err_msg.lower():
            raise ConflictError("An account with this email already exists")
        raise

    log.info("User registered", extra={"context": {"user_id": user_id, "email": email}})
    return {"user_id": user_id, "message": "User registered successfully"}


def authenticate_user(email: str, password: str) -> dict:
    """
    Verify credentials and return a JWT.
    Raises AuthenticationError on bad credentials.
    Returns {"access_token": str}.
    """
    if not email or not password:
        raise ValidationError("email and password are required")

    row = user_model.find_by_email(email)
    if not row:
        raise AuthenticationError()

    user_id, stored_hash = row

    if not bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8")):
        raise AuthenticationError()

    access_token = create_access_token(identity=str(user_id))

    log.info("User authenticated", extra={"context": {"user_id": user_id}})
    return {"access_token": access_token}
