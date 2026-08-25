from datetime import date, datetime, time, timezone
from unittest.mock import Mock
from zoneinfo import ZoneInfo

import pytest

from chatbot.availability import (
    BookingRules,
    BusinessHours,
    TimeSlot,
)
from chatbot.booking.models import Booking
from chatbot.booking.repository import BookingRepository
from chatbot.booking.service import (
    BookingService,
    BookingSlotUnavailableError,
)
from chatbot.booking.state import BookingState
from chatbot.calendar import (
    CalendarService,
    InMemoryCalendarProvider,
)


MADRID = ZoneInfo("Europe/Madrid")


class FakeBookingRepository(BookingRepository):

    def __init__(self) -> None:
        self.saved_booking: Booking | None = None

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


def make_unconfirmed_state(
    *,
    booking_date: str = "27/07/2026",
    booking_time: str = "16:30",
) -> BookingState:
    return BookingState(
        name="Yanko",
        phone="600123123",
        date=booking_date,
        time=booking_time,
    )


def make_business_hours() -> BusinessHours:
    return BusinessHours.standard_week(
        start=time(9, 0),
        end=time(18, 0),
        timezone_name="Europe/Madrid",
    )


def make_booking_rules() -> BookingRules:
    return BookingRules.hourly(
        slot_interval_minutes=30,
    )


def make_now() -> datetime:
    return datetime(
        2026,
        7,
        27,
        8,
        0,
        tzinfo=MADRID,
    )


def make_available_slot(
    *,
    hour: int = 16,
    minute: int = 30,
) -> TimeSlot:
    start = datetime(
        2026,
        7,
        27,
        hour,
        minute,
        tzinfo=MADRID,
    )

    end = start + make_booking_rules().appointment_duration

    return TimeSlot(
        start=start,
        end=end,
        occupied_start=start,
        occupied_end=end,
    )


def test_booking_service_saves_booking() -> None:
    repository = FakeBookingRepository()

    service = BookingService(
        repository,
    )

    booking = Booking(
        name="Yanko",
        phone="600123123",
        date="25/07/2026",
        time="16:30",
    )

    service.create_booking(
        booking,
    )

    assert repository.saved_booking == booking


def test_booking_service_creates_booking_from_state() -> None:
    repository = FakeBookingRepository()

    service = BookingService(
        repository,
    )

    booking = service.create_booking_from_state(
        make_complete_state(),
    )

    assert repository.saved_booking == booking

    assert booking == Booking(
        name="Yanko",
        phone="600123123",
        date="25/07/2026",
        time="16:30",
    )


def test_booking_service_confirms_state_after_creation() -> None:
    repository = FakeBookingRepository()

    service = BookingService(
        repository,
    )

    state = BookingState(
        name="Yanko",
        phone="600123123",
        date="25/07/2026",
        time="16:30",
    )

    assert state.has_required_data is True
    assert state.confirmed is False
    assert state.is_complete is False

    booking = service.create_booking_from_state(
        state,
    )

    assert repository.saved_booking == booking
    assert state.confirmed is True
    assert state.is_complete is True
    assert state.booking_id is None


