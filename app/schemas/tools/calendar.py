from datetime import date, datetime, timedelta
from typing import Annotated, Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    field_validator,
    model_validator,
)


def _normalize_datetime(value: datetime, timezone: str) -> datetime:
    target_timezone = ZoneInfo(timezone)
    if value.utcoffset() is None:
        return value.replace(tzinfo=target_timezone)
    return value.astimezone(target_timezone)


class CalendarBaseArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")

    calendar_id: str = Field(default="primary", min_length=1)
    timezone: str = Field(default="America/Bogota", min_length=1)

    @field_validator("calendar_id")
    @classmethod
    def validate_calendar_id(cls, value: str) -> str:
        normalized_value = value.strip()
        if not normalized_value:
            raise ValueError("calendar_id must not be empty")
        return normalized_value

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        normalized_value = value.strip()
        try:
            ZoneInfo(normalized_value)
        except ZoneInfoNotFoundError as error:
            raise ValueError("timezone must be a valid IANA timezone") from error
        return normalized_value


class CalendarPrepareEventArguments(CalendarBaseArguments):
    confirmed: Literal[False] = False
    title: str | None = Field(default=None, min_length=5, max_length=100)
    description: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    location: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def normalize_and_validate_dates(self):
        if self.start_date is not None:
            self.start_date = _normalize_datetime(
                self.start_date,
                self.timezone,
            )
        if self.end_date is not None:
            self.end_date = _normalize_datetime(
                self.end_date,
                self.timezone,
            )

        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date <= self.start_date
        ):
            raise ValueError("end_date must be later than start_date")

        return self


class CalendarConfirmEventArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confirmed: Literal[True]


CalendarCreateEventArgumentsValue = Annotated[
    CalendarPrepareEventArguments | CalendarConfirmEventArguments,
    Field(discriminator="confirmed"),
]


class CalendarCreateEventArguments(
    RootModel[CalendarCreateEventArgumentsValue]
):
    pass


class CalendarGmailSourceSelectionBase(CalendarBaseArguments):
    selection_source: Literal[
        "active",
        "recent",
        "search",
        "previous_selection",
    ]
    recent_result_position: int | None = Field(
        default=None,
        ge=1,
        le=2,
    )
    selected_result_position: int | None = Field(default=None, ge=1)
    search_keywords: list[str] = Field(default_factory=list)
    start_date: date | None = None
    end_date: date | None = None
    max_results: int = Field(default=5, ge=1, le=15)
    event_title: str | None = Field(
        default=None,
        min_length=5,
        max_length=100,
    )
    event_description: str | None = None
    event_start_date: datetime | None = None
    event_end_date: datetime | None = None
    event_location: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_selection_mode(self):
        if bool(self.event_start_date) != bool(self.event_end_date):
            raise ValueError(
                "event_start_date and event_end_date must be provided together"
            )
        if self.event_start_date is not None:
            self.event_start_date = _normalize_datetime(
                self.event_start_date,
                self.timezone,
            )
            self.event_end_date = _normalize_datetime(
                self.event_end_date,
                self.timezone,
            )
            if self.event_end_date <= self.event_start_date:
                raise ValueError(
                    "event_end_date must be later than event_start_date"
                )

        if bool(self.start_date) != bool(self.end_date):
            raise ValueError(
                "start_date and end_date must be provided together"
            )
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date <= self.start_date
        ):
            raise ValueError("end_date must be later than start_date")

        contact_hints = getattr(
            self,
            "sender_hint",
            getattr(self, "recipient_hint", []),
        )
        has_search_criteria = bool(
            contact_hints
            or self.search_keywords
            or self.start_date
            or self.end_date
        )

        if self.selection_source == "active":
            if (
                self.recent_result_position is not None
                or self.selected_result_position is not None
                or has_search_criteria
            ):
                raise ValueError(
                    "active selection does not accept positions or filters"
                )
            return self

        if self.selection_source == "recent":
            if self.recent_result_position is None:
                raise ValueError(
                    "recent_result_position is required for recent selection"
                )
            if (
                self.selected_result_position is not None
                or has_search_criteria
            ):
                raise ValueError(
                    "recent selection accepts only a recent position"
                )
            return self

        if self.selection_source == "search":
            if (
                self.recent_result_position is not None
                or self.selected_result_position is not None
            ):
                raise ValueError(
                    "search selection does not accept result positions"
                )
            if not has_search_criteria:
                raise ValueError(
                    "search selection requires at least one filter"
                )
            return self

        if self.selected_result_position is None:
            raise ValueError(
                "selected_result_position is required for "
                "previous_selection"
            )
        if (
            self.recent_result_position is not None
            or has_search_criteria
        ):
            raise ValueError(
                "previous_selection accepts only a selected position"
            )

        return self


class CalendarEmailSourceArguments(CalendarGmailSourceSelectionBase):
    source_type: Literal["email"]
    sender_hint: list[str] = Field(default_factory=list)


class CalendarSentEmailSourceArguments(CalendarGmailSourceSelectionBase):
    source_type: Literal["sent_email"]
    recipient_hint: list[str] = Field(default_factory=list)


class CalendarDraftSourceArguments(CalendarGmailSourceSelectionBase):
    source_type: Literal["draft"]
    recipient_hint: list[str] = Field(default_factory=list)


CalendarPrepareEventFromEmailArgumentsValue = Annotated[
    CalendarEmailSourceArguments
    | CalendarSentEmailSourceArguments
    | CalendarDraftSourceArguments,
    Field(discriminator="source_type"),
]


