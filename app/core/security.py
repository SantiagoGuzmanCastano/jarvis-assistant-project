from datetime import datetime, timedelta, timezone
import os

from dotenv import load_dotenv
from fastapi import HTTPException,status
from jose import JWTError
import jwt
from passlib.context import CryptContext
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


def create_access_token(id: int):

    expires_at= datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)

    payload = {'sub': str(id)}

    access_token = jwt.encode(payload, settings.jwt_secret_key, settings.jwt_alrogithm)

    return access_token


def decode_token(token: str):

    try:
        payload = jwt.decode(token, settings.jwt_secret_key, settings.jwt_alrogithm)

        return payload['sub']
    
    #error del token, token invalido
    except jwt.PyJWTError:
        return None
    
    #el token se leyo pero el userid no era un numero valido
    #caso raro, nunca sucederia, por seguridad
    except ValueError:
        return None