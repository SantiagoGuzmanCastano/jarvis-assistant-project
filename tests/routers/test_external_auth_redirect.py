from unittest.mock import Mock

import pytest
from starlette.requests import Request

from app.core.errors import AppError
from app.core.oauth_state import OAuthState
from app.routers import external_auth


def _request_with_origin(origin: str) -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/external-auth/google/connect",
            "headers": [
                (b"origin", origin.encode("ascii")),
            ],
        }
    )


def test_google_connect_preserves_allowed_request_origin(
    monkeypatch,
) -> None:
    create_state_mock = Mock(return_value="signed-state")
    build_url_mock = Mock(return_value="https://google.example/auth")
    monkeypatch.setattr(
        external_auth,
        "create_oauth_state",
        create_state_mock,
    )
    monkeypatch.setattr(
        external_auth,
        "build_google_auth_url",
        build_url_mock,
    )

    result = external_auth.connect_google(
        request=_request_with_origin("http://localhost:4173"),
        current_user=Mock(id=7),
    )

    create_state_mock.assert_called_once_with(
        user_id=7,
        frontend_url="http://localhost:4173",
    )
    build_url_mock.assert_called_once_with(state="signed-state")
    assert result == {"auth_url": "https://google.example/auth"}


def test_google_connect_rejects_unlisted_request_origin() -> None:
    with pytest.raises(AppError) as error_info:
        external_auth.connect_google(
            request=_request_with_origin(
                "https://attacker.example",
            ),
            current_user=Mock(id=7),
        )

    assert error_info.value.code == "invalid_frontend_origin"
    assert error_info.value.status_code == 400


def test_google_callback_redirects_to_configured_frontend(
    monkeypatch,
) -> None:
    verify_state_mock = Mock(
        return_value=OAuthState(
            user_id=7,
            frontend_url="http://localhost:4173",
        )
    )
    complete_oauth_mock = Mock()
    monkeypatch.setattr(
        external_auth,
        "verify_oauth_state",
        verify_state_mock,
    )
    monkeypatch.setattr(
        external_auth,
        "complete_google_oauth",
        complete_oauth_mock,
    )
    session = Mock()

    response = external_auth.google_callback(
        code="authorization-code",
        state="signed-state",
        session=session,
    )

    verify_state_mock.assert_called_once_with("signed-state")
    complete_oauth_mock.assert_called_once_with(
        user_id=7,
        code="authorization-code",
        session=session,
    )
    assert response.status_code == 303
    assert (
        response.headers["location"]
        == "http://localhost:4173?google_connected=1"
    )
