from chatbot.booking import BookingState, BookingStep
from chatbot.capabilities.booking import BookingCapability
from chatbot.conversation.context import ConversationContext


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
        "Encantado, Yanko. ¿Cuál es tu número de teléfono?"
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
        message="Mañana",
    )

    assert context.booking.date == "Mañana"
    assert context.booking.next_step is BookingStep.TIME
    assert response.text == "¿A qué hora quieres la cita?"

def test_booking_capability_completes_booking() -> None:
    capability = BookingCapability()
    context = ConversationContext(session_id="user_1")

    context.booking = BookingState(
        name="Yanko",
        phone="600123123",
        date="Mañana",
    )
    context.set_active_capability("booking")

    response = capability.handle(
        context=context,
        message="17:00",
    )

    assert context.booking.time == "17:00"
    assert context.booking.is_complete is True
    assert response.text == (
        "Perfecto, Yanko. He registrado tu solicitud para Mañana a las 17:00."
    )

def test_booking_capability_does_not_advance_with_invalid_phone():
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
        "¿Puedes escribirlo de nuevo?"
    )