from datetime import datetime, timedelta, timezone
import os

from dotenv import load_dotenv
from fastapi import HTTPException,status
from jose import JWTError
import jwt
from passlib.context import CryptContext
from app.core.config import settings

import hashlib
import hmac

from app.core.config import settings


# 1: HASHEAR CONTRASEÑA
# CryptContext configura el algoritmo de hashing que se va a usar
# schemes=["bcrypt"] le dice que use bcrypt para hashear y verificar contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated ="auto")

# Convierte la contraseña real en un string irreversible para guardar en la DB
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


# 2: VERIFICAMOS LA CONTRASEÑA
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: int) -> str:
    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(
        minutes=settings.access_token_expire_minutes
    )

    payload = {
        "sub": str(user_id),
        "iat": issued_at,
        "exp": expires_at,
        "type": "access",
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_alrogithm,
    )


def create_refresh_token(user_id: int) -> str:
    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(
        days=settings.refresh_token_expire_days
    )

    payload = {
        "sub": str(user_id),
        "iat": issued_at,
        "exp": expires_at,
        "type": "refresh",
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_alrogithm,
    )

    
    # devolvemos el tok

def decode_token(token: str) -> int | None:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_alrogithm],
        )

        if payload.get("type") != "access":
            return None

        subject = payload.get("sub")

        if subject is None:
            return None

        return int(subject)

    except (jwt.PyJWTError, TypeError, ValueError):
        return None
    


def decode_refresh_token(token: str) -> int | None:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_alrogithm],
        )

        if payload.get("type") != "refresh":
            return None

        subject = payload.get("sub")

        if subject is None:
            return None

        return int(subject)

    except (jwt.PyJWTError, TypeError, ValueError):
        return None

def hash_refresh_token(refresh_token: str) -> str:
    return hmac.new(
        settings.refresh_token_hash_key.encode("utf-8"),
        refresh_token.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()