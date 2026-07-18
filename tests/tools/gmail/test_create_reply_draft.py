from unittest.mock import Mock, patch

from app.tools.external.gmail_tools import gmail_create_reply_draft_tool


@patch("app.tools.external.gmail_tools.search_latest_gmail_messages_for_metadata")
@patch("app.tools.external.gmail_tools.delete_tool_state")
@patch("app.tools.external.gmail_tools.get_valid_google_access_token")
def test_recent_result_position_uses_recent_reply_flow(
    access_token_mock: Mock,
    delete_state_mock: Mock,
    search_latest_mock: Mock,
) -> None:
    access_token_mock.return_value = "access-token"
    search_latest_mock.return_value = []

    result = gmail_create_reply_draft_tool(
        arguments={
            "recent_result_position": 1,
            "reply_body": "Gracias por la información.",
        },
        user_id=7,
        session=Mock(),
        conversation_id=11,
    )

    assert result["created"] is False
    assert result["reason"] == "invalid_recent_result_position"
    search_latest_mock.assert_called_once_with(
        access_token="access-token",
        max_results=1,
    )
    delete_state_mock.assert_called_once()
