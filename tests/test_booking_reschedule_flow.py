from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo
from unittest.mock import Mock

from chatbot.availability import (
    BookingRules,
    BusinessHours,
    TimeSlot,
)
from chatbot.booking import (
    Booking,
    BookingManagementAction,
    BookingManagementStep,
    BookingManagementState,
    BookingService,
    BookingSlotUnavailableError,
)
from chatbot.capabilities.booking import BookingCapability
from chatbot.conversation.context import ConversationContext
from chatbot.language import Language


def test_existing_booking_reschedule_requests_phone() -> None:
    booking_service = Mock(
        spec=BookingService
    )

    capability = BookingCapability(
        booking_service=booking_service,
    )

    context = ConversationContext(
        session_id="reschedule-existing-booking",
    )
    context.set_active_capability(
        "booking",
    )

    response = capability.handle(
        context=context,
        message="Quiero cambiar mi cita",
    )

    assert context.booking is None
    assert context.booking_management is not None
    assert (
        context.booking_management.action
        is BookingManagementAction.RESCHEDULE
    )
    assert (
        context.booking_management.next_step
        is BookingManagementStep.PHONE
    )

    assert response.text == (
        "Para cambiar tu cita, indícame el número "
        "de teléfono que usaste al reservar."
    )
    assert response.metadata[
        "booking_management_step"
    ] == "phone"


def test_existing_booking_reschedule_requests_phone_in_english(
) -> None:
    booking_service = Mock(
        spec=BookingService
    )

    capability = BookingCapability(
        booking_service=booking_service,
    )

    context = ConversationContext(
        session_id="reschedule-existing-booking-en",
        language=Language.EN,
    )
    context.set_active_capability(
        "booking",
    )

    response = capability.handle(
        context=context,
        message="I want to reschedule my appointment",
    )

    assert context.booking_management is not None
    assert (
        context.booking_management.action
        is BookingManagementAction.RESCHEDULE
    )
    assert response.text == (
        "To reschedule your appointment, please provide "
        "the phone number you used when booking."
    )


def test_existing_booking_reschedule_offers_available_dates(
) -> None:
    booking = Booking(
        name="Yanko",
        phone="+34600123123",
        date="30/08/2026",
        time="16:30",
        service_id="highlights",
        service_name="Mechas",
        duration_minutes=120,
        calendar_booking_id="calendar-event-123",
    )

    booking_service = Mock(
        spec=BookingService
    )
    booking_service.find_active_bookings_by_phone.return_value = (
        booking,
    )
    booking_service.get_available_dates.return_value = (
        date(
            2026,
            9,
            2,
        ),
        date(
            2026,
            9,
            3,
        ),
    )

    business_hours = BusinessHours.standard_week(
        start=time(
            9,
            0,
        ),
        end=time(
            20,
            0,
        ),
        timezone_name="Europe/Madrid",
    )

    capability = BookingCapability(
        booking_service=booking_service,
        business_hours=business_hours,
        booking_rules=BookingRules.hourly(),
    )

    context = ConversationContext(
        session_id="reschedule-available-dates",
    )
    context.set_active_capability(
        "booking",
    )

    capability.handle(
        context=context,
        message="Quiero cambiar mi cita",
    )

    response = capability.handle(
        context=context,
        message="600123123",
    )

    booking_service.find_active_bookings_by_phone.assert_called_once_with(
        "+34600123123"
    )
    booking_service.get_available_dates.assert_called_once()

    availability_call = (
        booking_service.get_available_dates.call_args
    )
    effective_rules = availability_call.kwargs[
        "rules"
    ]

    assert effective_rules.appointment_duration == timedelta(
        minutes=120
    )

    assert context.booking is None
    assert context.booking_management is not None
    assert (
        context.booking_management.selected_booking
        is booking
    )
    assert context.booking_management.available_dates == (
        "02/09/2026",
        "03/09/2026",
    )
    assert (
        context.booking_management.next_step
        is BookingManagementStep.DATE
    )

    assert "02/09/2026" in response.text
    assert "03/09/2026" in response.text
    assert "nueva fecha" in response.text.lower()
    assert response.metadata[
        "booking_management_step"
    ] == "date"

