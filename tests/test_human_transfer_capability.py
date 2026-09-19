from types import SimpleNamespace

from chatbot.capabilities.human_transfer import (
    HumanTransferCapability,
)
from chatbot.conversation import ConversationContext
from chatbot.language import Language


def build_context(
    *,
    language: Language = Language.ES,
    pending_actions: list | None = None,
) -> ConversationContext:
    context = ConversationContext(
        session_id="human-transfer-test",
    )
    context.set_language(language)

    if pending_actions is not None:
        context.pending_actions = pending_actions

    return context


def test_human_transfer_capability_has_expected_name():
    capability = HumanTransferCapability()

    assert capability.name == "human_transfer"


def test_human_transfer_handles_spanish_request():
    capability = HumanTransferCapability()
    context = build_context()

    assert capability.can_handle(
        context,
        "Quiero hablar con una persona",
    )


def test_human_transfer_handles_english_request():
    capability = HumanTransferCapability()
    context = build_context(
        language=Language.EN,
    )

    assert capability.can_handle(
        context,
        "I want to speak to an agent",
    )


def test_human_transfer_does_not_handle_unrelated_message():
    capability = HumanTransferCapability()
    context = build_context()

    assert not capability.can_handle(
        context,
        "Quiero reservar para mañana",
    )


def test_human_transfer_requests_reason_before_registering_action():
    capability = HumanTransferCapability()
    context = build_context()

    response = capability.handle(
        context,
        "Necesito hablar con alguien",
    )

    assert response.text == (
        "Claro. Cuéntame brevemente qué necesitas y se lo "
        "trasladaré al equipo."
    )
    assert response.metadata["capability"] == (
        "human_transfer"
    )
    assert response.metadata["human_transfer_step"] == (
        "reason"
    )
    assert context.pending_actions == []
    assert capability.has_active_flow(context) is True


def test_human_transfer_registers_reason_as_pending_action():
    capability = HumanTransferCapability()
    pending_actions = []
    context = build_context(
        pending_actions=pending_actions,
    )

    capability.handle(
        context,
        "Quiero hablar con una persona",
    )
    response = capability.handle(
        context,
        "Quiero asesoramiento para mi cabello.",
    )

    assert response.metadata["human_transfer_requested"] is True
    assert response.metadata["transfer_registered"] is True
    assert pending_actions == [
        {
            "type": "human_transfer",
            "status": "pending",
            "message": (
                "Quiero asesoramiento para mi cabello."
            ),
        }
    ]
    assert capability.has_active_flow(context) is False


def test_human_transfer_can_be_cancelled_before_registering_action():
    capability = HumanTransferCapability()
    context = build_context()

    capability.handle(
        context,
        "Quiero hablar con una persona",
    )
    response = capability.handle(
        context,
        "cancelar",
    )

    assert response.metadata["human_transfer_cancelled"] is True
    assert context.pending_actions == []
    assert capability.has_active_flow(context) is False


def test_human_transfer_handles_missing_pending_actions():
    capability = HumanTransferCapability()

    context = SimpleNamespace(
        language=Language.ES,
    )

    response = capability.handle(
        context,
        "Quiero hablar con alguien",
    )

    assert response.metadata["human_transfer_step"] == (
        "reason"
    )


def test_human_transfer_uses_custom_knowledge_response():
    class CustomKnowledgeService:
        def get_section(
            self,
            section: str,
            default=None,
        ):
            knowledge = {
                "human_transfer": {
                    "response": {
                        "es": (
                            "Avisaremos al equipo para que te atienda."
                        ),
                        "en": (
                            "We will notify the team to assist you."
                        ),
                    },
                },
            }

            return knowledge.get(
                section,
                default,
            )

    context = build_context(
        language=Language.EN,
    )
    context.knowledge_service = (
        CustomKnowledgeService()
    )

    capability = HumanTransferCapability()

    capability.handle(
        context,
        "I need human support",
    )
    response = capability.handle(
        context,
        "I need help choosing a service.",
    )

    assert response.text == (
        "We will notify the team to assist you."
    )
    assert response.metadata["transfer_registered"] is True
