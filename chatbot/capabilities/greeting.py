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
        "holis",
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

_STRETCHED_HOLA_PATTERN = re.compile(
    r"^hol(?:a+|i+s+)$"
)

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

        if _STRETCHED_HOLA_PATTERN.fullmatch(
            normalized_message
        ):
            return True

        greetings = {
            greeting
            for language_greetings in _GREETINGS.values()
            for greeting in language_greetings
        }

        greeting_only_messages = greetings | {
            "hola chatbot",
            "hello there",
        }

        return (
            normalized_message
            in greeting_only_messages
        )
    def handle(
        self,
        context: Any,
        message: str,
    ) -> Response:
        language = self._get_language(
            context
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
            },
        )

    @staticmethod
    def _get_configured_response(
        *,
        context: Any,
        language: Language,
    ) -> str:
        default_response = _RESPONSES[
            language
        ]

        knowledge_service = getattr(
            context,
            "knowledge_service",
            None,
        )

        if knowledge_service is None:
            return default_response

        get_section = getattr(
            knowledge_service,
            "get_section",
            None,
        )

        if not callable(
            get_section
        ):
            return default_response

        try:
            greetings = get_section(
                "greetings",
                {},
            )
        except FileNotFoundError:
            return default_response

        if not isinstance(
            greetings,
            dict,
        ):
            return default_response

        response_text = default_response

        welcome = greetings.get(
            "welcome",
            {},
        )

        if isinstance(
            welcome,
            dict,
        ):
            configured_response = welcome.get(
                language.value
            )

            if (
                isinstance(
                    configured_response,
                    str,
                )
                and configured_response.strip()
            ):
                response_text = (
                    configured_response.strip()
                )

        return (
            GreetingCapability
            ._append_guided_menu(
                response_text=response_text,
                greetings=greetings,
                language=language,
            )
        )

    @staticmethod
    def _append_guided_menu(
        *,
        response_text: str,
        greetings: dict[str, Any],
        language: Language,
    ) -> str:
        menu = greetings.get(
            "menu",
            {},
        )

        if (
            not isinstance(
                menu,
                dict,
            )
            or menu.get("enabled") is not True
        ):
            return response_text

        items = menu.get(
            "items",
            {},
        )

        if not isinstance(
            items,
            dict,
        ):
            return response_text

        labels = {
            Language.ES: {
                "services": (
                    "\u2022 Servicios y precios: "
                    "escribe \u00abprecios\u00bb."
                ),
                "booking": (
                    "\u2022 Reservar una cita: "
                    "escribe \u00abreservar\u00bb."
                ),
                "faq": (
                    "\u2022 Preguntas frecuentes: "
                    "escribe tu pregunta directamente."
                ),
                "human_transfer": (
                    "\u2022 Hablar con una persona: "
                    "escribe \u00abhablar con una persona\u00bb."
                ),
            },
            Language.EN: {
                "services": (
                    "\u2022 Services and prices: "
                    "write \u201cprices\u201d."
                ),
                "booking": (
                    "\u2022 Book an appointment: "
                    "write \u201cbook\u201d."
                ),
                "faq": (
                    "\u2022 Frequently asked questions: "
                    "write your question directly."
                ),
                "human_transfer": (
                    "\u2022 Speak to a person: "
                    "write \u201cspeak to a person\u201d."
                ),
            },
        }

        introductions = {
            Language.ES: "Opciones r\u00e1pidas:",
            Language.EN: "Quick options:",
        }

        selected_items = [
            labels[language][item_name]
            for item_name in (
                "services",
                "booking",
                "faq",
                "human_transfer",
            )
            if items.get(
                item_name
            ) is True
        ]

        if not selected_items:
            return response_text

        return (
            response_text
            + "\n\n"
            + introductions[language]
            + "\n"
            + "\n".join(
                selected_items
            )
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