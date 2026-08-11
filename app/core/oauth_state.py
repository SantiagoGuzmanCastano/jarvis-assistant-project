# state no es lógica de Google
# state no es lógica de DB
# state es seguridad/utilidad del backend

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.core.config import settings


#Cuando mandas al usuario a Google a autenticarse, cualquier atacante podría fabricar un callback falso hacia tu backend con un code de Google válido pero haciéndose pasar por otra sesión. El state existe para que tu backend pueda verificar "yo inicié este flujo, no alguien más".

@dataclass(frozen=True)
class OAuthState:
    user_id: int
    frontend_url: str


def validate_frontend_url(frontend_url: str) -> str:
    normalized_url = frontend_url.rstrip("/")
    allowed_urls = {
        origin.rstrip("/")
        for origin in settings.cors_allowed_origins
    }
    if normalized_url not in allowed_urls:
        raise ValueError("Invalid OAuth frontend URL")
    return normalized_url


def create_oauth_state(user_id: int, frontend_url: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

    payload = {
        "sub": str(user_id),
        "frontend_url": validate_frontend_url(frontend_url),
        "exp": expires_at,
        "type": "oauth_state",
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_alrogithm,
    )

    #usuario que inicio el flujo



def verify_oauth_state(state: str) -> OAuthState:
    try:
        payload = jwt.decode(
            state,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_alrogithm],
        )
    except JWTError:
        raise ValueError("Invalid OAuth state")

    if payload.get("type") != "oauth_state":
        raise ValueError("Invalid OAuth state type")

    frontend_url = payload.get("frontend_url")
    if not isinstance(frontend_url, str):
        raise ValueError("Invalid OAuth frontend URL")

    return OAuthState(
        user_id=int(payload["sub"]),
        frontend_url=validate_frontend_url(frontend_url),
    )

    #aca verificamos de que usuario es el flujo
