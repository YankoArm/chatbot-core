from types import SimpleNamespace

from chatbot.capabilities.human_transfer import (
    HumanTransferCapability,
)
from chatbot.language import Language


def build_context(
    *,
    language: Language = Language.ES,
    pending_actions: list | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        language=language,
        pending_actions=(
            pending_actions
            if pending_actions is not None
            else []
        ),
    )


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


def test_human_transfer_returns_spanish_response():
    capability = HumanTransferCapability()
    context = build_context()

    response = capability.handle(
        context,
        "Necesito hablar con alguien",
    )

    assert response.metadata["capability"] == (
        "human_transfer"
    )
    assert response.metadata["handled"] is True
    assert response.metadata["language"] == "es"
    assert (
        response.metadata["human_transfer_requested"]
        is True
    )
    assert response.metadata["transfer_registered"] is True
    assert "persona" in response.text.lower()


def test_human_transfer_returns_english_response():
    capability = HumanTransferCapability()
    context = build_context(
        language=Language.EN,
    )

    response = capability.handle(
        context,
        "I need human support",
    )

    assert response.metadata["language"] == "en"
    assert response.metadata["transfer_registered"] is True
    assert "person" in response.text.lower()


def test_human_transfer_registers_pending_action():
    capability = HumanTransferCapability()
    pending_actions = []

    context = build_context(
        pending_actions=pending_actions,
    )

    capability.handle(
        context,
        "Quiero hablar con una persona",
    )

    assert pending_actions == [
        {
            "type": "human_transfer",
            "status": "pending",
            "message": "Quiero hablar con una persona",
        }
    ]


def test_human_transfer_handles_missing_pending_actions():
    capability = HumanTransferCapability()

    context = SimpleNamespace(
        language=Language.ES,
    )

    response = capability.handle(
        context,
        "Quiero hablar con alguien",
    )

    assert (
        response.metadata["human_transfer_requested"]
        is True
    )
    assert response.metadata["transfer_registered"] is False

def test_human_transfer_uses_custom_knowledge_response(
) -> None:
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

    response = capability.handle(
        context,
        "I need human support",
    )

    assert response.text == (
        "We will notify the team to assist you."
    )
    assert response.metadata[
        "transfer_registered"
    ] is True