from datetime import datetime

import pytest

from chatbot.booking.models import Booking
from chatbot.booking.repository import BookingRepository
from chatbot.booking.service import BookingService
from chatbot.booking.state import BookingState
from chatbot.calendar import InMemoryCalendarProvider

class FakeBookingRepository(BookingRepository):

    def __init__(self):
        self.saved_booking = None

    def save(
        self,
        booking: Booking,
    ) -> None:
        self.saved_booking = booking


def make_complete_state() -> BookingState:
    state = BookingState()

    state.name = "Yanko"
    state.phone = "600123123"
    state.date = "25/07/2026"
    state.time = "16:30"

    state.confirm()

    return state

def test_booking_service_saves_booking():
    repository = FakeBookingRepository()

    service = BookingService(
        repository
    )

    booking = Booking(
        name="Yanko",
        phone="600123123",
        date="25/07/2026",
        time="16:30",
    )

    service.create_booking(
        booking
    )

    assert repository.saved_booking == booking


def test_booking_service_creates_booking_from_state():
    repository = FakeBookingRepository()

    service = BookingService(
        repository
    )

    booking = service.create_booking_from_state(
        make_complete_state()
    )

    assert repository.saved_booking == booking

    assert booking == Booking(
        name="Yanko",
        phone="600123123",
        date="25/07/2026",
        time="16:30",
    )


def test_booking_service_creates_calendar_event():
    repository = FakeBookingRepository()
    calendar = InMemoryCalendarProvider()

    service = BookingService(
        repository=repository,
        calendar_provider=calendar,
    )

    booking = service.create_booking_from_state(
        make_complete_state()
    )

    bookings = calendar.list_bookings(
        start=datetime(
            2026,
            7,
            25,
            16,
            0,
        ),
        end=datetime(
            2026,
            7,
            25,
            18,
            0,
        ),
    )

    assert repository.saved_booking == booking
    assert len(bookings) == 1

    assert bookings[0]["start"] == datetime(
        2026,
        7,
        25,
        16,
        30,
    )

    assert bookings[0]["end"] == datetime(
        2026,
        7,
        25,
        17,
        30,
    )

    assert bookings[0]["title"] == (
        "Booking - Yanko"
    )

    assert bookings[0]["metadata"][
        "client_phone"
    ] == "600123123"


def test_booking_service_rejects_unavailable_time():
    repository = FakeBookingRepository()
    calendar = InMemoryCalendarProvider()

    calendar.create_booking(
        start=datetime(
            2026,
            7,
            25,
            16,
            0,
        ),
        end=datetime(
            2026,
            7,
            25,
            17,
            0,
        ),
        title="Existing booking",
    )

    service = BookingService(
        repository=repository,
        calendar_provider=calendar,
    )

    with pytest.raises(
        ValueError,
        match="not available",
    ):
        service.create_booking_from_state(
            make_complete_state()
        )

    assert repository.saved_booking is None


def test_booking_service_uses_configured_duration():
    repository = FakeBookingRepository()
    calendar = InMemoryCalendarProvider()

    service = BookingService(
        repository=repository,
        calendar_provider=calendar,
        duration_minutes=30,
    )

    service.create_booking_from_state(
        make_complete_state()
    )

    bookings = calendar.list_bookings(
        start=datetime(
            2026,
            7,
            25,
            16,
            0,
        ),
        end=datetime(
            2026,
            7,
            25,
            18,
            0,
        ),
    )

    assert bookings[0]["start"] == datetime(
        2026,
        7,
        25,
        16,
        30,
    )

    assert bookings[0]["end"] == datetime(
        2026,
        7,
        25,
        17,
        0,
    )


def test_booking_service_rejects_invalid_duration():
    repository = FakeBookingRepository()

    with pytest.raises(
        ValueError,
        match="duration must be greater than zero",
    ):
        BookingService(
            repository=repository,
            duration_minutes=0,
        )


def test_booking_service_rejects_invalid_datetime_format():
    repository = FakeBookingRepository()
    calendar = InMemoryCalendarProvider()

    state = make_complete_state()
    state.date = "2026-07-25"

    service = BookingService(
        repository=repository,
        calendar_provider=calendar,
    )

    with pytest.raises(
        ValueError,
        match="DD/MM/YYYY and HH:MM",
    ):
        service.create_booking_from_state(
            state
        )