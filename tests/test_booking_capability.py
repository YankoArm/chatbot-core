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