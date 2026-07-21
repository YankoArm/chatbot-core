from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from chatbot.activation import ActivationManager
from chatbot.conversation import ConversationStore
from chatbot.language import (
    BaseLanguageDetector,
    Language,
)
from chatbot.responses import Response


@dataclass(slots=True)
class FlowForgeApplication:
    """
    Runtime representation of a configured FlowForge Instance.
    """

    instance: Any
    orchestrator: Any
    capability_manager: Any
    conversation_store: ConversationStore
    activation_manager: ActivationManager | None = None
    connector_manager: Any | None = None
    language_detector: BaseLanguageDetector | None = None

    def chat(
        self,
        session_id: str,
        message: str,
    ) -> Response:

        context = self.conversation_store.get(session_id)

        if (
            self.language_detector is not None
            and context.language is None
        ):
            default_language = getattr(
                self.instance,
                "default_language",
                Language.ES.value,
            )

            context.language = self.language_detector.detect(
                message,
                default_language=Language(default_language),
            )

        if self.activation_manager is not None:

            decision = self.activation_manager.handle(
                message=message,
                state=context.activation_state,
            )

            if not decision.continue_processing:
                return decision.response

        return self.orchestrator.process(
            context,
            message,
        )

    def reset_session(
        self,
        session_id: str,
    ) -> None:
        self.conversation_store.reset(session_id)

    def reload(self) -> None:
        raise NotImplementedError

    def info(self) -> dict:
        return {
            "instance": self.instance,
            "capabilities": [
                capability.name
                for capability in self.capability_manager.all()
            ],
            "active_sessions": self.conversation_store.count(),
        }