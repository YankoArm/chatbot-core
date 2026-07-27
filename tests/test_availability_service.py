from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from chatbot.availability import (
    AvailabilityService,
    BookingRules,
    BusinessHours,
    BusyPeriod,
    InvalidAvailabilityWindowError,
    TimeSlot,
    Weekday,
)


MADRID = ZoneInfo("Europe/Madrid")


def build_business_hours() -> BusinessHours:
    return BusinessHours.standard_week(
        start=time(9, 0),
        end=time(12, 0),
        timezone_name="Europe/Madrid",
    )


def build_rules() -> BookingRules:
    return BookingRules.hourly(
        slot_interval_minutes=30,
    )


def build_now() -> datetime:
    return datetime(
        2026,
        7,
        27,
        6,
        0,
        tzinfo=timezone.utc,
    )


def build_slot(
    start_hour: int,
    start_minute: int = 0,
) -> TimeSlot:
    start = datetime(
        2026,
        7,
        27,
        start_hour,
        start_minute,
        tzinfo=MADRID,
    )

    end = start + timedelta(hours=1)

    return TimeSlot(
        start=start,
        end=end,
        occupied_start=start,
        occupied_end=end,
    )


def test_busy_period_requires_aware_datetimes() -> None:
    with pytest.raises(ValueError):
        BusyPeriod(
            start=datetime(2026, 7, 27, 10, 0),
            end=datetime(
                2026,
                7,
                27,
                11,
                0,
                tzinfo=MADRID,
            ),
        )


def test_busy_period_requires_end_after_start() -> None:
    start = datetime(
        2026,
        7,
        27,
        10,
        0,
        tzinfo=MADRID,
    )

    with pytest.raises(ValueError):
        BusyPeriod(
            start=start,
            end=start,
        )


def test_busy_period_overlaps_slot() -> None:
    slot = build_slot(10)

    busy = BusyPeriod(
        start=datetime(
            2026,
            7,
            27,
            10,
            30,
            tzinfo=MADRID,
        ),
        end=datetime(
            2026,
            7,
            27,
            11,
            30,
            tzinfo=MADRID,
        ),
    )

    assert busy.overlaps_slot(slot)


def test_busy_period_touching_slot_end_does_not_overlap() -> None:
    slot = build_slot(10)

    busy = BusyPeriod(
        start=datetime(
            2026,
            7,
            27,
            11,
            0,
            tzinfo=MADRID,
        ),
        end=datetime(
            2026,
            7,
            27,
            12,
            0,
            tzinfo=MADRID,
        ),
    )

    assert not busy.overlaps_slot(slot)


def test_get_available_slots_for_date_returns_all_slots() -> None:
    service = AvailabilityService()

    slots = service.get_available_slots_for_date(
        date(2026, 7, 27),
        business_hours=build_business_hours(),
        rules=build_rules(),
        now=build_now(),
    )

    assert [
        slot.start.strftime("%H:%M")
        for slot in slots
    ] == [
        "09:00",
        "09:30",
        "10:00",
        "10:30",
        "11:00",
    ]


def test_get_available_slots_for_closed_day_returns_empty() -> None:
    service = AvailabilityService()

    slots = service.get_available_slots_for_date(
        date(2026, 8, 2),
        business_hours=build_business_hours(),
        rules=build_rules(),
        now=build_now(),
    )

    assert slots == ()


def test_busy_period_removes_overlapping_slots() -> None:
    service = AvailabilityService()

    busy = BusyPeriod(
        start=datetime(
            2026,
            7,
            27,
            10,
            0,
            tzinfo=MADRID,
        ),
        end=datetime(
            2026,
            7,
            27,
            11,
            0,
            tzinfo=MADRID,
        ),
    )

    slots = service.get_available_slots_for_date(
        date(2026, 7, 27),
        business_hours=build_business_hours(),
        rules=build_rules(),
        busy_periods=(busy,),
        now=build_now(),
    )

    assert [
        slot.start.strftime("%H:%M")
        for slot in slots
    ] == [
        "09:00",
        "11:00",
    ]


