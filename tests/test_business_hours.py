from __future__ import annotations

from datetime import date, time

import pytest

from chatbot.availability import (
    BusinessHours,
    InvalidTimeRangeError,
    OverlappingTimeRangeError,
    TimeRange,
    Weekday,
)


def test_time_range_requires_end_after_start() -> None:
    with pytest.raises(
        ValueError,
    ):
        TimeRange(
            start=time(10, 0),
            end=time(9, 0),
        )


def test_time_range_rejects_equal_start_and_end() -> None:
    with pytest.raises(
        ValueError,
    ):
        TimeRange(
            start=time(10, 0),
            end=time(10, 0),
        )


def test_time_range_contains_start() -> None:
    time_range = TimeRange(
        start=time(9, 0),
        end=time(14, 0),
    )

    assert time_range.contains(
        time(9, 0),
    )


def test_time_range_contains_time_before_end() -> None:
    time_range = TimeRange(
        start=time(9, 0),
        end=time(14, 0),
    )

    assert time_range.contains(
        time(13, 59),
    )


def test_time_range_does_not_contain_end() -> None:
    time_range = TimeRange(
        start=time(9, 0),
        end=time(14, 0),
    )

    assert not time_range.contains(
        time(14, 0),
    )


def test_time_ranges_overlap() -> None:
    first = TimeRange(
        start=time(9, 0),
        end=time(14, 0),
    )

    second = TimeRange(
        start=time(13, 0),
        end=time(17, 0),
    )

    assert first.overlaps(second)
    assert second.overlaps(first)


def test_consecutive_time_ranges_do_not_overlap() -> None:
    first = TimeRange(
        start=time(9, 0),
        end=time(14, 0),
    )

    second = TimeRange(
        start=time(14, 0),
        end=time(17, 0),
    )

    assert not first.overlaps(second)
    assert not second.overlaps(first)


def test_business_hours_uses_utc_by_default() -> None:
    business_hours = BusinessHours()

    assert business_hours.timezone_name == "UTC"


def test_business_hours_accepts_timezone() -> None:
    business_hours = BusinessHours(
        timezone_name="Europe/Madrid",
    )

    assert business_hours.timezone_name == "Europe/Madrid"


def test_business_hours_rejects_empty_timezone() -> None:
    with pytest.raises(
        ValueError,
    ):
        BusinessHours(
            timezone_name="   ",
        )


def test_business_hours_contains_all_weekdays() -> None:
    business_hours = BusinessHours()

    assert set(
        business_hours.schedule,
    ) == set(Weekday)


def test_business_hours_is_closed_when_day_has_no_ranges() -> None:
    business_hours = BusinessHours()

    assert business_hours.is_closed(
        Weekday.MONDAY,
    )


def test_business_hours_returns_ranges_for_weekday() -> None:
    morning = TimeRange(
        start=time(9, 0),
        end=time(14, 0),
    )

    afternoon = TimeRange(
        start=time(17, 0),
        end=time(20, 0),
    )

    business_hours = BusinessHours(
        {
            Weekday.MONDAY: (
                morning,
                afternoon,
            ),
        },
        timezone_name="Europe/Madrid",
    )

    assert business_hours.hours_for_weekday(
        Weekday.MONDAY,
    ) == (
        morning,
        afternoon,
    )


def test_business_hours_accepts_integer_weekday() -> None:
    monday_hours = (
        TimeRange(
            start=time(9, 0),
            end=time(14, 0),
        ),
    )

    business_hours = BusinessHours(
        {
            0: monday_hours,
        }
    )

    assert business_hours.hours_for_weekday(
        0,
    ) == monday_hours


def test_business_hours_rejects_invalid_weekday() -> None:
    with pytest.raises(
        ValueError,
    ):
        BusinessHours(
            {
                7: (),
            }
        )


def test_business_hours_sorts_ranges() -> None:
    morning = TimeRange(
        start=time(9, 0),
        end=time(14, 0),
    )

    afternoon = TimeRange(
        start=time(17, 0),
        end=time(20, 0),
    )

    business_hours = BusinessHours(
        {
            Weekday.MONDAY: (
                afternoon,
                morning,
            ),
        }
    )

    assert business_hours.hours_for_weekday(
        Weekday.MONDAY,
    ) == (
        morning,
        afternoon,
    )


