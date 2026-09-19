from chatbot.capabilities.capability_manager import (
    CapabilityManager,
)
from chatbot.capabilities.human_transfer import (
    HumanTransferCapability,
)
from chatbot.conversation import (
    ConversationContext,
    ConversationOrchestrator,
)


def test_human_transfer_collects_reason_before_registering_request():
    capability_manager = CapabilityManager()
    capability_manager.register(
        HumanTransferCapability()
    )

    orchestrator = ConversationOrchestrator(
        capability_manager=capability_manager,
    )
    context = ConversationContext(
        session_id="human-transfer-reason",
    )

    start_response = orchestrator.process(
        context=context,
        message="Quiero hablar con una persona",
    )

    final_response = orchestrator.process(
        context=context,
        message=(
            "Tengo dudas sobre mi cabello y quiero que "
            "un especialista me asesore."
        ),
    )

    assert start_response.text == (
        "Claro. Cuéntame brevemente qué necesitas y se lo "
        "trasladaré al equipo."
    )
    assert context.active_capability is None

    assert final_response.text == (
        "Gracias. He enviado tu solicitud al equipo para que "
        "una persona continúe la conversación contigo."
    )
    assert final_response.metadata["capability"] == (
        "human_transfer"
    )
    assert final_response.metadata["human_transfer_requested"] is True
    assert context.pending_actions == [
        {
            "type": "human_transfer",
            "status": "pending",
            "message": (
                "Tengo dudas sobre mi cabello y quiero que "
                "un especialista me asesore."
            ),
        }
    ]
