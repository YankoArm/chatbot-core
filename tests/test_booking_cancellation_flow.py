from unittest.mock import Mock

from chatbot.booking import (
    Booking,
    BookingAlreadyCancelledError,
    BookingManagementAction,
    BookingManagementStep,
    BookingService,
    BookingState,
    BookingStatus,
    InMemoryBookingRepository,
)
from chatbot.capabilities.booking import BookingCapability
from chatbot.calendar import CalendarService
from chatbot.language import Language
from chatbot.conversation.context import ConversationContext


def test_existing_booking_cancellation_requests_phone() -> None:
    booking_service = Mock(
        spec=BookingService
    )

    capability = BookingCapability(
        booking_service=booking_service,
    )

    context = ConversationContext(
        session_id="cancel-existing-booking",
    )
    context.set_active_capability(
        "booking",
    )

    response = capability.handle(
        context=context,
        message="Quiero cancelar mi cita",
    )

    assert context.booking is None
    assert context.booking_management is not None
    assert (
        context.booking_management.action
        is BookingManagementAction.CANCEL
    )
    assert (
        context.booking_management.next_step
        is BookingManagementStep.PHONE
    )

    assert response.text == (
        "Para localizar tu cita, indícame el número "
        "de teléfono que usaste al reservar."
    )
    assert response.metadata["capability"] == "booking"
    assert response.metadata["booking_management_step"] == (
        "phone"
    )


def test_cancelling_new_booking_does_not_start_existing_management(
) -> None:
    capability = BookingCapability()

    context = ConversationContext(
        session_id="cancel-new-booking",
        booking=BookingState(),
    )
    context.set_active_capability(
        "booking",
    )

    response = capability.handle(
        context=context,
        message="cancelar",
    )

    assert context.booking is None
    assert context.booking_management is None
    assert response.text == (
        "La solicitud de reserva ha sido cancelada. "
        "Puedes empezar otra cuando quieras."
    )

def test_existing_booking_cancellation_reports_no_active_bookings(
) -> None:
    booking_service = Mock(
        spec=BookingService
    )
    booking_service.find_active_bookings_by_phone.return_value = ()

    capability = BookingCapability(
        booking_service=booking_service,
    )

    context = ConversationContext(
        session_id="cancel-booking-not-found",
    )
    context.set_active_capability(
        "booking",
    )

    capability.handle(
        context=context,
        message="Quiero cancelar mi cita",
    )

    response = capability.handle(
        context=context,
        message="600123123",
    )

    booking_service.find_active_bookings_by_phone.assert_called_once_with(
        "+34600123123"
    )

    assert context.booking is None
    assert context.booking_management is not None
    assert context.booking_management.phone is None
    assert context.booking_management.matching_bookings == ()
    assert (
        context.booking_management.next_step
        is BookingManagementStep.PHONE
    )

    assert response.text == (
        "No he encontrado ninguna cita activa asociada "
        "a ese teléfono. Comprueba el número e inténtalo "
        "de nuevo o escribe «cancelar» para salir."
    )


def test_existing_booking_cancellation_selects_single_booking(
) -> None:
    booking = Booking(
        name="Yanko",
        phone="+34600123123",
        date="30/08/2026",
        time="16:30",
        service_name="Mechas",
        calendar_booking_id="calendar-event-123",
    )

    booking_service = Mock(
        spec=BookingService
    )
    booking_service.find_active_bookings_by_phone.return_value = (
        booking,
    )

    capability = BookingCapability(
        booking_service=booking_service,
    )

    context = ConversationContext(
        session_id="cancel-single-booking",
    )
    context.set_active_capability(
        "booking",
    )

    capability.handle(
        context=context,
        message="Quiero cancelar mi cita",
    )

    response = capability.handle(
        context=context,
        message="+34 600 123 123",
    )

    assert context.booking_management is not None
    assert context.booking_management.phone == (
        "+34600123123"
    )
    assert context.booking_management.matching_bookings == (
        booking,
    )
    assert context.booking_management.selected_booking is booking
    assert (
        context.booking_management.next_step
        is BookingManagementStep.CONFIRMATION
    )

    assert response.text == (
        "He encontrado esta cita:\n\n"
        "Servicio: Mechas\n"
        "Fecha: 30/08/2026\n"
        "Hora: 16:30\n\n"
        "¿Quieres cancelarla? Responde «sí» para "
        "confirmar o «no» para conservarla."
    )
    assert response.metadata[
        "booking_management_step"
    ] == "confirmation"

