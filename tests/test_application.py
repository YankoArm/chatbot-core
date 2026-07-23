from chatbot.application import Bootstrap
from chatbot.capabilities.booking.capability import BookingCapability
from chatbot.capabilities.capability_manager import CapabilityManager
from chatbot.conversation import ConversationOrchestrator


def build_test_app():
    manager = CapabilityManager()
    manager.register(BookingCapability())

    orchestrator = ConversationOrchestrator(manager)

    return Bootstrap().build(
        instance="test_instance",
        orchestrator=orchestrator,
        capability_manager=manager,
    )


def test_application_chat_returns_response():
    app = build_test_app()

    response = app.chat(
        session_id="user_1",
        message="Quiero reservar una cita",
    )

    assert response.text == (
        "Perfecto. Vamos a reservar una cita. ¿Cómo te llamas?"
    )
    assert response.metadata["capability"] == "booking"


def test_application_preserves_session_context():
    app = build_test_app()

    app.chat(
        session_id="user_1",
        message="Quiero reservar una cita",
    )

    context = app.conversation_store.get("user_1")

    assert context.active_capability == "booking"


def test_application_info_returns_runtime_data():
    app = build_test_app()

    info = app.info()

    assert info["instance"] == "test_instance"
    assert info["capabilities"] == ["booking"]
    assert info["active_sessions"] == 0


def test_application_reset_session_clears_context():
    app = build_test_app()

    app.chat(
        session_id="user_1",
        message="Quiero reservar una cita",
    )

    app.reset_session("user_1")

    context = app.conversation_store.get("user_1")

    assert context.active_capability is None