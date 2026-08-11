from datetime import datetime
from unittest.mock import Mock, patch
from zoneinfo import ZoneInfo

from app.integrations.google_oauth import GOOGLE_CALENDAR_SCOPES
from app.schemas.tools.calendar import CalendarFindFreeSlotsArguments
from app.schemas.tools.calendar_results import CalendarFindFreeSlotsResult
from app.services.chat import CALENDAR_TOOL_NAMES
from app.services.intent_router import build_tool_intent_prompt
from app.services.intent_router_parser import parse_tool_intent_response
from app.services.tool_execution import (
    build_tool_context,
    tool_execution_system,
)
from app.tools.registry import TOOLS


BOGOTA = ZoneInfo("America/Bogota")


def test_find_free_slots_is_registered_with_typed_contracts() -> None:
    definition = TOOLS["calendar_find_free_slots"]

    assert definition["arguments_schema"] is CalendarFindFreeSlotsArguments
    assert definition["result_schema"] is CalendarFindFreeSlotsResult
    assert definition.get("requires_conversation_id", False) is False


def test_find_free_slots_is_protected_as_a_calendar_tool() -> None:
    assert "calendar_find_free_slots" in CALENDAR_TOOL_NAMES
    assert (
        "https://www.googleapis.com/auth/calendar.events.freebusy"
        in GOOGLE_CALENDAR_SCOPES
    )


@patch(
    "app.tools.external.calendar.free_slots.calculate_free_slots",
    return_value=[
        (
            datetime(2026, 7, 30, 11, tzinfo=BOGOTA),
            datetime(2026, 7, 30, 13, tzinfo=BOGOTA),
        )
    ],
)
@patch(
    "app.tools.external.calendar.free_slots.extract_busy_intervals",
    return_value=[
        (
            datetime(2026, 7, 30, 10, tzinfo=BOGOTA),
            datetime(2026, 7, 30, 11, tzinfo=BOGOTA),
        )
    ],
)
@patch(
    "app.tools.external.calendar.free_slots.query_calendar_freebusy",
    return_value={"calendars": {"primary": {"busy": []}}},
)
@patch(
    "app.tools.external.calendar.free_slots.get_valid_google_access_token",
    return_value="access-token",
)
def test_find_free_slots_executes_end_to_end_through_registry(
    access_token_mock: Mock,
    query_mock: Mock,
    extract_mock: Mock,
    calculate_mock: Mock,
) -> None:
    session = Mock()

    result = tool_execution_system(
        tool_name="calendar_find_free_slots",
        arguments={
            "start_date": "2026-07-30T09:00:00-05:00",
            "end_date": "2026-07-30T17:00:00-05:00",
            "duration_minutes": 60,
        },
        user_id=7,
        session=session,
        conversation_id=11,
    )

    assert result == {
        "success": True,
        "requested_duration_minutes": 60,
        "range_start": "2026-07-30T09:00:00-05:00",
        "range_end": "2026-07-30T17:00:00-05:00",
        "timezone": "America/Bogota",
        "calendar_id": "primary",
        "free_slots": [
            {
                "start_date": "2026-07-30T11:00:00-05:00",
                "end_date": "2026-07-30T13:00:00-05:00",
                "available_duration_minutes": 120,
            }
        ],
        "returned_count": 1,
    }
    access_token_mock.assert_called_once_with(user_id=7, session=session)
    query_mock.assert_called_once_with(
        access_token="access-token",
        calendar_id="primary",
        timezone="America/Bogota",
        start_date="2026-07-30T09:00:00-05:00",
        end_date="2026-07-30T17:00:00-05:00",
    )
    extract_mock.assert_called_once_with(
        response={"calendars": {"primary": {"busy": []}}},
        calendar_id="primary",
        timezone="America/Bogota",
    )
    calculate_mock.assert_called_once()


def test_intent_router_exposes_find_free_slots() -> None:
    prompt = build_tool_intent_prompt()
    intent = parse_tool_intent_response(
        """
        {
          "needs_tool": true,
          "tool_name": "calendar_find_free_slots",
          "arguments": {
            "start_date": "2026-07-30T09:00:00-05:00",
            "end_date": "2026-07-30T17:00:00-05:00",
            "duration_minutes": 60
          }
        }
        """
    )

    assert "For calendar_find_free_slots:" in prompt
    assert intent.tool_name == "calendar_find_free_slots"


def test_find_free_slots_context_preserves_read_only_semantics() -> None:
    context = build_tool_context(
        "calendar_find_free_slots",
        {
            "success": True,
            "free_slots": [],
            "returned_count": 0,
        },
    )

    assert "no free window long enough was found" in context
    assert "Do not claim that Calendar was modified" in context
    assert "untrusted external data" in context
