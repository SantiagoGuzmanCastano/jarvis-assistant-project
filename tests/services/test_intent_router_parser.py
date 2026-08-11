import pytest

from app.services.intent_router_parser import parse_tool_intent_response
from app.services.intent_router import build_tool_intent_prompt
from app.schemas.intent_router import ToolIntent
from app.tools.names import ALL_TOOL_NAMES
from app.tools.registry import TOOLS


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


def test_reply_draft_prompt_uses_active_email_after_exact_read() -> None:
    prompt = build_tool_intent_prompt()

    assert 'Use selection_source: "active" only when Jarvis just read exactly one received email' in prompt
    assert '"selection_source": "active"' in prompt
    assert "Do not reconstruct sender_hint" in prompt


def test_move_to_trash_prompt_uses_active_email_only_after_exact_read() -> None:
    prompt = build_tool_intent_prompt()

    assert "the user explicitly asks to move that same email to Trash/Papelera" in prompt
    assert '"tool_name": "gmail_move_email_to_trash"' in prompt
    assert "Do not use active mode after Jarvis only listed emails" in prompt


def test_read_specific_email_prompt_supports_active_email() -> None:
    prompt = build_tool_intent_prompt()

    assert "For gmail_read_specific_email:" in prompt
    assert 'Use selection_source "active"' in prompt
    assert "exact received email Jarvis already read" in prompt


def test_intent_prompt_remains_compact_and_uses_registry_contracts() -> None:
    prompt = build_tool_intent_prompt()

    assert len(prompt) < 40_000
    assert "Argument contracts (JSON Schema):" in prompt
    assert '"calendar_prepare_event_from_email"' in prompt


def test_tools_info_prompt_requires_literal_true_argument() -> None:
    prompt = build_tool_intent_prompt()

    assert "For get_tools_info:" in prompt
    assert '{"tools": true}' in prompt
    assert "complete registered catalog" in prompt
    assert "what can you do?" in prompt
    assert "oye, tu que puedes hacer?" in prompt
    assert "en que me puedes ayudar?" in prompt


def test_calendar_email_preparation_prompt_expands_keyword_variants() -> None:
    prompt = build_tool_intent_prompt()

    calendar_rules = prompt.split(
        "For calendar_prepare_event_from_email:",
        maxsplit=1,
    )[1].split("Argument contracts (JSON Schema):", maxsplit=1)[0]
    assert "accented, and unaccented variants" in calendar_rules
    assert '"reunion"' in calendar_rules
    assert '"reunión"' in calendar_rules


def test_calendar_email_preparation_prompt_prioritizes_event_overrides() -> None:
    prompt = build_tool_intent_prompt()

    calendar_rules = prompt.split(
        "For calendar_prepare_event_from_email:",
        maxsplit=1,
    )[1].split("Argument contracts (JSON Schema):", maxsplit=1)[0]
    assert "event_title" in calendar_rules
    assert "Explicit event_* values take priority" in calendar_rules
    assert "Gmail search dates into event_start_date" in calendar_rules


def test_calendar_email_selection_modes_are_mutually_exclusive() -> None:
    prompt = build_tool_intent_prompt()

    calendar_rules = prompt.split(
        "For calendar_prepare_event_from_email:",
        maxsplit=1,
    )[1].split("Argument contracts (JSON Schema):", maxsplit=1)[0]
    assert "selection_source modes are mutually exclusive" in calendar_rules
    assert 'use selection_source "search" even when the user says' in calendar_rules
    assert 'use selection_source "previous_selection"' in calendar_rules
    assert "Do not reconstruct that list's sender" in calendar_rules


def test_calendar_pending_proposal_continues_with_create_event() -> None:
    prompt = build_tool_intent_prompt()

    calendar_rules = prompt.split(
        "For calendar_prepare_event_from_email:",
        maxsplit=1,
    )[1].split("Argument contracts (JSON Schema):", maxsplit=1)[0]
    assert "must use calendar_create_event with confirmed false" in (
        calendar_rules
    )
    assert "never call calendar_prepare_event_from_email again" in (
        calendar_rules
    )
    assert '"tool_name":"calendar_create_event"' in calendar_rules


def test_tool_name_contract_matches_registry() -> None:
    assert ALL_TOOL_NAMES == frozenset(TOOLS)

    tool_name_schema = ToolIntent.model_json_schema()["properties"][
        "tool_name"
    ]
    allowed_names = next(
        option["enum"]
        for option in tool_name_schema["anyOf"]
        if "enum" in option
    )
    assert frozenset(allowed_names) == ALL_TOOL_NAMES
