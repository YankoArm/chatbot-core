from dataclasses import replace
from pathlib import Path

from chatbot.booking import (
    Booking,
    BookingStatus,
    SQLiteBookingRepository,
)


def make_booking() -> Booking:
    return Booking(
        name="Yanko",
        phone="+34600123123",
        date="30/08/2026",
        time="16:30",
        service_id="highlights",
        service_name="Mechas",
        duration_minutes=120,
        price_cents=6500,
        price_type="from",
        currency="EUR",
        calendar_booking_id="calendar-event-123",
    )


def build_repository(
    database_path: Path,
) -> SQLiteBookingRepository:
    return SQLiteBookingRepository(
        database_path=database_path,
    )


def test_sqlite_repository_persists_booking_after_reopening(
    tmp_path: Path,
) -> None:
    database_path = (
        tmp_path
        / "bookings.sqlite3"
    )
    booking = make_booking()

    repository = build_repository(
        database_path
    )
    repository.save(
        booking
    )
    repository.close()

    reopened_repository = build_repository(
        database_path
    )

    assert reopened_repository.find_by_phone(
        "+34600123123"
    ) == (
        booking,
    )

    reopened_repository.close()


def test_sqlite_repository_preserves_all_booking_fields(
    tmp_path: Path,
) -> None:
    repository = build_repository(
        tmp_path / "bookings.sqlite3"
    )
    booking = make_booking()

    repository.save(
        booking
    )

    stored_booking = repository.find_by_phone(
        booking.phone
    )[0]

    assert stored_booking.name == "Yanko"
    assert stored_booking.service_id == "highlights"
    assert stored_booking.service_name == "Mechas"
    assert stored_booking.duration_minutes == 120
    assert stored_booking.price_cents == 6500
    assert stored_booking.price_type == "from"
    assert stored_booking.currency == "EUR"
    assert stored_booking.calendar_booking_id == (
        "calendar-event-123"
    )
    assert stored_booking.status is BookingStatus.CONFIRMED

    repository.close()


def test_sqlite_repository_updates_booking_status(
    tmp_path: Path,
) -> None:
    repository = build_repository(
        tmp_path / "bookings.sqlite3"
    )
    booking = make_booking()

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

    assert repository.find_by_phone(
        booking.phone
    ) == (
        cancelled_booking,
    )

    repository.close()


def test_sqlite_repository_returns_empty_for_unknown_phone(
    tmp_path: Path,
) -> None:
    repository = build_repository(
        tmp_path / "bookings.sqlite3"
    )

    assert repository.find_by_phone(
        "+34600000000"
    ) == ()

    repository.close()


def test_sqlite_repository_keeps_multiple_bookings_for_phone(
    tmp_path: Path,
) -> None:
    repository = build_repository(
        tmp_path / "bookings.sqlite3"
    )

    first_booking = make_booking()
    second_booking = replace(
        first_booking,
        date="02/09/2026",
        time="10:00",
        calendar_booking_id="calendar-event-456",
    )

    repository.save(
        first_booking
    )
    repository.save(
        second_booking
    )

    assert repository.find_by_phone(
        first_booking.phone
    ) == (
        first_booking,
        second_booking,
    )

    repository.close()


def test_sqlite_repository_rejects_update_of_unknown_booking(
    tmp_path: Path,
) -> None:
    import pytest

    repository = build_repository(
        tmp_path / "bookings.sqlite3"
    )

    with pytest.raises(
        ValueError,
        match="Cannot update a booking that is not stored",
    ):
        repository.update(
            make_booking()
        )

    repository.close()