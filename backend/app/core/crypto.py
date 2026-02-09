"""
Field-level encryption for sensitive data (API keys, session cookies).
Uses Fernet symmetric encryption keyed from settings.ENCRYPTION_KEY.
"""
import os
import base64
import hashlib
from cryptography.fernet import Fernet

from app.core.config import settings


def _get_fernet() -> Fernet:
    """Derive a Fernet key from ENCRYPTION_KEY or SECRET_KEY."""
    raw_key = settings.ENCRYPTION_KEY or settings.SECRET_KEY
    # Fernet requires 32 url-safe base64-encoded bytes.
    # Derive a deterministic 32-byte key via SHA-256.
    digest = hashlib.sha256(raw_key.encode()).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt_value(plaintext: str) -> str:
    """Encrypt a plaintext string. Returns a base64-encoded ciphertext."""
    if not plaintext:
        return plaintext
    f = _get_fernet()
    return f.encrypt(plaintext.encode()).decode()


def decrypt_value(ciphertext: str) -> str:
    """Decrypt a ciphertext string. Returns the original plaintext."""
    if not ciphertext:
        return ciphertext
    try:
        f = _get_fernet()
        return f.decrypt(ciphertext.encode()).decode()
    except Exception:
        # If decryption fails, the value might be stored as plaintext (pre-migration)
        return ciphertext
