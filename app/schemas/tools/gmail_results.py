from pydantic import BaseModel, Field


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


class DraftActionDetails(BaseModel):
    draft_id: str
    to: str
    subject: str
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


class EmailSelectionActionResult(ToolActionResult):
    matching_emails: list[ReceivedEmailSummary] = Field(default_factory=list)
    returned_count: int = 0
    has_more: bool = False


class DraftSelectionActionResult(ToolActionResult):
    matching_drafts: list[DraftSummary] | None = None
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


class UpdateDraftResult(DraftSelectionActionResult):
    draft: DraftActionDetails | None = None
    updated_fields: dict[str, bool] = Field(default_factory=dict)


class DeleteDraftResult(DraftSelectionActionResult):
    draft: DraftSummary | None = None


class ReadEmailResult(EmailSelectionActionResult):
    emails: list[ReceivedEmailDetails] = Field(default_factory=list)


class ReadDraftResult(DraftSelectionActionResult):
    drafts: list[DraftDetails] = Field(default_factory=list)


class ReceivedEmailTrashResult(EmailSelectionActionResult):
    email: ReceivedEmailSummary | None = None


class SentEmailTrashResult(ToolActionResult):
    email: SentEmailSummary | None = None
    matching_emails: list[SentEmailSummary] = Field(default_factory=list)
    returned_count: int = 0
    has_more: bool = False



class ReplyDraftResult(EmailSelectionActionResult):
    draft: ReplyDraftReference | None = None
