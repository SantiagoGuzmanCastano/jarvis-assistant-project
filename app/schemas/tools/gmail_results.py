from pydantic import BaseModel, Field, model_validator


class ReceivedEmailSummary(BaseModel):
    position: int | None = None
    sender: str
    subject: str
    date: str
    snippet: str


class ReceivedEmailDetails(ReceivedEmailSummary):
    body: str


class SentEmailSummary(BaseModel):
    position: int | None = None
    recipient: str
    subject: str
    date: str
    snippet: str


class DraftSummary(BaseModel):
    position: int | None = None
    draft_id: str
    to: str
    subject: str
    date: str
    snippet: str


class DraftDetails(DraftSummary):
    body: str


class DraftCreationReference(BaseModel):
    draft_id: str
    recipient_email: str
    subject: str


class ReplyDraftReference(BaseModel):
    draft_id: str
    message_id: str
    thread_id: str
    recipient_email: str
    subject: str


class CurrentTimeResult(BaseModel):
    current_time: str


class ToolListResult(BaseModel):
    returned_count: int
    has_more: bool
    next_page_token: str | None = None


class ReceivedEmailListResult(ToolListResult):
    emails: list[ReceivedEmailSummary]


class SentEmailListResult(ToolListResult):
    emails: list[SentEmailSummary]


class DraftListResult(ToolListResult):
    drafts: list[DraftSummary]


class ToolActionResult(BaseModel):
    success: bool
    reason: str | None = None
    message: str | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_success(cls, value: object) -> object:
        if not isinstance(value, dict) or "success" in value:
            return value

        normalized = value.copy()
        for legacy_field in ("sent", "updated", "created", "trashed", "deleted", "read", "found"):
            if legacy_field in normalized:
                normalized["success"] = normalized[legacy_field]
                break
        return normalized


class EmailSelectionActionResult(ToolActionResult):
    matching_emails: list[ReceivedEmailSummary] = Field(default_factory=list)
    returned_count: int = 0
    has_more: bool = False


class DraftSelectionActionResult(ToolActionResult):
    matching_drafts: list[DraftSummary] = Field(default_factory=list)
    returned_count: int = 0
    has_more: bool = False


class CreateDraftResult(ToolActionResult):
    draft: DraftCreationReference | None = None
    missing_fields: list[str] = Field(default_factory=list)


class CreateMultipleDraftItemResult(ToolActionResult):
    draft: DraftCreationReference | None = None
    missing_fields: list[str] = Field(default_factory=list)


class CreateMultipleDraftsResult(ToolActionResult):
    created_count: int
    failed_count: int
    results: list[CreateMultipleDraftItemResult]


class SendDraftResult(DraftSelectionActionResult):
    draft: DraftSummary | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_send_result(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value
        normalized = value.copy()
        normalized.setdefault("draft", normalized.get("selected_draft"))
        normalized.setdefault("matching_drafts", normalized.get("matching_drafts_found", []))
        return normalized


class UpdateDraftResult(DraftSelectionActionResult):
    draft: DraftDetails | None = None
    updated_fields: dict[str, bool] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_update_result(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value
        normalized = value.copy()
        normalized.setdefault("draft", normalized.get("selected_draft"))
        normalized.setdefault("matching_drafts", normalized.get("matching_drafts_found", []))
        return normalized


class DeleteDraftResult(DraftSelectionActionResult):
    draft: DraftSummary | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_delete_result(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value
        normalized = value.copy()
        drafts = normalized.get("drafts", [])
        if normalized.get("success") or normalized.get("deleted"):
            normalized.setdefault("draft", drafts[0] if drafts else None)
        return normalized


class ReadEmailResult(EmailSelectionActionResult):
    emails: list[ReceivedEmailDetails] = Field(default_factory=list)


class ReadDraftResult(DraftSelectionActionResult):
    drafts: list[DraftDetails] = Field(default_factory=list)


class ReceivedEmailTrashResult(EmailSelectionActionResult):
    email: ReceivedEmailSummary | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_trash_result(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value
        normalized = value.copy()
        emails = normalized.get("emails", [])
        if normalized.get("success") or normalized.get("trashed"):
            normalized.setdefault("email", emails[0] if emails else None)
        return normalized


class SentEmailTrashResult(ToolActionResult):
    email: SentEmailSummary | None = None
    matching_emails: list[SentEmailSummary] = Field(default_factory=list)
    returned_count: int = 0
    has_more: bool = False

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_sent_trash_result(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value
        normalized = value.copy()
        emails = normalized.get("emails", [])
        if normalized.get("success") or normalized.get("trashed"):
            normalized.setdefault("email", emails[0] if emails else None)
        return normalized


class ReplyDraftResult(EmailSelectionActionResult):
    draft: ReplyDraftReference | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_reply_result(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value
        normalized = value.copy()
        if normalized.get("created") and "draft" not in normalized:
            normalized["draft"] = {
                key: normalized[key]
                for key in (
                    "draft_id",
                    "message_id",
                    "thread_id",
                    "recipient_email",
                    "subject",
                )
            }
        return normalized
