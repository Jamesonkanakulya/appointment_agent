from cryptography.fernet import Fernet
from .config import settings


def _get_fernet() -> Fernet:
    key = settings.encryption_key
    if not key:
        # Generate a key on-the-fly (not persistent — only for dev without ENCRYPTION_KEY set)
        return Fernet(Fernet.generate_key())
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt(value: str) -> str:
    if not value:
        return value
    return _get_fernet().encrypt(value.encode()).decode()


def decrypt(value: str) -> str:
    if not value:
        return value
    try:
        return _get_fernet().decrypt(value.encode()).decode()
    except Exception:
        # Return as-is if decryption fails (e.g., not encrypted yet)
        return value