def test_existing_booking_cancellation_lists_multiple_bookings(
) -> None:
    first_booking = Booking(
        name="Yanko",
        phone="+34600123123",
        date="30/08/2026",
        time="16:30",
        service_name="Mechas",
        calendar_booking_id="calendar-event-1",
    )
    second_booking = Booking(
        name="Yanko",
        phone="+34600123123",
        date="02/09/2026",
        time="10:00",
        service_name="Corte de hombre",
        calendar_booking_id="calendar-event-2",
    )

    booking_service = Mock(
        spec=BookingService
    )
    booking_service.find_active_bookings_by_phone.return_value = (
        first_booking,
        second_booking,
    )

    capability = BookingCapability(
        booking_service=booking_service,
    )

    context = ConversationContext(
        session_id="cancel-multiple-bookings",
    )
    context.set_active_capability(
        "booking",
    )

    capability.handle(
        context=context,
        message="Quiero cancelar mi cita",
    )

    response = capability.handle(
        context=context,
        message="600123123",
    )

    assert context.booking_management is not None
    assert context.booking_management.selected_booking is None
    assert (
        context.booking_management.next_step
        is BookingManagementStep.SELECTION
    )

    assert response.text == (
        "He encontrado varias citas activas:\n\n"
        "1. Mechas — 30/08/2026 a las 16:30\n"
        "2. Corte de hombre — 02/09/2026 a las 10:00\n\n"
        "Escribe el número de la cita que quieres cancelar."
    )
    assert response.metadata[
        "booking_management_step"
    ] == "selection"


def test_existing_booking_cancellation_selects_booking_by_number(
) -> None:
    first_booking = Booking(
        name="Yanko",
        phone="+34600123123",
        date="30/08/2026",
        time="16:30",
        service_name="Mechas",
        calendar_booking_id="calendar-event-1",
    )
    second_booking = Booking(
        name="Yanko",
        phone="+34600123123",
        date="02/09/2026",
        time="10:00",
        service_name="Corte de hombre",
        calendar_booking_id="calendar-event-2",
    )

    booking_service = Mock(
        spec=BookingService
    )
    booking_service.find_active_bookings_by_phone.return_value = (
        first_booking,
        second_booking,
    )

    capability = BookingCapability(
        booking_service=booking_service,
    )

    context = ConversationContext(
        session_id="select-booking-to-cancel",
    )
    context.set_active_capability(
        "booking",
    )

    capability.handle(
        context=context,
        message="Quiero cancelar mi cita",
    )
    capability.handle(
        context=context,
        message="600123123",
    )

    response = capability.handle(
        context=context,
        message="2",
    )

    assert context.booking_management is not None
    assert (
        context.booking_management.selected_booking
        is second_booking
    )
    assert (
        context.booking_management.next_step
        is BookingManagementStep.CONFIRMATION
    )

    assert "Servicio: Corte de hombre" in response.text
    assert "Fecha: 02/09/2026" in response.text
    assert "Hora: 10:00" in response.text
    assert response.metadata[
        "booking_management_step"
    ] == "confirmation"


def test_existing_booking_cancellation_rejects_invalid_selection(
) -> None:
    bookings = (
        Booking(
            name="Yanko",
            phone="+34600123123",
            date="30/08/2026",
            time="16:30",
            calendar_booking_id="calendar-event-1",
        ),
        Booking(
            name="Yanko",
            phone="+34600123123",
            date="02/09/2026",
            time="10:00",
            calendar_booking_id="calendar-event-2",
        ),
    )

    booking_service = Mock(
        spec=BookingService
    )
    booking_service.find_active_bookings_by_phone.return_value = (
        bookings
    )

    capability = BookingCapability(
        booking_service=booking_service,
    )

    context = ConversationContext(
        session_id="invalid-booking-selection",
    )
    context.set_active_capability(
        "booking",
    )

    capability.handle(
        context=context,
        message="Quiero cancelar mi cita",
    )
    capability.handle(
        context=context,
        message="600123123",
    )

    response = capability.handle(
        context=context,
        message="3",
    )

    assert context.booking_management is not None
    assert context.booking_management.selected_booking is None
    assert (
        context.booking_management.next_step
        is BookingManagementStep.SELECTION
    )
    assert response.text == (
        "Esa opción no es válida. Escribe un número "
        "entre 1 y 2."
    )