def test_business_hours_rejects_overlapping_ranges() -> None:
    with pytest.raises(
        OverlappingTimeRangeError,
    ):
        BusinessHours(
            {
                Weekday.MONDAY: (
                    TimeRange(
                        start=time(9, 0),
                        end=time(14, 0),
                    ),
                    TimeRange(
                        start=time(13, 0),
                        end=time(17, 0),
                    ),
                ),
            }
        )


def test_business_hours_accepts_consecutive_ranges() -> None:
    first = TimeRange(
        start=time(9, 0),
        end=time(14, 0),
    )

    second = TimeRange(
        start=time(14, 0),
        end=time(17, 0),
    )

    business_hours = BusinessHours(
        {
            Weekday.MONDAY: (
                first,
                second,
            ),
        }
    )

    assert business_hours.hours_for_weekday(
        Weekday.MONDAY,
    ) == (
        first,
        second,
    )


def test_business_hours_rejects_non_time_range_entries() -> None:
    with pytest.raises(
        InvalidTimeRangeError,
    ):
        BusinessHours(
            {
                Weekday.MONDAY: (
                    ("09:00", "14:00"),
                ),
            }
        )


def test_hours_for_date_uses_date_weekday() -> None:
    monday_hours = (
        TimeRange(
            start=time(9, 0),
            end=time(14, 0),
        ),
    )

    business_hours = BusinessHours(
        {
            Weekday.MONDAY: monday_hours,
        }
    )

    monday = date(
        2026,
        7,
        27,
    )

    assert monday.weekday() == Weekday.MONDAY

    assert business_hours.hours_for_date(
        monday,
    ) == monday_hours


def test_is_closed_accepts_date() -> None:
    business_hours = BusinessHours(
        {
            Weekday.MONDAY: (
                TimeRange(
                    start=time(9, 0),
                    end=time(14, 0),
                ),
            ),
        }
    )

    monday = date(
        2026,
        7,
        27,
    )

    sunday = date(
        2026,
        8,
        2,
    )

    assert not business_hours.is_closed(
        monday,
    )

    assert business_hours.is_closed(
        sunday,
    )


def test_contains_returns_true_inside_business_hours() -> None:
    business_hours = BusinessHours(
        {
            Weekday.MONDAY: (
                TimeRange(
                    start=time(9, 0),
                    end=time(14, 0),
                ),
            ),
        }
    )

    assert business_hours.contains(
        time(11, 30),
        weekday=Weekday.MONDAY,
    )


def test_contains_returns_false_outside_business_hours() -> None:
    business_hours = BusinessHours(
        {
            Weekday.MONDAY: (
                TimeRange(
                    start=time(9, 0),
                    end=time(14, 0),
                ),
            ),
        }
    )

    assert not business_hours.contains(
        time(17, 0),
        weekday=Weekday.MONDAY,
    )


def test_standard_week_creates_monday_to_friday_schedule() -> None:
    business_hours = BusinessHours.standard_week(
        start=time(9, 0),
        end=time(18, 0),
        timezone_name="Europe/Madrid",
    )

    expected_range = (
        TimeRange(
            start=time(9, 0),
            end=time(18, 0),
        ),
    )

    for weekday in (
        Weekday.MONDAY,
        Weekday.TUESDAY,
        Weekday.WEDNESDAY,
        Weekday.THURSDAY,
        Weekday.FRIDAY,
    ):
        assert business_hours.hours_for_weekday(
            weekday,
        ) == expected_range

    assert business_hours.is_closed(
        Weekday.SATURDAY,
    )

    assert business_hours.is_closed(
        Weekday.SUNDAY,
    )

    assert (
        business_hours.timezone_name
        == "Europe/Madrid"
    )


def test_schedule_mapping_is_read_only() -> None:
    business_hours = BusinessHours()

    with pytest.raises(
        TypeError,
    ):
        business_hours.schedule[
            Weekday.MONDAY
        ] = ()