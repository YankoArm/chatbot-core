from __future__ import annotations

import pytest

from chatbot.language import (
    Language,
    RuleBasedLanguageDetector,
)


@pytest.fixture
def detector() -> RuleBasedLanguageDetector:
    return RuleBasedLanguageDetector()


@pytest.mark.parametrize(
    "message",
    [
        "Hola",
        "Buenas tardes",
        "Quiero reservar una cita",
        "¿Cuánto cuesta la consulta?",
        "Necesito información sobre los servicios",
        "Gracias por la ayuda",
        "¿Cuál es el horario?",
    ],
)
def test_detects_spanish(
    detector: RuleBasedLanguageDetector,
    message: str,
) -> None:
    assert detector.detect(message) is Language.ES


@pytest.mark.parametrize(
    "message",
    [
        "Hello",
        "Good afternoon",
        "I want to book an appointment",
        "How much does the consultation cost?",
        "I need information about your services",
        "Thanks for your help",
        "What are your opening hours?",
        "What is your address?",
        "What payment methods do you accept?",
        "What is your cancellation policy?",
    ],
)
def test_detects_english(
    detector: RuleBasedLanguageDetector,
    message: str,
) -> None:
    assert detector.detect(message) is Language.EN


def test_uses_spanish_as_default() -> None:
    detector = RuleBasedLanguageDetector()

    assert detector.detect("12345") is Language.ES


def test_supports_custom_default_language() -> None:
    detector = RuleBasedLanguageDetector()

    result = detector.detect(
        "12345",
        default_language=Language.EN,
    )

    assert result is Language.EN


def test_uses_default_language_for_empty_message() -> None:
    detector = RuleBasedLanguageDetector()

    assert detector.detect("") is Language.ES


def test_normalizes_accents() -> None:
    detector = RuleBasedLanguageDetector()

    assert detector.detect(
        "¿Cuánto cuesta y cuál es el horario?"
    ) is Language.ES


def test_language_values_are_serializable_strings() -> None:
    assert Language.ES.value == "es"
    assert Language.EN.value == "en"