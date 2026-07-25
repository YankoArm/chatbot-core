import pytest

from chatbot.booking import BookingState, BookingStep
from chatbot.capabilities.booking import BookingCapability
from chatbot.conversation.context import ConversationContext


class FakeBookingService:
    def __init__(self) -> None:
        self.received_state: BookingState | None = None

    def create_booking_from_state(
        self,
        state: BookingState,
    ) -> None:
        self.received_state = state

        state.confirm(
            booking_id="booking-123",
        )


def test_booking_capability_confirms_booking_through_service() -> None:
    booking_service = FakeBookingService()

    capability = BookingCapability(
        booking_service=booking_service,
    )

    context = ConversationContext(
        session_id="user_1",
    )

    context.booking = BookingState(
        name="Yanko",
        phone="600123123",
        date="28/07/2026",
        time="16:30",
    )

    context.set_active_capability(
        "booking",
    )

    response = capability.handle(
        context=context,
        message="sí",
    )

    assert booking_service.received_state is context.booking
    assert context.booking.confirmed is True
    assert context.booking.is_complete is True
    assert context.booking.booking_id == "booking-123"
    assert context.booking.next_step is BookingStep.COMPLETE

    assert response.metadata["handled"] is True
    assert response.metadata["booking_step"] == "complete"
    assert "Reserva confirmada correctamente" in response.text


def test_booking_capability_stores_name_and_requests_phone() -> None:
    capability = BookingCapability()
    context = ConversationContext(session_id="user_1")

    context.booking = BookingState()
    context.set_active_capability("booking")

    response = capability.handle(
        context=context,
        message="Yanko",
    )

    assert context.booking.name == "Yanko"
    assert context.booking.next_step is BookingStep.PHONE

    assert response.text == (
        "Encantado, Yanko. "
        "¿Cuál es tu número de teléfono?"
    )


def test_booking_capability_stores_phone_and_requests_date() -> None:
    capability = BookingCapability()
    context = ConversationContext(session_id="user_1")

    context.booking = BookingState(
        name="Yanko",
    )

    context.set_active_capability("booking")

    response = capability.handle(
        context=context,
        message="600123123",
    )

    assert context.booking.phone == "600123123"
    assert context.booking.next_step is BookingStep.DATE
    assert response.text == "¿Para qué día quieres la cita?"


def test_booking_capability_stores_date_and_requests_time() -> None:
    capability = BookingCapability()
    context = ConversationContext(session_id="user_1")

    context.booking = BookingState(
        name="Yanko",
        phone="600123123",
    )

    context.set_active_capability("booking")

    response = capability.handle(
        context=context,
        message="25/07/2026",
    )

    assert context.booking.date == "25/07/2026"
    assert context.booking.next_step is BookingStep.TIME
    assert response.text == "¿A qué hora quieres la cita?"


def test_booking_capability_moves_to_confirmation_after_time() -> None:
    capability = BookingCapability()
    context = ConversationContext(session_id="user_1")

    context.booking = BookingState(
        name="Yanko",
        phone="600123123",
        date="28/07/2026",
    )

    context.set_active_capability("booking")

    response = capability.handle(
        context=context,
        message="17:00",
    )

    assert context.booking.time == "17:00"
    assert context.booking.has_required_data is True
    assert context.booking.is_complete is False
    assert context.booking.next_step is BookingStep.CONFIRMATION

    assert "Estos son los datos de tu reserva" in response.text
    assert "Yanko" in response.text
    assert "600123123" in response.text
    assert "28/07/2026" in response.text
    assert "17:00" in response.text


def test_booking_capability_does_not_advance_with_invalid_phone() -> None:
    capability = BookingCapability()
    context = ConversationContext(session_id="user_1")

    context.booking = BookingState(
        name="Yanko",
    )

    context.set_active_capability("booking")

    response = capability.handle(
        context=context,
        message="abc",
    )

    assert context.booking.phone is None
    assert context.booking.next_step is BookingStep.PHONE

    assert response.text == (
        "El teléfono no parece válido. "
        "Escribe únicamente entre 7 y 15 dígitos."
    )


