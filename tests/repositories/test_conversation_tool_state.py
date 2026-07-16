from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.core.config import settings
from app.repositories.conversation import create_tool_state, get_tool_payload


def _tool_state(*, payload: dict | list, expires_at: datetime) -> SimpleNamespace:
    return SimpleNamespace(
        payload_json=payload,
        expires_at=expires_at,
    )


@patch("app.repositories.conversation.get_tool_state")
def test_get_tool_payload_returns_active_payload(get_tool_state_mock: Mock) -> None:
    session = Mock()
    payload = {"state_type": "gmail_email_selection", "emails": []}
    get_tool_state_mock.return_value = _tool_state(
        payload=payload,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=1),
    )

    result = get_tool_payload(
        user_id=7,
        conversation_id=11,
        session=session,
    )

    assert result == payload


@patch("app.repositories.conversation.delete_tool_state")
@patch("app.repositories.conversation.get_tool_state")
def test_get_tool_payload_deletes_expired_state(
    get_tool_state_mock: Mock,
    delete_tool_state_mock: Mock,
) -> None:
    session = Mock()
    get_tool_state_mock.return_value = _tool_state(
        payload={"state_type": "gmail_email_selection", "emails": []},
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
    )

    result = get_tool_payload(
        user_id=7,
        conversation_id=11,
        session=session,
    )

    assert result is None
    delete_tool_state_mock.assert_called_once_with(
        user_id=7,
        conversation_id=11,
        session=session,
    )


@patch("app.repositories.conversation.ConversationToolState")
@patch("app.repositories.conversation.get_tool_state")
def test_create_tool_state_replaces_existing_state(
    get_tool_state_mock: Mock,
    tool_state_model_mock: Mock,
) -> None:
    session = Mock()
    existing_tool_state = Mock()
    created_tool_state = Mock()
    get_tool_state_mock.return_value = existing_tool_state
    tool_state_model_mock.return_value = created_tool_state
    payload = {"state_type": "gmail_email_selection", "emails": []}

    result = create_tool_state(
        payload=payload,
        user_id=7,
        conversation_id=11,
        session=session,
    )

    created_values = tool_state_model_mock.call_args.kwargs

    assert result is created_tool_state
    assert created_values["payload_json"] == payload
    assert (
        created_values["expires_at"] - created_values["created_at"]
        == timedelta(minutes=settings.tool_state_expire_minutes)
    )
    session.delete.assert_called_once_with(existing_tool_state)
    session.flush.assert_called_once_with()
    session.add.assert_called_once_with(created_tool_state)
    session.commit.assert_called_once_with()
    session.refresh.assert_called_once_with(created_tool_state)
