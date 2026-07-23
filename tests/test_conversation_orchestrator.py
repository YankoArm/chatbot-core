from chatbot.capabilities.booking.capability import BookingCapability
from chatbot.capabilities.capability_manager import CapabilityManager
from chatbot.conversation import ConversationContext, ConversationOrchestrator


def test_orchestrator_selects_matching_capability():
    manager = CapabilityManager()
    manager.register(BookingCapability())

    orchestrator = ConversationOrchestrator(manager)
    context = ConversationContext(session_id="test_session")

    response = orchestrator.process(
        context=context,
        message="Quiero reservar una cita",
    )

    assert response.text == (
        "Perfecto. Vamos a reservar una cita. ¿Cómo te llamas?"
    )
    assert response.metadata["capability"] == "booking"
    assert response.metadata["handled"] is True
    assert context.active_capability == "booking"


def test_orchestrator_returns_default_response_when_no_capability_matches():
    manager = CapabilityManager()
    manager.register(BookingCapability())

    orchestrator = ConversationOrchestrator(manager)
    context = ConversationContext(session_id="test_session")

    response = orchestrator.process(
        context=context,
        message="Hola, buenas tardes",
    )

    assert response.metadata["handled"] is False
    assert context.active_capability is None