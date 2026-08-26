from __future__ import annotations

import re
import unicodedata
from typing import Any

from chatbot.capabilities.base_capability import BaseCapability
from chatbot.language import Language
from chatbot.responses import Response


_FAQ_KEYWORDS = {
    Language.ES: {
        "precio",
        "precios",
        "cuanto cuesta",
        "cuanto vale",
        "tarifa",
        "tarifas",
        "servicio",
        "servicios",
        "sesion",
        "sesiones",
        "informacion",
        "horario",
        "horarios",
        "donde",
        "ubicacion",
        "direccion",
        "formas de pago",
        "metodos de pago",
    },
    Language.EN: {
        "price",
        "prices",
        "how much",
        "cost",
        "rates",
        "service",
        "services",
        "session",
        "sessions",
        "information",
        "opening hours",
        "schedule",
        "where",
        "location",
        "address",
        "payment methods",
    },
}

_FALLBACK_RESPONSES = {
    Language.ES: (
        "Puedo ayudarte con información sobre servicios, precios, "
        "horarios, ubicación y formas de pago. "
        "¿Qué te gustaría saber?"
    ),
    Language.EN: (
        "I can help you with information about services, prices, "
        "opening hours, location and payment methods. "
        "What would you like to know?"
    ),
}


class FAQCapability(BaseCapability):
    """
    Handle common informational questions.

    FAQCapability detects general questions about services, prices,
    opening hours, location and payment methods.

    Specific answers can be supplied through the conversation context
    using a ``faq`` dictionary stored inside ``context.variables``.
    """

    name = "faq"
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

        keywords = {
            keyword
            for language_keywords in _FAQ_KEYWORDS.values()
            for keyword in language_keywords
        }

        if any(
            keyword in normalized_message
            for keyword in keywords
        ):
            return True

        language = self._get_language(context)

        return (
            self._find_answer(
                context=context,
                message=message,
                language=language,
            )
            is not None
        )

    def handle(
        self,
        context: Any,
        message: str,
    ) -> Response:
        language = self._get_language(context)

        answer = self._find_answer(
            context=context,
            message=message,
            language=language,
        )

        return Response(
            text=answer or _FALLBACK_RESPONSES[language],
            metadata={
                "capability": self.name,
                "handled": True,
                "language": language.value,
                "answer_found": answer is not None,
            },
        )

    def _find_answer(
        self,
        context: Any,
        message: str,
        language: Language,
    ) -> str | None:
        """
        Find the most suitable configured FAQ answer.

        The last matched FAQ entry is remembered so short follow-up
        questions can preserve their conversational subject.
        """

        knowledge_service = getattr(
            context,
            "knowledge_service",
            None,
        )

        if knowledge_service is None:
            return None

        faq_entries = knowledge_service.get_section(
            "faq",
            {},
        )

        if not isinstance(faq_entries, dict):
            return None

        normalized_message = self._normalize_text(
            message
        )

        follow_up_messages = {
            "y cuanto cuesta",
            "cuanto cuesta",
            "y cuanto vale",
            "cuanto vale",
            "y cuanto dura",
            "cuanto dura",
            "and how much is it",
            "how much is it",
            "and how much does it cost",
            "how much does it cost",
            "and how long does it take",
            "how long does it take",
        }

        get_variable = getattr(
            context,
            "get_variable",
            None,
        )

        if (
            normalized_message in follow_up_messages
            and callable(get_variable)
        ):
            previous_entry_id = get_variable(
                "last_faq_entry_id"
            )
            previous_entry = faq_entries.get(
                previous_entry_id
            )

            if isinstance(previous_entry, dict):
                previous_answers = previous_entry.get(
                    "answers",
                    {},
                )

                if isinstance(previous_answers, dict):
                    previous_answer = previous_answers.get(
                        language.value
                    )

                    if (
                        isinstance(previous_answer, str)
                        and previous_answer.strip()
                    ):
                        return previous_answer

        for entry_id, entry in faq_entries.items():
            if not isinstance(entry, dict):
                continue

            keywords = entry.get(
                "keywords",
                [],
            )
            answers = entry.get(
                "answers",
                {},
            )

            if not isinstance(keywords, list):
                continue

            if not isinstance(answers, dict):
                continue

            normalized_keywords = (
                self._normalize_text(keyword)
                for keyword in keywords
                if isinstance(keyword, str)
            )

            matches = any(
                keyword
                and keyword in normalized_message
                for keyword in normalized_keywords
            )

            if not matches:
                continue

            answer = answers.get(
                language.value
            )

            if isinstance(answer, str) and answer.strip():
                set_variable = getattr(
                    context,
                    "set_variable",
                    None,
                )

                if callable(set_variable):
                    set_variable(
                        "last_faq_entry_id",
                        entry_id,
                    )

                return answer

        return None

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

        if language in _FALLBACK_RESPONSES:
            return language

        return Language.ES

    @staticmethod
    def _normalize_text(
        message: str,
    ) -> str:
        """
        Normalize text for reliable FAQ keyword recognition.
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