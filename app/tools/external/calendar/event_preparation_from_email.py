from datetime import datetime
from email.utils import parsedate_to_datetime
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.integrations.gmail.content import format_full_gmail_message
from app.integrations.gmail.drafts import (
    fetch_gmail_draft_full,
    fetch_specific_gmail_drafts,
    format_gmail_draft_full,
)
from app.integrations.gmail.messages import (
    fetch_full_latest_gmail_messages,
    fetch_full_specific_gmail_messages_metadata,
    fetch_specific_gmail_message_format_FSD,
)
from app.integrations.gmail.search import build_gmail_query
from app.integrations.gmail.sent import (
    fetch_sent_gmail_messages,
    fetch_specific_sent_gmail_messages,
)
from app.repositories.conversation import (
    create_tool_state,
    get_tool_payload,
)
from app.services.calendar_event_extraction import (
    extract_calendar_event_from_gmail_content,
)
from app.services.external_auth_service import (
    get_valid_google_access_token,
)
from app.tools.external.calendar.event_creation import (
    CALENDAR_PENDING_EVENT_CREATION_STATE,
)


CALENDAR_GMAIL_SOURCE_SELECTION_STATE = (
    "calendar_gmail_source_selection"
)


def _reference_datetime(
    source_date: str,
    timezone: str,
) -> datetime:
    target_timezone = ZoneInfo(timezone)
    if source_date:
        try:
            parsed_date = parsedate_to_datetime(source_date)
            if parsed_date.utcoffset() is None:
                parsed_date = parsed_date.replace(tzinfo=target_timezone)
            return parsed_date.astimezone(target_timezone)
        except (TypeError, ValueError, OverflowError):
            pass

    return datetime.now(target_timezone)


def _message_headers(message: dict) -> dict[str, str]:
    return {
        header.get("name", "").lower(): header.get("value", "")
        for header in message.get("payload", {}).get("headers", [])
        if isinstance(header, dict)
    }


def _email_candidate_from_message(
    message: dict,
    position: int,
) -> dict:
    headers = _message_headers(message)
    return {
        "position": position,
        "source_type": "email",
        "source_id": message.get("id"),
        "thread_id": message.get("threadId"),
        "contact": headers.get("from", ""),
        "subject": headers.get("subject", ""),
        "date": headers.get("date", ""),
        "snippet": message.get("snippet", ""),
    }


def _email_candidate_from_search(
    email: dict,
    position: int,
) -> dict:
    return {
        "position": position,
        "source_type": "email",
        "source_id": email.get("message_id"),
        "thread_id": email.get("thread_id"),
        "contact": email.get("sender", ""),
        "subject": email.get("subject", ""),
        "date": email.get("date", ""),
        "snippet": email.get("snippet", ""),
    }


def _sent_email_candidate(
    email: dict,
    position: int,
) -> dict:
    return {
        "position": position,
        "source_type": "sent_email",
        "source_id": email.get("message_id"),
        "thread_id": email.get("thread_id"),
        "contact": email.get("recipient", ""),
        "subject": email.get("subject", ""),
        "date": email.get("date", ""),
        "snippet": email.get("snippet", ""),
    }


def _draft_candidate(draft: dict, position: int) -> dict:
    return {
        "position": position,
        "source_type": "draft",
        "source_id": draft.get("draft_id"),
        "contact": draft.get("to", ""),
        "subject": draft.get("subject", ""),
        "date": draft.get("date", ""),
        "snippet": draft.get("snippet", ""),
    }


def _public_candidate(candidate: dict) -> dict:
    return {
        key: candidate.get(key)
        for key in (
            "position",
            "source_type",
            "contact",
            "subject",
            "date",
            "snippet",
        )
    }


def _validate_candidates(candidates: list[dict]) -> None:
    if any(
        not isinstance(candidate.get("source_id"), str)
        or not candidate["source_id"]
        for candidate in candidates
    ):
        raise AppError(
            code="external_provider_invalid_response",
            message="Gmail returned an invalid source candidate.",
            status_code=502,
        )


def _normalize_draft_content(draft: dict) -> dict | None:
    subject = draft.get("subject")
    body = draft.get("body")
    if not isinstance(subject, str) or not isinstance(body, str):
        return None

    recipient = draft.get("to", "")
    return {
        "source_type": "draft",
        "sender": "",
        "recipient": recipient if isinstance(recipient, str) else "",
        "subject": subject,
        "date": (
            draft.get("date")
            if isinstance(draft.get("date"), str)
            else ""
        ),
        "body": body,
    }


