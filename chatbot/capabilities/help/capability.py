from __future__ import annotations

import re
import unicodedata
from typing import Any

from chatbot.capabilities.base_capability import BaseCapability
from chatbot.language import Language
from chatbot.responses import Response


_HELP_MESSAGES = {
    Language.ES: {
        "booking": (
            "Estás realizando una reserva. Responde a la "
            "pregunta actual para continuar. También puedes "
            "escribir «cancelar» o «hablar con una persona»."
        ),
        "general": (
            "Puedo ayudarte a reservar una cita, consultar "
            "servicios y precios, ver horarios y ubicación, "
            "o hablar con una persona."
        ),
    },
    Language.EN: {
        "booking": (
            "You are making a booking. Reply to the current "
            "question to continue. You can also write “cancel” "
            "or “speak to a person”."
        ),
        "general": (
            "I can help you book an appointment, check services "
            "and prices, view opening hours and location, or "
            "speak to a person."
        ),
    },
}


class HelpCapability(BaseCapability):
    """
    Provide contextual help without discarding an active flow.
    """

    name = "help"
    version = "1.0"
    dependencies: list[str] = []
    interrupts_active_flow = True
    preserves_active_flow = True

    def can_handle(
        self,
        context: Any,
        message: str,
    ) -> bool:
        normalized = self._normalize_text(
            message
        )

        return normalized in {
            "ayuda",
            "necesito ayuda",
            "que puedo hacer",
            "help",
            "i need help",
            "what can i do",
        }

    def handle(
        self,
        context: Any,
        message: str,
    ) -> Response:
        language = self._get_language(context)
        message_type = (
            "booking"
            if getattr(context, "booking", None) is not None
            else "general"
        )

        return Response(
            text=_HELP_MESSAGES[language][message_type],
            metadata={
                "capability": self.name,
                "handled": True,
                "language": language.value,
                "active_flow_preserved": True,
            },
        )

    @staticmethod
    def _get_language(
        context: Any,
    ) -> Language:
        language = getattr(
            context,
            "language",
            None,
        )

        if language in _HELP_MESSAGES:
            return language

        return Language.ES

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