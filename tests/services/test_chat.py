from unittest.mock import Mock, call, patch

import pytest

from app.core.errors import AppError
from app.schemas.intent_router import ToolIntent
from app.services import chat
from app.services.chat import create_chat_response


@patch("app.services.chat.generate_gemini_response")
@patch("app.services.chat.detect_tool_intent")
@patch("app.services.chat.build_system_prompt")
@patch("app.services.chat.get_user_settings_by_user_id")
@patch("app.services.chat.get_recent_conversation_messages")
@patch("app.services.chat.create_message")
@patch("app.services.chat.get_user_conversation_by_id")
def test_chat_without_tool_generates_and_saves_assistant_response(
    conversation_mock: Mock,
    create_message_mock: Mock,
    recent_messages_mock: Mock,
    settings_mock: Mock,
    system_prompt_mock: Mock,
    detect_intent_mock: Mock,
    generate_response_mock: Mock,
) -> None:
    session = Mock()
    conversation_mock.return_value = Mock()
    settings_mock.return_value = Mock()
    system_prompt_mock.return_value = "You are Jarvis."
    recent_messages_mock.return_value = []
    detect_intent_mock.return_value = ToolIntent(
        needs_tool=False,
        tool_name=None,
        arguments={},
    )
    assistant_message = Mock()
    create_message_mock.side_effect = [Mock(), assistant_message]
    generate_response_mock.return_value = "Hola, ¿en qué te ayudo?"

    result = create_chat_response(
        conversation_id=11,
        user_id=7,
        session=session,
        content="Hola",
    )

    assert result is assistant_message
    generate_response_mock.assert_called_once_with(
        messages=[{"role": "user", "parts": [{"text": "Hola"}]}],
        system_prompt="You are Jarvis.",
    )
    create_message_mock.assert_has_calls(
        [
            call(content="Hola", conversation_id=11, session=session, role="user"),
            call(
                content="Hola, ¿en qué te ayudo?",
                conversation_id=11,
                session=session,
                role="assistant",
            ),
        ]
    )


@patch("app.services.chat.generate_gemini_response")
@patch("app.services.chat.build_tool_context", return_value="Tool context")
@patch("app.services.chat.tool_execution_system", return_value={"current_time": "10:00"})
@patch("app.services.chat.detect_tool_intent")
@patch("app.services.chat.build_system_prompt")
@patch("app.services.chat.get_user_settings_by_user_id")
@patch("app.services.chat.get_recent_conversation_messages")
@patch("app.services.chat.create_message")
@patch("app.services.chat.get_user_conversation_by_id")
def test_chat_with_tool_adds_tool_context_before_generating_response(
    conversation_mock: Mock,
    create_message_mock: Mock,
    recent_messages_mock: Mock,
    settings_mock: Mock,
    system_prompt_mock: Mock,
    detect_intent_mock: Mock,
    execute_tool_mock: Mock,
    build_context_mock: Mock,
    generate_response_mock: Mock,
) -> None:
    session = Mock()
    conversation_mock.return_value = Mock()
    settings_mock.return_value = Mock()
    system_prompt_mock.return_value = "You are Jarvis."
    recent_messages_mock.return_value = []
    detect_intent_mock.return_value = ToolIntent(
        needs_tool=True,
        tool_name="get_current_time",
        arguments={},
    )
    create_message_mock.side_effect = [Mock(), Mock()]
    generate_response_mock.return_value = "Son las 10:00."

    create_chat_response(
        conversation_id=11,
        user_id=7,
        session=session,
        content="¿Qué hora es?",
    )

    execute_tool_mock.assert_called_once_with(
        tool_name="get_current_time",
        arguments={},
        user_id=7,
        session=session,
        conversation_id=11,
    )
    build_context_mock.assert_called_once_with(
        tool_name="get_current_time",
        tool_result={"current_time": "10:00"},
    )
    generate_response_mock.assert_called_once_with(
        messages=[
            {"role": "user", "parts": [{"text": "¿Qué hora es?"}]},
            {"role": "user", "parts": [{"text": "Tool context"}]},
        ],
        system_prompt="You are Jarvis.",
    )


