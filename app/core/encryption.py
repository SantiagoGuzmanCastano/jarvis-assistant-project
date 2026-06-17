

from cryptography.fernet import Fernet

from app.core.config import settings


fernet = Fernet(settings.token_encryption_key)


def encrypt_token(token: str) -> str:
    return fernet.encrypt(token.encode()).decode()


def decrypt_token(encrypted_token: str) -> str:
    return fernet.decrypt(encrypted_token.encode()).decode()