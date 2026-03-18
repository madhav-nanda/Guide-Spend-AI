"""
Fernet symmetric encryption for sensitive tokens (Plaid access tokens).
Tokens are encrypted before DB storage and decrypted only when needed for API calls.
"""
from cryptography.fernet import Fernet
from config import Config
from utils.logger import get_logger

log = get_logger("encryption")

_fernet = None


def init_fernet():
    """Initialize the Fernet cipher. Called once at app startup."""
    global _fernet
    key = Config.PLAID_ENCRYPTION_KEY
    if not key:
        log.error("PLAID_ENCRYPTION_KEY not set — token encryption disabled")
        return
    _fernet = Fernet(key.encode())


def encrypt_token(token: str) -> str:
    """Encrypt a plaintext token for storage."""
    if not _fernet:
        raise RuntimeError("Fernet not initialized — cannot encrypt")
    return _fernet.encrypt(token.encode()).decode()


def decrypt_token(encrypted_token: str) -> str:
    """Decrypt a stored token for use in API calls."""
    if not _fernet:
        raise RuntimeError("Fernet not initialized — cannot decrypt")
    return _fernet.decrypt(encrypted_token.encode()).decode()
