from __future__ import annotations

import re
import unicodedata
from typing import Any

from chatbot.capabilities.base_capability import BaseCapability
from chatbot.language import Language
from chatbot.responses import Response


_GREETINGS = {
    Language.ES: {
        "hola",
        "buenas",
        "buenos dias",
        "buenas tardes",
        "buenas noches",
        "que tal",
    },
    Language.EN: {
        "hi",
        "hello",
        "hey",
        "good morning",
        "good afternoon",
        "good evening",
        "how are you",
    },
}

_RESPONSES = {
    Language.ES: "¡Hola! 👋 ¿En qué puedo ayudarte?",
    Language.EN: "Hello! 👋 How can I help you?",
}


class GreetingCapability(BaseCapability):
    """
    Handle common Spanish and English greetings.

    GreetingCapability is stateless. The conversation language is detected
    and persisted by FlowForgeApplication before this capability is invoked.
    """

    name = "greeting"
    version = "1.0"
    dependencies: list[str] = []

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

        greetings = {
            greeting
            for language_greetings in _GREETINGS.values()
            for greeting in language_greetings
        }

        return any(
            normalized_message == greeting
            or normalized_message.startswith(
                f"{greeting} "
            )
            for greeting in greetings
        )

    def handle(
        self,
        context: Any,
        message: str,
    ) -> Response:
        language = self._get_language(context)

        return Response(
            text=_RESPONSES[language],
            metadata={
                "capability": self.name,
                "handled": True,
                "language": language.value,
            },
        )

    @staticmethod
    def _get_language(
        context: Any,
    ) -> Language:
        """
        Return the selected conversation language.

        Spanish is used as a safe fallback when the context does not yet
        contain a supported language.
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
        Normalize user text for reliable greeting recognition.
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