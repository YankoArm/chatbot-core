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