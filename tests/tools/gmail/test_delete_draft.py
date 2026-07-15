from unittest.mock import Mock, patch

from app.tools.external.gmail_tools import gmail_delete_draft_tool


@patch("app.tools.external.gmail_tools.delete_tool_state")
@patch("app.tools.external.gmail_tools.delete_gmail_draft")
@patch("app.tools.external.gmail_tools.get_tool_payload")
@patch("app.tools.external.gmail_tools.get_valid_google_access_token")
def test_selected_draft_is_permanently_deleted_and_state_is_cleared(
    access_token_mock: Mock,
    get_payload_mock: Mock,
    delete_draft_mock: Mock,
    delete_state_mock: Mock,
) -> None:
    session = Mock()
    drafts = [
        {"draft_id": "draft-1", "subject": "Factura enero"},
        {"draft_id": "draft-2", "subject": "Factura febrero"},
    ]
    access_token_mock.return_value = "access-token"
    get_payload_mock.return_value = {
        "state_type": "gmail_delete_draft_selection",
        "drafts": drafts,
    }

    result = gmail_delete_draft_tool(
        arguments={"selected_result_index": 2},
        session=session,
        user_id=7,
        conversation_id=11,
    )

    assert result == {
        "deleted": True,
        "drafts": [drafts[1]],
        "returned_count": 1,
        "has_more": False,
    }
    delete_draft_mock.assert_called_once_with(
        draft_id="draft-2",
        access_token="access-token",
    )
    delete_state_mock.assert_called_once_with(
        user_id=7,
        conversation_id=11,
        session=session,
    )


def test_multiple_draft_delete_request_is_rejected() -> None:
    result = gmail_delete_draft_tool(
        arguments={"requested_draft_count": 2},
        session=Mock(),
        user_id=7,
        conversation_id=11,
    )

    assert result["deleted"] is False
    assert result["reason"] == "multiple_draft_delete_not_supported"


@patch("app.tools.external.gmail_tools.create_tool_state")
@patch("app.tools.external.gmail_tools.delete_tool_state")
@patch("app.tools.external.gmail_tools.fetch_specific_gmail_drafts")
@patch("app.tools.external.gmail_tools.build_gmail_query", return_value="to:lina@example.com")
@patch("app.tools.external.gmail_tools.get_valid_google_access_token")
def test_multiple_draft_delete_search_saves_selection_state(
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

    result = gmail_delete_draft_tool(
        arguments={"recipient_hint": ["Lina"]},
        session=session,
        user_id=7,
        conversation_id=11,
    )

    assert result["deleted"] is False
    assert result["reason"] == "multiple_matching_drafts"
    assert delete_state_mock.call_count == 2
    create_state_mock.assert_called_once_with(
        user_id=7,
        conversation_id=11,
        session=session,
        payload={
            "state_type": "gmail_delete_draft_selection",
            "drafts": drafts,
            "search_arguments": {
                "start_date": None,
                "end_date": None,
                "recipient_hint": ["Lina"],
                "search_keywords": [],
            },
        },
    )
