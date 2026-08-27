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


def test_orchestrator_continues_active_booking_flow():
    manager = CapabilityManager()
    manager.register(BookingCapability())

    orchestrator = ConversationOrchestrator(manager)
    context = ConversationContext(session_id="test_session")

    orchestrator.process(
        context=context,
        message="Quiero reservar una cita",
    )

    response = orchestrator.process(
        context=context,
        message="Yanko",
    )

    assert context.booking is not None
    assert context.booking.name == "Yanko"
    assert response.text == (
        "Encantado, Yanko. "
        "¿Cuál es tu número de teléfono? "
        "Puedes incluir el prefijo internacional, "
        "por ejemplo +34."
    )
    assert response.metadata["capability"] == "booking"
    assert response.metadata["handled"] is True

def test_orchestrator_does_not_duplicate_active_capability_history():
    manager = CapabilityManager()
    manager.register(BookingCapability())

    orchestrator = ConversationOrchestrator(manager)
    context = ConversationContext(session_id="test_session")

    orchestrator.process(
        context=context,
        message="Quiero reservar una cita",
    )

    assert context.active_capability == "booking"
    assert context.previous_capabilities == []

def test_orchestrator_continues_active_booking_management_flow(
) -> None:
    manager = CapabilityManager()
    manager.register(
        BookingCapability()
    )

    orchestrator = ConversationOrchestrator(
        manager
    )
    context = ConversationContext(
        session_id="active-booking-management"
    )

    start_response = orchestrator.process(
        context=context,
        message="Quiero cambiar mi cita",
    )

    assert start_response.metadata[
        "booking_management_step"
    ] == "phone"
    assert context.booking is None
    assert context.booking_management is not None
    assert context.active_capability == "booking"

    response = orchestrator.process(
        context=context,
        message="600123123",
    )

    assert response.metadata[
        "capability"
    ] == "booking"
    assert response.metadata[
        "booking_management_step"
    ] == "phone"
    assert response.metadata["handled"] is True
    assert "ninguna cita activa" in response.text.lower()
    assert context.booking_management is not None