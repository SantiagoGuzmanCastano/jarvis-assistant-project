import jwt

from app.core.config import settings
from app.core.security import create_access_token

from datetime import datetime, timedelta, timezone

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    decode_token,
    hash_refresh_token,
)

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


def test_create_refresh_token_includes_required_claims() -> None:
    token = create_refresh_token(user_id=7)

    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_alrogithm],
    )

    assert payload["sub"] == "7"
    assert payload["type"] == "refresh"
    assert payload["exp"] > payload["iat"]
    assert decode_refresh_token(token) == 7


def test_decode_refresh_token_rejects_an_expired_token() -> None:
    now = datetime.now(timezone.utc)
    expired_token = jwt.encode(
        {
            "sub": "7",
            "type": "refresh",
            "iat": now - timedelta(days=8),
            "exp": now - timedelta(days=1),
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_alrogithm,
    )

    assert decode_refresh_token(expired_token) is None


def test_decode_refresh_token_rejects_an_access_token() -> None:
    access_token = create_access_token(user_id=7)

    assert decode_refresh_token(access_token) is None


def test_decode_refresh_token_rejects_a_token_signed_with_another_key() -> None:
    now = datetime.now(timezone.utc)
    token_signed_with_another_key = jwt.encode(
        {
            "sub": "7",
            "type": "refresh",
            "iat": now,
            "exp": now + timedelta(days=1),
        },
        "another-secret-key-with-at-least-32-bytes",
        algorithm=settings.jwt_alrogithm,
    )

    assert decode_refresh_token(token_signed_with_another_key) is None


def test_hash_refresh_token_is_deterministic_and_token_specific() -> None:
    first_hash = hash_refresh_token("refresh-token-one")

    assert first_hash == hash_refresh_token("refresh-token-one")
    assert first_hash != hash_refresh_token("refresh-token-two")