def _load_active_source(*, source_type: str, user_id: int, conversation_id: int, session: Session) -> dict | None:
    state_type = (
        "gmail_active_email"
        if source_type in ("email", "sent_email")
        else "gmail_active_draft"
    )
    payload_key = (
        "active_email"
        if source_type in ("email", "sent_email")
        else "active_draft"
    )
    tool_payload = get_tool_payload(
        user_id=user_id,
        conversation_id=conversation_id,
        state_type=state_type,
        session=session,
    )
    active_source = (
        tool_payload.get(payload_key)
        if isinstance(tool_payload, dict)
        else None
    )
    if not isinstance(active_source, dict):
        return None

    if source_type == "draft":
        return _normalize_draft_content(active_source)
        #se devuelve la info del draft

    expected_active_source = (
        "received"
        if source_type == "email"
        else "sent"
    )
    if active_source.get("source") != expected_active_source:
        return None

    message_id = active_source.get("message_id")
    if not isinstance(message_id, str) or not message_id:
        return None

    access_token = get_valid_google_access_token(
        user_id=user_id,
        session=session,
    )
    message = fetch_full_specific_gmail_messages_metadata(
        access_token=access_token,
        message_id=message_id,
    )
    return {
        "source_type": source_type,
        **format_full_gmail_message(message),
    }
    #se devuelve la info del email

def _load_candidate_content(
    *,
    candidate: dict,
    access_token: str,
) -> dict | None:
    source_id = candidate.get("source_id")
    position = candidate.get("position")
    if (
        not isinstance(source_id, str)
        or not source_id
        or not isinstance(position, int)
    ):
        return None

    candidate_source_type = candidate.get("source_type")
    if candidate_source_type in ("email", "sent_email"):
        message = fetch_full_specific_gmail_messages_metadata(
            access_token=access_token,
            message_id=source_id,
        )
        return {
            "source_type": candidate_source_type,
            **format_full_gmail_message(message),
        }

    draft = format_gmail_draft_full(
        draft=fetch_gmail_draft_full(
            access_token=access_token,
            draft_id=source_id,
        ),
        position=position,
    )
    return _normalize_draft_content(draft)


def _load_recent_source(*, source_type: str,recent_result_position: int,
    access_token: str,) -> dict | None:
    if source_type == "email":
        messages = fetch_full_latest_gmail_messages(
            access_token=access_token,
            max_results=recent_result_position,
        )
        if recent_result_position > len(messages):
            return None
        return {
            "source_type": "email",
            **format_full_gmail_message(
                messages[recent_result_position - 1]
            ),
        }

    if source_type == "sent_email":
        result = fetch_sent_gmail_messages(
            access_token=access_token,
            max_results=recent_result_position,
        )
        emails = result.get("emails", [])
        if recent_result_position > len(emails):
            return None
        candidate = _sent_email_candidate(
            emails[recent_result_position - 1],
            recent_result_position,
        )
        return _load_candidate_content(
            candidate=candidate,
            access_token=access_token,
        )

    draft_results = fetch_specific_gmail_drafts(
        access_token=access_token,
        max_results=recent_result_position,
        query="",
    )
    drafts = draft_results.get("drafts", [])
    if recent_result_position > len(drafts):
        return None
    candidate = _draft_candidate(
        drafts[recent_result_position - 1],
        recent_result_position,
    )
    return _load_candidate_content(
        candidate=candidate,
        access_token=access_token,
    )