def test_multiple_busy_periods_are_applied() -> None:
    service = AvailabilityService()

    busy_periods = (
        BusyPeriod(
            start=datetime(
                2026,
                7,
                27,
                9,
                0,
                tzinfo=MADRID,
            ),
            end=datetime(
                2026,
                7,
                27,
                10,
                0,
                tzinfo=MADRID,
            ),
        ),
        BusyPeriod(
            start=datetime(
                2026,
                7,
                27,
                11,
                0,
                tzinfo=MADRID,
            ),
            end=datetime(
                2026,
                7,
                27,
                12,
                0,
                tzinfo=MADRID,
            ),
        ),
    )

    slots = service.get_available_slots_for_date(
        date(2026, 7, 27),
        business_hours=build_business_hours(),
        rules=build_rules(),
        busy_periods=busy_periods,
        now=build_now(),
    )

    assert [
        slot.start.strftime("%H:%M")
        for slot in slots
    ] == [
        "10:00",
    ]


def test_busy_period_respects_slot_buffers() -> None:
    service = AvailabilityService()

    rules = BookingRules.hourly(
        slot_interval_minutes=30,
        buffer_before_minutes=15,
        buffer_after_minutes=15,
    )

    busy = BusyPeriod(
        start=datetime(
            2026,
            7,
            27,
            11,
            45,
            tzinfo=MADRID,
        ),
        end=datetime(
            2026,
            7,
            27,
            12,
            0,
            tzinfo=MADRID,
        ),
    )

    slots = service.get_available_slots_for_date(
        date(2026, 7, 27),
        business_hours=build_business_hours(),
        rules=rules,
        busy_periods=(busy,),
        now=build_now(),
    )

    assert [
        slot.start.strftime("%H:%M")
        for slot in slots
    ] == [
        "09:30",
        "10:00",
        "10:30",
    ]


def test_minimum_notice_filters_early_slots() -> None:
    service = AvailabilityService()

    rules = BookingRules(
        appointment_duration=timedelta(hours=1),
        slot_interval=timedelta(minutes=30),
        minimum_notice=timedelta(hours=3),
    )

    now = datetime(
        2026,
        7,
        27,
        7,
        0,
        tzinfo=MADRID,
    )

    slots = service.get_available_slots_for_date(
        date(2026, 7, 27),
        business_hours=build_business_hours(),
        rules=rules,
        now=now,
    )

    assert [
        slot.start.strftime("%H:%M")
        for slot in slots
    ] == [
        "10:00",
        "10:30",
        "11:00",
    ]


def test_maximum_advance_filters_late_slots() -> None:
    service = AvailabilityService()

    rules = BookingRules(
        appointment_duration=timedelta(hours=1),
        maximum_advance=timedelta(days=1),
    )

    slots = service.get_available_slots_between(
        date(2026, 7, 27),
        date(2026, 7, 29),
        business_hours=build_business_hours(),
        rules=rules,
        now=build_now(),
    )

    assert all(
        slot.start.date()
        in {
            date(2026, 7, 27),
            date(2026, 7, 28),
        }
        for slot in slots
    )


def test_past_slots_are_rejected_by_default() -> None:
    service = AvailabilityService()

    now = datetime(
        2026,
        7,
        27,
        10,
        15,
        tzinfo=MADRID,
    )

    slots = service.get_available_slots_for_date(
        date(2026, 7, 27),
        business_hours=build_business_hours(),
        rules=build_rules(),
        now=now,
    )

    assert [
        slot.start.strftime("%H:%M")
        for slot in slots
    ] == [
        "10:30",
        "11:00",
    ]


def test_past_slots_can_be_allowed() -> None:
    service = AvailabilityService()

    rules = BookingRules(
        appointment_duration=timedelta(hours=1),
        slot_interval=timedelta(minutes=30),
        allow_past_bookings=True,
    )

    now = datetime(
        2026,
        7,
        27,
        10,
        15,
        tzinfo=MADRID,
    )

    slots = service.get_available_slots_for_date(
        date(2026, 7, 27),
        business_hours=build_business_hours(),
        rules=rules,
        now=now,
    )

    assert [
        slot.start.strftime("%H:%M")
        for slot in slots
    ] == [
        "09:00",
        "09:30",
        "10:00",
        "10:30",
        "11:00",
    ]


