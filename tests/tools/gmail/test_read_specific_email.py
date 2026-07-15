import base64
from unittest.mock import Mock, patch

from app.tools.external.gmail_tools import gmail_read_specific_email_tool


def _gmail_email(message_id: str, sender: str, subject: str, body: str) -> dict:
    encoded_body = base64.urlsafe_b64encode(body.encode()).decode()

    return {
        "id": message_id,
        "snippet": body,
        "payload": {
            "mimeType": "text/plain",
            "headers": [
                {"name": "From", "value": sender},
                {"name": "Subject", "value": subject},
                {"name": "Date", "value": "Mon, 1 Jun 2026 10:00:00 -0500"},
            ],
            "body": {"data": encoded_body},
        },
    }


@patch("app.tools.external.gmail_tools.create_tool_state")
@patch("app.tools.external.gmail_tools.delete_tool_state")
@patch("app.tools.external.gmail_tools.fetch_full_specific_gmail_messages")
@patch("app.tools.external.gmail_tools.get_valid_google_access_token")
@patch("app.tools.external.gmail_tools.build_gmail_query", return_value="from:ana@example.com")
def test_search_with_multiple_matches_saves_state_and_requests_selection(build_query_mock: Mock, access_token_mock: Mock, fetch_messages_mock: Mock, delete_state_mock: Mock,create_state_mock: Mock,) -> None:

    session = Mock()
    #mock significa objeto falso controlable

    emails = [
        _gmail_email(
            message_id="email-1",
            sender="Ana <ana@example.com>",
            subject="Factura enero",
            body="Primer correo",
        ),
        _gmail_email(
            message_id="email-2",
            sender="Ana <ana@example.com>",
            subject="Factura febrero",
            body="Segundo correo",
        ),
        _gmail_email(
            message_id="email-3",
            sender="Ana <ana@example.com>",
            subject="Factura marzo",
            body="Tercer correo",
        ),
    ]

    # access_token_mock
    # → representa get_valid_google_access_token.
    access_token_mock.return_value = "access-token"

    # fetch_messages_mock
    # → representa la llamada a Gmail.
    fetch_messages_mock.return_value = emails

    result = gmail_read_specific_email_tool(
        arguments={"sender_hint": ["Ana"], "search_keywords": ["factura"]},
        session=session,
        user_id=7,
        conversation_id=11,
    )

    #espero que read sea false ...
    assert result["read"] is False
    assert result["reason"] == "multiple_matching_emails"
    assert result["returned_count"] == 3
    assert [email["position"] for email in result["matching_emails"]] == [1, 2, 3]

    # build_query_mock
    # → representa build_gmail_query.
    #durante la ejecución anterior, el tool llamo exactamente una vez al mock de construir query??
    build_query_mock.assert_called_once()

    # fetch_messages_mock
    # → representa la llamada a Gmail a verificar (assert)
    fetch_messages_mock.assert_called_once_with(
        access_token="access-token",
        max_results=3,
        query="from:ana@example.com",
    )
    
    # delete_state_mock
    # → representa borrar el estado temporal anterior.
    delete_state_mock.assert_called_once_with(user_id=7, conversation_id=11, session=session)

    # create_state_mock
    # → representa guardar los candidatos para la selección.
    create_state_mock.assert_called_once_with(
        user_id=7,
        session=session,
        conversation_id=11,
        payload={"emails": emails},
    )



@patch("app.tools.external.gmail_tools.delete_tool_state")
@patch("app.tools.external.gmail_tools.get_tool_payload")
def test_selected_position_returns_saved_email_and_clears_state( get_payload_mock: Mock, delete_state_mock: Mock,) -> None:
    session = Mock()
    emails = [
        _gmail_email("email-1", "Ana <ana@example.com>", "Factura enero", "Primer correo"),
        _gmail_email("email-2", "Ana <ana@example.com>", "Factura febrero", "Segundo correo"),
        _gmail_email("email-3", "Ana <ana@example.com>", "Factura marzo", "Tercer correo"),
    ]
    get_payload_mock.return_value = {"emails": emails}

    result = gmail_read_specific_email_tool(
        arguments={"selected_result_position": 2},
        session=session,
        user_id=7,
        conversation_id=11,
    )

    assert result == {
        "read": True,
        "emails": [
            {
                "from": "Ana <ana@example.com>",
                "subject": "Factura febrero",
                "date": "Mon, 1 Jun 2026 10:00:00 -0500",
                "body": "Segundo correo",
            }
        ],
        "returned_count": 1,
        "has_more": False,
    }

    #el assert verifica que al seleccionar el correo 2, el tool busco el estado temporal usando el usuario, ls conversion y la session
    get_payload_mock.assert_called_once_with(user_id=7, conversation_id=11, session=session)

    #despues verifica si se borro
    delete_state_mock.assert_called_once_with(user_id=7, conversation_id=11, session=session)


#caso:

#Usuario selecciona “3”
# → no existe estado temporal
# → el tool no puede saber cuál correo es el 3
# → devuelve missing_tool_state
# → no intenta borrar estado

@patch("app.tools.external.gmail_tools.delete_tool_state")
@patch("app.tools.external.gmail_tools.get_tool_payload",return_value=None,)
def test_selected_position_without_state_returns_error(get_payload_mock: Mock, delete_state_mock: Mock,) -> None:

    session = Mock()
    get_payload_mock.return_value = None

    result = gmail_read_specific_email_tool(
        arguments={"selected_result_position": 2},
        session=session,
        user_id=7,
        conversation_id=11,
    )

    assert result == {
                "read": False,
                "reason": "missing_tool_state",
                "message": "No previous email selection was found.",
                "emails": [],
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
def test_selected_position_out_of_range_returns_error(get_payload_mock: Mock, delete_state_mock: Mock,) -> None:
    session = Mock()
    emails = [
        _gmail_email("email-1", "Ana <ana@example.com>", "Factura enero", "Primer correo"),
        _gmail_email("email-2", "Ana <ana@example.com>", "Factura febrero", "Segundo correo"),
    ]
    get_payload_mock.return_value = {"emails": emails}

    result = gmail_read_specific_email_tool(
        arguments={"selected_result_position": 3},
        session=session,
        user_id=7,
        conversation_id=11,
    )


    assert result == {
                "read": False,
                "reason": "invalid_selected_result_position",
                "message": "Selected email position is out of range.",
                "available_positions": len(emails),
                "emails": [],
                "returned_count": 0,
                "has_more": False,
            }

    get_payload_mock.assert_called_once_with(
    user_id=7,
    conversation_id=11,
    session=session,
    )
    delete_state_mock.assert_not_called()