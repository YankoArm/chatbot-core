from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from chatbot.activation import ActivationManager
from chatbot.capabilities.capability_manager import CapabilityManager
from chatbot.conversation import (
    ConversationOrchestrator,
    ConversationStore,
)
from chatbot.instances import Instance
from chatbot.language import (
    BaseLanguageDetector,
    Language,
)
from chatbot.responses import Response


@dataclass(slots=True)
class FlowForgeApplication:
    """
    Runtime representation of a configured FlowForge instance.

    The application acts as the main entry point for every conversation
    channel. It obtains the session context, selects the conversation
    language, evaluates activation rules and delegates message processing
    to the conversation orchestrator.
    """

    instance: Instance
    orchestrator: ConversationOrchestrator
    capability_manager: CapabilityManager
    conversation_store: ConversationStore

    activation_manager: ActivationManager | None = None
    connector_manager: Any | None = None
    language_detector: BaseLanguageDetector | None = None

    def chat(
        self,
        session_id: str,
        message: str,
    ) -> Response:
        """
        Process a user message within a conversation session.

        The detected language is persisted in the conversation context and
        reused during the remainder of the session.
        """

        normalized_session_id = session_id.strip()

        if not normalized_session_id:
            raise ValueError(
                "Session ID cannot be empty."
            )

        normalized_message = message.strip()

        context = self.conversation_store.get(
            normalized_session_id
        )

        self._ensure_conversation_language(
            context=context,
            message=normalized_message,
        )

        activation_response = self._process_activation(
            context=context,
            message=normalized_message,
        )

        if activation_response is not None:
            return activation_response

        return self.orchestrator.process(
            context=context,
            message=normalized_message,
        )

    def reset_session(
        self,
        session_id: str,
    ) -> None:
        """
        Reset all transient data associated with a conversation session.
        """

        normalized_session_id = session_id.strip()

        if not normalized_session_id:
            raise ValueError(
                "Session ID cannot be empty."
            )

        self.conversation_store.reset(
            normalized_session_id
        )

    def reload(self) -> None:
        """
        Reload the configured application runtime.

        Dynamic runtime reloading is not implemented yet.
        """

        raise NotImplementedError(
            "Dynamic application reloading is not implemented."
        )

    def info(self) -> dict[str, Any]:
        """
        Return a serializable summary of the running application.
        """

        return {
            "instance": getattr(
                self.instance,
                "name",
                str(self.instance),
            ),
            "default_language": (
                self._get_default_language().value
            ),
            "language_detection": (
                self.language_detector is not None
            ),
            "capabilities": [
                capability.name
                for capability
                in self.capability_manager.all()
            ],
            "active_sessions": (
                self.conversation_store.count()
            ),
        }

    def _ensure_conversation_language(
        self,
        context: Any,
        message: str,
    ) -> None:
        """
        Detect and persist the language of a conversation.

        Language detection only runs when the context does not already have
        a language and the message contains enough alphabetic content.

        Structured values such as phone numbers, dates and times must not
        select or overwrite the language.
        """

        if context.language is not None:
            return

        if self.language_detector is None:
            context.set_language(
                self._get_default_language()
            )
            return

        if not self.language_detector.is_detectable(
            message
        ):
            return

        detected_language = self.language_detector.detect(
            text=message,
            default_language=self._get_default_language(),
        )

        context.set_language(
            detected_language
        )

    def _process_activation(
        self,
        context: Any,
        message: str,
    ) -> Response | None:
        """
        Evaluate activation rules before conversational delegation.

        Return an activation response when normal processing must stop.
        """

        if self.activation_manager is None:
            return None

        decision = self.activation_manager.handle(
            message=message,
            state=context.activation_state,
        )

        if decision.continue_processing:
            return None

        return decision.response

    def _get_default_language(self) -> Language:
        """
        Return the configured default language safely.

        Instance configurations may provide the language either as a
        Language enum member or as its serialized string value.
        """

        configured_language = getattr(
            self.instance,
            "default_language",
            Language.ES,
        )

        if isinstance(
            configured_language,
            Language,
        ):
            return configured_language

        try:
            return Language(
                str(configured_language).casefold()
            )
        except ValueError:
            return Language.ES