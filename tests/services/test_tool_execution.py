from unittest.mock import Mock

import pytest

from app.core.errors import AppError
from app.schemas.tools.gmail import CreateDraftArguments, EmailSearchArguments
from app.services import tool_execution


def test_tool_execution_validates_and_normalizes_arguments(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tool_function = Mock(return_value={"executed": True})
    monkeypatch.setattr(
        tool_execution,
        "TOOLS",
        {
            "fake_email_search": {
                "function": tool_function,
                "arguments_schema": EmailSearchArguments,
            },
        },
    )
    session = Mock()

    result = tool_execution.tool_execution_system(
        tool_name="fake_email_search",
        arguments={"sender_hint": ["Ana"]},
        user_id=7,
        session=session,
        conversation_id=11,
    )

    assert result == {"executed": True}
    tool_function.assert_called_once_with(
        arguments={
            "search_keywords": [],
            "start_date": None,
            "end_date": None,
            "max_results": 3,
            "sender_hint": ["Ana"],
        },
        user_id=7,
        session=session,
    )


def test_tool_execution_rejects_invalid_arguments_without_executing_tool(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tool_function = Mock()
    monkeypatch.setattr(
        tool_execution,
        "TOOLS",
        {
            "fake_create_draft": {
                "function": tool_function,
                "arguments_schema": CreateDraftArguments,
            },
        },
    )

    with pytest.raises(AppError) as error_info:
        tool_execution.tool_execution_system(
            tool_name="fake_create_draft",
            arguments={
                "recipient_email": "lina",
                "subject": "Factura",
                "body": "Adjunto la factura.",
            },
            user_id=7,
            session=Mock(),
            conversation_id=11,
        )

    error = error_info.value

    assert error.code == "invalid_tool_arguments"
    assert error.status_code == 422
    assert error.details == {
        "fields": [
            {
                "field": "recipient_email",
                "message": "value is not a valid email address: An email address must have an @-sign.",
            },
        ],
    }
    tool_function.assert_not_called()