def _search_source_candidates(
    *,
    arguments: dict,
    access_token: str,
) -> tuple[list[dict], bool]:
    source_type = arguments["source_type"]
    if source_type == "email":
        query = build_gmail_query(
            search_scope="received",
            start_date=arguments.get("start_date"),
            end_date=arguments.get("end_date"),
            search_keywords=arguments.get("search_keywords", []),
            sender_hint=arguments.get("sender_hint", []),
        )
        result = fetch_specific_gmail_message_format_FSD(
            access_token=access_token,
            max_results=int(arguments.get("max_results", 5)),
            query=query,
        )
        candidates = [
            _email_candidate_from_search(email, position)
            for position, email in enumerate(
                result.get("emails", []),
                start=1,
            )
        ]
        return candidates, bool(result.get("has_more"))

    if source_type == "sent_email":
        query = build_gmail_query(
            search_scope="sent",
            start_date=arguments.get("start_date"),
            end_date=arguments.get("end_date"),
            search_keywords=arguments.get("search_keywords", []),
            recipient_hint=arguments.get("recipient_hint", []),
        )
        result = fetch_specific_sent_gmail_messages(
            access_token=access_token,
            max_results=int(arguments.get("max_results", 5)),
            query=query,
            search_keywords=arguments.get("search_keywords", []),
        )
        candidates = [
            _sent_email_candidate(email, position)
            for position, email in enumerate(
                result.get("emails", []),
                start=1,
            )
        ]
        return candidates, bool(result.get("has_more"))

    query = build_gmail_query(
        search_scope="draft",
        start_date=arguments.get("start_date"),
        end_date=arguments.get("end_date"),
        search_keywords=arguments.get("search_keywords", []),
        recipient_hint=arguments.get("recipient_hint", []),
    )
    result = fetch_specific_gmail_drafts(
        access_token=access_token,
        max_results=int(arguments.get("max_results", 5)),
        query=query,
        search_keywords=arguments.get("search_keywords", []),
    )
    candidates = [
        _draft_candidate(draft, position)
        for position, draft in enumerate(
            result.get("drafts", []),
            start=1,
        )
    ]
    return candidates, bool(result.get("has_more"))


def _load_previous_selection(
    *,
    source_type: str,
    selected_result_position: int,
    user_id: int,
    conversation_id: int,
    session: Session,
) -> dict | None:
    if source_type == "email":
        state_types = (
            CALENDAR_GMAIL_SOURCE_SELECTION_STATE,
            "gmail_email_selection",
            "gmail_read_specific_email_selection",
        )
    elif source_type == "sent_email":
        state_types = (
            CALENDAR_GMAIL_SOURCE_SELECTION_STATE,
            "gmail_sent_email_selection",
        )
    else:
        state_types = (
            CALENDAR_GMAIL_SOURCE_SELECTION_STATE,
            "gmail_draft_selection",
            "gmail_read_specific_draft_selection",
        )

    candidates = None
    for state_type in state_types:
        tool_payload = get_tool_payload(
            user_id=user_id,
            conversation_id=conversation_id,
            state_type=state_type,
            session=session,
        )
        if not isinstance(tool_payload, dict):
            continue

        if state_type == CALENDAR_GMAIL_SOURCE_SELECTION_STATE:
            if (
                tool_payload.get("source_type") == source_type
                and isinstance(
                    tool_payload.get("candidates"),
                    list,
                )
            ):
                candidates = tool_payload["candidates"]
                break
            continue

        payload_key = (
            "emails"
            if source_type in ("email", "sent_email")
            else "drafts"
        )
        gmail_sources = tool_payload.get(payload_key)
        if not isinstance(gmail_sources, list):
            continue

        if source_type == "email":
            candidates = [
                (
                    _email_candidate_from_search(source, position)
                    if isinstance(source, dict)
                    and "message_id" in source
                    else _email_candidate_from_message(source, position)
                )
                for position, source in enumerate(
                    gmail_sources,
                    start=1,
                )
                if isinstance(source, dict)
            ]
        elif source_type == "sent_email":
            candidates = [
                _sent_email_candidate(source, position)
                for position, source in enumerate(
                    gmail_sources,
                    start=1,
                )
                if isinstance(source, dict)
            ]
        else:
            candidates = [
                _draft_candidate(source, position)
                for position, source in enumerate(
                    gmail_sources,
                    start=1,
                )
                if isinstance(source, dict)
            ]
        break

    if (
        not isinstance(candidates, list)
        or selected_result_position < 1
        or selected_result_position > len(candidates)
    ):
        return None

    access_token = get_valid_google_access_token(
        user_id=user_id,
        session=session,
    )
    return _load_candidate_content(
        candidate=candidates[selected_result_position - 1],
        access_token=access_token,
    )