def test_booking_service_creates_calendar_event() -> None:
    repository = FakeBookingRepository()
    calendar_provider = InMemoryCalendarProvider()

    calendar_service = CalendarService(
        provider=calendar_provider,
    )

    service = BookingService(
        repository=repository,
        calendar_service=calendar_service,
    )

    state = make_complete_state()

    booking = service.create_booking_from_state(
        state,
    )

    bookings = calendar_provider.list_bookings(
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

    assert state.booking_id == bookings[0]["id"]


def test_booking_service_creates_booking_when_slot_is_still_available(
) -> None:
    repository = FakeBookingRepository()
    calendar_service = Mock(spec=CalendarService)

    business_hours = make_business_hours()
    rules = make_booking_rules()
    now = make_now()

    calendar_service.get_available_slots_for_date.return_value = (
        make_available_slot(),
    )

    calendar_service.create_booking.return_value = (
        "booking-123"
    )

    service = BookingService(
        repository=repository,
        calendar_service=calendar_service,
    )

    state = make_unconfirmed_state()

    booking = service.create_booking_from_state(
        state,
        business_hours=business_hours,
        rules=rules,
        now=now,
    )

    assert repository.saved_booking == booking
    assert state.confirmed is True
    assert state.is_complete is True
    assert state.booking_id == "booking-123"
    assert state.available_times == ()

    calendar_service.get_available_slots_for_date.assert_called_once_with(
        date(
            2026,
            7,
            27,
        ),
        business_hours=business_hours,
        rules=rules,
        now=now,
    )

    calendar_service.create_booking.assert_called_once()


def test_booking_service_rejects_slot_that_became_unavailable(
) -> None:
    repository = FakeBookingRepository()
    calendar_service = Mock(spec=CalendarService)

    business_hours = make_business_hours()
    rules = make_booking_rules()
    now = make_now()

    calendar_service.get_available_slots_for_date.return_value = (
        make_available_slot(
            hour=15,
            minute=0,
        ),
    )

    service = BookingService(
        repository=repository,
        calendar_service=calendar_service,
    )

    state = make_unconfirmed_state(
        booking_time="16:30",
    )

    assert state.confirmed is False
    assert state.booking_id is None

    with pytest.raises(
        BookingSlotUnavailableError,
    ):
        service.create_booking_from_state(
            state,
            business_hours=business_hours,
            rules=rules,
            now=now,
        )

    assert repository.saved_booking is None
    assert state.confirmed is False
    assert state.is_complete is False
    assert state.booking_id is None

    calendar_service.get_available_slots_for_date.assert_called_once_with(
        date(
            2026,
            7,
            27,
        ),
        business_hours=business_hours,
        rules=rules,
        now=now,
    )

    calendar_service.create_booking.assert_not_called()


def test_booking_service_rejects_unavailable_time() -> None:
    repository = FakeBookingRepository()
    calendar_provider = InMemoryCalendarProvider()

    calendar_provider.create_booking(
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

    calendar_service = CalendarService(
        provider=calendar_provider,
    )

    service = BookingService(
        repository=repository,
        calendar_service=calendar_service,
    )

    state = make_complete_state()

    with pytest.raises(
        ValueError,
        match="not available",
    ):
        service.create_booking_from_state(
            state,
        )

    assert repository.saved_booking is None
    assert state.booking_id is None


def test_booking_service_uses_configured_duration() -> None:
    repository = FakeBookingRepository()
    calendar_provider = InMemoryCalendarProvider()

    calendar_service = CalendarService(
        provider=calendar_provider,
        default_duration_minutes=30,
    )

    service = BookingService(
        repository=repository,
        calendar_service=calendar_service,
    )

    service.create_booking_from_state(
        make_complete_state(),
    )

    bookings = calendar_provider.list_bookings(
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


def test_booking_service_rejects_invalid_datetime_format() -> None:
    repository = FakeBookingRepository()
    calendar_provider = InMemoryCalendarProvider()

    calendar_service = CalendarService(
        provider=calendar_provider,
    )

    state = make_complete_state()
    state.date = "2026-07-25"

    service = BookingService(
        repository=repository,
        calendar_service=calendar_service,
    )

    with pytest.raises(
        ValueError,
        match="DD/MM/YYYY and HH:MM",
    ):
        service.create_booking_from_state(
            state,
        )

    assert repository.saved_booking is None


def test_get_available_slots_for_date_delegates_to_calendar_service(
) -> None:
    repository = FakeBookingRepository()
    calendar_service = Mock()

    business_hours = Mock(spec=BusinessHours)
    rules = Mock(spec=BookingRules)

    now = datetime(
        2026,
        7,
        27,
        10,
        0,
        tzinfo=timezone.utc,
    )

    target_date = date(
        2026,
        7,
        28,
    )

    expected_slots = (
        Mock(spec=TimeSlot),
        Mock(spec=TimeSlot),
    )

    calendar_service.get_available_slots_for_date.return_value = (
        expected_slots
    )

    service = BookingService(
        repository=repository,
        calendar_service=calendar_service,
    )

    result = service.get_available_slots_for_date(
        target_date,
        business_hours=business_hours,
        rules=rules,
        now=now,
    )

    assert result == expected_slots

    calendar_service.get_available_slots_for_date.assert_called_once_with(
        target_date,
        business_hours=business_hours,
        rules=rules,
        now=now,
    )


def test_get_available_slots_for_date_returns_empty_without_calendar(
) -> None:
    repository = FakeBookingRepository()

    service = BookingService(
        repository=repository,
    )

    result = service.get_available_slots_for_date(
        date(
            2026,
            7,
            28,
        ),
        business_hours=Mock(
            spec=BusinessHours,
        ),
        rules=Mock(
            spec=BookingRules,
        ),
        now=datetime(
            2026,
            7,
            27,
            10,
            0,
            tzinfo=timezone.utc,
        ),
    )

    assert result == ()


def test_booking_service_creates_service_aware_calendar_event() -> None:
    repository = FakeBookingRepository()
    calendar_provider = InMemoryCalendarProvider()

    calendar_service = CalendarService(
        provider=calendar_provider,
    )

    service = BookingService(
        repository=repository,
        calendar_service=calendar_service,
    )

    state = BookingState(
        requires_service_selection=True,
        service_id="highlights",
        service_name="Mechas",
        service_duration_minutes=120,
        service_price_cents=6500,
        service_price_type="from",
        service_currency="EUR",
        name="Yanko",
        phone="+34600123123",
        date="25/07/2026",
        time="16:30",
    )

    booking = service.create_booking_from_state(
        state,
    )

    assert repository.saved_booking == booking
    assert booking.service_id == "highlights"
    assert booking.service_name == "Mechas"
    assert booking.duration_minutes == 120
    assert booking.price_cents == 6500
    assert booking.price_type == "from"
    assert booking.currency == "EUR"

    bookings = calendar_provider.list_bookings(
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
            19,
            0,
        ),
    )

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
        18,
        30,
    )
    assert bookings[0]["title"] == (
        "Mechas - Yanko"
    )
    assert "Service: Mechas" in bookings[0]["description"]
    assert "Phone: +34600123123" in bookings[0]["description"]
    assert bookings[0]["metadata"]["service_id"] == (
        "highlights"
    )
    assert bookings[0]["metadata"]["service_name"] == (
        "Mechas"
    )
    assert bookings[0]["metadata"]["duration_minutes"] == 120