class CalendarPrepareEventFromEmailArguments(
    RootModel[CalendarPrepareEventFromEmailArgumentsValue]
):
    pass


class CalendarGetUpcomingEventsArguments(CalendarBaseArguments):
    start_date: datetime | None = None
    end_date: datetime | None = None
    max_results: int = Field(default=10, ge=1, le=15)

    @model_validator(mode="after")
    def normalize_and_validate_dates(self):
        if self.start_date is not None:
            self.start_date = _normalize_datetime(
                self.start_date,
                self.timezone,
            )

        if self.end_date is not None:
            self.end_date = _normalize_datetime(
                self.end_date,
                self.timezone,
            )

        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date <= self.start_date
        ):
            raise ValueError("end_date must be later than start_date")

        return self


class CalendarFindFreeSlotsArguments(CalendarBaseArguments):
    start_date: datetime
    end_date: datetime
    duration_minutes: int = Field(gt=0, le=1440)

    @model_validator(mode="after")
    def normalize_and_validate_dates(self):
        self.start_date = _normalize_datetime(self.start_date, self.timezone)
        self.end_date = _normalize_datetime(self.end_date, self.timezone)

        if self.end_date <= self.start_date:
            raise ValueError("end_date must be later than start_date")
        if timedelta(minutes=self.duration_minutes) > (
            self.end_date - self.start_date
        ):
            raise ValueError(
                "duration_minutes must fit inside the requested range"
            )

        return self


class CalendarPrepareEventUpdateArguments(CalendarBaseArguments):
    confirmed: Literal[False] = False
    title: str | None = Field(default=None, min_length=3, max_length=100)
    description: str | None = Field(
        default=None,
        min_length=3,
        max_length=500,
    )
    start_date: datetime | None = None
    end_date: datetime | None = None
    selected_result_position: int | None = Field(default=None, ge=1)
    max_results: int = Field(default=10, ge=1, le=15)
    new_title: str | None = Field(
        default=None,
        min_length=3,
        max_length=100,
    )
    new_description: str | None = Field(default=None, max_length=5000)
    new_start_date: datetime | None = None
    new_end_date: datetime | None = None
    new_location: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def normalize_and_validate_update(self):
        for field_name in (
            "start_date",
            "end_date",
            "new_start_date",
            "new_end_date",
        ):
            value = getattr(self, field_name)
            if value is not None:
                setattr(
                    self,
                    field_name,
                    _normalize_datetime(value, self.timezone),
                )

        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date <= self.start_date
        ):
            raise ValueError("end_date must be later than start_date")

        if (
            self.new_start_date is not None
            and self.new_end_date is not None
            and self.new_end_date <= self.new_start_date
        ):
            raise ValueError(
                "new_end_date must be later than new_start_date"
            )

        has_search_criteria = any(
            value is not None
            for value in (
                self.title,
                self.description,
                self.start_date,
                self.end_date,
            )
        )
        has_update_fields = any(
            value is not None
            for value in (
                self.new_title,
                self.new_description,
                self.new_start_date,
                self.new_end_date,
                self.new_location,
            )
        )

        if (
            self.selected_result_position is None
            and not has_search_criteria
        ):
            raise ValueError(
                "at least one event search criterion is required"
            )

        if (
            self.selected_result_position is None
            and not has_update_fields
        ):
            raise ValueError("at least one update field is required")

        return self


class CalendarConfirmEventUpdateArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confirmed: Literal[True]


CalendarUpdateEventArgumentsValue = Annotated[
    CalendarPrepareEventUpdateArguments
    | CalendarConfirmEventUpdateArguments,
    Field(discriminator="confirmed"),
]


class CalendarUpdateEventArguments(
    RootModel[CalendarUpdateEventArgumentsValue]
):
    pass


class CalendarPrepareEventDeleteArguments(CalendarBaseArguments):
    confirmed: Literal[False] = False
    title: str | None = Field(default=None, min_length=3, max_length=100)
    description: str | None = Field(
        default=None,
        min_length=3,
        max_length=500,
    )
    start_date: datetime | None = None
    end_date: datetime | None = None
    selected_result_position: int | None = Field(default=None, ge=1)
    max_results: int = Field(default=10, ge=1, le=15)

    @model_validator(mode="after")
    def normalize_and_validate_selection(self):
        if self.start_date is not None:
            self.start_date = _normalize_datetime(
                self.start_date,
                self.timezone,
            )
        if self.end_date is not None:
            self.end_date = _normalize_datetime(
                self.end_date,
                self.timezone,
            )
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date <= self.start_date
        ):
            raise ValueError("end_date must be later than start_date")

        has_search_criteria = any(
            value is not None
            for value in (
                self.title,
                self.description,
                self.start_date,
                self.end_date,
            )
        )
        if (
            self.selected_result_position is None
            and not has_search_criteria
        ):
            raise ValueError(
                "at least one event search criterion is required"
            )

        return self


class CalendarConfirmEventDeleteArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confirmed: Literal[True]


CalendarDeleteEventArgumentsValue = Annotated[
    CalendarPrepareEventDeleteArguments
    | CalendarConfirmEventDeleteArguments,
    Field(discriminator="confirmed"),
]


class CalendarDeleteEventArguments(
    RootModel[CalendarDeleteEventArgumentsValue]
):
    pass
