


from unittest.mock import Mock, patch

from app.tools.external.gmail_tools import gmail_read_specific_draft_tool


def _gmail_draft(subject: str, date: str, snippet: str, body: str, draft_id: str, to: str, position: int) -> dict:

    return {
            "position": position,
            "draft_id": draft_id,
            "to": to,
            "subject": subject,
            "date": date,
            "snippet": snippet,
            "body": body,
        }


@patch("app.tools.external.gmail_tools.create_tool_state")
@patch("app.tools.external.gmail_tools.delete_tool_state")
@patch("app.tools.external.gmail_tools.fetch_specific_gmail_drafts_full")
@patch("app.tools.external.gmail_tools.get_valid_google_access_token")
@patch("app.tools.external.gmail_tools.build_gmail_query",return_value="to:lina@example.com factura",)
def test_search_with_multiple_matches_saves_state_and_requests_selection(build_query_mock: Mock, access_token_mock: Mock, fetch_drafts_mock: Mock, delete_state_mock: Mock, create_state_mock: Mock,):

    session = Mock()

    drafts = [
        _gmail_draft(
            position=1,
            draft_id="draft-1",
            to="lina@example.com",
            subject="Factura enero",
            date="2026-01-15T10:00:00-05:00",
            snippet="Te envío la factura de enero.",
            body="Hola Lina,\n\nTe envío la factura de enero adjunta.",
        ),
        _gmail_draft(
            position=2,
            draft_id="draft-2",
            to="lina@example.com",
            subject="Factura febrero",
            date="2026-02-15T10:00:00-05:00",
            snippet="Te envío la factura de febrero.",
            body="Hola Lina,\n\nTe envío la factura de febrero adjunta.",
        ),
        _gmail_draft(
            position=3,
            draft_id="draft-3",
            to="lina@example.com",
            subject="Factura marzo",
            date="2026-03-15T10:00:00-05:00",
            snippet="Te envío la factura de marzo.",
            body="Hola Lina,\n\nTe envío la factura de marzo adjunta.",
        ),
    ]

    access_token_mock.return_value = "access-token"

    # fetch_drafts_mock
    # → representa la llamada a Gmail.
    fetch_drafts_mock.return_value = {
    "drafts": drafts,
    "returned_count": 3,
    "has_more": False,
}

    result = gmail_read_specific_draft_tool(
        arguments={
            "recipient_hint": ["Lina", "lina@example.com"],
            "search_keywords": ["factura"],
            "start_date": "2026-01-01",
            "end_date": "2026-04-01",
            "max_results": 5,
        },
        session=session,
        user_id=7,
        conversation_id=11,
    )

    assert result["read"] is False
    assert result["reason"] == "multiple_matching_drafts"
    assert result["returned_count"] == 3
    assert [draft["position"] for draft in result["matching_drafts"]] == [1, 2, 3]

    build_query_mock.assert_called_once()

    fetch_drafts_mock.assert_called_once_with(
        access_token='access-token',
        max_results = 5,
        query = "to:lina@example.com factura"
    )

    assert delete_state_mock.call_count == 2
    create_state_mock.assert_called_once_with(
    user_id=7,
    conversation_id=11,
    session=session,
    payload={
        "state_type": "gmail_read_specific_draft_selection",
        "drafts": drafts,
        "search_arguments": {
            "start_date": "2026-01-01",
            "end_date": "2026-04-01",
            "recipient_hint": ["Lina", "lina@example.com"],
            "search_keywords": ["factura"],
        },
    },
)


@patch("app.tools.external.gmail_tools.delete_tool_state")
@patch("app.tools.external.gmail_tools.get_tool_payload")
def test_selected_position_returns_saved_draft_and_clears_state(get_payload_mock: Mock, delete_state_mock: Mock,) -> None:
    session = Mock()
    drafts = [
        _gmail_draft(
            position=1,
            draft_id="draft-1",
            to="lina@example.com",
            subject="Factura enero",
            date="2026-01-15T10:00:00-05:00",
            snippet="Factura de enero.",
            body="Hola Lina,\n\nTe envio la factura de enero adjunta.",
        ),
        _gmail_draft(
            position=2,
            draft_id="draft-2",
            to="lina@example.com",
            subject="Factura febrero",
            date="2026-02-15T10:00:00-05:00",
            snippet="Factura de febrero.",
            body="Hola Lina,\n\nTe envio la factura de febrero adjunta.",
        ),
        _gmail_draft(
            position=3,
            draft_id="draft-3",
            to="lina@example.com",
            subject="Factura marzo",
            date="2026-03-15T10:00:00-05:00",
            snippet="Factura de marzo.",
            body="Hola Lina,\n\nTe envio la factura de marzo adjunta.",
        ),
    ]
    get_payload_mock.return_value = {
        "state_type": "gmail_read_specific_draft_selection",
        "drafts": drafts,
    }

    result = gmail_read_specific_draft_tool(
        arguments={"selected_result_index": 2},
        session=session,
        user_id=7,
        conversation_id=11,
    )

    assert result == {
        "read": True,
        "drafts": [drafts[1]],
        "returned_count": 1,
        "has_more": False,
    }
    get_payload_mock.assert_called_once_with(
        user_id=7,
        conversation_id=11,
        session=session,
    )
    delete_state_mock.assert_called_once_with(
        user_id=7,
        conversation_id=11,
        session=session,
    )


@patch("app.tools.external.gmail_tools.delete_tool_state")
@patch("app.tools.external.gmail_tools.get_tool_payload")
def test_selected_position_without_state_returns_error(
    get_payload_mock: Mock,
    delete_state_mock: Mock,
) -> None:
    session = Mock()
    get_payload_mock.return_value = None

    result = gmail_read_specific_draft_tool(
        arguments={"selected_result_index": 2},
        session=session,
        user_id=7,
        conversation_id=11,
    )

    assert result == {
        "read": False,
        "reason": "missing_tool_state",
        "message": "No previous draft selection was found.",
        "drafts": [],
        "returned_count": 0,
        "has_more": False,
    }
    get_payload_mock.assert_called_once_with(
        user_id=7,
        conversation_id=11,
        session=session,
    )
    delete_state_mock.assert_not_called()


@patch("app.tools.external.gmail_tools.delete_tool_state")
@patch("app.tools.external.gmail_tools.get_tool_payload")
def test_selected_position_out_of_range_returns_error(
    get_payload_mock: Mock,
    delete_state_mock: Mock,
) -> None:
    session = Mock()
    drafts = [
        _gmail_draft(
            position=1,
            draft_id="draft-1",
            to="lina@example.com",
            subject="Factura enero",
            date="2026-01-15T10:00:00-05:00",
            snippet="Factura de enero.",
            body="Primer borrador.",
        ),
        _gmail_draft(
            position=2,
            draft_id="draft-2",
            to="lina@example.com",
            subject="Factura febrero",
            date="2026-02-15T10:00:00-05:00",
            snippet="Factura de febrero.",
            body="Segundo borrador.",
        ),
    ]
    get_payload_mock.return_value = {
        "state_type": "gmail_read_specific_draft_selection",
        "drafts": drafts,
    }

    result = gmail_read_specific_draft_tool(
        arguments={"selected_result_index": 3},
        session=session,
        user_id=7,
        conversation_id=11,
    )

    assert result == {
        "read": False,
        "reason": "invalid_selected_result_index",
        "message": "Selected draft index is out of range.",
        "available_positions": 2,
        "drafts": [],
        "returned_count": 0,
        "has_more": False,
    }
    delete_state_mock.assert_not_called()

