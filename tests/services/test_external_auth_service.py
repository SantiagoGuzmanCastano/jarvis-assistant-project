from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import Mock

from app.services import external_auth_service


NOW_UTC_NAIVE = datetime(2026, 7, 29, 18, 0)


def _google_account(*, expires_at: datetime) -> SimpleNamespace:
    return SimpleNamespace(
        provider_account_id="lina@example.com",
        encrypted_access_token="encrypted-access",
        encrypted_refresh_token="encrypted-refresh",
        scopes="gmail.readonly",
        expires_at=expires_at,
    )


def test_valid_google_token_uses_utc_expiration_without_refresh(
    monkeypatch,
) -> None:
    account = _google_account(
        expires_at=NOW_UTC_NAIVE + timedelta(minutes=30)
    )
    monkeypatch.setattr(
        external_auth_service,
        "_utc_now_naive",
        Mock(return_value=NOW_UTC_NAIVE),
    )
    monkeypatch.setattr(
        external_auth_service,
        "get_external_account_by_user_id_and_provider",
        Mock(return_value=account),
    )
    decrypt_mock = Mock(return_value="current-access-token")
    refresh_mock = Mock()
    monkeypatch.setattr(
        external_auth_service,
        "decrypt_token",
        decrypt_mock,
    )
    monkeypatch.setattr(
        external_auth_service,
        "refresh_google_access_token",
        refresh_mock,
    )

    token = external_auth_service.get_valid_google_access_token(
        user_id=7,
        session=Mock(),
    )

    assert token == "current-access-token"
    decrypt_mock.assert_called_once_with("encrypted-access")
    refresh_mock.assert_not_called()


def test_expired_google_token_refreshes_using_utc_expiration(
    monkeypatch,
) -> None:
    account = _google_account(
        expires_at=NOW_UTC_NAIVE - timedelta(minutes=1)
    )
    session = Mock()
    monkeypatch.setattr(
        external_auth_service,
        "_utc_now_naive",
        Mock(return_value=NOW_UTC_NAIVE),
    )
    monkeypatch.setattr(
        external_auth_service,
        "get_external_account_by_user_id_and_provider",
        Mock(return_value=account),
    )
    monkeypatch.setattr(
        external_auth_service,
        "decrypt_token",
        Mock(return_value="refresh-token"),
    )
    refresh_mock = Mock(
        return_value={
            "access_token": "new-access-token",
            "expires_in": 3600,
        }
    )
    monkeypatch.setattr(
        external_auth_service,
        "refresh_google_access_token",
        refresh_mock,
    )
    monkeypatch.setattr(
        external_auth_service,
        "encrypt_token",
        Mock(return_value="new-encrypted-access"),
    )
    update_mock = Mock()
    monkeypatch.setattr(
        external_auth_service,
        "update_external_account_tokens",
        update_mock,
    )

    token = external_auth_service.get_valid_google_access_token(
        user_id=7,
        session=session,
    )

    assert token == "new-access-token"
    refresh_mock.assert_called_once_with(refresh_token="refresh-token")
    update_mock.assert_called_once_with(
        external_account=account,
        provider_account_id="lina@example.com",
        encrypted_access_token="new-encrypted-access",
        encrypted_refresh_token=None,
        scopes="gmail.readonly",
        expires_at=NOW_UTC_NAIVE + timedelta(hours=1),
        session=session,
    )


def test_aware_expiration_is_normalized_to_utc_naive() -> None:
    bogota_expiration = datetime(
        2026,
        7,
        29,
        13,
        0,
        tzinfo=timezone(timedelta(hours=-5)),
    )

    assert external_auth_service._as_utc_naive(
        bogota_expiration
    ) == NOW_UTC_NAIVE


def test_external_account_scope_check_requires_every_calendar_scope() -> None:
    account = SimpleNamespace(
        scopes=(
            "openid gmail.readonly "
            "https://www.googleapis.com/auth/calendar.events "
            "https://www.googleapis.com/auth/calendar.events.freebusy"
        )
    )
    required_scopes = [
        "https://www.googleapis.com/auth/calendar.events",
        "https://www.googleapis.com/auth/calendar.events.freebusy",
    ]

    assert external_auth_service.external_account_has_scopes(
        external_account=account,
        required_scopes=required_scopes,
    )

    account.scopes = (
        "openid gmail.readonly "
        "https://www.googleapis.com/auth/calendar.events"
    )

    assert not external_auth_service.external_account_has_scopes(
        external_account=account,
        required_scopes=required_scopes,
    )