def test_naive_now_is_rejected() -> None:
    service = AvailabilityService()

    with pytest.raises(ValueError):
        service.get_available_slots_for_date(
            date(2026, 7, 27),
            business_hours=build_business_hours(),
            rules=build_rules(),
            now=datetime(2026, 7, 27, 8, 0),
        )


def test_get_available_slots_between_includes_both_dates() -> None:
    service = AvailabilityService()

    business_hours = BusinessHours(
        {
            Weekday.MONDAY: (
                build_business_hours().hours_for_weekday(
                    Weekday.MONDAY
                )
            ),
            Weekday.TUESDAY: (
                build_business_hours().hours_for_weekday(
                    Weekday.TUESDAY
                )
            ),
        },
        timezone_name="Europe/Madrid",
    )

    slots = service.get_available_slots_between(
        date(2026, 7, 27),
        date(2026, 7, 28),
        business_hours=business_hours,
        rules=build_rules(),
        now=build_now(),
    )

    dates = {
        slot.start.date()
        for slot in slots
    }

    assert dates == {
        date(2026, 7, 27),
        date(2026, 7, 28),
    }


def test_invalid_availability_window_is_rejected() -> None:
    service = AvailabilityService()

    with pytest.raises(
        InvalidAvailabilityWindowError,
    ):
        service.get_available_slots_between(
            date(2026, 7, 28),
            date(2026, 7, 27),
            business_hours=build_business_hours(),
            rules=build_rules(),
            now=build_now(),
        )


def test_filter_available_slots_preserves_order() -> None:
    service = AvailabilityService()

    slots = (
        build_slot(11),
        build_slot(9),
        build_slot(10),
    )

    result = service.filter_available_slots(
        slots,
        rules=build_rules(),
        now=build_now(),
    )

    assert result == slots


def test_is_slot_available_returns_true() -> None:
    service = AvailabilityService()

    assert service.is_slot_available(
        build_slot(10),
        rules=build_rules(),
        now=build_now(),
    )


def test_is_slot_available_returns_false_when_busy() -> None:
    service = AvailabilityService()

    busy = BusyPeriod(
        start=datetime(
            2026,
            7,
            27,
            10,
            0,
            tzinfo=MADRID,
        ),
        end=datetime(
            2026,
            7,
            27,
            11,
            0,
            tzinfo=MADRID,
        ),
    )

    assert not service.is_slot_available(
        build_slot(10),
        rules=build_rules(),
        busy_periods=(busy,),
        now=build_now(),
    )


def test_find_next_available_slot_returns_first_slot() -> None:
    service = AvailabilityService()

    result = service.find_next_available_slot(
        date(2026, 7, 27),
        date(2026, 7, 27),
        business_hours=build_business_hours(),
        rules=build_rules(),
        now=build_now(),
    )

    assert result is not None
    assert result.start.strftime("%H:%M") == "09:00"


def test_find_next_available_slot_skips_busy_slots() -> None:
    service = AvailabilityService()

    busy = BusyPeriod(
        start=datetime(
            2026,
            7,
            27,
            9,
            0,
            tzinfo=MADRID,
        ),
        end=datetime(
            2026,
            7,
            27,
            10,
            30,
            tzinfo=MADRID,
        ),
    )

    result = service.find_next_available_slot(
        date(2026, 7, 27),
        date(2026, 7, 27),
        business_hours=build_business_hours(),
        rules=build_rules(),
        busy_periods=(busy,),
        now=build_now(),
    )

    assert result is not None
    assert result.start.strftime("%H:%M") == "10:30"


def test_find_next_available_slot_returns_none() -> None:
    service = AvailabilityService()

    busy = BusyPeriod(
        start=datetime(
            2026,
            7,
            27,
            8,
            0,
            tzinfo=MADRID,
        ),
        end=datetime(
            2026,
            7,
            27,
            13,
            0,
            tzinfo=MADRID,
        ),
    )

    result = service.find_next_available_slot(
        date(2026, 7, 27),
        date(2026, 7, 27),
        business_hours=build_business_hours(),
        rules=build_rules(),
        busy_periods=(busy,),
        now=build_now(),
    )

    assert result is None