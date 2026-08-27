from chatbot.booking import (
    Booking,
    BookingManagementAction,
    BookingManagementState,
    BookingManagementStep,
)


def make_booking(
    *,
    date: str = "30/08/2026",
    time: str = "16:30",
) -> Booking:
    return Booking(
        name="Yanko",
        phone="+34600123123",
        date=date,
        time=time,
        calendar_booking_id=(
            f"calendar-{date}-{time}"
        ),
    )


def test_booking_management_starts_by_requesting_phone() -> None:
    state = BookingManagementState(
        action=BookingManagementAction.CANCEL,
    )

    assert state.next_step is BookingManagementStep.PHONE
    assert state.is_complete is False


def test_booking_management_requests_selection_for_multiple_bookings(
) -> None:
    first_booking = make_booking()
    second_booking = make_booking(
        date="31/08/2026",
        time="10:00",
    )

    state = BookingManagementState(
        action=BookingManagementAction.CANCEL,
        phone="+34600123123",
        matching_bookings=(
            first_booking,
            second_booking,
        ),
    )

    assert state.next_step is BookingManagementStep.SELECTION


def test_booking_management_requests_confirmation_after_selection(
) -> None:
    booking = make_booking()

    state = BookingManagementState(
        action=BookingManagementAction.CANCEL,
        phone="+34600123123",
        matching_bookings=(
            booking,
        ),
        selected_booking=booking,
    )

    assert state.next_step is BookingManagementStep.CONFIRMATION


def test_booking_management_can_be_completed() -> None:
    booking = make_booking()

    state = BookingManagementState(
        action=BookingManagementAction.CANCEL,
        phone="+34600123123",
        matching_bookings=(
            booking,
        ),
        selected_booking=booking,
    )

    state.complete()

    assert state.next_step is BookingManagementStep.COMPLETE
    assert state.is_complete is True


def test_booking_management_reset_preserves_action() -> None:
    booking = make_booking()

    state = BookingManagementState(
        action=BookingManagementAction.CANCEL,
        phone="+34600123123",
        matching_bookings=(
            booking,
        ),
        selected_booking=booking,
    )

    state.complete()
    state.reset()

    assert state.action is BookingManagementAction.CANCEL
    assert state.phone is None
    assert state.matching_bookings == ()
    assert state.selected_booking is None
    assert state.is_complete is False
    assert state.next_step is BookingManagementStep.PHONE