from __future__ import annotations

from datetime import timedelta

import pytest

from chatbot.availability import (
    BookingRules,
    InvalidBookingNoticeError,
    InvalidBookingWindowError,
    InvalidBufferError,
    InvalidDurationError,
    InvalidSlotIntervalError,
)


def test_booking_rules_accepts_valid_configuration() -> None:
    rules = BookingRules(
        appointment_duration=timedelta(hours=1),
        slot_interval=timedelta(minutes=30),
        buffer_before=timedelta(minutes=10),
        buffer_after=timedelta(minutes=15),
        minimum_notice=timedelta(hours=24),
        maximum_advance=timedelta(days=90),
    )

    assert rules.appointment_duration == timedelta(hours=1)
    assert rules.slot_interval == timedelta(minutes=30)
    assert rules.buffer_before == timedelta(minutes=10)
    assert rules.buffer_after == timedelta(minutes=15)
    assert rules.minimum_notice == timedelta(hours=24)
    assert rules.maximum_advance == timedelta(days=90)
    assert rules.allow_past_bookings is False


def test_booking_rules_uses_default_values() -> None:
    rules = BookingRules(
        appointment_duration=timedelta(hours=1),
    )

    assert rules.slot_interval == timedelta(minutes=30)
    assert rules.buffer_before == timedelta(0)
    assert rules.buffer_after == timedelta(0)
    assert rules.minimum_notice == timedelta(0)
    assert rules.maximum_advance is None
    assert rules.allow_past_bookings is False


def test_occupied_duration_without_buffers() -> None:
    rules = BookingRules(
        appointment_duration=timedelta(hours=1),
    )

    assert rules.occupied_duration == timedelta(hours=1)


def test_occupied_duration_includes_buffers() -> None:
    rules = BookingRules(
        appointment_duration=timedelta(hours=1),
        buffer_before=timedelta(minutes=10),
        buffer_after=timedelta(minutes=15),
    )

    assert rules.occupied_duration == timedelta(
        hours=1,
        minutes=25,
    )


@pytest.mark.parametrize(
    "duration",
    [
        timedelta(0),
        timedelta(minutes=-1),
        timedelta(hours=-1),
    ],
)
def test_rejects_invalid_appointment_duration(
    duration: timedelta,
) -> None:
    with pytest.raises(
        InvalidDurationError,
    ):
        BookingRules(
            appointment_duration=duration,
        )


@pytest.mark.parametrize(
    "slot_interval",
    [
        timedelta(0),
        timedelta(minutes=-1),
        timedelta(hours=-1),
    ],
)
def test_rejects_invalid_slot_interval(
    slot_interval: timedelta,
) -> None:
    with pytest.raises(
        InvalidSlotIntervalError,
    ):
        BookingRules(
            appointment_duration=timedelta(hours=1),
            slot_interval=slot_interval,
        )


def test_rejects_negative_buffer_before() -> None:
    with pytest.raises(
        InvalidBufferError,
    ):
        BookingRules(
            appointment_duration=timedelta(hours=1),
            buffer_before=timedelta(minutes=-1),
        )


def test_rejects_negative_buffer_after() -> None:
    with pytest.raises(
        InvalidBufferError,
    ):
        BookingRules(
            appointment_duration=timedelta(hours=1),
            buffer_after=timedelta(minutes=-1),
        )


def test_accepts_zero_buffers() -> None:
    rules = BookingRules(
        appointment_duration=timedelta(hours=1),
        buffer_before=timedelta(0),
        buffer_after=timedelta(0),
    )

    assert rules.buffer_before == timedelta(0)
    assert rules.buffer_after == timedelta(0)


def test_rejects_negative_minimum_notice() -> None:
    with pytest.raises(
        InvalidBookingNoticeError,
    ):
        BookingRules(
            appointment_duration=timedelta(hours=1),
            minimum_notice=timedelta(minutes=-1),
        )


def test_accepts_zero_minimum_notice() -> None:
    rules = BookingRules(
        appointment_duration=timedelta(hours=1),
        minimum_notice=timedelta(0),
    )

    assert rules.minimum_notice == timedelta(0)


