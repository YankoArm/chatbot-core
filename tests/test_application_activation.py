from __future__ import annotations

from dataclasses import dataclass

from chatbot.activation import (
    ActivationManager,
    AlwaysActivePolicy,
    ExactPhrasePolicy,
)
from chatbot.application.application import FlowForgeApplication
from chatbot.conversation import ConversationStore
from chatbot.responses import Response


PROMPT_MESSAGE = (
    "Este número también se utiliza de forma personal. "
    "Para iniciar el asistente, escribe únicamente TAROT."
)


@dataclass
class FakeCapability:
    name: str


class FakeCapabilityManager:
    def all(self) -> list[FakeCapability]:
        return [FakeCapability(name="fake")]


class SpyOrchestrator:
    def __init__(self) -> None:
        self.calls: list[tuple[object, str]] = []

    def process(self, context, message: str) -> Response:
        self.calls.append((context, message))

        return Response(
            text=f"processed:{message}",
        )


def build_application(
    activation_manager: ActivationManager | None = None,
) -> tuple[FlowForgeApplication, SpyOrchestrator]:

    orchestrator = SpyOrchestrator()

    application = FlowForgeApplication(
        instance={"id": "test"},
        orchestrator=orchestrator,
        capability_manager=FakeCapabilityManager(),
        conversation_store=ConversationStore(),
        activation_manager=activation_manager,
    )

    return application, orchestrator


def test_chat_reaches_orchestrator_without_activation_manager() -> None:
    application, orchestrator = build_application()

    response = application.chat(
        session_id="session-1",
        message="Hola",
    )

    assert response.text == "processed:Hola"
    assert len(orchestrator.calls) == 1


def test_always_active_policy_allows_message() -> None:
    manager = ActivationManager(
        policy=AlwaysActivePolicy(),
    )

    application, orchestrator = build_application(manager)

    response = application.chat(
        session_id="session-1",
        message="Hola",
    )

    assert response.text == "processed:Hola"
    assert len(orchestrator.calls) == 1


def test_exact_phrase_policy_returns_prompt_before_orchestrator() -> None:
    manager = ActivationManager(
        policy=ExactPhrasePolicy(
            phrases=["Tarot"],
            prompt_message=PROMPT_MESSAGE,
            activated_message="Asistente activado.",
        ),
    )

    application, orchestrator = build_application(manager)

    response = application.chat(
        session_id="session-1",
        message="Hola",
    )

    assert response.text == PROMPT_MESSAGE
    assert orchestrator.calls == []


def test_exact_phrase_activates_and_reaches_orchestrator() -> None:
    manager = ActivationManager(
        policy=ExactPhrasePolicy(
            phrases=["Tarot"],
            prompt_message=PROMPT_MESSAGE,
            activated_message="Asistente activado.",
        ),
    )

    application, orchestrator = build_application(manager)

    response = application.chat(
        session_id="session-1",
        message="Tarot",
    )

    assert response.text == "Asistente activado."
    assert len(orchestrator.calls) == 0


def test_active_session_allows_following_messages() -> None:
    manager = ActivationManager(
        policy=ExactPhrasePolicy(
            phrases=["Tarot"],
            prompt_message=PROMPT_MESSAGE,
            activated_message="Asistente activado.",
        ),
    )

    application, orchestrator = build_application(manager)

    application.chat(
        session_id="session-1",
        message="Tarot",
    )

    response = application.chat(
        session_id="session-1",
        message="Quiero una lectura",
    )

    assert response.text == "processed:Quiero una lectura"
    assert len(orchestrator.calls) == 1


def test_activation_state_is_isolated_by_session() -> None:
    manager = ActivationManager(
        policy=ExactPhrasePolicy(
            phrases=["Tarot"],
            prompt_message=PROMPT_MESSAGE,
            activated_message="Asistente activado.",
        ),
    )

    application, orchestrator = build_application(manager)

    application.chat(
        session_id="session-1",
        message="Tarot",
    )

    response = application.chat(
        session_id="session-2",
        message="Hola",
    )

    assert response.text == PROMPT_MESSAGE
    assert len(orchestrator.calls) == 0


def test_reset_session_requires_activation_again() -> None:
    manager = ActivationManager(
        policy=ExactPhrasePolicy(
            phrases=["Tarot"],
            prompt_message=PROMPT_MESSAGE,
            activated_message="Asistente activado.",
        ),
    )

    application, orchestrator = build_application(manager)

    application.chat(
        session_id="session-1",
        message="Tarot",
    )

    application.reset_session("session-1")

    response = application.chat(
        session_id="session-1",
        message="Quiero una lectura",
    )

    assert response.text == PROMPT_MESSAGE
    assert len(orchestrator.calls) == 0