def test_existing_booking_reschedule_selects_one_of_multiple_bookings(
) -> None:
    first_booking = Booking(
        name="Yanko",
        phone="+34600123123",
        date="30/08/2026",
        time="16:30",
        service_name="Mechas",
        duration_minutes=120,
        calendar_booking_id="calendar-event-1",
    )
    second_booking = Booking(
        name="Yanko",
        phone="+34600123123",
        date="02/09/2026",
        time="10:00",
        service_name="Corte de hombre",
        duration_minutes=30,
        calendar_booking_id="calendar-event-2",
    )

    booking_service = Mock(
        spec=BookingService
    )
    booking_service.find_active_bookings_by_phone.return_value = (
        first_booking,
        second_booking,
    )
    booking_service.get_available_dates.return_value = (
        date(
            2026,
            9,
            4,
        ),
        date(
            2026,
            9,
            5,
        ),
    )

    business_hours = BusinessHours.standard_week(
        start=time(
            9,
            0,
        ),
        end=time(
            20,
            0,
        ),
        timezone_name="Europe/Madrid",
    )

    capability = BookingCapability(
        booking_service=booking_service,
        business_hours=business_hours,
        booking_rules=BookingRules.hourly(),
    )

    context = ConversationContext(
        session_id="reschedule-multiple-bookings",
    )
    context.set_active_capability(
        "booking",
    )

    capability.handle(
        context=context,
        message="Quiero cambiar mi cita",
    )

    selection_response = capability.handle(
        context=context,
        message="600123123",
    )

    assert context.booking_management is not None
    assert (
        context.booking_management.next_step
        is BookingManagementStep.SELECTION
    )
    assert "1." in selection_response.text
    assert "2." in selection_response.text

    response = capability.handle(
        context=context,
        message="2",
    )

    assert (
        context.booking_management.selected_booking
        is second_booking
    )
    assert context.booking_management.available_dates == (
        "04/09/2026",
        "05/09/2026",
    )
    assert (
        context.booking_management.next_step
        is BookingManagementStep.DATE
    )

    availability_call = (
        booking_service.get_available_dates.call_args
    )
    effective_rules = availability_call.kwargs[
        "rules"
    ]

    assert effective_rules.appointment_duration == timedelta(
        minutes=30
    )
    assert "04/09/2026" in response.text
    assert "05/09/2026" in response.text
    assert response.metadata[
        "booking_management_step"
    ] == "date"


def test_existing_booking_reschedule_offers_available_times(
) -> None:
    booking = Booking(
        name="Yanko",
        phone="+34600123123",
        date="30/08/2026",
        time="16:30",
        service_name="Mechas",
        duration_minutes=120,
        calendar_booking_id="calendar-event-123",
    )

    booking_service = Mock(
        spec=BookingService
    )
    booking_service.find_active_bookings_by_phone.return_value = (
        booking,
    )
    booking_service.get_available_dates.return_value = (
        date(
            2026,
            9,
            2,
        ),
    )

    timezone = ZoneInfo(
        "Europe/Madrid"
    )
    first_start = datetime(
        2026,
        9,
        2,
        10,
        0,
        tzinfo=timezone,
    )
    second_start = datetime(
        2026,
        9,
        2,
        12,
        30,
        tzinfo=timezone,
    )

    booking_service.get_available_slots_for_date.return_value = (
        TimeSlot(
            start=first_start,
            end=first_start + timedelta(
                minutes=120,
            ),
            occupied_start=first_start,
            occupied_end=first_start + timedelta(
                minutes=120,
            ),
        ),
        TimeSlot(
            start=second_start,
            end=second_start + timedelta(
                minutes=120,
            ),
            occupied_start=second_start,
            occupied_end=second_start + timedelta(
                minutes=120,
            ),
        ),
    )

    business_hours = BusinessHours.standard_week(
        start=time(
            9,
            0,
        ),
        end=time(
            20,
            0,
        ),
        timezone_name="Europe/Madrid",
    )

    capability = BookingCapability(
        booking_service=booking_service,
        business_hours=business_hours,
        booking_rules=BookingRules.hourly(),
    )

    context = ConversationContext(
        session_id="reschedule-available-times",
    )
    context.set_active_capability(
        "booking",
    )

    capability.handle(
        context=context,
        message="Quiero cambiar mi cita",
    )
    capability.handle(
        context=context,
        message="600123123",
    )

    response = capability.handle(
        context=context,
        message="02/09/2026",
    )

    assert context.booking_management is not None
    assert context.booking_management.new_date == (
        "02/09/2026"
    )
    assert context.booking_management.available_times == (
        "10:00",
        "12:30",
    )
    assert (
        context.booking_management.next_step
        is BookingManagementStep.TIME
    )

    availability_call = (
        booking_service
        .get_available_slots_for_date
        .call_args
    )
    effective_rules = availability_call.kwargs[
        "rules"
    ]

    assert effective_rules.appointment_duration == timedelta(
        minutes=120
    )
    assert "10:00" in response.text
    assert "12:30" in response.text
    assert "nueva hora" in response.text.lower()
    assert response.metadata[
        "booking_management_step"
    ] == "time"


def test_existing_booking_reschedule_builds_confirmation(
) -> None:
    booking = Booking(
        name="Yanko",
        phone="+34600123123",
        date="30/08/2026",
        time="16:30",
        service_name="Mechas",
        duration_minutes=120,
        calendar_booking_id="calendar-event-123",
    )

    management = BookingManagementState(
        action=BookingManagementAction.RESCHEDULE,
        phone="+34600123123",
        matching_bookings=(
            booking,
        ),
        selected_booking=booking,
        new_date="02/09/2026",
        available_dates=(
            "02/09/2026",
        ),
        available_times=(
            "10:00",
            "12:30",
        ),
    )

    capability = BookingCapability(
        booking_service=Mock(
            spec=BookingService
        ),
    )

    context = ConversationContext(
        session_id="reschedule-confirmation",
        booking_management=management,
    )
    context.set_active_capability(
        "booking",
    )

    response = capability.handle(
        context=context,
        message="12:30",
    )

    assert context.booking_management is management
    assert management.new_time == "12:30"
    assert (
        management.next_step
        is BookingManagementStep.CONFIRMATION
    )

    assert "Mechas" in response.text
    assert "30/08/2026" in response.text
    assert "16:30" in response.text
    assert "02/09/2026" in response.text
    assert "12:30" in response.text
    assert "confirmar" in response.text.lower()
    assert response.metadata[
        "booking_management_step"
    ] == "confirmation"

