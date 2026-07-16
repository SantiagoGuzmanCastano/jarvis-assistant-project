import jwt

from app.core.config import settings
from app.core.security import create_access_token

from datetime import datetime, timedelta, timezone

from app.core.security import create_access_token, decode_token

def test_create_access_token_includes_required_claims() -> None:
    token = create_access_token(user_id=7)

    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_alrogithm],
    )

    assert payload["sub"] == "7"
    assert payload["type"] == "access"
    assert "iat" in payload
    assert "exp" in payload
    assert payload["exp"] > payload["iat"]


def test_decode_token_rejects_expired_token() -> None:
    now = datetime.now(timezone.utc)

    expired_token = jwt.encode(
        {
            "sub": "7",
            "type": "access",
            "iat": now - timedelta(minutes=2),
            "exp": now - timedelta(minutes=1),
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_alrogithm,
    )

    assert decode_token(expired_token) is None

def test_decode_token_rejects_non_access_token() -> None:
    now = datetime.now(timezone.utc)

    expired_token = jwt.encode(
        {
            "sub": "7",
            "type": "asdfg",
            "iat": now,
            "exp": now + timedelta(minutes=1),
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_alrogithm,
    )

    assert decode_token(expired_token) is None