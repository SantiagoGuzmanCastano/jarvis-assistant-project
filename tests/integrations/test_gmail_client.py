




from unittest.mock import Mock, patch

import pytest
import requests

from app.core.errors import AppError
from app.integrations.gmail.client import request_gmail


GMAIL_MESSAGES_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages"

@patch("app.integrations.gmail.client.requests.request")
def test_request_gmail_timeout_becomes_provider_unavailable(
    request_mock: Mock,
) -> None:
    request_mock.side_effect = requests.Timeout()

    with pytest.raises(AppError) as error_info:
        request_gmail(
            method="GET",
            url=GMAIL_MESSAGES_URL,
            headers={"Authorization": "Bearer fake-access-token"},
            params={"q": "is:unread"},
        )

    error = error_info.value

    assert error.code == "external_provider_unavailable"
    assert error.status_code == 503


@patch("app.integrations.gmail.client.requests.request")
def test_request_gmail_unauthorized_becomes_authentication_failed(
    request_mock: Mock,
) -> None:
    #creamos una respuesta http falsa
    response_mock = Mock()
    response_mock.status_code = 401

    #configuramos el reemplazo falso de requests.request(..) para que al ser llamado, lance un HTTPError y lleve dentro nuestra respuesta falsa
    request_mock.side_effect = requests.HTTPError(response=response_mock)
    #side efect define que pasa cuando llamas al mock
    #cuando request_gmail intente llamar a requests.request, lanza este error

    #ejecuta request_gmail esperando que lance un AppError
    #significa:
    #Ejecuta el código indentado. Si lanza AppError, el test sigue y guarda ese error en error_info. Si no lo lanza, el test falla.
    with pytest.raises(AppError) as error_info:
        request_gmail(
            method="GET",
            url=GMAIL_MESSAGES_URL,
            headers={"Authorization": "Bearer fake-access-token"},
            params={"q": "is:unread"},
        )

    error = error_info.value

    assert error.code == "external_provider_authentication_failed"
    assert error.status_code == 401


@patch("app.integrations.gmail.client.requests.request")
def test_request_gmail_forbidden_becomes_provider_forbidden(
    request_mock: Mock,
) -> None:
    response_mock = Mock()
    response_mock.status_code = 403
    request_mock.side_effect = requests.HTTPError(response=response_mock)

    with pytest.raises(AppError) as error_info:
        request_gmail(method="GET", url=GMAIL_MESSAGES_URL)

    error = error_info.value

    assert error.code == "external_provider_forbidden"
    assert error.status_code == 403


@patch("app.integrations.gmail.client.requests.request")
def test_request_gmail_not_found_becomes_provider_not_found(
    request_mock: Mock,
) -> None:
    response_mock = Mock()
    response_mock.status_code = 404
    request_mock.side_effect = requests.HTTPError(response=response_mock)

    with pytest.raises(AppError) as error_info:
        request_gmail(method="GET", url=GMAIL_MESSAGES_URL)

    error = error_info.value

    assert error.code == "external_provider_not_found"
    assert error.status_code == 404


@patch("app.integrations.gmail.client.requests.request")
def test_request_gmail_rate_limited_becomes_provider_rate_limited(
    request_mock: Mock,
) -> None:
    response_mock = Mock()
    response_mock.status_code = 429
    request_mock.side_effect = requests.HTTPError(response=response_mock)

    with pytest.raises(AppError) as error_info:
        request_gmail(method="GET", url=GMAIL_MESSAGES_URL)

    error = error_info.value

    assert error.code == "external_provider_rate_limited"
    assert error.status_code == 429


@patch("app.integrations.gmail.client.requests.request")
def test_request_gmail_server_error_becomes_provider_unavailable(
    request_mock: Mock,
) -> None:
    response_mock = Mock()
    response_mock.status_code = 500
    request_mock.side_effect = requests.HTTPError(response=response_mock)

    with pytest.raises(AppError) as error_info:
        request_gmail(method="GET", url=GMAIL_MESSAGES_URL)

    error = error_info.value

    assert error.code == "external_provider_unavailable"
    assert error.status_code == 503


@patch("app.integrations.gmail.client.requests.request")
def test_request_gmail_client_error_becomes_provider_error(
    request_mock: Mock,
) -> None:
    response_mock = Mock()
    response_mock.status_code = 400
    request_mock.side_effect = requests.HTTPError(response=response_mock)

    with pytest.raises(AppError) as error_info:
        request_gmail(method="GET", url=GMAIL_MESSAGES_URL)

    error = error_info.value

    assert error.code == "external_provider_error"
    assert error.status_code == 502


@patch("app.integrations.gmail.client.requests.request")
def test_request_gmail_request_exception_becomes_provider_unavailable(
    request_mock: Mock,
) -> None:
    request_mock.side_effect = requests.RequestException()

    with pytest.raises(AppError) as error_info:
        request_gmail(method="GET", url=GMAIL_MESSAGES_URL)

    error = error_info.value

    assert error.code == "external_provider_unavailable"
    assert error.status_code == 503


@patch("app.integrations.gmail.client.requests.request")
def test_request_gmail_returns_successful_response(request_mock: Mock) -> None:
    response_mock = Mock()
    request_mock.return_value = response_mock

    response = request_gmail(
        method="GET",
        url=GMAIL_MESSAGES_URL,
        headers={"Authorization": "Bearer fake-access-token"},
        params={"q": "is:unread"},
    )

    assert response is response_mock
    response_mock.raise_for_status.assert_called_once_with()
