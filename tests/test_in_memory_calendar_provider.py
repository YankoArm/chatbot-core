from datetime import datetime

from zoneinfo import ZoneInfo
import pytest

from chatbot.calendar import (
    InMemoryCalendarProvider,
)


def make_datetime(
    hour: int,
    minute: int = 0,
) -> datetime:
    return datetime(
        2026,
        8,
        10,
        hour,
        minute,
    )


def test_provider_reports_empty_slot_as_available():
    provider = InMemoryCalendarProvider()

    assert provider.is_available(
        start=make_datetime(10),
        end=make_datetime(11),
    ) is True


def test_provider_creates_and_lists_booking():
    provider = InMemoryCalendarProvider()

    booking_id = provider.create_booking(
        start=make_datetime(10),
        end=make_datetime(11),
        title="Tarot session",
        attendee="client@example.com",
        metadata={
            "client_name": "Lucía",
        },
    )

    bookings = provider.list_bookings(
        start=make_datetime(9),
        end=make_datetime(12),
    )

    assert len(bookings) == 1
    assert bookings[0]["id"] == booking_id
    assert bookings[0]["title"] == (
        "Tarot session"
    )
    assert bookings[0]["attendee"] == (
        "client@example.com"
    )
    assert bookings[0]["metadata"] == {
        "client_name": "Lucía",
    }


def test_provider_reports_overlapping_slot_as_unavailable():
    provider = InMemoryCalendarProvider()

    provider.create_booking(
        start=make_datetime(10),
        end=make_datetime(11),
        title="Existing session",
    )

    assert provider.is_available(
        start=make_datetime(10, 30),
        end=make_datetime(11, 30),
    ) is False


def test_provider_allows_adjacent_booking():
    provider = InMemoryCalendarProvider()

    provider.create_booking(
        start=make_datetime(10),
        end=make_datetime(11),
        title="First session",
    )

    assert provider.is_available(
        start=make_datetime(11),
        end=make_datetime(12),
    ) is True


def test_provider_rejects_overlapping_booking():
    provider = InMemoryCalendarProvider()

    provider.create_booking(
        start=make_datetime(10),
        end=make_datetime(11),
        title="Existing session",
    )

    with pytest.raises(
        ValueError,
        match="not available",
    ):
        provider.create_booking(
            start=make_datetime(10, 30),
            end=make_datetime(11, 30),
            title="Conflicting session",
        )


def test_provider_cancels_booking():
    provider = InMemoryCalendarProvider()

    booking_id = provider.create_booking(
        start=make_datetime(10),
        end=make_datetime(11),
        title="Tarot session",
    )

    provider.cancel_booking(
        booking_id
    )

    assert provider.list_bookings(
        start=make_datetime(9),
        end=make_datetime(12),
    ) == []

    assert provider.is_available(
        start=make_datetime(10),
        end=make_datetime(11),
    ) is True


def test_provider_rejects_invalid_time_range():
    provider = InMemoryCalendarProvider()

    with pytest.raises(
        ValueError,
        match="end must be after start",
    ):
        provider.is_available(
            start=make_datetime(11),
            end=make_datetime(10),
        )


def test_provider_rejects_empty_title():
    provider = InMemoryCalendarProvider()

    with pytest.raises(
        ValueError,
        match="title cannot be empty",
    ):
        provider.create_booking(
            start=make_datetime(10),
            end=make_datetime(11),
            title="   ",
        )


def test_provider_raises_when_cancelling_missing_booking():
    provider = InMemoryCalendarProvider()

    with pytest.raises(
        KeyError,
        match="Booking not found",
    ):
        provider.cancel_booking(
            "missing-booking"
        )

def test_provider_reschedules_existing_booking() -> None:
    provider = InMemoryCalendarProvider()

    booking_id = provider.create_booking(
        start=make_datetime(10),
        end=make_datetime(11),
        title="Original appointment",
    )

    provider.reschedule_booking(
        booking_id,
        start=make_datetime(12),
        end=make_datetime(13),
    )

    assert provider.is_available(
        start=make_datetime(10),
        end=make_datetime(11),
    ) is True

    assert provider.is_available(
        start=make_datetime(12),
        end=make_datetime(13),
    ) is False

    bookings = provider.list_bookings(
        start=make_datetime(11),
        end=make_datetime(14),
    )

    assert len(bookings) == 1
    assert bookings[0]["id"] == booking_id
    assert bookings[0]["start"] == make_datetime(12)
    assert bookings[0]["end"] == make_datetime(13)
    assert bookings[0]["title"] == (
        "Original appointment"
    )


def test_provider_rejects_rescheduling_unknown_booking() -> None:
    provider = InMemoryCalendarProvider()

    with pytest.raises(
        KeyError,
        match="Booking not found",
    ):
        provider.reschedule_booking(
            "missing-booking",
            start=make_datetime(12),
            end=make_datetime(13),
        )


def test_provider_compares_naive_and_aware_local_datetimes(
) -> None:
    provider = InMemoryCalendarProvider(
        timezone_name="Europe/Madrid",
    )

    provider.create_booking(
        start=datetime(
            2026,
            8,
            27,
            10,
            0,
        ),
        end=datetime(
            2026,
            8,
            27,
            11,
            0,
        ),
        title="Naive local appointment",
    )

    timezone = ZoneInfo(
        "Europe/Madrid"
    )

    bookings = provider.list_bookings(
        start=datetime(
            2026,
            8,
            27,
            9,
            30,
            tzinfo=timezone,
        ),
        end=datetime(
            2026,
            8,
            27,
            11,
            30,
            tzinfo=timezone,
        ),
    )

    assert len(bookings) == 1

    assert provider.is_available(
        start=datetime(
            2026,
            8,
            27,
            10,
            30,
            tzinfo=timezone,
        ),
        end=datetime(
            2026,
            8,
            27,
            11,
            30,
            tzinfo=timezone,
        ),
    ) is False