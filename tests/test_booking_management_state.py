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

def test_reschedule_management_requests_new_date_after_selection(
) -> None:
    booking = make_booking()

    state = BookingManagementState(
        action=BookingManagementAction.RESCHEDULE,
        phone="+34600123123",
        matching_bookings=(
            booking,
        ),
        selected_booking=booking,
    )

    assert state.next_step is BookingManagementStep.DATE


def test_reschedule_management_requests_time_after_new_date(
) -> None:
    booking = make_booking()

    state = BookingManagementState(
        action=BookingManagementAction.RESCHEDULE,
        phone="+34600123123",
        matching_bookings=(
            booking,
        ),
        selected_booking=booking,
        new_date="02/09/2026",
        available_dates=(
            "02/09/2026",
            "03/09/2026",
        ),
    )

    assert state.next_step is BookingManagementStep.TIME


def test_reschedule_management_requests_confirmation_after_new_time(
) -> None:
    booking = make_booking()

    state = BookingManagementState(
        action=BookingManagementAction.RESCHEDULE,
        phone="+34600123123",
        matching_bookings=(
            booking,
        ),
        selected_booking=booking,
        new_date="02/09/2026",
        new_time="10:00",
        available_times=(
            "10:00",
            "10:30",
        ),
    )

    assert state.next_step is BookingManagementStep.CONFIRMATION


def test_reschedule_reset_clears_new_availability_selection(
) -> None:
    booking = make_booking()

    state = BookingManagementState(
        action=BookingManagementAction.RESCHEDULE,
        phone="+34600123123",
        matching_bookings=(
            booking,
        ),
        selected_booking=booking,
        new_date="02/09/2026",
        new_time="10:00",
        available_dates=(
            "02/09/2026",
        ),
        available_times=(
            "10:00",
            "10:30",
        ),
    )

    state.reset()

    assert state.action is (
        BookingManagementAction.RESCHEDULE
    )
    assert state.new_date is None
    assert state.new_time is None
    assert state.available_dates == ()
    assert state.available_times == ()
    assert state.next_step is BookingManagementStep.PHONE