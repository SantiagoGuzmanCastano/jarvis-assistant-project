from datetime import datetime, timedelta


BusyInterval = tuple[datetime, datetime]


def merge_busy_intervals(
    busy_intervals: list[BusyInterval],
) -> list[BusyInterval]:
    sorted_intervals = sorted(
        busy_intervals,
        key=lambda interval: interval[0],
    )
    merged_intervals: list[BusyInterval] = []

    for current_start, current_end in sorted_intervals:
        if current_end <= current_start:
            raise ValueError(
                "Busy interval end must be later than its start."
            )

        if not merged_intervals:
            merged_intervals.append((current_start, current_end))
            continue

        last_start, last_end = merged_intervals[-1]

        if current_start <= last_end:
            merged_intervals[-1] = (
                last_start,
                max(last_end, current_end),
            )
            continue

        merged_intervals.append((current_start, current_end))

    return merged_intervals


def calculate_free_slots(
    range_start: datetime,
    range_end: datetime,
    busy_intervals: list[BusyInterval],
    duration_minutes: int,
) -> list[BusyInterval]:
    if range_end <= range_start:
        raise ValueError("Range end must be later than range start.")
    if duration_minutes <= 0:
        raise ValueError("Duration must be greater than zero.")

    minimum_duration = timedelta(minutes=duration_minutes)
    if minimum_duration > range_end - range_start:
        raise ValueError("Duration must fit inside the requested range.")

    clamped_busy_intervals = []
    for busy_start, busy_end in busy_intervals:
        clamped_start = max(busy_start, range_start)
        clamped_end = min(busy_end, range_end)

        if clamped_end > clamped_start:
            clamped_busy_intervals.append(
                (clamped_start, clamped_end)
            )

    merged_busy_intervals = merge_busy_intervals(
        clamped_busy_intervals
    )
    free_slots = []
    cursor = range_start

    for busy_start, busy_end in merged_busy_intervals:
        if busy_start - cursor >= minimum_duration:
            free_slots.append((cursor, busy_start))

        cursor = max(cursor, busy_end)

    if range_end - cursor >= minimum_duration:
        free_slots.append((cursor, range_end))

    return free_slots