def test_accepts_no_maximum_advance() -> None:
    rules = BookingRules(
        appointment_duration=timedelta(hours=1),
        maximum_advance=None,
    )

    assert rules.maximum_advance is None


@pytest.mark.parametrize(
    "maximum_advance",
    [
        timedelta(0),
        timedelta(minutes=-1),
        timedelta(days=-1),
    ],
)
def test_rejects_invalid_maximum_advance(
    maximum_advance: timedelta,
) -> None:
    with pytest.raises(
        InvalidBookingWindowError,
    ):
        BookingRules(
            appointment_duration=timedelta(hours=1),
            maximum_advance=maximum_advance,
        )


def test_rejects_minimum_notice_greater_than_maximum_advance() -> None:
    with pytest.raises(
        InvalidBookingWindowError,
    ):
        BookingRules(
            appointment_duration=timedelta(hours=1),
            minimum_notice=timedelta(days=10),
            maximum_advance=timedelta(days=5),
        )


def test_accepts_minimum_notice_equal_to_maximum_advance() -> None:
    rules = BookingRules(
        appointment_duration=timedelta(hours=1),
        minimum_notice=timedelta(days=5),
        maximum_advance=timedelta(days=5),
    )

    assert rules.minimum_notice == rules.maximum_advance


def test_allow_past_bookings_can_be_enabled() -> None:
    rules = BookingRules(
        appointment_duration=timedelta(hours=1),
        allow_past_bookings=True,
    )

    assert rules.allow_past_bookings is True


def test_hourly_factory_creates_one_hour_appointment() -> None:
    rules = BookingRules.hourly()

    assert rules.appointment_duration == timedelta(hours=1)


def test_hourly_factory_uses_default_slot_interval() -> None:
    rules = BookingRules.hourly()

    assert rules.slot_interval == timedelta(minutes=30)


def test_hourly_factory_accepts_custom_slot_interval() -> None:
    rules = BookingRules.hourly(
        slot_interval_minutes=15,
    )

    assert rules.slot_interval == timedelta(minutes=15)


def test_hourly_factory_builds_buffers() -> None:
    rules = BookingRules.hourly(
        buffer_before_minutes=10,
        buffer_after_minutes=15,
    )

    assert rules.buffer_before == timedelta(minutes=10)
    assert rules.buffer_after == timedelta(minutes=15)
    assert rules.occupied_duration == timedelta(
        hours=1,
        minutes=25,
    )


def test_hourly_factory_builds_minimum_notice() -> None:
    rules = BookingRules.hourly(
        minimum_notice_hours=24,
    )

    assert rules.minimum_notice == timedelta(days=1)


def test_hourly_factory_builds_maximum_advance() -> None:
    rules = BookingRules.hourly(
        maximum_advance_days=90,
    )

    assert rules.maximum_advance == timedelta(days=90)


def test_hourly_factory_accepts_unlimited_advance() -> None:
    rules = BookingRules.hourly(
        maximum_advance_days=None,
    )

    assert rules.maximum_advance is None


def test_hourly_factory_rejects_invalid_slot_interval() -> None:
    with pytest.raises(
        InvalidSlotIntervalError,
    ):
        BookingRules.hourly(
            slot_interval_minutes=0,
        )


def test_hourly_factory_rejects_negative_buffer() -> None:
    with pytest.raises(
        InvalidBufferError,
    ):
        BookingRules.hourly(
            buffer_after_minutes=-1,
        )


def test_hourly_factory_rejects_invalid_maximum_advance() -> None:
    with pytest.raises(
        InvalidBookingWindowError,
    ):
        BookingRules.hourly(
            maximum_advance_days=0,
        )


def test_booking_rules_is_immutable() -> None:
    rules = BookingRules(
        appointment_duration=timedelta(hours=1),
    )

    with pytest.raises(
        AttributeError,
    ):
        rules.appointment_duration = timedelta(
            hours=2,
        )