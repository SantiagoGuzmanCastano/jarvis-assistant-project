from datetime import datetime

from sqlalchemy.orm import Session

from app.integrations.calendar.freebusy import (
    extract_busy_intervals,
    query_calendar_freebusy,
)
from app.services.calendar_availability import calculate_free_slots
from app.services.external_auth_service import get_valid_google_access_token


def calendar_find_free_slots_tool(
    arguments: dict,
    user_id: int,
    session: Session,
) -> dict:
    start_date = datetime.fromisoformat(arguments["start_date"])
    end_date = datetime.fromisoformat(arguments["end_date"])
    duration_minutes = int(arguments["duration_minutes"])
    calendar_id = arguments.get("calendar_id", "primary")
    timezone = arguments.get("timezone", "America/Bogota")

    access_token = get_valid_google_access_token(
        user_id=user_id,
        session=session,
    )
    response = query_calendar_freebusy(
        access_token=access_token,
        calendar_id=calendar_id,
        timezone=timezone,
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
    )
    busy_intervals = extract_busy_intervals(
        response=response,
        calendar_id=calendar_id,
        timezone=timezone,
    )
    free_intervals = calculate_free_slots(
        range_start=start_date,
        range_end=end_date,
        busy_intervals=busy_intervals,
        duration_minutes=duration_minutes,
    )

    free_slots = [
        {
            "start_date": free_start,
            "end_date": free_end,
            "available_duration_minutes": int(
                (free_end - free_start).total_seconds() // 60
            ),
        }
        for free_start, free_end in free_intervals
    ]

    return {
        "success": True,
        "requested_duration_minutes": duration_minutes,
        "range_start": start_date,
        "range_end": end_date,
        "timezone": timezone,
        "calendar_id": calendar_id,
        "free_slots": free_slots,
        "returned_count": len(free_slots),
    }
