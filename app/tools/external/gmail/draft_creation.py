from sqlalchemy.orm import Session

from app.integrations.gmail.drafts import create_gmail_draft
from app.repositories.conversation import create_tool_state
from app.services.external_auth_service import get_valid_google_access_token


def gmail_create_email_draft_tool(
    arguments: dict,
    user_id: int,
    session: Session,
    conversation_id: int,
) -> dict:
    recipient_email = arguments.get("recipient_email")
    subject = arguments.get("subject")
    body = arguments.get("body")
    missing_fields = [
        field
        for field, value in {
            "recipient_email": recipient_email,
            "subject": subject,
            "body": body,
        }.items()
        if value is None
    ]

    if missing_fields:
        return {
            "success": False,
            "reason": "missing_required_fields",
            "message": "Recipient email, subject, and body are required.",
            "missing_fields": missing_fields,
        }

    access_token = get_valid_google_access_token(user_id=user_id, session=session)
    new_draft = create_gmail_draft(
        access_token=access_token,
        body=body,
        subject=subject,
        recipient_email=recipient_email,
    )
    create_tool_state(
        user_id=user_id,
        conversation_id=conversation_id,
        session=session,
        state_type="gmail_active_draft",
        payload={
            "active_draft": {
                "draft_id": new_draft["id"],
                "to": recipient_email,
                "subject": subject,
                "body": body,
            }
        },
    )
    return {
        "success": True,
        "draft": {
            "draft_id": new_draft["id"],
            "recipient_email": recipient_email,
            "subject": subject,
        },
    }


def gmail_create_multiple_email_drafts_tool(
    arguments: dict,
    user_id: int,
    session: Session,
) -> dict:
    drafts_to_create = arguments.get("to_create_list", [])
    if not isinstance(drafts_to_create, list):
        return {
            "success": False,
            "reason": "invalid_to_create_list",
            "message": "to_create_list must be a list.",
            "created_count": 0,
            "failed_count": 0,
            "results": [],
        }

    access_token = get_valid_google_access_token(user_id=user_id, session=session)
    results: list[dict] = []
    created_count = 0
    failed_count = 0

    for draft in drafts_to_create:
        recipient_email = draft.get("recipient_email")
        subject = draft.get("subject")
        body = draft.get("body")
        missing_fields = [
            field
            for field, value in {
                "recipient_email": recipient_email,
                "subject": subject,
                "body": body,
            }.items()
            if not value
        ]

        if missing_fields:
            failed_count += 1
            results.append(
                {
                    "success": False,
                    "reason": "missing_required_fields",
                    "message": "Draft is missing required fields.",
                    "missing_fields": missing_fields,
                }
            )
            continue

        new_draft = create_gmail_draft(
            access_token=access_token,
            body=body,
            subject=subject,
            recipient_email=recipient_email,
        )
        created_count += 1
        results.append(
            {
                "success": True,
                "draft": {
                    "draft_id": new_draft["id"],
                    "recipient_email": recipient_email,
                    "subject": subject,
                },
            }
        )

    success = failed_count == 0
    partial_failure = created_count > 0 and failed_count > 0
    return {
        "success": success,
        "reason": "partial_failure" if partial_failure else (
            "all_drafts_failed" if not success else None
        ),
        "message": "Some drafts could not be created." if partial_failure else None,
        "created_count": created_count,
        "failed_count": failed_count,
        "results": results,
    }