@patch("app.services.chat.generate_gemini_response")
@patch("app.services.chat.tool_execution_system")
@patch("app.services.chat.get_external_account_by_user_id_and_provider", return_value=None)
@patch("app.services.chat.detect_tool_intent")
@patch("app.services.chat.build_system_prompt")
@patch("app.services.chat.get_user_settings_by_user_id")
@patch("app.services.chat.get_recent_conversation_messages", return_value=[])
@patch("app.services.chat.create_message")
@patch("app.services.chat.get_user_conversation_by_id")
def test_chat_returns_connection_message_when_gmail_is_not_connected(
    conversation_mock: Mock,
    create_message_mock: Mock,
    recent_messages_mock: Mock,
    settings_mock: Mock,
    system_prompt_mock: Mock,
    detect_intent_mock: Mock,
    account_mock: Mock,
    execute_tool_mock: Mock,
    generate_response_mock: Mock,
) -> None:
    session = Mock()
    conversation_mock.return_value = Mock()
    settings_mock.return_value = Mock()
    system_prompt_mock.return_value = "You are Jarvis."
    detect_intent_mock.return_value = ToolIntent(
        needs_tool=True,
        tool_name="gmail_read_latest_email",
        arguments={"max_results": 1},
    )
    assistant_message = Mock()
    create_message_mock.side_effect = [Mock(), assistant_message]

    result = create_chat_response(
        conversation_id=11,
        user_id=7,
        session=session,
        content="Revisa mi último correo",
    )

    assert result is assistant_message
    account_mock.assert_called_once_with(user_id=7, provider="google", session=session)
    execute_tool_mock.assert_not_called()
    generate_response_mock.assert_not_called()
    create_message_mock.assert_has_calls(
        [
            call(content="Revisa mi último correo", conversation_id=11, session=session, role="user"),
            call(
                content="Para usar Gmail, primero conecta tu cuenta de Google desde Configuración > Cuenta Google.",
                conversation_id=11,
                session=session,
                role="assistant",
            ),
        ]
    )


def test_chat_requests_reconnection_when_calendar_scopes_are_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = Mock()
    assistant_message = Mock()
    create_message_mock = Mock(side_effect=[Mock(), assistant_message])
    execute_tool_mock = Mock()
    generate_response_mock = Mock()
    monkeypatch.setattr(
        chat,
        "get_user_conversation_by_id",
        Mock(return_value=Mock(title_changed_by_user=True)),
    )
    monkeypatch.setattr(
        chat,
        "get_user_settings_by_user_id",
        Mock(return_value=Mock()),
    )
    monkeypatch.setattr(
        chat,
        "get_recent_conversation_messages",
        Mock(return_value=[]),
    )
    monkeypatch.setattr(
        chat,
        "build_system_prompt",
        Mock(return_value="You are Jarvis."),
    )
    monkeypatch.setattr(
        chat,
        "detect_tool_intent",
        Mock(
            return_value=ToolIntent(
                needs_tool=True,
                tool_name="calendar_get_upcoming_events",
                arguments={},
            )
        ),
    )
    monkeypatch.setattr(
        chat,
        "get_external_account_by_user_id_and_provider",
        Mock(
            return_value=Mock(
                scopes=(
                    "openid email profile "
                    "https://www.googleapis.com/auth/gmail.readonly"
                )
            )
        ),
    )
    monkeypatch.setattr(chat, "create_message", create_message_mock)
    monkeypatch.setattr(chat, "tool_execution_system", execute_tool_mock)
    monkeypatch.setattr(
        chat,
        "generate_gemini_response",
        generate_response_mock,
    )

    result = create_chat_response(
        conversation_id=11,
        user_id=7,
        session=session,
        content="Muéstrame mi calendario",
    )

    assert result is assistant_message
    execute_tool_mock.assert_not_called()
    generate_response_mock.assert_not_called()
    create_message_mock.assert_has_calls(
        [
            call(
                content="Muéstrame mi calendario",
                conversation_id=11,
                session=session,
                role="user",
            ),
            call(
                content=chat.CALENDAR_RECONNECTION_REQUIRED_MESSAGE,
                conversation_id=11,
                session=session,
                role="assistant",
            ),
        ]
    )


