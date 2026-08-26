from __future__ import annotations

import re
import unicodedata

from chatbot.language.detector import BaseLanguageDetector
from chatbot.language.models import Language


class RuleBasedLanguageDetector(BaseLanguageDetector):
    """
    Detects Spanish or English using lightweight vocabulary rules.

    This implementation is deterministic and dependency-free. It is
    intended as the initial FlowForge detector and can later be replaced
    by a statistical or external implementation.
    """

    _SPANISH_WORDS = {
        "hola",
        "buenas",
        "buenos",
        "dias",
        "tardes",
        "noches",
        "quiero",
        "quisiera",
        "necesito",
        "gracias",
        "precio",
        "precios",
        "cuanto",
        "cuesta",
        "cita",
        "citas",
        "reservar",
        "reserva",
        "servicio",
        "servicios",
        "horario",
        "horarios",
        "donde",
        "cuando",
        "como",
        "ayuda",
        "informacion",
        "consulta",
        "consultas",
        "por",
        "para",
        "con",
        "una",
        "un",
        "el",
        "la",
        "los",
        "las",
    }

    _ENGLISH_WORDS = {
        "what",
        "is",
        "are",
        "your",
        "you",
        "do",
        "address",
        "location",
        "payment",
        "methods",
        "accept",
        "pay",
        "card",
        "cash",
        "cancellation",
        "policy",
        "cancel",
        "reschedule",
        "hello",
        "hi",
        "hey",
        "good",
        "morning",
        "afternoon",
        "evening",
        "want",
        "would",
        "need",
        "thanks",
        "thank",
        "price",
        "prices",
        "cost",
        "appointment",
        "appointments",
        "book",
        "booking",
        "reserve",
        "service",
        "services",
        "schedule",
        "hours",
        "where",
        "when",
        "how",
        "help",
        "information",
        "consultation",
        "consultations",
        "with",
        "for",
        "the",
        "a",
        "an",
    }

    def detect(
        self,
        text: str,
        default_language: Language = Language.ES,
    ) -> Language:
        words = self._tokenize(text)

        if not words:
            return default_language

        spanish_score = sum(
            word in self._SPANISH_WORDS
            for word in words
        )

        english_score = sum(
            word in self._ENGLISH_WORDS
            for word in words
        )

        if english_score > spanish_score:
            return Language.EN

        if spanish_score > english_score:
            return Language.ES

        return default_language

    @classmethod
    def _tokenize(cls, text: str) -> list[str]:
        normalized_text = cls._normalize(text)

        return re.findall(
            r"[a-z]+",
            normalized_text,
        )

    @staticmethod
    def _normalize(text: str) -> str:
        normalized_text = unicodedata.normalize(
            "NFKD",
            text.strip().lower(),
        )

        return "".join(
            character
            for character in normalized_text
            if not unicodedata.combining(character)
        )