def test_existing_booking_cancellation_confirms_cancellation(
) -> None:
    booking = Booking(
        name="Yanko",
        phone="+34600123123",
        date="30/08/2026",
        time="16:30",
        service_name="Mechas",
        calendar_booking_id="calendar-event-123",
    )
    cancelled_booking = Booking(
        name="Yanko",
        phone="+34600123123",
        date="30/08/2026",
        time="16:30",
        service_name="Mechas",
        calendar_booking_id="calendar-event-123",
        status=BookingStatus.CANCELLED,
    )

    booking_service = Mock(
        spec=BookingService
    )
    booking_service.find_active_bookings_by_phone.return_value = (
        booking,
    )
    booking_service.cancel_booking.return_value = (
        cancelled_booking
    )

    capability = BookingCapability(
        booking_service=booking_service,
    )

    context = ConversationContext(
        session_id="confirm-existing-cancellation",
    )
    context.set_active_capability(
        "booking",
    )

    capability.handle(
        context=context,
        message="Quiero cancelar mi cita",
    )
    capability.handle(
        context=context,
        message="600123123",
    )

    response = capability.handle(
        context=context,
        message="sí",
    )

    booking_service.cancel_booking.assert_called_once_with(
        booking
    )

    assert context.booking is None
    assert context.booking_management is None
    assert context.active_capability is None

    assert response.text == (
        "Tu cita ha sido cancelada correctamente.\n\n"
        "Servicio: Mechas\n"
        "Fecha: 30/08/2026\n"
        "Hora: 16:30\n\n"
        "Si necesitas otra cita, puedes reservarla "
        "cuando quieras."
    )
    assert response.metadata[
        "booking_management_step"
    ] == "complete"
    assert response.metadata[
        "booking_cancelled"
    ] is True


def test_existing_booking_cancellation_can_be_rejected(
) -> None:
    booking = Booking(
        name="Yanko",
        phone="+34600123123",
        date="30/08/2026",
        time="16:30",
        service_name="Mechas",
        calendar_booking_id="calendar-event-123",
    )

    booking_service = Mock(
        spec=BookingService
    )
    booking_service.find_active_bookings_by_phone.return_value = (
        booking,
    )

    capability = BookingCapability(
        booking_service=booking_service,
    )

    context = ConversationContext(
        session_id="reject-existing-cancellation",
    )
    context.set_active_capability(
        "booking",
    )

    capability.handle(
        context=context,
        message="Quiero cancelar mi cita",
    )
    capability.handle(
        context=context,
        message="600123123",
    )

    response = capability.handle(
        context=context,
        message="no",
    )

    booking_service.cancel_booking.assert_not_called()

    assert context.booking_management is None
    assert context.active_capability is None

    assert response.text == (
        "De acuerdo. Tu cita se mantiene sin cambios."
    )
    assert response.metadata[
        "booking_cancelled"
    ] is False

def test_existing_booking_management_can_be_cancelled_from_phone_step(
) -> None:
    booking_service = Mock(
        spec=BookingService
    )

    capability = BookingCapability(
        booking_service=booking_service,
    )

    context = ConversationContext(
        session_id="exit-management-from-phone",
    )
    context.set_active_capability(
        "booking",
    )

    capability.handle(
        context=context,
        message="Quiero cancelar mi cita",
    )

    response = capability.handle(
        context=context,
        message="cancelar",
    )

    booking_service.find_active_bookings_by_phone.assert_not_called()
    booking_service.cancel_booking.assert_not_called()

    assert context.booking is None
    assert context.booking_management is None
    assert context.active_capability is None
    assert response.text == (
        "La gestión de tu cita ha finalizado sin realizar cambios."
    )
    assert response.metadata[
        "booking_cancelled"
    ] is False


def test_existing_booking_cancellation_repeats_unknown_confirmation(
) -> None:
    booking = Booking(
        name="Yanko",
        phone="+34600123123",
        date="30/08/2026",
        time="16:30",
        service_name="Mechas",
        calendar_booking_id="calendar-event-123",
    )

    booking_service = Mock(
        spec=BookingService
    )
    booking_service.find_active_bookings_by_phone.return_value = (
        booking,
    )

    capability = BookingCapability(
        booking_service=booking_service,
    )

    context = ConversationContext(
        session_id="unknown-cancellation-confirmation",
    )
    context.set_active_capability(
        "booking",
    )

    capability.handle(
        context=context,
        message="Quiero cancelar mi cita",
    )
    capability.handle(
        context=context,
        message="600123123",
    )

    response = capability.handle(
        context=context,
        message="quizá",
    )

    booking_service.cancel_booking.assert_not_called()

    assert context.booking_management is not None
    assert (
        context.booking_management.next_step
        is BookingManagementStep.CONFIRMATION
    )
    assert response.text == (
        "No he entendido la respuesta. Escribe «sí» "
        "para cancelar la cita o «no» para conservarla."
    )

