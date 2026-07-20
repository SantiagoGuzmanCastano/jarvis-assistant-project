from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.core.config import settings
from app.repositories.conversation import (
    create_tool_state,
    get_tool_payload,
    get_tool_state,
)


def _tool_state(*, payload: dict, expires_at: datetime) -> SimpleNamespace:
    return SimpleNamespace(
        payload_json=payload,
        expires_at=expires_at,
    )


@patch("app.repositories.conversation.get_tool_state")
def test_get_tool_payload_returns_active_payload(get_tool_state_mock: Mock) -> None:
    session = Mock()
    payload = {"emails": []}
    get_tool_state_mock.return_value = _tool_state(
        payload=payload,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=1),
    )

    result = get_tool_payload(
        user_id=7,
        conversation_id=11,
        session=session,
        state_type="gmail_email_selection",
    )

    assert result == payload
    get_tool_state_mock.assert_called_once_with(
        user_id=7,
        conversation_id=11,
        session=session,
        expected_state_type="gmail_email_selection",
    )


@patch("app.repositories.conversation.delete_tool_state")
@patch("app.repositories.conversation.get_tool_state")
def test_get_tool_payload_deletes_expired_state(
    get_tool_state_mock: Mock,
    delete_tool_state_mock: Mock,
) -> None:
    session = Mock()
    get_tool_state_mock.return_value = _tool_state(
        payload={"emails": []},
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
    )

    result = get_tool_payload(
        user_id=7,
        conversation_id=11,
        session=session,
        state_type="gmail_email_selection",
    )

    assert result is None
    delete_tool_state_mock.assert_called_once_with(
        user_id=7,
        conversation_id=11,
        session=session,
    )


@patch("app.repositories.conversation.delete")
@patch("app.repositories.conversation.ConversationToolState")
def test_create_tool_state_replaces_existing_state(
    tool_state_model_mock: Mock,
    delete_mock: Mock,
) -> None:
    session = Mock()
    created_tool_state = Mock()
    tool_state_model_mock.return_value = created_tool_state
    delete_mock.return_value.where.return_value = Mock()
    payload = {"emails": []}

    result = create_tool_state(
        payload=payload,
        user_id=7,
        conversation_id=11,
        state_type="gmail_email_selection",
        session=session,
    )

    created_values = tool_state_model_mock.call_args.kwargs

    assert result is created_tool_state
    assert created_values["payload_json"] == payload
    assert created_values["state_type"] == "gmail_email_selection"
    assert (
        created_values["expires_at"] - created_values["created_at"]
        == timedelta(minutes=settings.tool_state_expire_minutes)
    )
    session.execute.assert_called_once()
    session.flush.assert_called_once_with()
    session.add.assert_called_once_with(created_tool_state)
    session.commit.assert_called_once_with()
    session.refresh.assert_called_once_with(created_tool_state)


@patch("app.repositories.conversation.select")
@patch("app.repositories.conversation.ConversationToolState")
def test_get_tool_state_filters_by_expected_state_type(
    tool_state_model_mock: Mock,
    select_mock: Mock,
) -> None:
    session = Mock()
    session.scalars.return_value.first.return_value = None
    select_mock.return_value.where.return_value = Mock()

    get_tool_state(
        user_id=7,
        conversation_id=11,
        session=session,
        expected_state_type="gmail_email_selection",
    )

    tool_state_model_mock.state_type.__eq__.assert_called_once_with(
        "gmail_email_selection"
    )