def _extract_and_store_event(
    *,
    source_content: dict,
    source_type: str,
    event_overrides: dict,
    timezone: str,
    calendar_id: str,
    user_id: int,
    conversation_id: int,
    session: Session,
) -> dict:
    
    extracted_event = extract_calendar_event_from_gmail_content(
        source_content=source_content,
        timezone=timezone,
        reference_datetime=_reference_datetime(
            source_date=source_content.get("date", ""),
            timezone=timezone,
        ),
    )
    pending_event = {
        "title": extracted_event.title,
        "description": extracted_event.description,
        "start_date": (
            extracted_event.start_date.isoformat()
            if extracted_event.start_date is not None
            else None
        ),
        "end_date": (
            extracted_event.end_date.isoformat()
            if extracted_event.end_date is not None
            else None
        ),
        "timezone": timezone,
        "calendar_id": calendar_id,
        "location": extracted_event.location,
    }
    override_mapping = {
        "event_title": "title",
        "event_description": "description",
        "event_start_date": "start_date",
        "event_end_date": "end_date",
        "event_location": "location",
    }
    for argument_name, event_field in override_mapping.items():
        override_value = event_overrides.get(argument_name)
        if override_value is not None:
            pending_event[event_field] = override_value

    missing_fields = [
        field_name
        for field_name in ("title", "start_date", "end_date")
        if pending_event[field_name] is None
    ]
    if (
        pending_event["title"] is not None
        and len(pending_event["title"].strip()) < 5
        and "title" not in missing_fields
    ):
        missing_fields.insert(0, "title")

    create_tool_state(
        user_id=user_id,
        conversation_id=conversation_id,
        state_type=CALENDAR_PENDING_EVENT_CREATION_STATE,
        payload={
            "pending_event": pending_event,
            "source_type": source_type,
        },
        session=session,
    )

    return {
        "success": True,
        "requires_details": bool(missing_fields),
        "requires_confirmation": not missing_fields,
        "reason": (
            "missing_event_details"
            if missing_fields
            else "confirmation_required"
        ),
        "message": (
            "The event proposal is incomplete."
            if missing_fields
            else "The extracted event requires explicit confirmation."
        ),
        "missing_fields": missing_fields,
        "source_type": source_type,
        "extracted_event": pending_event,
    }


def calendar_prepare_event_from_email_tool(arguments: dict,user_id: int,session: Session,conversation_id: int,) -> dict:
    source_type = arguments["source_type"]
    #email o draft
    selection_source = arguments["selection_source"]
    #active, recent, previous selection
    timezone = arguments.get("timezone", "America/Bogota")
    calendar_id = arguments.get("calendar_id", "primary")

    if selection_source == "active":
        source_content = _load_active_source(
            source_type=source_type,
            user_id=user_id,
            conversation_id=conversation_id,
            session=session,
        )
    elif selection_source == "recent":
        access_token = get_valid_google_access_token(
            user_id=user_id,
            session=session,
        )
        source_content = _load_recent_source(
            source_type=source_type,
            recent_result_position=int(
                arguments["recent_result_position"]
            ),
            access_token=access_token,
        )
    elif selection_source == "previous_selection":
        source_content = _load_previous_selection(
            source_type=source_type,
            selected_result_position=int(
                arguments["selected_result_position"]
            ),
            user_id=user_id,
            conversation_id=conversation_id,
            session=session,
        )
    else:
        access_token = get_valid_google_access_token(
            user_id=user_id,
            session=session,
        )
        candidates, has_more = _search_source_candidates(
            arguments=arguments,
            access_token=access_token,
        )
        _validate_candidates(candidates)
        if not candidates:
            return {
                "success": False,
                "reason": "no_matching_gmail_source",
                "message": "No matching Gmail source was found.",
            }

        if len(candidates) > 1 or has_more:
            create_tool_state(
                user_id=user_id,
                conversation_id=conversation_id,
                state_type=CALENDAR_GMAIL_SOURCE_SELECTION_STATE,
                payload={
                    "source_type": source_type,
                    "candidates": candidates,
                },
                session=session,
            )
            matching_sources = [
                _public_candidate(candidate)
                for candidate in candidates
            ]
            return {
                "success": False,
                "requires_selection": True,
                "reason": "multiple_matching_gmail_sources",
                "message": (
                    "Multiple matching Gmail sources were found. "
                    "Select one before extracting an event."
                ),
                "source_type": source_type,
                "matching_sources": matching_sources,
                "returned_count": len(matching_sources),
                "has_more": has_more,
            }

        source_content = _load_candidate_content(
            candidate=candidates[0],
            access_token=access_token,
        )

    if source_content is None:
        return {
            "success": False,
            "reason": f"missing_{selection_source}_{source_type}",
            "message": (
                "The requested Gmail source could not be resolved "
                "in this conversation."
            ),
        }



    return _extract_and_store_event(
        source_content=source_content,
        source_type=source_type,
        event_overrides={
            field_name: arguments.get(field_name)
            for field_name in (
                "event_title",
                "event_description",
                "event_start_date",
                "event_end_date",
                "event_location",
            )
        },
        timezone=timezone,
        calendar_id=calendar_id,
        user_id=user_id,
        conversation_id=conversation_id,
        session=session,
    )
