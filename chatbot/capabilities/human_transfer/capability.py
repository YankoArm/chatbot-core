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

_RESPONSES = {
    Language.ES: (
        "De acuerdo. Voy a solicitar que una persona continúe "
        "la conversación contigo."
    ),
    Language.EN: (
        "Understood. I will request that a person continues "
        "the conversation with you."
    ),
}


class HumanTransferCapability(BaseCapability):
    """
    Handle requests to continue the conversation with a human.

    This capability does not perform the external transfer itself.
    It records a pending human-transfer action in the conversation context
    so that the application or channel connector can process it.
    """

    name = "human_transfer"
    version = "1.0"
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

    def handle(
        self,
        context: Any,
        message: str,
    ) -> Response:
        language = self._get_language(
            context
        )

        transfer_registered = self._register_transfer(
            context=context,
            message=message,
        )
        response_text = (
            self._get_configured_response(
                context=context,
                language=language,
            )
        )

        return Response(
            text=response_text,
            metadata={
                "capability": self.name,
                "handled": True,
                "language": language.value,
                "human_transfer_requested": True,
                "transfer_registered": transfer_registered,
            },
        )

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
            return _RESPONSES[
                language
            ]

        get_section = getattr(
            knowledge_service,
            "get_section",
            None,
        )

        if not callable(
            get_section
        ):
            return _RESPONSES[
                language
            ]

        try:
            transfer_settings = get_section(
                "human_transfer",
                {},
            )
        except FileNotFoundError:
            return _RESPONSES[
                language
            ]

        if not isinstance(
            transfer_settings,
            dict,
        ):
            return _RESPONSES[
                language
            ]

        responses = transfer_settings.get(
            "response",
            {},
        )

        if not isinstance(
            responses,
            dict,
        ):
            return _RESPONSES[
                language
            ]

        configured_response = responses.get(
            language.value
        )

        if (
            isinstance(
                configured_response,
                str,
            )
            and configured_response.strip()
        ):
            return configured_response.strip()

        return _RESPONSES[
            language
        ]
    def _register_transfer(
        self,
        context: Any,
        message: str,
    ) -> bool:
        """
        Register a pending human-transfer action in the context.

        Expected context attribute:

        context.pending_actions: list[dict]
        """

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
        """
        Return the selected conversation language.

        Spanish is used as a safe fallback when the context does not contain
        a supported language.
        """

        language = getattr(
            context,
            "language",
            None,
        )

        if language in _RESPONSES:
            return language

        return Language.ES

    @staticmethod
    def _normalize_text(
        message: str,
    ) -> str:
        """
        Normalize text for reliable transfer-request recognition.
        """

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