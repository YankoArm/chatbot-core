from dataclasses import replace

from chatbot.booking import (
    Booking,
    BookingStatus,
    InMemoryBookingRepository,
)


def test_repository_finds_bookings_by_phone() -> None:
    repository = InMemoryBookingRepository()

    matching_booking = Booking(
        name="Yanko",
        phone="+34600123123",
        date="30/08/2026",
        time="16:30",
    )
    other_booking = Booking(
        name="Otra persona",
        phone="+34600999999",
        date="31/08/2026",
        time="10:00",
    )

    repository.save(
        matching_booking
    )
    repository.save(
        other_booking
    )

    result = repository.find_by_phone(
        "+34600123123"
    )

    assert result == (
        matching_booking,
    )


def test_repository_returns_empty_result_for_unknown_phone() -> None:
    repository = InMemoryBookingRepository()

    assert repository.find_by_phone(
        "+34600000000"
    ) == ()

def test_repository_updates_booking_without_deleting_history() -> None:
    repository = InMemoryBookingRepository()

    booking = Booking(
        name="Yanko",
        phone="+34600123123",
        date="30/08/2026",
        time="16:30",
        calendar_booking_id="calendar-event-123",
    )

    repository.save(
        booking
    )

    cancelled_booking = replace(
        booking,
        status=BookingStatus.CANCELLED,
    )

    repository.update(
        cancelled_booking
    )

    assert repository.list_all() == [
        cancelled_booking,
    ]
    assert repository.find_by_phone(
        "+34600123123"
    ) == (
        cancelled_booking,
    )