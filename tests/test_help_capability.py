from chatbot.booking import BookingState
from chatbot.capabilities.help import HelpCapability
from chatbot.conversation.context import ConversationContext
from chatbot.language import Language


def test_help_capability_handles_spanish_help() -> None:
    capability = HelpCapability()
    context = ConversationContext(
        session_id="help-es",
    )

    assert capability.can_handle(
        context,
        "Ayuda",
    )


def test_help_capability_handles_english_help() -> None:
    capability = HelpCapability()
    context = ConversationContext(
        session_id="help-en",
        language=Language.EN,
    )

    assert capability.can_handle(
        context,
        "Help",
    )


def test_help_capability_returns_general_help() -> None:
    capability = HelpCapability()
    context = ConversationContext(
        session_id="help-general",
        language=Language.ES,
    )

    response = capability.handle(
        context,
        "ayuda",
    )

    assert "reservar una cita" in response.text
    assert response.metadata["capability"] == "help"
    assert response.metadata["active_flow_preserved"] is True


def test_help_capability_returns_booking_help() -> None:
    capability = HelpCapability()
    context = ConversationContext(
        session_id="help-booking",
        language=Language.ES,
        booking=BookingState(),
    )

    response = capability.handle(
        context,
        "ayuda",
    )

    assert "Estás realizando una reserva" in response.text
    assert "cancelar" in response.text
    assert "hablar con una persona" in response.text