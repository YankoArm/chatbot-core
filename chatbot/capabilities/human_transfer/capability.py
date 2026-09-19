from __future__ import annotations

import re
import unicodedata
from typing import Any

from chatbot.capabilities.base_capability import BaseCapability
from chatbot.language import Language
from chatbot.responses import Response


_TRANSFER_KEYWORDS = {
    Language.ES: {
        "hablar con una persona",
        "hablar con alguien",
        "hablar con un agente",
        "hablar con un humano",
        "atencion humana",
        "atencion personal",
        "contactar con alguien",
        "necesito ayuda",
        "quiero hablar con alguien",
        "quiero hablar con una persona",
        "operador",
        "agente",
        "humano",
    },
    Language.EN: {
        "speak to a person",
        "speak with a person",
        "speak to someone",
        "speak with someone",
        "speak to an agent",
        "speak with an agent",
        "speak to a human",
        "human support",
        "human assistance",
        "contact someone",
        "i need help",
        "operator",
        "agent",
        "human",
    },
}

_REASON_PROMPTS = {
    Language.ES: (
        "Claro. Cuéntame brevemente qué necesitas y se lo "
        "trasladaré al equipo."
    ),
    Language.EN: (
        "Of course. Briefly tell me what you need and I will "
        "pass it on to the team."
    ),
}

_RESPONSES = {
    Language.ES: (
        "Gracias. He enviado tu solicitud al equipo para que "
        "una persona continúe la conversación contigo."
    ),
    Language.EN: (
        "Thank you. I have sent your request to the team so "
        "that a person can continue the conversation with you."
    ),
}

_CANCELLATION_WORDS = {
    "cancelar",
    "salir",
    "no",
    "cancel",
    "exit",
    "stop",
}

_STATE_KEY = "human_transfer"


class HumanTransferCapability(BaseCapability):
    """
    Collect a short reason before requesting human attention.
    """

    name = "human_transfer"
    version = "1.1"
    dependencies: list[str] = []
    interrupts_active_flow = True

    def can_handle(
        self,
        context: Any,
        message: str,
    ) -> bool:
        normalized_message = self._normalize_text(
            message
        )

        if not normalized_message:
            return False

        keywords = {
            keyword
            for language_keywords in _TRANSFER_KEYWORDS.values()
            for keyword in language_keywords
        }

        return any(
            keyword in normalized_message
            for keyword in keywords
        )

    def has_active_flow(
        self,
        context: Any,
    ) -> bool:
        return isinstance(
            self._get_state(context),
            dict,
        )

    def handle(
        self,
        context: Any,
        message: str,
    ) -> Response:
        language = self._get_language(
            context
        )
        state = self._get_state(context)

        if not isinstance(state, dict):
            self._set_state(
                context,
                {"step": "reason"},
            )

            return self._response(
                language=language,
                text=_REASON_PROMPTS[language],
                step="reason",
            )

        reason = message.strip()

        if self._normalize_text(reason) in _CANCELLATION_WORDS:
            self._clear_state(context)
            self._clear_active_capability(context)

            return Response(
                text=(
                    "De acuerdo. He cancelado la solicitud "
                    "de atención."
                ),
                metadata={
                    "capability": self.name,
                    "handled": True,
                    "human_transfer_cancelled": True,
                },
            )

        transfer_registered = self._register_transfer(
            context=context,
            message=reason,
        )
        self._clear_state(context)
        self._clear_active_capability(context)

        return Response(
            text=self._get_configured_response(
                context=context,
                language=language,
            ),
            metadata={
                "capability": self.name,
                "handled": True,
                "language": language.value,
                "human_transfer_requested": True,
                "transfer_registered": transfer_registered,
            },
        )

    @staticmethod
    def _get_state(
        context: Any,
    ) -> Any:
        get_variable = getattr(
            context,
            "get_variable",
            None,
        )

        if not callable(get_variable):
            return None

        return get_variable(_STATE_KEY)

    @staticmethod
    def _set_state(
        context: Any,
        state: dict[str, str],
    ) -> None:
        set_variable = getattr(
            context,
            "set_variable",
            None,
        )

        if callable(set_variable):
            set_variable(_STATE_KEY, state)

    @staticmethod
    def _clear_state(
        context: Any,
    ) -> None:
        remove_variable = getattr(
            context,
            "remove_variable",
            None,
        )

        if callable(remove_variable):
            remove_variable(_STATE_KEY)

    @staticmethod
    def _clear_active_capability(
        context: Any,
    ) -> None:
        clear_active_capability = getattr(
            context,
            "clear_active_capability",
            None,
        )

        if callable(clear_active_capability):
            clear_active_capability()

    @staticmethod
    def _get_configured_response(
        *,
        context: Any,
        language: Language,
    ) -> str:
        knowledge_service = getattr(
            context,
            "knowledge_service",
            None,
        )

        if knowledge_service is None:
            return _RESPONSES[language]

        get_section = getattr(
            knowledge_service,
            "get_section",
            None,
        )

        if not callable(get_section):
            return _RESPONSES[language]

        try:
            transfer_settings = get_section(
                "human_transfer",
                {},
            )
        except FileNotFoundError:
            return _RESPONSES[language]

        if not isinstance(
            transfer_settings,
            dict,
        ):
            return _RESPONSES[language]

        responses = transfer_settings.get(
            "response",
            {},
        )

        if not isinstance(responses, dict):
            return _RESPONSES[language]

        configured_response = responses.get(
            language.value
        )

        if (
            isinstance(configured_response, str)
            and configured_response.strip()
        ):
            return configured_response.strip()

        return _RESPONSES[language]

    @staticmethod
    def _register_transfer(
        *,
        context: Any,
        message: str,
    ) -> bool:
        pending_actions = getattr(
            context,
            "pending_actions",
            None,
        )

        if not isinstance(pending_actions, list):
            return False

        pending_actions.append(
            {
                "type": "human_transfer",
                "status": "pending",
                "message": message,
            }
        )

        return True

    @staticmethod
    def _get_language(
        context: Any,
    ) -> Language:
        language = getattr(
            context,
            "language",
            None,
        )

        if language in _RESPONSES:
            return language

        return Language.ES

    @staticmethod
    def _response(
        *,
        language: Language,
        text: str,
        step: str,
    ) -> Response:
        return Response(
            text=text,
            metadata={
                "capability": "human_transfer",
                "handled": True,
                "language": language.value,
                "human_transfer_step": step,
            },
        )

    @staticmethod
    def _normalize_text(
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

        normalized = normalized.casefold()

        normalized = re.sub(
            r"[^a-z0-9\s]",
            " ",
            normalized,
        )

        return re.sub(
            r"\s+",
            " ",
            normalized,
        ).strip()