@patch("app.services.chat.detect_tool_intent", side_effect=ValueError("invalid"))
@patch("app.services.chat.build_system_prompt")
@patch("app.services.chat.get_user_settings_by_user_id")
@patch("app.services.chat.get_recent_conversation_messages", return_value=[])
@patch("app.services.chat.create_message")
@patch("app.services.chat.get_user_conversation_by_id")
def test_chat_rejects_invalid_tool_intent(
    conversation_mock: Mock,
    create_message_mock: Mock,
    recent_messages_mock: Mock,
    settings_mock: Mock,
    system_prompt_mock: Mock,
    detect_intent_mock: Mock,
) -> None:
    conversation_mock.return_value = Mock()
    settings_mock.return_value = Mock()
    system_prompt_mock.return_value = "You are Jarvis."

    with pytest.raises(AppError) as error_info:
        create_chat_response(
            conversation_id=11,
            user_id=7,
            session=Mock(),
            content="Haz algo",
        )

    assert error_info.value.code == "invalid_tool_intent"
    assert error_info.value.status_code == 400
    create_message_mock.assert_not_called()


@patch(
    "app.services.chat.generate_gemini_response",
    side_effect=AppError(
        code="external_provider_invalid_response",
        message="Gemini returned an empty response.",
        status_code=502,
    ),
)
@patch("app.services.chat.detect_tool_intent")
@patch("app.services.chat.build_system_prompt")
@patch("app.services.chat.get_user_settings_by_user_id")
@patch("app.services.chat.get_recent_conversation_messages", return_value=[])
@patch("app.services.chat.create_message")
@patch("app.services.chat.get_user_conversation_by_id")
def test_chat_does_not_persist_messages_when_gemini_returns_no_text(
    conversation_mock: Mock,
    create_message_mock: Mock,
    recent_messages_mock: Mock,
    settings_mock: Mock,
    system_prompt_mock: Mock,
    detect_intent_mock: Mock,
    generate_response_mock: Mock,
) -> None:
    conversation_mock.return_value = Mock()
    settings_mock.return_value = Mock()
    system_prompt_mock.return_value = "You are Jarvis."
    detect_intent_mock.return_value = ToolIntent(
        needs_tool=False,
        tool_name=None,
        arguments={},
    )

    with pytest.raises(AppError) as error_info:
        create_chat_response(
            conversation_id=11,
            user_id=7,
            session=Mock(),
            content="Hola",
        )

    assert error_info.value.code == "external_provider_invalid_response"
    create_message_mock.assert_not_called()


@patch("app.services.chat.create_message")
@patch("app.services.chat.get_user_conversation_by_id", return_value=None)
def test_chat_rejects_missing_conversation(
    conversation_mock: Mock,
    create_message_mock: Mock,
) -> None:
    with pytest.raises(AppError) as error_info:
        create_chat_response(
            conversation_id=11,
            user_id=7,
            session=Mock(),
            content="Hola",
        )

    assert error_info.value.code == "conversation_not_found"
    assert error_info.value.status_code == 404
    create_message_mock.assert_not_called()


@patch("app.services.chat.get_user_settings_by_user_id", return_value=None)
@patch("app.services.chat.create_message")
@patch("app.services.chat.get_user_conversation_by_id", return_value=Mock())
def test_chat_rejects_missing_user_settings(
    conversation_mock: Mock,
    create_message_mock: Mock,
    settings_mock: Mock,
) -> None:
    session = Mock()

    with pytest.raises(AppError) as error_info:
        create_chat_response(
            conversation_id=11,
            user_id=7,
            session=session,
            content="Hola",
        )

    assert error_info.value.code == "user_settings_not_configured"
    assert error_info.value.status_code == 400
    create_message_mock.assert_not_called()


@patch("app.services.chat.auto_generate_title_name")
@patch("app.services.chat.generate_gemini_response", return_value="Hola, ¿en qué te ayudo?")
@patch("app.services.chat.detect_tool_intent")
@patch("app.services.chat.build_system_prompt", return_value="You are Jarvis.")
@patch("app.services.chat.get_user_settings_by_user_id")
@patch("app.services.chat.get_recent_conversation_messages", return_value=[])
@patch("app.services.chat.create_message")
@patch("app.services.chat.get_user_conversation_by_id")
def test_chat_generates_title_from_first_message(
    conversation_mock: Mock,
    create_message_mock: Mock,
    recent_messages_mock: Mock,
    settings_mock: Mock,
    system_prompt_mock: Mock,
    detect_intent_mock: Mock,
    generate_response_mock: Mock,
    auto_title_mock: Mock,
) -> None:
    conversation_mock.return_value = Mock(title_changed_by_user=False)
    settings_mock.return_value = Mock()
    session = Mock()
    detect_intent_mock.return_value = ToolIntent(
        needs_tool=False,
        tool_name=None,
        arguments={},
    )

    create_chat_response(conversation_id=11, user_id=7, session=session, content="Planifica mi semana")

    auto_title_mock.assert_called_once_with(
        first_message_content="Planifica mi semana",
        conversation_id=11,
        session=session,
        user_id=7,
    )