def test_booking_capability_does_not_advance_with_invalid_name() -> None:
    capability = BookingCapability()
    context = ConversationContext(session_id="user_1")

    context.booking = BookingState()

    response = capability.handle(
        context=context,
        message="1",
    )

    assert context.booking.name is None
    assert context.booking.next_step is BookingStep.NAME

    assert response.text == (
        "Ese nombre no parece válido. "
        "¿Puedes escribirlo de nuevo?"
    )


def test_booking_capability_does_not_advance_with_invalid_date() -> None:
    capability = BookingCapability()
    context = ConversationContext(session_id="user_1")

    context.booking = BookingState(
        name="Yanko",
        phone="600123123",
    )

    response = capability.handle(
        context=context,
        message="ahora",
    )

    assert context.booking.date is None
    assert context.booking.next_step is BookingStep.DATE

    assert response.text == (
        "La fecha no parece válida. "
        "Escríbela con el formato DD/MM/YYYY "
        "o pregúntame qué días hay disponibles."
    )


def test_booking_capability_does_not_advance_with_invalid_time() -> None:
    capability = BookingCapability()
    context = ConversationContext(session_id="user_1")

    context.booking = BookingState(
        name="Yanko",
        phone="600123123",
        date="25/07/2026",
    )

    response = capability.handle(
        context=context,
        message="ahora",
    )

    assert context.booking.time is None
    assert context.booking.next_step is BookingStep.TIME

    assert response.text == (
        "La hora no parece válida. "
        "Escríbela con el formato HH:MM."
    )


def test_booking_capability_returns_available_dates_without_advancing() -> None:
    capability = BookingCapability()
    context = ConversationContext(session_id="user_1")

    context.booking = BookingState(
        name="Yanko",
        phone="600123123",
    )

    context.set_active_capability("booking")

    response = capability.handle(
        context=context,
        message="¿Qué días hay disponibles?",
    )

    assert context.booking.date is None
    assert context.booking.next_step is BookingStep.DATE

    assert "Tengo disponibilidad" in response.text
    assert "¿Qué día prefieres?" in response.text


@pytest.mark.parametrize(
    "message",
    [
        "que dias hay",
        "¿Qué días hay?",
        "QUE DIAS HAY DISPONIBLES?",
        "que dias tienes?",
        "¿qué fechas tienes?",
        "hay huecos?",
    ],
)
def test_booking_capability_recognizes_availability_questions(
    message: str,
) -> None:
    capability = BookingCapability()
    context = ConversationContext(session_id="user_1")

    context.booking = BookingState(
        name="Yanko",
        phone="600123123",
    )

    context.set_active_capability("booking")

    response = capability.handle(
        context=context,
        message=message,
    )

    assert context.booking.date is None
    assert context.booking.next_step is BookingStep.DATE
    assert "Tengo disponibilidad" in response.text


def test_booking_capability_confirms_booking() -> None:
    capability = BookingCapability()
    context = ConversationContext(session_id="user_1")

    context.booking = BookingState(
        name="Yanko",
        phone="600123123",
        date="28/07/2026",
        time="17:00",
    )

    context.set_active_capability("booking")

    response = capability.handle(
        context=context,
        message="sí",
    )

    assert context.booking.confirmed is True
    assert context.booking.is_complete is True
    assert context.booking.next_step is BookingStep.COMPLETE

    assert "Reserva confirmada correctamente" in response.text


def test_booking_capability_cancels_booking() -> None:
    capability = BookingCapability()
    context = ConversationContext(session_id="user_1")

    context.booking = BookingState(
        name="Yanko",
        phone="600123123",
        date="28/07/2026",
        time="17:00",
    )

    context.set_active_capability("booking")

    response = capability.handle(
        context=context,
        message="no",
    )

    assert context.booking is None
    assert "cancelada" in response.text.lower()
    assert response.metadata["booking_step"] == "cancelled"


def test_booking_capability_keeps_confirmation_step_for_unknown_answer() -> None:
    capability = BookingCapability()
    context = ConversationContext(session_id="user_1")

    context.booking = BookingState(
        name="Yanko",
        phone="600123123",
        date="28/07/2026",
        time="17:00",
    )

    context.set_active_capability("booking")

    response = capability.handle(
        context=context,
        message="quizás",
    )

    assert context.booking.confirmed is False
    assert context.booking.next_step is BookingStep.CONFIRMATION
    assert "sí" in response.text.lower()
    assert "no" in response.text.lower()