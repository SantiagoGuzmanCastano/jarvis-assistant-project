from datetime import datetime, timedelta, timezone
from unittest.mock import ANY, Mock, call, patch

import pytest

from app.core.errors import AppError
from app.services import auth


def test_login_revokes_active_sessions_before_creating_a_new_one() -> None:
    session = Mock()
    user = Mock(id=7, hashed_password="hashed-password")
    operations = Mock()

    with (
        patch.object(auth, "get_user_by_email", return_value=user),
        patch.object(auth, "verify_password", return_value=True),
        patch.object(auth, "create_access_token", return_value="access-token"),
        patch.object(auth, "create_refresh_token", return_value="refresh-token"),
        patch.object(auth, "hash_refresh_token", return_value="refresh-token-hash"),
        patch.object(auth, "revoke_active_refresh_sessions_for_user") as revoke_sessions,
        patch.object(auth, "create_refresh_session") as create_session,
    ):
        operations.attach_mock(revoke_sessions, "revoke_sessions")
        operations.attach_mock(create_session, "create_session")

        result = auth.login_user(
            Mock(email="lina@example.com", password="password123"),
            session,
        )

    assert result == {
        "access_token": "access-token",
        "refresh_token": "refresh-token",
        "token_type": "bearer",
    }
    assert operations.mock_calls == [
        call.revoke_sessions(user_id=7, session=session, revoked_at=ANY),
        call.create_session(
            user_id=7,
            token_hash="refresh-token-hash",
            session=session,
            expires_at=ANY,
        ),
    ]
    session.commit.assert_called_once()


def test_logout_revokes_the_current_refresh_session() -> None:
    session = Mock()

    with (
        patch.object(auth, "hash_refresh_token", return_value="token-hash"),
        patch.object(auth, "revoke_refresh_session") as revoke_session,
        patch.object(auth, "create_access_token") as create_access_token,
        patch.object(auth, "create_refresh_token") as create_refresh_token,
    ):
        auth.log_user_out("current-refresh-token", session)

    revoke_session.assert_called_once()
    assert revoke_session.call_args.kwargs["token_hash"] == "token-hash"
    assert revoke_session.call_args.kwargs["session"] is session
    create_access_token.assert_not_called()
    create_refresh_token.assert_not_called()
    session.commit.assert_called_once()


def test_logout_is_idempotent_for_an_unknown_refresh_token() -> None:
    session = Mock()

    with (
        patch.object(auth, "hash_refresh_token", return_value="unknown-token-hash"),
        patch.object(auth, "revoke_refresh_session") as revoke_session,
    ):
        auth.log_user_out("unknown-refresh-token", session)

    revoke_session.assert_called_once()
    assert revoke_session.call_args.kwargs["token_hash"] == "unknown-token-hash"
    session.commit.assert_called_once()


def test_refresh_user_session_rotates_an_active_session() -> None:
    session = Mock()
    current_session = Mock(
        user_id=7,
        revoked_at=None,
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
    )

    with (
        patch.object(auth, "decode_refresh_token", return_value=7),
        patch.object(
            auth,
            "hash_refresh_token",
            side_effect=["current-token-hash", "new-token-hash"],
        ),
        patch.object(
            auth,
            "get_refresh_session_by_token_hash",
            return_value=current_session,
        ),
        patch.object(auth, "create_access_token", return_value="new-access-token"),
        patch.object(auth, "create_refresh_token", return_value="new-refresh-token"),
        patch.object(auth, "revoke_refresh_session") as revoke_session,
        patch.object(auth, "create_refresh_session") as create_session,
    ):
        result = auth.refresh_user_session("current-refresh-token", session)

    assert result == {
        "access_token": "new-access-token",
        "refresh_token": "new-refresh-token",
        "token_type": "bearer",
    }
    revoke_session.assert_called_once()
    assert revoke_session.call_args.kwargs["token_hash"] == "current-token-hash"
    assert revoke_session.call_args.kwargs["session"] is session

    create_session.assert_called_once()
    assert create_session.call_args.kwargs == {
        "user_id": 7,
        "token_hash": "new-token-hash",
        "session": session,
        "expires_at": create_session.call_args.kwargs["expires_at"],
    }
    assert create_session.call_args.kwargs["expires_at"] > datetime.now(timezone.utc)
    session.commit.assert_called_once()


def test_refresh_user_session_rejects_an_invalid_jwt() -> None:
    session = Mock()

    with patch.object(auth, "decode_refresh_token", return_value=None):
        with pytest.raises(AppError) as error_info:
            auth.refresh_user_session("invalid-refresh-token", session)

    assert error_info.value.code == "invalid_refresh_token"
    assert error_info.value.status_code == 401
    session.commit.assert_not_called()


@pytest.mark.parametrize(
    "current_session",
    [
        None,
        Mock(
            user_id=7,
            revoked_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        ),
        Mock(
            user_id=7,
            revoked_at=None,
            expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
        ),
        Mock(
            user_id=8,
            revoked_at=None,
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        ),
    ],
    ids=["missing", "revoked", "expired", "wrong-user"],
)
def test_refresh_user_session_rejects_invalid_database_sessions(
    current_session: Mock | None,
) -> None:
    session = Mock()

    with (
        patch.object(auth, "decode_refresh_token", return_value=7),
        patch.object(auth, "hash_refresh_token", return_value="token-hash"),
        patch.object(
            auth,
            "get_refresh_session_by_token_hash",
            return_value=current_session,
        ),
        patch.object(auth, "revoke_refresh_session") as revoke_session,
        patch.object(auth, "create_refresh_session") as create_session,
    ):
        with pytest.raises(AppError) as error_info:
            auth.refresh_user_session("refresh-token", session)

    assert error_info.value.code == "invalid_refresh_token"
    assert error_info.value.status_code == 401
    revoke_session.assert_not_called()
    create_session.assert_not_called()
    session.commit.assert_not_called()