def test_existing_booking_cancellation_works_in_english(
) -> None:
    booking = Booking(
        name="Yanko",
        phone="+34600123123",
        date="30/08/2026",
        time="16:30",
        service_name="Highlights",
        calendar_booking_id="calendar-event-123",
    )
    cancelled_booking = Booking(
        name="Yanko",
        phone="+34600123123",
        date="30/08/2026",
        time="16:30",
        service_name="Highlights",
        calendar_booking_id="calendar-event-123",
        status=BookingStatus.CANCELLED,
    )

    booking_service = Mock(
        spec=BookingService
    )
    booking_service.find_active_bookings_by_phone.return_value = (
        booking,
    )
    booking_service.cancel_booking.return_value = (
        cancelled_booking
    )

    capability = BookingCapability(
        booking_service=booking_service,
    )

    context = ConversationContext(
        session_id="cancel-booking-english",
        language=Language.EN,
    )
    context.set_active_capability(
        "booking",
    )

    first_response = capability.handle(
        context=context,
        message="Cancel my appointment",
    )

    assert first_response.text == (
        "To find your appointment, please provide the "
        "phone number you used when booking."
    )

    confirmation_response = capability.handle(
        context=context,
        message="+34 600 123 123",
    )

    assert confirmation_response.text == (
        "I found this appointment:\n\n"
        "Service: Highlights\n"
        "Date: 30/08/2026\n"
        "Time: 16:30\n\n"
        "Would you like to cancel it? Reply “yes” to "
        "confirm or “no” to keep it."
    )

    completed_response = capability.handle(
        context=context,
        message="yes",
    )

    booking_service.cancel_booking.assert_called_once_with(
        booking
    )
    assert context.booking_management is None
    assert context.active_capability is None
    assert completed_response.text == (
        "Your appointment has been cancelled successfully.\n\n"
        "Service: Highlights\n"
        "Date: 30/08/2026\n"
        "Time: 16:30\n\n"
        "If you need another appointment, you can book "
        "one whenever you want."
    )


def test_existing_booking_cancellation_handles_already_cancelled_conflict(
) -> None:
    booking = Booking(
        name="Yanko",
        phone="+34600123123",
        date="30/08/2026",
        time="16:30",
        service_name="Mechas",
        calendar_booking_id="calendar-event-123",
    )

    booking_service = Mock(
        spec=BookingService
    )
    booking_service.find_active_bookings_by_phone.return_value = (
        booking,
    )
    booking_service.cancel_booking.side_effect = (
        BookingAlreadyCancelledError()
    )

    capability = BookingCapability(
        booking_service=booking_service,
    )

    context = ConversationContext(
        session_id="already-cancelled-conflict",
    )
    context.set_active_capability(
        "booking",
    )

    capability.handle(
        context=context,
        message="Quiero cancelar mi cita",
    )
    capability.handle(
        context=context,
        message="600123123",
    )

    response = capability.handle(
        context=context,
        message="sí",
    )

    assert context.booking_management is None
    assert context.active_capability is None
    assert response.text == (
        "Esa cita ya no está activa. Es posible que se haya "
        "cancelado desde otro canal."
    )
    assert response.metadata[
        "booking_cancelled"
    ] is False
    assert response.metadata[
        "booking_conflict"
    ] is True

def test_existing_booking_cancellation_updates_repository_and_calendar(
) -> None:
    repository = InMemoryBookingRepository()
    calendar_service = Mock(
        spec=CalendarService
    )

    booking = Booking(
        name="Yanko",
        phone="+34600123123",
        date="30/08/2026",
        time="16:30",
        service_name="Mechas",
        calendar_booking_id="calendar-event-123",
    )

    repository.save(
        booking
    )

    booking_service = BookingService(
        repository=repository,
        calendar_service=calendar_service,
    )

    capability = BookingCapability(
        booking_service=booking_service,
    )

    context = ConversationContext(
        session_id="integrated-existing-cancellation",
    )
    context.set_active_capability(
        "booking",
    )

    capability.handle(
        context=context,
        message="Quiero cancelar mi cita",
    )
    capability.handle(
        context=context,
        message="600123123",
    )

    response = capability.handle(
        context=context,
        message="sí",
    )

    calendar_service.cancel_booking.assert_called_once_with(
        "calendar-event-123"
    )

    stored_bookings = repository.find_by_phone(
        "+34600123123"
    )

    assert len(stored_bookings) == 1
    assert stored_bookings[0].status is (
        BookingStatus.CANCELLED
    )
    assert stored_bookings[0].calendar_booking_id == (
        "calendar-event-123"
    )

    assert booking_service.find_active_bookings_by_phone(
        "+34600123123"
    ) == ()

    assert context.booking_management is None
    assert response.metadata["booking_cancelled"] is True