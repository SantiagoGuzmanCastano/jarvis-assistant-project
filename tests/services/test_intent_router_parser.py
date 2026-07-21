import pytest

from app.services.intent_router_parser import parse_tool_intent_response
from app.services.intent_router import build_tool_intent_prompt


def test_parser_accepts_registered_tool() -> None:
    intent = parse_tool_intent_response(
        '{"needs_tool": true, "tool_name": "get_current_time", "arguments": {}}'
    )

    assert intent.needs_tool is True
    assert intent.tool_name == "get_current_time"
    assert intent.arguments == {}


def test_parser_rejects_unknown_tool() -> None:
    with pytest.raises(ValueError, match="Unknown tool"):
        parse_tool_intent_response(
            '{"needs_tool": true, "tool_name": "unknown_tool", "arguments": {}}'
        )


def test_parser_normalizes_no_tool_response() -> None:
    intent = parse_tool_intent_response(
        '{"needs_tool": false, "tool_name": "get_current_time", "arguments": {"x": 1}}'
    )

    assert intent.needs_tool is False
    assert intent.tool_name is None
    assert intent.arguments == {}


def test_reply_draft_prompt_prioritizes_sender_over_recent_position() -> None:
    prompt = build_tool_intent_prompt()

    assert "A sender always takes priority over recent position." in prompt
    assert "reply to Ana's latest email" in prompt
