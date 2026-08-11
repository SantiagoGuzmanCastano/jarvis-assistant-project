from datetime import date, datetime
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import (
    AnyHttpUrl,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


class CalendarEventProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=5, max_length=100)
    description: str | None = None
    start_date: datetime
    end_date: datetime
    timezone: str
    calendar_id: str = Field(min_length=1)
    location: str | None = None

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as error:
            raise ValueError("timezone must be a valid IANA timezone") from error
        return value

    @model_validator(mode="after")
    def validate_date_order(self):
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be later than start_date")
        return self


class CalendarCreatedEvent(CalendarEventProposal):
    event_id: str = Field(min_length=1)
    html_link: AnyHttpUrl


class CalendarPartialEventProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, max_length=100)
    description: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    timezone: str
    calendar_id: str = Field(min_length=1)
    location: str | None = None

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as error:
            raise ValueError(
                "timezone must be a valid IANA timezone"
            ) from error
        return value


class CalendarGmailSourceCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    position: int = Field(ge=1)
    source_type: Literal["email", "sent_email", "draft"]
    contact: str | None = None
    subject: str | None = None
    date: str | None = None
    snippet: str | None = None


class CalendarPrepareEventFromEmailResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    requires_selection: bool = False
    requires_details: bool = False
    requires_confirmation: bool = False
    reason: str | None = None
    message: str | None = None
    missing_fields: list[
        Literal["title", "start_date", "end_date"]
    ] = Field(default_factory=list)
    source_type: Literal["email", "sent_email", "draft"] | None = None
    matching_sources: list[CalendarGmailSourceCandidate] = Field(
        default_factory=list
    )
    returned_count: int = Field(default=0, ge=0)
    has_more: bool = False
    extracted_event: CalendarPartialEventProposal | None = None

    @model_validator(mode="after")
    def validate_result_state(self):
        if self.returned_count != len(self.matching_sources):
            raise ValueError(
                "returned_count must match the number of matching sources"
            )

        if self.requires_selection:
            if (
                self.success
                or self.requires_details
                or self.requires_confirmation
                or not self.matching_sources
                or self.extracted_event is not None
                or self.source_type is None
            ):
                raise ValueError("invalid Gmail source-selection result")
            return self

        if not self.success:
            if (
                self.requires_selection
                or self.requires_details
                or self.requires_confirmation
                or self.extracted_event is not None
            ):
                raise ValueError("invalid failed event extraction")
            return self

        if self.extracted_event is None or self.source_type is None:
            raise ValueError(
                "a successful extraction requires source and event data"
            )
        if self.requires_details == self.requires_confirmation:
            raise ValueError(
                "an extraction must require details or confirmation"
            )
        if self.requires_details and not self.missing_fields:
            raise ValueError("missing_fields are required")
        if self.requires_confirmation and self.missing_fields:
            raise ValueError(
                "a complete proposal cannot contain missing fields"
            )

        return self


class CalendarUpcomingEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(min_length=1)
    title: str | None = None
    description: str | None = None
    start_date: date | datetime
    end_date: date | datetime
    timezone: str
    all_day: bool
    location: str | None = None
    html_link: AnyHttpUrl | None = None
    attendees: list[str] = Field(default_factory=list)

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as error:
            raise ValueError("timezone must be a valid IANA timezone") from error
        return value


class CalendarGetUpcomingEventsResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    events: list[CalendarUpcomingEvent]
    returned_count: int = Field(ge=0)
    has_more: bool
    range_start: datetime
    range_end: datetime
    timezone: str
    calendar_id: str = Field(min_length=1)

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as error:
            raise ValueError("timezone must be a valid IANA timezone") from error
        return value

    @model_validator(mode="after")
    def validate_result(self):
        if not self.success:
            raise ValueError("calendar event listing result must be successful")
        if self.returned_count != len(self.events):
            raise ValueError("returned_count must match the number of events")
        if self.range_end <= self.range_start:
            raise ValueError("range_end must be later than range_start")
        return self


class CalendarFreeSlot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start_date: datetime
    end_date: datetime
    available_duration_minutes: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_slot(self):
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be later than start_date")
        return self


class CalendarFindFreeSlotsResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    requested_duration_minutes: int = Field(gt=0, le=1440)
    range_start: datetime
    range_end: datetime
    timezone: str
    calendar_id: str = Field(min_length=1)
    free_slots: list[CalendarFreeSlot]
    returned_count: int = Field(ge=0)

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as error:
            raise ValueError("timezone must be a valid IANA timezone") from error
        return value

    @model_validator(mode="after")
    def validate_result(self):
        if not self.success:
            raise ValueError("free-slot result must be successful")
        if self.range_end <= self.range_start:
            raise ValueError("range_end must be later than range_start")
        if self.returned_count != len(self.free_slots):
            raise ValueError(
                "returned_count must match the number of free slots"
            )

        for free_slot in self.free_slots:
            if (
                free_slot.start_date < self.range_start
                or free_slot.end_date > self.range_end
            ):
                raise ValueError(
                    "free slots must stay inside the requested range"
                )
            if (
                free_slot.available_duration_minutes
                < self.requested_duration_minutes
            ):
                raise ValueError(
                    "free slots must fit the requested duration"
                )

        return self


class CalendarCreateEventResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    requires_confirmation: bool = False
    reason: str | None = None
    message: str | None = None
    missing_fields: list[str] = Field(default_factory=list)
    pending_event: CalendarEventProposal | None = None
    event: CalendarCreatedEvent | None = None

    @model_validator(mode="after")
    def validate_result_state(self):
        if self.requires_confirmation:
            if self.success:
                raise ValueError(
                    "a pending confirmation cannot be a successful creation"
                )
            if self.pending_event is None or self.event is not None:
                raise ValueError(
                    "a pending confirmation requires only pending_event"
                )
            return self

        if self.success:
            if self.event is None or self.pending_event is not None:
                raise ValueError(
                    "a successful creation requires only event"
                )
            return self

        if self.pending_event is not None or self.event is not None:
            raise ValueError(
                "a failed creation cannot contain event data"
            )

        return self


class CalendarEventCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    position: int = Field(ge=1)
    event_id: str = Field(min_length=1)
    title: str | None = None
    description: str | None = None
    start_date: date | datetime
    end_date: date | datetime
    timezone: str
    all_day: bool
    location: str | None = None

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as error:
            raise ValueError(
                "timezone must be a valid IANA timezone"
            ) from error
        return value


class CalendarEventUpdateSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    description: str | None = None
    start_date: datetime
    end_date: datetime
    timezone: str
    location: str | None = None

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as error:
            raise ValueError(
                "timezone must be a valid IANA timezone"
            ) from error
        return value

    @model_validator(mode="after")
    def validate_date_order(self):
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be later than start_date")
        return self


class CalendarPendingEventUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_event: CalendarEventUpdateSnapshot
    proposed_event: CalendarEventUpdateSnapshot
    updated_fields: list[
        Literal[
            "title",
            "description",
            "start_date",
            "end_date",
            "location",
        ]
    ] = Field(min_length=1)


class CalendarUpdatedEvent(CalendarEventUpdateSnapshot):
    event_id: str = Field(min_length=1)
    calendar_id: str = Field(min_length=1)
    html_link: AnyHttpUrl | None = None


class CalendarUpdateEventResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    requires_selection: bool = False
    requires_confirmation: bool = False
    reason: str | None = None
    message: str | None = None
    matching_events: list[CalendarEventCandidate] = Field(
        default_factory=list
    )
    returned_count: int = Field(default=0, ge=0)
    has_more: bool = False
    pending_update: CalendarPendingEventUpdate | None = None
    event: CalendarUpdatedEvent | None = None
    updated_fields: list[
        Literal[
            "title",
            "description",
            "start_date",
            "end_date",
            "location",
        ]
    ] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_result_state(self):
        if self.returned_count != len(self.matching_events):
            raise ValueError(
                "returned_count must match the number of matching events"
            )

        if self.requires_selection:
            if (
                self.success
                or self.requires_confirmation
                or not self.matching_events
                or self.pending_update is not None
                or self.event is not None
            ):
                raise ValueError("invalid event-selection result")
            return self

        if self.requires_confirmation:
            if (
                self.success
                or self.pending_update is None
                or self.event is not None
            ):
                raise ValueError("invalid event-confirmation result")
            return self

        if self.success:
            if (
                self.event is None
                or self.pending_update is not None
                or not self.updated_fields
            ):
                raise ValueError("invalid successful event update")
            return self

        if self.pending_update is not None or self.event is not None:
            raise ValueError(
                "a failed update cannot contain event update data"
            )

        return self


class CalendarDeleteEventResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    requires_selection: bool = False
    requires_confirmation: bool = False
    reason: str | None = None
    message: str | None = None
    matching_events: list[CalendarEventCandidate] = Field(
        default_factory=list
    )
    returned_count: int = Field(default=0, ge=0)
    has_more: bool = False
    pending_event: CalendarEventCandidate | None = None
    deleted_event: CalendarEventCandidate | None = None

    @model_validator(mode="after")
    def validate_result_state(self):
        if self.returned_count != len(self.matching_events):
            raise ValueError(
                "returned_count must match the number of matching events"
            )

        if self.requires_selection:
            if (
                self.success
                or self.requires_confirmation
                or not self.matching_events
                or self.pending_event is not None
                or self.deleted_event is not None
            ):
                raise ValueError("invalid event-deletion selection result")
            return self

        if self.requires_confirmation:
            if (
                self.success
                or self.pending_event is None
                or self.deleted_event is not None
            ):
                raise ValueError(
                    "invalid event-deletion confirmation result"
                )
            return self

        if self.success:
            if (
                self.deleted_event is None
                or self.pending_event is not None
            ):
                raise ValueError("invalid successful event deletion")
            return self

        if self.pending_event is not None or self.deleted_event is not None:
            raise ValueError(
                "a failed deletion cannot contain event data"
            )

        return self
