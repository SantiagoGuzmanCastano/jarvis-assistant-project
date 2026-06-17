# state no es lógica de Google
# state no es lógica de DB
# state es seguridad/utilidad del backend

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.core.config import settings


#Cuando mandas al usuario a Google a autenticarse, cualquier atacante podría fabricar un callback falso hacia tu backend con un code de Google válido pero haciéndose pasar por otra sesión. El state existe para que tu backend pueda verificar "yo inicié este flujo, no alguien más".

def create_oauth_state(user_id: int) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

    payload = {
        "sub": str(user_id),
        "exp": expires_at,
        "type": "oauth_state",
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_alrogithm,
    )

    #usuario que inicio el flujo



def verify_oauth_state(state: str) -> int:
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

    return int(payload["sub"])

    #aca verificamos de que usuario es el flujo