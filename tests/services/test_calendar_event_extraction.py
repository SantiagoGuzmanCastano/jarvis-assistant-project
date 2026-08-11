from datetime import datetime
from unittest.mock import Mock
from zoneinfo import ZoneInfo

import pytest

from app.services import calendar_event_extraction
from app.services.calendar_event_extraction import (
    ExtractedCalendarEvent,
    extract_calendar_event_from_gmail_content,
)


def test_calendar_extraction_normalizes_dates_and_uses_subject_title(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    generator_mock = Mock(
        return_value=ExtractedCalendarEvent(
            title=None,
            description="Revisar Phase 9",
            start_date=datetime.fromisoformat(
                "2026-07-31T15:00:00+00:00"
            ),
            end_date=datetime.fromisoformat(
                "2026-07-31T16:00:00+00:00"
            ),
            location="Meet",
        )
    )
    monkeypatch.setattr(
        calendar_event_extraction,
        "generate_gemini_structured_response",
        generator_mock,
    )

    result = extract_calendar_event_from_gmail_content(
        source_content={
            "source_type": "active_email",
            "subject": "Reunión Jarvis",
            "body": "Mañana de 10 a 11.",
        },
        timezone="America/Bogota",
        reference_datetime=datetime(
            2026,
            7,
            30,
            9,
            tzinfo=ZoneInfo("America/Bogota"),
        ),
    )

    assert result.title == "Reunión Jarvis"
    assert result.start_date.isoformat() == "2026-07-31T10:00:00-05:00"
    assert result.end_date.isoformat() == "2026-07-31T11:00:00-05:00"
    generator_mock.assert_called_once()


def test_calendar_extraction_drops_invalid_end_instead_of_inventing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        calendar_event_extraction,
        "generate_gemini_structured_response",
        Mock(
            return_value=ExtractedCalendarEvent(
                title="Reunión Jarvis",
                start_date=datetime.fromisoformat(
                    "2026-07-31T11:00:00-05:00"
                ),
                end_date=datetime.fromisoformat(
                    "2026-07-31T10:00:00-05:00"
                ),
            )
        ),
    )

    result = extract_calendar_event_from_gmail_content(
        source_content={
            "source_type": "active_draft",
            "subject": "Reunión Jarvis",
            "body": "Contenido",
        },
        timezone="America/Bogota",
        reference_datetime=datetime(
            2026,
            7,
            30,
            tzinfo=ZoneInfo("America/Bogota"),
        ),
    )

    assert result.end_date is None
