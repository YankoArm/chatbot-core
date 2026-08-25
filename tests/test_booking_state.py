from chatbot.booking import (
    BookingState,
    BookingStep,
)


def test_booking_state_starts_empty() -> None:
    state = BookingState()

    assert state.name is None
    assert state.phone is None
    assert state.date is None
    assert state.time is None
    assert state.is_complete is False


def test_booking_state_starts_at_name_step() -> None:
    state = BookingState()

    assert state.next_step is BookingStep.NAME


def test_booking_state_advances_to_phone_step() -> None:
    state = BookingState(
        name="Yanko",
    )

    assert state.next_step is BookingStep.PHONE


def test_booking_state_advances_to_date_step() -> None:
    state = BookingState(
        name="Yanko",
        phone="600123123",
    )

    assert state.next_step is BookingStep.DATE


def test_booking_state_advances_to_time_step() -> None:
    state = BookingState(
        name="Yanko",
        phone="600123123",
        date="mañana",
    )

    assert state.next_step is BookingStep.TIME


def test_booking_state_is_not_complete_before_confirmation() -> None:
    state = BookingState(
        name="Yanko",
        phone="600123123",
        date="28/07/2026",
        time="17:00",
    )

    assert state.has_required_data is True
    assert state.is_complete is False
    assert state.next_step is BookingStep.CONFIRMATION

def test_booking_state_is_complete_after_confirmation() -> None:
    state = BookingState(
        name="Yanko",
        phone="600123123",
        date="28/07/2026",
        time="17:00",
    )

    state.confirm(
        booking_id="calendar-event-123",
    )

    assert state.confirmed is True
    assert state.booking_id == "calendar-event-123"
    assert state.is_complete is True
    assert state.next_step is BookingStep.COMPLETE

def test_booking_state_reset_clears_all_data() -> None:
    state = BookingState(
        name="Yanko",
        phone="600123123",
        date="mañana",
        time="17:00",
    )

    state.reset()

    assert state.name is None
    assert state.phone is None
    assert state.date is None
    assert state.time is None
    assert state.is_complete is False
    assert state.next_step is BookingStep.NAME

def test_booking_state_starts_without_available_dates() -> None:
    booking = BookingState()

    assert booking.available_dates == ()

def test_booking_state_starts_at_service_when_required() -> None:
    state = BookingState(
        requires_service_selection=True,
    )

    assert state.service_id is None
    assert state.service_name is None
    assert state.next_step is BookingStep.SERVICE
    assert state.has_required_data is False


def test_booking_state_advances_after_service_selection() -> None:
    state = BookingState(
        requires_service_selection=True,
        service_id="highlights",
        service_name="Mechas",
        service_duration_minutes=120,
        service_price_cents=6500,
        service_price_type="from",
        service_currency="EUR",
    )

    assert state.next_step is BookingStep.NAME


def test_booking_state_requires_selected_service_to_complete() -> None:
    state = BookingState(
        requires_service_selection=True,
        name="Yanko",
        phone="+34600123123",
        date="28/08/2026",
        time="17:00",
    )

    assert state.has_required_data is False

    state.service_id = "highlights"
    state.service_name = "Mechas"
    state.service_duration_minutes = 120
    state.service_price_cents = 6500
    state.service_price_type = "from"
    state.service_currency = "EUR"

    assert state.has_required_data is True


def test_booking_state_reset_clears_service_selection() -> None:
    state = BookingState(
        requires_service_selection=True,
        service_id="highlights",
        service_name="Mechas",
        service_duration_minutes=120,
        service_price_cents=6500,
        service_price_type="from",
        service_currency="EUR",
        name="Yanko",
    )

    state.reset()

    assert state.service_id is None
    assert state.service_name is None
    assert state.service_duration_minutes is None
    assert state.service_price_cents is None
    assert state.service_price_type is None
    assert state.service_currency is None
    assert state.next_step is BookingStep.SERVICE