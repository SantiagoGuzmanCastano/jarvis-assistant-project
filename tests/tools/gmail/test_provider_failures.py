from unittest.mock import Mock, patch

import pytest
import requests

from app.core.errors import AppError
from app.integrations.gmail.messages import move_gmail_message_to_trash


@patch("app.integrations.gmail.client.requests.request")
def test_move_to_trash_maps_gmail_server_error_to_provider_unavailable(
    request_mock: Mock,
) -> None:
    response = Mock()
    response.status_code = 500
    response.raise_for_status.side_effect = requests.HTTPError(response=response)
    request_mock.return_value = response

    with pytest.raises(AppError) as error_info:
        move_gmail_message_to_trash(
            access_token="access-token",
            message_id="message-1",
        )

    error = error_info.value

    assert error.code == "external_provider_unavailable"
    assert error.status_code == 503
