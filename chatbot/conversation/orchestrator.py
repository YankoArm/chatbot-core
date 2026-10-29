from __future__ import annotations

import unicodedata

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
            "No he entendido del todo lo que necesitas. "
            "Puedes explicármelo de otra forma o escribir «ayuda» "
            "para ver en qué puedo ayudarte. Si lo prefieres, "
            "también puedes pedir hablar con una persona."
        ),
    },
    Language.EN: {
        "empty_message": (
            "I did not receive a message. "
            "How can I help you?"
        ),
        "unhandled": (
            "I did not quite understand what you need. "
            "You can explain it another way or write “help” "
            "to see what I can do. If you prefer, you can "
            "also ask to speak with a person."
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

        pending_switch_response = (
            self._handle_pending_flow_switch(
                context=context,
                message=normalized_message,
            )
        )

        if pending_switch_response is not None:
            return pending_switch_response

        flow_switch_response = (
            self._offer_flow_switch(
                context=context,
                message=normalized_message,
            )
        )

        if flow_switch_response is not None:
            return flow_switch_response

        interruption_response = (
            self._delegate_interrupting_message(
                context=context,
                message=normalized_message,
            )
        )

        if interruption_response is not None:
            return interruption_response

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

    def _handle_pending_flow_switch(
        self,
        context: ConversationContext,
        message: str,
    ) -> Response | None:
        pending = context.get_variable(
            "_pending_flow_switch"
        )

        if not isinstance(pending, dict):
            return None

        normalized = self._normalize_control_text(
            message
        )

        confirmations = {
            "si",
            "yes",
            "vale",
            "ok",
            "okay",
            "de acuerdo",
            "confirmar",
        }

        rejections = {
            "no",
            "cancelar",
            "seguir",
            "continuar",
            "cancel",
            "continue",
        }

        language = (
            context.language
            or self.default_language
        )

        if normalized in confirmations:
            target_name = pending.get("target")
            original_message = pending.get(
                "message",
                message,
            )

            context.remove_variable(
                "_pending_flow_switch"
            )

            if pending.get("source") == "human_transfer":
                context.remove_variable(
                    "human_transfer"
                )

            context.clear_active_capability()

            target = self.capability_manager.get(
                target_name
            )

            if target is None:
                return self._fallback_response(
                    context=context,
                    response_key="unhandled",
                )

            context.set_active_capability(
                target.name
            )

            return target.handle(
                context,
                original_message,
            )

        if normalized in rejections:
            context.remove_variable(
                "_pending_flow_switch"
            )

            if language is Language.EN:
                text = (
                    "Okay. We will keep the request to speak "
                    "with a person open. Briefly tell me what "
                    "you need."
                )
            else:
                text = (
                    "De acuerdo. Mantengo abierta la solicitud "
                    "para hablar con una persona. Cu\u00e9ntame "
                    "brevemente qu\u00e9 necesitas."
                )

            return Response(
                text=text,
                metadata={
                    "handled": True,
                    "flow_switch_rejected": True,
                    "active_capability": (
                        context.active_capability
                    ),
                },
            )

        if language is Language.EN:
            text = (
                "Please answer Yes to start the booking "
                "or No to continue with human assistance."
            )
        else:
            text = (
                "Responde S\u00ed para comenzar la reserva "
                "o No para continuar con la solicitud de "
                "atenci\u00f3n humana."
            )

        return Response(
            text=text,
            metadata={
                "handled": True,
                "flow_switch_confirmation": True,
            },
        )

    def _offer_flow_switch(
        self,
        context: ConversationContext,
        message: str,
    ) -> Response | None:
        if context.active_capability != "human_transfer":
            return None

        booking = self.capability_manager.get(
            "booking"
        )

        if booking is None:
            return None

        if not self._is_explicit_booking_request(
            message
        ):
            return None

        if not booking.can_handle(
            context,
            message,
        ):
            return None

        context.set_variable(
            "_pending_flow_switch",
            {
                "source": "human_transfer",
                "target": "booking",
                "message": message,
            },
        )

        language = (
            context.language
            or self.default_language
        )

        if language is Language.EN:
            prompt = (
                "It looks like you want to make a booking. "
                "Do you want to leave the human assistance "
                "request and start a booking? Reply Yes or No."
            )
        else:
            prompt = (
                "Parece que quieres reservar una cita. "
                "\u00bfQuieres dejar la solicitud para hablar "
                "con una persona y comenzar una reserva? "
                "Responde S\u00ed o No."
            )

        return Response(
            text=prompt,
            metadata={
                "handled": True,
                "flow_switch_confirmation": True,
                "flow_switch_from": "human_transfer",
                "flow_switch_to": "booking",
            },
        )

    @classmethod
    def _is_explicit_booking_request(
        cls,
        message: str,
    ) -> bool:
        normalized = cls._normalize_control_text(
            message
        )

        explicit_patterns = (
            "quiero reservar",
            "me gustaria reservar",
            "necesito reservar",
            "reservar una cita",
            "reservar cita",
            "pedir una cita",
            "pedir cita",
            "solicitar una cita",
            "agendar una cita",
            "concertar una cita",
            "quiero una cita",
            "quiero cita",
            "hacer una reserva",
            "quiero hacer una reserva",
            "i want to book",
            "i would like to book",
            "book an appointment",
            "make an appointment",
            "schedule an appointment",
            "make a booking",
        )

        return any(
            pattern in normalized
            for pattern in explicit_patterns
        )

    @staticmethod
    def _normalize_control_text(
        message: str,
    ) -> str:
        normalized = unicodedata.normalize(
            "NFKD",
            message,
        )

        normalized = "".join(
            character
            for character in normalized
            if not unicodedata.combining(character)
        )

        return " ".join(
            normalized.casefold().split()
        )

    def _delegate_interrupting_message(
        self,
        context: ConversationContext,
        message: str,
    ) -> Response | None:
        """
        Allow explicitly interrupting capabilities to take control of
        an unfinished conversational flow.
        """

        if not self._has_active_incomplete_flow(
            context
        ):
            return None

        for capability in self.capability_manager.all():
            if not capability.interrupts_active_flow:
                continue

            if (
                capability.name == "faq"
                and context.active_capability != "human_transfer"
            ):
                continue

            if not capability.can_handle(
                context,
                message,
            ):
                continue

            if not capability.preserves_active_flow:
                context.set_active_capability(
                    capability.name
                )

            return capability.handle(
                context,
                message,
            )

        return None

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
        Return whether the active capability owns an unfinished flow.
        """

        active_capability_name = (
            context.active_capability
        )

        if active_capability_name is None:
            return False

        active_capability = (
            self.capability_manager.get(
                active_capability_name
            )
        )

        if active_capability is None:
            return False

        return active_capability.has_active_flow(
            context
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
