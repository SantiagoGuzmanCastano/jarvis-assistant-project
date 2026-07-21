from unittest.mock import Mock, patch

import pytest

from app.core.errors import AppError
from app.services import auth, conversation, external_auth_service, user_settings


def test_register_user_rejects_an_existing_email() -> None:
    with patch.object(auth, "get_user_by_email", return_value=Mock()):
        with pytest.raises(AppError) as error_info:
            auth.register_user(Mock(email="lina@example.com"), Mock())

    assert error_info.value.code == "user_already_registered"
    assert error_info.value.status_code == 400


def test_login_user_rejects_unknown_credentials() -> None:
    with patch.object(auth, "get_user_by_email", return_value=None):
        with pytest.raises(AppError) as error_info:
            auth.login_user(Mock(email="lina@example.com", password="secret"), Mock())

    assert error_info.value.code == "invalid_credentials"
    assert error_info.value.status_code == 401


@pytest.mark.parametrize(
    "service_function, arguments",
    [
        ("get_user_conversation_detail", (Mock(id=7), 11, Mock())),
        ("create_user_message", (Mock(id=7), 11, Mock(), Mock(content="Hola"))),
        ("delete_current_user_conversation", (7, 11, Mock())),
    ],
)
def test_conversation_services_reject_missing_conversations(
    service_function: str,
    arguments: tuple,
) -> None:
    with patch.object(conversation, "get_user_conversation_by_id", return_value=None):
        with pytest.raises(AppError) as error_info:
            getattr(conversation, service_function)(*arguments)

    assert error_info.value.code == "conversation_not_found"
    assert error_info.value.status_code == 404


def test_google_token_service_rejects_missing_account() -> None:
    with patch.object(
        external_auth_service,
        "get_external_account_by_user_id_and_provider",
        return_value=None,
    ):
        with pytest.raises(AppError) as error_info:
            external_auth_service.get_valid_google_access_token(7, Mock())

    assert error_info.value.code == "external_account_not_found"
    assert error_info.value.status_code == 404


def test_google_token_service_rejects_missing_refresh_token() -> None:
    account = Mock()
    account.expires_at = None
    account.encrypted_refresh_token = None

    with patch.object(
        external_auth_service,
        "get_external_account_by_user_id_and_provider",
        return_value=account,
    ):
        with pytest.raises(AppError) as error_info:
            external_auth_service.get_valid_google_access_token(7, Mock())

    assert error_info.value.code == "google_refresh_token_not_found"
    assert error_info.value.status_code == 404


def test_external_account_listing_rejects_empty_list() -> None:
    with patch.object(external_auth_service, "list_external_accounts", return_value=[]):
        with pytest.raises(AppError) as error_info:
            external_auth_service.list_current_user_external_accounts(7, Mock())

    assert error_info.value.code == "external_accounts_not_found"
    assert error_info.value.status_code == 404


def test_create_settings_rejects_existing_settings() -> None:
    with patch.object(user_settings, "get_user_settings_by_user_id", return_value=Mock()):
        with pytest.raises(AppError) as error_info:
            user_settings.create_current_user_setting(7, Mock(), Mock())

    assert error_info.value.code == "user_settings_already_exists"
    assert error_info.value.status_code == 400


def test_update_settings_rejects_missing_settings() -> None:
    with patch.object(user_settings, "get_user_settings_by_user_id", return_value=None):
        with pytest.raises(AppError) as error_info:
            user_settings.update_current_user_settings(7, Mock(), Mock())

    assert error_info.value.code == "user_settings_not_found"
    assert error_info.value.status_code == 404


def test_update_settings_rejects_an_empty_update() -> None:
    body = Mock()
    body.model_dump.return_value = {}

    with patch.object(user_settings, "get_user_settings_by_user_id", return_value=Mock()):
        with pytest.raises(AppError) as error_info:
            user_settings.update_current_user_settings(7, Mock(), body)

    assert error_info.value.code == "empty_user_settings_update"
    assert error_info.value.status_code == 400


@pytest.mark.parametrize(
    "service_function",
    ["get_current_user_settings", "restart_current_user_settings"],
)
def test_settings_services_reject_missing_settings(service_function: str) -> None:
    with patch.object(user_settings, "get_user_settings_by_user_id", return_value=None):
        with pytest.raises(AppError) as error_info:
            getattr(user_settings, service_function)(7, Mock())

    assert error_info.value.code == "user_settings_not_found"
    assert error_info.value.status_code == 404
