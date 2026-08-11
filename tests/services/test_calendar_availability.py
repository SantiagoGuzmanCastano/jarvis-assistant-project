from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from app.services.calendar_availability import (
    calculate_free_slots,
    merge_busy_intervals,
)


BOGOTA = ZoneInfo("America/Bogota")


def _datetime(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 7, 30, hour, minute, tzinfo=BOGOTA)


def test_merge_busy_intervals_merges_overlapping_and_adjacent_periods() -> None:
    result = merge_busy_intervals(
        [
            (_datetime(13), _datetime(14)),
            (_datetime(10, 30), _datetime(11, 30)),
            (_datetime(10), _datetime(11)),
            (_datetime(14), _datetime(14, 30)),
        ]
    )

    assert result == [
        (_datetime(10), _datetime(11, 30)),
        (_datetime(13), _datetime(14, 30)),
    ]


def test_calculate_free_slots_returns_only_maximal_windows_that_fit() -> None:
    result = calculate_free_slots(
        range_start=_datetime(9),
        range_end=_datetime(17),
        busy_intervals=[
            (_datetime(13), _datetime(14, 30)),
            (_datetime(10), _datetime(11)),
            (_datetime(8), _datetime(9, 30)),
        ],
        duration_minutes=60,
    )

    assert result == [
        (_datetime(11), _datetime(13)),
        (_datetime(14, 30), _datetime(17)),
    ]


def test_calculate_free_slots_rejects_duration_larger_than_range() -> None:
    with pytest.raises(
        ValueError,
        match="Duration must fit inside the requested range",
    ):
        calculate_free_slots(
            range_start=_datetime(9),
            range_end=_datetime(10),
            busy_intervals=[],
            duration_minutes=90,
        )
