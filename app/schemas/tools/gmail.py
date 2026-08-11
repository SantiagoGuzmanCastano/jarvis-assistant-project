from datetime import date
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, model_validator


class GmailSearchFilters(BaseModel):
    search_keywords: list[str] = Field(default_factory=list)
    start_date: date | None = None
    end_date: date | None = None
    max_results: int = Field(default=3, ge=1, le=15)


class EmailSearchArguments(GmailSearchFilters):
    sender_hint: list[str] = Field(default_factory=list)


class RecipientSearchArguments(GmailSearchFilters):
    recipient_hint: list[str] = Field(default_factory=list)


class MaxResultsArguments(BaseModel):
    max_results: int = Field(default=3, ge=1, le=15)


class DraftListArguments(MaxResultsArguments):
    max_results: int = Field(default=3, ge=1, le=5)


class ReadLatestEmailArguments(MaxResultsArguments):
    max_results: int = Field(default=1, ge=1, le=2)
    recent_result_position: int | None = Field(default=None, ge=1)


class ReadSpecificEmailArguments(EmailSearchArguments):
    selection_source: Literal["active"] | None = None
    requested_result_count: int = Field(default=1, ge=1, le=15)
    selected_result_position: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def validate_active_selection(self):
        if self.selection_source != "active":
            return self

        if (
            self.selected_result_position is not None
            or self.sender_hint
            or self.search_keywords
            or self.start_date is not None
            or self.end_date is not None
        ):
            raise ValueError(
                "active selection does not accept positions or filters"
            )

        return self


class ReadSpecificDraftArguments(RecipientSearchArguments):
    requested_result_count: int = Field(default=1, ge=1, le=15)
    selected_result_position: int | None = Field(default=None, ge=1)
    recent_result_position: int | None = Field(default=None, ge=1)
    reuse_previous_search: bool = False


class CreateDraftArguments(BaseModel):
    recipient_email: EmailStr
    subject: str = Field(min_length=1)
    body: str = Field(min_length=1)


class DraftToCreate(BaseModel):
    recipient_email: EmailStr | None = None
    subject: str | None = None
    body: str | None = None


class CreateMultipleDraftsArguments(BaseModel):
    to_create: int = Field(ge=1)
    to_create_list: list[DraftToCreate] = Field(min_length=1)


class SendDraftArguments(RecipientSearchArguments):
    requested_result_count: int | None = Field(default=1, ge=1, le=15)
    selected_result_position: int | None = Field(default=None, ge=1)
    recent_result_position: int | None = Field(default=None, ge=1)


class MoveEmailToTrashArguments(EmailSearchArguments):
    selection_source: Literal["active", "recent", "search"] | None = None
    requested_result_count: int = Field(default=1, ge=1, le=15)
    selected_result_position: int | None = Field(default=None, ge=1)
    recent_result_position: int | None = Field(default=None, ge=1)
    reuse_previous_search: bool = False


class MoveSentEmailToTrashArguments(RecipientSearchArguments):
    requested_result_count: int = Field(default=1, ge=1, le=15)
    selected_result_position: int | None = Field(default=None, ge=1)
    recent_result_position: int | None = Field(default=None, ge=1)
    reuse_previous_search: bool = False


class DeleteDraftArguments(RecipientSearchArguments):
    requested_result_count: int = Field(default=1, ge=1, le=15)
    selected_result_position: int | None = Field(default=None, ge=1)
    recent_result_position: int | None = Field(default=None, ge=1)
    reuse_previous_search: bool = False


class UpdateDraftArguments(RecipientSearchArguments):
    selection_source: Literal["active", "recent", "search"]
    recent_result_position: int | None = Field(default=None, ge=1)
    selected_result_position: int | None = Field(default=None, ge=1)
    reuse_previous_search: bool = False
    new_recipient_email: EmailStr | None = None
    new_subject: str | None = None
    new_body: str | None = None


class CreateReplyDraftArguments(EmailSearchArguments):
    selection_source: Literal["active", "recent", "search"] | None = None
    reply_body: str | None = Field(default=None, min_length=1)
    selected_result_position: int | None = Field(default=None, ge=1)
    recent_result_position: int | None = Field(default=None, ge=1)
