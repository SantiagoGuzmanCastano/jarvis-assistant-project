from unittest.mock import Mock, patch

import pytest
import requests

from app.core.config import settings
from app.core.errors import AppError
from app.integrations.google_oauth import _request_google_oauth


@patch("app.integrations.google_oauth.requests.request")
def test_google_oauth_request_returns_json_on_success(request_mock: Mock) -> None:
    response = Mock()
    response.json.return_value = {"access_token": "token"}
    request_mock.return_value = response

    result = _request_google_oauth(
        method="POST",
        url="https://google.example/token",
        data={"code": "authorization-code"},
    )

    assert result == {"access_token": "token"}
    request_mock.assert_called_once_with(
        method="POST",
        url="https://google.example/token",
        data={"code": "authorization-code"},
        headers=None,
        timeout=settings.google_request_timeout_seconds,
    )
    response.raise_for_status.assert_called_once()


@patch("app.integrations.google_oauth.requests.request")
def test_google_oauth_timeout_becomes_provider_unavailable(
    request_mock: Mock,
) -> None:
    request_mock.side_effect = requests.Timeout()

    with pytest.raises(AppError) as error_info:
        _request_google_oauth(method="GET", url="https://google.example/userinfo")

    error = error_info.value
    assert error.code == "external_provider_unavailable"
    assert error.status_code == 503


@pytest.mark.parametrize(
    ("provider_status", "expected_code", "expected_status"),
    [
        (401, "external_provider_authentication_failed", 401),
        (403, "external_provider_forbidden", 403),
        (404, "external_provider_not_found", 404),
        (429, "external_provider_rate_limited", 429),
        (500, "external_provider_unavailable", 503),
    ],
)
@patch("app.integrations.google_oauth.requests.request")
def test_google_oauth_http_errors_are_mapped_to_app_error(
    request_mock: Mock,
    provider_status: int,
    expected_code: str,
    expected_status: int,
) -> None:
    provider_response = Mock(status_code=provider_status)
    http_error = requests.HTTPError(response=provider_response)
    response = Mock()
    response.raise_for_status.side_effect = http_error
    request_mock.return_value = response

    with pytest.raises(AppError) as error_info:
        _request_google_oauth(method="GET", url="https://google.example/userinfo")

    error = error_info.value
    assert error.code == expected_code
    assert error.status_code == expected_status
