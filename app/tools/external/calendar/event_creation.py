
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.integrations.calendar.create_calendar_event import create_calendar_event
from app.repositories.conversation import (
    create_tool_state,
    delete_tool_state,
    get_tool_payload,
)
from app.services.external_auth_service import get_valid_google_access_token


CALENDAR_PENDING_EVENT_CREATION_STATE = "calendar_pending_event_creation"


def calendar_create_event_tool(arguments: dict,user_id: int,session: Session,conversation_id: int,) -> dict:
    
    if not arguments.get("confirmed", False):
        existing_payload = get_tool_payload(
            user_id=user_id,
            conversation_id=conversation_id,
            state_type=CALENDAR_PENDING_EVENT_CREATION_STATE,
            session=session,
        )
        existing_event = (
            existing_payload.get("pending_event")
            if isinstance(existing_payload, dict)
            else None
        )
        pending_event = (
            dict(existing_event)
            if isinstance(existing_event, dict)
            else {
                "title": None,
                "description": None,
                "start_date": None,
                "end_date": None,
                "location": None,
                "calendar_id": arguments.get("calendar_id", "primary"),
                "timezone": arguments.get(
                    "timezone",
                    "America/Bogota",
                ),
            }
        )
        for field_name in (
            "title",
            "description",
            "start_date",
            "end_date",
            "location",
        ):
            if arguments.get(field_name) is not None:
                pending_event[field_name] = arguments[field_name]

        missing_fields = [
            field
            for field in ("title", "start_date", "end_date")
            if pending_event[field] is None
        ]
        if missing_fields:
            create_tool_state(
                user_id=user_id,
                conversation_id=conversation_id,
                state_type=CALENDAR_PENDING_EVENT_CREATION_STATE,
                payload={"pending_event": pending_event},
                session=session,
            )
            return {
                "success": False,
                "reason": "missing_required_fields",
                "message": "Title, start date, and end date are required.",
                "missing_fields": missing_fields,
            }

        start_date = datetime.fromisoformat(pending_event["start_date"])
        end_date = datetime.fromisoformat(pending_event["end_date"])
        if end_date <= start_date:
            return {
                "success": False,
                "reason": "invalid_event_range",
                "message": "Event end must be later than its start.",
            }

        create_tool_state(
            user_id=user_id,
            conversation_id=conversation_id,
            state_type=CALENDAR_PENDING_EVENT_CREATION_STATE,
            payload={"pending_event": pending_event},
            session=session,
        )
        return {
            "success": False,
            "requires_confirmation": True,
            "reason": "confirmation_required",
            "message": "The event is ready and requires explicit confirmation.",
            "pending_event": pending_event,
        }

    tool_payload = get_tool_payload(
        user_id=user_id,
        conversation_id=conversation_id,
        state_type=CALENDAR_PENDING_EVENT_CREATION_STATE,
        session=session,
    )
    pending_event = (
        tool_payload.get("pending_event")
        if isinstance(tool_payload, dict)
        else None
    )
    if not isinstance(pending_event, dict):
        return {
            "success": False,
            "reason": "missing_pending_event",
            "message": "No pending calendar event was found to confirm.",
        }

    access_token = get_valid_google_access_token(user_id=user_id, session=session)
    response = create_calendar_event(
        title=pending_event["title"],
        description=pending_event.get("description"),
        start_date=pending_event["start_date"],
        end_date=pending_event["end_date"],
        access_token=access_token,
        calendar_id=pending_event["calendar_id"],
        timezone=pending_event["timezone"],
        location=pending_event.get("location"),
    )
    event_id = response.get("id")

    if not isinstance(event_id, str) or not event_id:
        raise AppError(
            code="external_provider_invalid_response",
            message="Google Calendar did not confirm the event creation.",
            status_code=502,
        )

    event_start = response.get("start", {})
    event_end = response.get("end", {})
    html_link = response.get("htmlLink")

    if not isinstance(html_link, str) or not html_link:
        raise AppError(
            code="external_provider_invalid_response",
            message="Google Calendar did not return a link for the created event.",
            status_code=502,
        )

    delete_tool_state(
        user_id=user_id,
        conversation_id=conversation_id,
        session=session,
    )

    return {
        "success": True,
        "requires_confirmation": False,
        "event": {
            "event_id": event_id,
            "title": response.get("summary", pending_event["title"]),
            "description": response.get(
                "description",
                pending_event.get("description"),
            ),
            "start_date": event_start.get(
                "dateTime",
                pending_event["start_date"],
            ),
            "end_date": event_end.get(
                "dateTime",
                pending_event["end_date"],
            ),
            "timezone": event_start.get(
                "timeZone",
                pending_event["timezone"],
            ),
            "calendar_id": pending_event["calendar_id"],
            "location": response.get(
                "location",
                pending_event.get("location"),
            ),
            "html_link": html_link,
        },
    }
