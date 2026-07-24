from __future__ import annotations

from chatbot.booking import BookingStep
from chatbot.capabilities.capability_manager import CapabilityManager
from chatbot.conversation.context import ConversationContext
from chatbot.language.detector import BaseLanguageDetector
from chatbot.language.models import Language
from chatbot.responses import Response


_FALLBACK_RESPONSES = {
    Language.ES: {
        "empty_message": (
            "No he recibido ningún mensaje. "
            "¿En qué puedo ayudarte?"
        ),
        "unhandled": (
            "Lo siento, no sé cómo gestionar esa solicitud."
        ),
    },
    Language.EN: {
        "empty_message": (
            "I did not receive a message. "
            "How can I help you?"
        ),
        "unhandled": (
            "I'm sorry, I don't know how to handle that request."
        ),
    },
}


class ConversationOrchestrator:
    """
    Coordinate conversation processing between context and capabilities.

    Responsibilities:

    - Detect and persist the conversation language.
    - Continue active conversational flows.
    - Delegate new requests to the appropriate capability.
    - Return a localized fallback response when no capability can handle
      the message.

    The orchestrator must not contain capability-specific business logic.
    """

    def __init__(
        self,
        capability_manager: CapabilityManager,
        language_detector: BaseLanguageDetector | None = None,
        default_language: Language = Language.ES,
    ) -> None:
        self.capability_manager = capability_manager
        self.language_detector = language_detector
        self.default_language = default_language

    def process(
        self,
        context: ConversationContext,
        message: str,
    ) -> Response:
        normalized_message = message.strip()

        self._ensure_conversation_language(
            context=context,
            message=normalized_message,
        )

        if not normalized_message:
            return self._fallback_response(
                context=context,
                response_key="empty_message",
            )

        active_response = self._continue_active_flow(
            context=context,
            message=normalized_message,
        )

        if active_response is not None:
            return active_response

        delegated_response = self._delegate_message(
            context=context,
            message=normalized_message,
        )

        if delegated_response is not None:
            return delegated_response

        return self._fallback_response(
            context=context,
            response_key="unhandled",
        )

    def _ensure_conversation_language(
        self,
        context: ConversationContext,
        message: str,
    ) -> None:
        """
        Detect the language once and persist it for the entire session.

        Short structured values such as dates, times and phone numbers are not
        used to select the conversation language.
        """

        if context.has_language:
            return

        if (
            self.language_detector is not None
            and self.language_detector.is_detectable(message)
        ):
            detected_language = self.language_detector.detect(
                text=message,
                default_language=self.default_language,
            )

            context.set_language(detected_language)
            return

        context.set_language(self.default_language)

    def _continue_active_flow(
        self,
        context: ConversationContext,
        message: str,
    ) -> Response | None:
        """
        Continue an active multi-step capability before checking new ones.
        """

        if not self._has_active_incomplete_flow(context):
            return None

        active_capability = self.capability_manager.get(
            context.active_capability
        )

        if active_capability is None:
            context.clear_active_capability()
            return None

        return active_capability.handle(
            context,
            message,
        )

    def _has_active_incomplete_flow(
        self,
        context: ConversationContext,
    ) -> bool:
        """
        Return whether the context contains an active unfinished flow.

        Booking is currently the first stateful capability. More stateful
        capabilities can later be introduced without changing the public
        process method.
        """

        return (
            context.active_capability == "booking"
            and context.booking is not None
            and context.booking.next_step
            is not BookingStep.COMPLETE
        )

    def _delegate_message(
        self,
        context: ConversationContext,
        message: str,
    ) -> Response | None:
        """
        Delegate a new request to the first capable registered capability.
        """

        for capability in self.capability_manager.all():
            if not capability.can_handle(
                context,
                message,
            ):
                continue

            context.set_active_capability(
                capability.name
            )

            return capability.handle(
                context,
                message,
            )

        return None

    def _fallback_response(
        self,
        context: ConversationContext,
        response_key: str,
    ) -> Response:
        """
        Build a fallback response in the conversation language.
        """

        language = (
            context.language
            or self.default_language
        )

        language_responses = _FALLBACK_RESPONSES.get(
            language,
            _FALLBACK_RESPONSES[self.default_language],
        )

        return Response(
            text=language_responses[response_key],
            metadata={
                "handled": False,
                "language": language.value,
            },
        )