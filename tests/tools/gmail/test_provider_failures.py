from unittest.mock import Mock, patch

import pytest
import requests

from app.integrations.gmail.messages import move_gmail_message_to_trash


@patch("app.integrations.gmail.messages.requests.post")
def test_move_to_trash_propagates_current_gmail_provider_error(
    post_mock: Mock,
) -> None:
    response = Mock()
    response.raise_for_status.side_effect = requests.HTTPError("Google unavailable")
    post_mock.return_value = response

    with pytest.raises(requests.HTTPError, match="Google unavailable"):
        move_gmail_message_to_trash(
            access_token="access-token",
            message_id="message-1",
        )

    response.raise_for_status.assert_called_once()