@patch("app.services.chat.auto_generate_title_name")
@patch("app.services.chat.generate_gemini_response", return_value="Respuesta")
@patch("app.services.chat.detect_tool_intent")
@patch("app.services.chat.build_system_prompt", return_value="You are Jarvis.")
@patch("app.services.chat.get_user_settings_by_user_id")
@patch("app.services.chat.get_recent_conversation_messages")
@patch("app.services.chat.create_message")
@patch("app.services.chat.get_user_conversation_by_id")
def test_chat_does_not_generate_title_when_conversation_has_messages(
    conversation_mock: Mock,
    create_message_mock: Mock,
    recent_messages_mock: Mock,
    settings_mock: Mock,
    system_prompt_mock: Mock,
    detect_intent_mock: Mock,
    generate_response_mock: Mock,
    auto_title_mock: Mock,
) -> None:
    conversation_mock.return_value = Mock(title_changed_by_user=False)
    settings_mock.return_value = Mock()
    recent_messages_mock.return_value = [Mock()]
    detect_intent_mock.return_value = ToolIntent(
        needs_tool=False,
        tool_name=None,
        arguments={},
    )

    create_chat_response(conversation_id=11, user_id=7, session=Mock(), content="Segundo mensaje")

    auto_title_mock.assert_not_called()


@patch("app.services.chat.auto_generate_title_name")
@patch("app.services.chat.generate_gemini_response", return_value="Respuesta")
@patch("app.services.chat.detect_tool_intent")
@patch("app.services.chat.build_system_prompt", return_value="You are Jarvis.")
@patch("app.services.chat.get_user_settings_by_user_id")
@patch("app.services.chat.get_recent_conversation_messages", return_value=[])
@patch("app.services.chat.create_message")
@patch("app.services.chat.get_user_conversation_by_id")
def test_chat_does_not_replace_user_changed_title(
    conversation_mock: Mock,
    create_message_mock: Mock,
    recent_messages_mock: Mock,
    settings_mock: Mock,
    system_prompt_mock: Mock,
    detect_intent_mock: Mock,
    generate_response_mock: Mock,
    auto_title_mock: Mock,
) -> None:
    conversation_mock.return_value = Mock(title_changed_by_user=True)
    settings_mock.return_value = Mock()
    detect_intent_mock.return_value = ToolIntent(
        needs_tool=False,
        tool_name=None,
        arguments={},
    )

    create_chat_response(conversation_id=11, user_id=7, session=Mock(), content="Planifica mi semana")

    auto_title_mock.assert_not_called()


@patch(
    "app.services.chat.auto_generate_title_name",
    side_effect=RuntimeError("Unexpected title provider failure"),
)
@patch("app.services.chat.generate_gemini_response", return_value="Respuesta de Jarvis")
@patch("app.services.chat.detect_tool_intent")
@patch("app.services.chat.build_system_prompt", return_value="You are Jarvis.")
@patch("app.services.chat.get_user_settings_by_user_id")
@patch("app.services.chat.get_recent_conversation_messages", return_value=[])
@patch("app.services.chat.create_message")
@patch("app.services.chat.get_user_conversation_by_id")
def test_chat_continues_when_automatic_title_generation_fails(
    conversation_mock: Mock,
    create_message_mock: Mock,
    recent_messages_mock: Mock,
    settings_mock: Mock,
    system_prompt_mock: Mock,
    detect_intent_mock: Mock,
    generate_response_mock: Mock,
    auto_title_mock: Mock,
) -> None:
    conversation_mock.return_value = Mock(title_changed_by_user=False)
    settings_mock.return_value = Mock()
    detect_intent_mock.return_value = ToolIntent(
        needs_tool=False,
        tool_name=None,
        arguments={},
    )
    assistant_message = Mock()
    create_message_mock.side_effect = [Mock(), assistant_message]

    result = create_chat_response(
        conversation_id=11,
        user_id=7,
        session=Mock(),
        content="Hola",
    )

    assert result is assistant_message
    auto_title_mock.assert_called_once()
    generate_response_mock.assert_called_once()
