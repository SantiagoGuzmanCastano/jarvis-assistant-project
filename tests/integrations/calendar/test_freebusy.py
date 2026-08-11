from unittest.mock import Mock, patch

import pytest

from app.core.errors import AppError
from app.integrations.calendar.freebusy import (
    CALENDAR_FREEBUSY_URL,
    extract_busy_intervals,
    query_calendar_freebusy,
)


@patch("app.integrations.calendar.freebusy.request_calendar")
def test_query_calendar_freebusy_builds_google_request(
    request_mock: Mock,
) -> None:
    response = Mock()
    response.json.return_value = {
        "calendars": {"primary": {"busy": []}}
    }
    request_mock.return_value = response

    result = query_calendar_freebusy(
        access_token="access-token",
        calendar_id="primary",
        timezone="America/Bogota",
        start_date="2026-07-30T09:00:00-05:00",
        end_date="2026-07-30T17:00:00-05:00",
    )

    assert result == {"calendars": {"primary": {"busy": []}}}
    request_mock.assert_called_once_with(
        method="POST",
        url=CALENDAR_FREEBUSY_URL,
        headers={"Authorization": "Bearer access-token"},
        json={
            "timeMin": "2026-07-30T09:00:00-05:00",
            "timeMax": "2026-07-30T17:00:00-05:00",
            "timeZone": "America/Bogota",
            "items": [{"id": "primary"}],
        },
    )


def test_extract_busy_intervals_parses_and_converts_provider_dates() -> None:
    result = extract_busy_intervals(
        response={
            "calendars": {
                "primary": {
                    "busy": [
                        {
                            "start": "2026-07-30T15:00:00Z",
                            "end": "2026-07-30T16:00:00Z",
                        }
                    ]
                }
            }
        },
        calendar_id="primary",
        timezone="America/Bogota",
    )

    assert result[0][0].isoformat() == "2026-07-30T10:00:00-05:00"
    assert result[0][1].isoformat() == "2026-07-30T11:00:00-05:00"


def test_extract_busy_intervals_rejects_missing_calendar_data() -> None:
    with pytest.raises(AppError) as error_info:
        extract_busy_intervals(
            response={"calendars": {}},
            calendar_id="primary",
            timezone="America/Bogota",
        )

    assert error_info.value.code == "external_provider_invalid_response"
    assert error_info.value.status_code == 502
