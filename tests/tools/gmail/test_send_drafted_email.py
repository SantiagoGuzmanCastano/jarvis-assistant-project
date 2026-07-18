from unittest.mock import Mock, patch

from app.tools.external.gmail_tools import gmail_send_drafted_email_tool


@patch("app.tools.external.gmail_tools.delete_tool_state")
@patch("app.tools.external.gmail_tools.send_gmail_draft")
@patch("app.tools.external.gmail_tools.get_tool_payload")
@patch("app.tools.external.gmail_tools.get_valid_google_access_token")
def test_selected_draft_is_sent_and_state_is_cleared(
    access_token_mock: Mock,
    get_payload_mock: Mock,
    send_draft_mock: Mock,
    delete_state_mock: Mock,
) -> None:
    session = Mock()
    drafts = [
        {"draft_id": "draft-1", "subject": "Factura enero"},
        {"draft_id": "draft-2", "subject": "Factura febrero"},
    ]
    access_token_mock.return_value = "access-token"
    get_payload_mock.return_value = drafts

    result = gmail_send_drafted_email_tool(
        arguments={"selected_result_position": 2},
        user_id=7,
        session=session,
        conversation_id=11,
    )

    assert result == {
        "sent": True,
        "draft_id": "draft-2",
        "selected_draft": drafts[1],
    }
    send_draft_mock.assert_called_once_with(
        draft_id="draft-2",
        access_token="access-token",
    )
    delete_state_mock.assert_called_once_with(
        user_id=7,
        conversation_id=11,
        session=session,
    )


@patch("app.tools.external.gmail_tools.get_valid_google_access_token")
def test_multiple_draft_send_request_is_rejected(
    access_token_mock: Mock,
) -> None:
    access_token_mock.return_value = "access-token"

    result = gmail_send_drafted_email_tool(
        arguments={"requested_result_count": 2},
        user_id=7,
        session=Mock(),
        conversation_id=11,
    )

    assert result == {
        "sent": False,
        "reason": "multiple_draft_send_not_supported",
        "requested_result_count": 2,
    }


@patch("app.tools.external.gmail_tools.create_tool_state")
@patch("app.tools.external.gmail_tools.delete_tool_state")
@patch("app.tools.external.gmail_tools.fetch_specific_gmail_drafts")
@patch("app.tools.external.gmail_tools.build_gmail_query", return_value="to:lina@example.com")
@patch("app.tools.external.gmail_tools.get_valid_google_access_token")
def test_multiple_draft_send_search_saves_selection_state(
    access_token_mock: Mock,
    build_query_mock: Mock,
    fetch_drafts_mock: Mock,
    delete_state_mock: Mock,
    create_state_mock: Mock,
) -> None:
    session = Mock()
    drafts = [{"draft_id": "draft-1"}, {"draft_id": "draft-2"}]
    access_token_mock.return_value = "access-token"
    fetch_drafts_mock.return_value = {"drafts": drafts, "returned_count": 2, "has_more": False}

    result = gmail_send_drafted_email_tool(
        arguments={"recipient_hint": ["Lina"]},
        user_id=7,
        session=session,
        conversation_id=11,
    )

    assert result["sent"] is False
    assert result["reason"] == "multiple_matching_drafts"
    create_state_mock.assert_called_once_with(
        user_id=7,
        conversation_id=11,
        payload=drafts,
        session=session,
    )


@patch("app.tools.external.gmail_tools.fetch_gmail_drafts")
@patch("app.tools.external.gmail_tools.get_valid_google_access_token")
def test_recent_result_position_uses_recent_draft_flow(
    access_token_mock: Mock,
    fetch_drafts_mock: Mock,
) -> None:
    access_token_mock.return_value = "access-token"
    fetch_drafts_mock.return_value = []

    result = gmail_send_drafted_email_tool(
        arguments={"recent_result_position": 1},
        user_id=7,
        session=Mock(),
        conversation_id=11,
    )

    assert result["sent"] is False
    assert result["reason"] == "invalid_recent_result_position"
    fetch_drafts_mock.assert_called_once_with(
        access_token="access-token",
        max_results=1,
    )
