from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.errors import AppError
from app.integrations.calendar.client import request_calendar


CALENDAR_FREEBUSY_URL = (
    "https://www.googleapis.com/calendar/v3/freeBusy"
)


def query_calendar_freebusy(
    access_token: str,
    calendar_id: str,
    timezone: str,
    start_date: str,
    end_date: str,
) -> dict:
    response = request_calendar(
        method="POST",
        url=CALENDAR_FREEBUSY_URL,
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        json={
            "timeMin": start_date,
            "timeMax": end_date,
            "timeZone": timezone,
            "items": [
                {
                    "id": calendar_id,
                }
            ],
        },
    )

    return response.json()


def extract_busy_intervals(
    response: dict,
    calendar_id: str,
    timezone: str,
) -> list[tuple[datetime, datetime]]:
    calendars = response.get("calendars")
    if not isinstance(calendars, dict):
        raise AppError(
            code="external_provider_invalid_response",
            message="Google Calendar returned an invalid availability response.",
            status_code=502,
        )

    calendar_data = calendars.get(calendar_id)
    if not isinstance(calendar_data, dict):
        raise AppError(
            code="external_provider_invalid_response",
            message="Google Calendar did not return the requested calendar.",
            status_code=502,
        )

    if calendar_data.get("errors"):
        raise AppError(
            code="external_provider_error",
            message="Google Calendar could not read calendar availability.",
            status_code=502,
        )

    busy_periods = calendar_data.get("busy")
    if not isinstance(busy_periods, list):
        raise AppError(
            code="external_provider_invalid_response",
            message="Google Calendar returned invalid busy intervals.",
            status_code=502,
        )

    target_timezone = ZoneInfo(timezone)
    busy_intervals = []

    for busy_period in busy_periods:
        if not isinstance(busy_period, dict):
            raise AppError(
                code="external_provider_invalid_response",
                message="Google Calendar returned an invalid busy interval.",
                status_code=502,
            )

        start_value = busy_period.get("start")
        end_value = busy_period.get("end")
        if not isinstance(start_value, str) or not isinstance(end_value, str):
            raise AppError(
                code="external_provider_invalid_response",
                message="Google Calendar returned an invalid busy interval.",
                status_code=502,
            )

        try:
            busy_start = datetime.fromisoformat(
                start_value.replace("Z", "+00:00")
            )
            busy_end = datetime.fromisoformat(
                end_value.replace("Z", "+00:00")
            )
        except ValueError as error:
            raise AppError(
                code="external_provider_invalid_response",
                message="Google Calendar returned an invalid busy interval.",
                status_code=502,
            ) from error

        if (
            busy_start.utcoffset() is None
            or busy_end.utcoffset() is None
            or busy_end <= busy_start
        ):
            raise AppError(
                code="external_provider_invalid_response",
                message="Google Calendar returned an invalid busy interval.",
                status_code=502,
            )

        busy_intervals.append(
            (
                busy_start.astimezone(target_timezone),
                busy_end.astimezone(target_timezone),
            )
        )

    return busy_intervals


# {
#     "kind": "calendar#freeBusy",
#     "timeMin": "2026-07-30T14:00:00.000Z",
#     "timeMax": "2026-07-30T22:00:00.000Z",
#     "calendars": {
#         "primary": {
#             "busy": [
#                 {
#                     "start": "2026-07-30T15:00:00Z",
#                     "end": "2026-07-30T16:00:00Z",
#                 },
#                 {
#                     "start": "2026-07-30T18:00:00Z",
#                     "end": "2026-07-30T19:30:00Z",
#                 },
#             ],
#         }
#     },
# }