def test_existing_booking_reschedule_confirms_change(
) -> None:
    booking = Booking(
        name="Yanko",
        phone="+34600123123",
        date="30/08/2026",
        time="16:30",
        service_name="Mechas",
        duration_minutes=120,
        calendar_booking_id="calendar-event-123",
    )
    updated_booking = Booking(
        name="Yanko",
        phone="+34600123123",
        date="02/09/2026",
        time="12:30",
        service_name="Mechas",
        duration_minutes=120,
        calendar_booking_id="calendar-event-123",
    )

    booking_service = Mock(
        spec=BookingService
    )
    booking_service.reschedule_booking.return_value = (
        updated_booking
    )

    management = BookingManagementState(
        action=BookingManagementAction.RESCHEDULE,
        phone="+34600123123",
        matching_bookings=(
            booking,
        ),
        selected_booking=booking,
        new_date="02/09/2026",
        new_time="12:30",
        available_dates=(
            "02/09/2026",
        ),
        available_times=(
            "12:30",
        ),
    )

    capability = BookingCapability(
        booking_service=booking_service,
    )

    context = ConversationContext(
        session_id="confirm-reschedule",
        booking_management=management,
    )
    context.set_active_capability(
        "booking",
    )

    response = capability.handle(
        context=context,
        message="sí",
    )

    booking_service.reschedule_booking.assert_called_once_with(
        booking,
        date="02/09/2026",
        time="12:30",
    )

    assert context.booking is None
    assert context.booking_management is None
    assert context.active_capability is None

    assert "Mechas" in response.text
    assert "02/09/2026" in response.text
    assert "12:30" in response.text
    assert "cambiado correctamente" in response.text.lower()
    assert response.metadata[
        "booking_management_step"
    ] == "complete"
    assert response.metadata[
        "booking_rescheduled"
    ] is True


def test_existing_booking_reschedule_can_be_rejected(
) -> None:
    booking = Booking(
        name="Yanko",
        phone="+34600123123",
        date="30/08/2026",
        time="16:30",
        service_name="Mechas",
        duration_minutes=120,
        calendar_booking_id="calendar-event-123",
    )

    booking_service = Mock(
        spec=BookingService
    )

    management = BookingManagementState(
        action=BookingManagementAction.RESCHEDULE,
        phone="+34600123123",
        matching_bookings=(
            booking,
        ),
        selected_booking=booking,
        new_date="02/09/2026",
        new_time="12:30",
        available_dates=(
            "02/09/2026",
        ),
        available_times=(
            "12:30",
        ),
    )

    capability = BookingCapability(
        booking_service=booking_service,
    )

    context = ConversationContext(
        session_id="reject-reschedule",
        booking_management=management,
    )
    context.set_active_capability(
        "booking",
    )

    response = capability.handle(
        context=context,
        message="no",
    )

    booking_service.reschedule_booking.assert_not_called()

    assert context.booking_management is None
    assert context.active_capability is None
    assert "ningún cambio" in response.text.lower()
    assert response.metadata[
        "booking_rescheduled"
    ] is False
    assert response.metadata[
        "booking_conflict"
    ] is False


def test_existing_booking_reschedule_handles_unavailable_slot(
) -> None:
    booking = Booking(
        name="Yanko",
        phone="+34600123123",
        date="30/08/2026",
        time="16:30",
        service_name="Mechas",
        duration_minutes=120,
        calendar_booking_id="calendar-event-123",
    )

    booking_service = Mock(
        spec=BookingService
    )
    booking_service.reschedule_booking.side_effect = (
        BookingSlotUnavailableError()
    )

    management = BookingManagementState(
        action=BookingManagementAction.RESCHEDULE,
        phone="+34600123123",
        matching_bookings=(
            booking,
        ),
        selected_booking=booking,
        new_date="02/09/2026",
        new_time="12:30",
        available_dates=(
            "02/09/2026",
        ),
        available_times=(
            "12:30",
        ),
    )

    capability = BookingCapability(
        booking_service=booking_service,
    )

    context = ConversationContext(
        session_id="reschedule-slot-conflict",
        booking_management=management,
    )
    context.set_active_capability(
        "booking",
    )

    response = capability.handle(
        context=context,
        message="sí",
    )

    booking_service.reschedule_booking.assert_called_once_with(
        booking,
        date="02/09/2026",
        time="12:30",
    )

    assert context.booking_management is None
    assert context.active_capability is None
    assert "ya no está disponible" in response.text.lower()
    assert response.metadata[
        "booking_rescheduled"
    ] is False
    assert response.metadata[
        "booking_conflict"
    ] is True