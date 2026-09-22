from chatbot.capabilities.capability_manager import (
    CapabilityManager,
)
from chatbot.capabilities.lead_capture import (
    LeadCaptureCapability,
)
from chatbot.conversation import (
    ConversationContext,
    ConversationOrchestrator,
)


def build_lead_capture_conversation():
    manager = CapabilityManager()
    manager.register(LeadCaptureCapability())

    return (
        ConversationOrchestrator(manager),
        ConversationContext(
            session_id="lead-capture-test",
        ),
    )


def test_lead_capture_collects_contact_and_requests_transfer():
    orchestrator, context = (
        build_lead_capture_conversation()
    )

    start_response = orchestrator.process(
        context=context,
        message="Quiero hablar con una persona",
    )

    name_response = orchestrator.process(
        context=context,
        message="Yanko",
    )

    phone_response = orchestrator.process(
        context=context,
        message="600123123",
    )

    final_response = orchestrator.process(
        context=context,
        message=(
            "Necesito información para un proyecto "
            "de automatización."
        ),
    )

    assert start_response.text == (
        "Para que una persona pueda ayudarte mejor, "
        "¿cómo te llamas?"
    )
    assert name_response.text == (
        "Gracias, Yanko. ¿Cuál es tu número de teléfono?"
    )
    assert phone_response.text == (
        "Perfecto. Cuéntame brevemente qué necesitas."
    )
    assert final_response.text == (
        "Gracias. He enviado tus datos al equipo para "
        "que una persona continúe la conversación contigo."
    )

    assert final_response.metadata["capability"] == (
        "lead_capture"
    )
    assert final_response.metadata["lead_captured"] is True
    assert (
        final_response.metadata["human_transfer_requested"]
        is True
    )
    assert context.active_capability is None
    assert context.pending_actions == [
        {
            "type": "lead_capture",
            "status": "captured",
            "name": "Yanko",
            "phone": "+34600123123",
            "reason": (
                "Necesito información para un proyecto "
                "de automatización."
            ),
        },
        {
            "type": "human_transfer",
            "status": "pending",
            "message": (
                "Necesito información para un proyecto "
                "de automatización."
            ),
        },
    ]


def test_lead_capture_rejects_invalid_phone_number():
    orchestrator, context = (
        build_lead_capture_conversation()
    )

    orchestrator.process(
        context=context,
        message="Quiero hablar con una persona",
    )
    orchestrator.process(
        context=context,
        message="Yanko",
    )

    response = orchestrator.process(
        context=context,
        message="no tengo teléfono",
    )

    assert response.text == (
        "No parece un número de teléfono válido. "
        "Inténtalo de nuevo, incluyendo el prefijo si lo necesitas."
    )
    assert response.metadata["lead_capture_step"] == "phone"
    assert context.active_capability == "lead_capture"
    assert context.get_variable("lead_capture") == {
        "step": "phone",
        "name": "Yanko",
    }


def test_lead_capture_can_be_cancelled_without_pending_actions():
    orchestrator, context = (
        build_lead_capture_conversation()
    )

    orchestrator.process(
        context=context,
        message="Quiero hablar con una persona",
    )

    response = orchestrator.process(
        context=context,
        message="cancelar",
    )

    assert response.text == (
        "De acuerdo. He cancelado la solicitud de atención."
    )
    assert response.metadata["capability"] == "lead_capture"
    assert response.metadata["lead_capture_cancelled"] is True
    assert context.active_capability is None
    assert context.get_variable("lead_capture") is None
    assert context.pending_actions == []


def test_lead_capture_acknowledges_positive_reply_after_completion():
    orchestrator, context = (
        build_lead_capture_conversation()
    )

    orchestrator.process(
        context=context,
        message="Quiero hablar con una persona",
    )
    orchestrator.process(
        context=context,
        message="Yanko",
    )
    orchestrator.process(
        context=context,
        message="600123123",
    )
    orchestrator.process(
        context=context,
        message="Necesito información sobre automatización.",
    )

    response = orchestrator.process(
        context=context,
        message="Genial",
    )

    assert response.text == (
        "Me alegra que todo haya sido de tu agrado. "
        "El equipo revisará tu solicitud y se pondrá en "
        "contacto contigo lo antes posible."
    )
    assert response.metadata["capability"] == "lead_capture"
    assert response.metadata["lead_capture_follow_up"] is True
