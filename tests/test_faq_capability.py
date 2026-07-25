from types import SimpleNamespace

from chatbot.capabilities.faq import FAQCapability
from chatbot.language import Language


def build_context(
    *,
    language: Language = Language.ES,
    variables: dict | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        language=language,
        variables=variables or {},
    )


def test_faq_capability_has_expected_name():
    capability = FAQCapability()

    assert capability.name == "faq"


def test_faq_capability_handles_price_question_in_spanish():
    capability = FAQCapability()
    context = build_context()

    assert capability.can_handle(
        context,
        "¿Cuánto cuesta una sesión?",
    )


def test_faq_capability_handles_service_question_in_english():
    capability = FAQCapability()
    context = build_context(
        language=Language.EN,
    )

    assert capability.can_handle(
        context,
        "What services do you offer?",
    )


def test_faq_capability_does_not_handle_unrelated_message():
    capability = FAQCapability()
    context = build_context()

    assert not capability.can_handle(
        context,
        "Quiero reservar para mañana",
    )


def test_faq_capability_returns_spanish_fallback():
    capability = FAQCapability()
    context = build_context(
        language=Language.ES,
    )

    response = capability.handle(
        context,
        "¿Qué servicios tienes?",
    )

    assert response.metadata["capability"] == "faq"
    assert response.metadata["handled"] is True
    assert response.metadata["language"] == "es"
    assert response.metadata["answer_found"] is False

    assert "servicios" in response.text.lower()


def test_faq_capability_returns_english_fallback():
    capability = FAQCapability()
    context = build_context(
        language=Language.EN,
    )

    response = capability.handle(
        context,
        "What are your prices?",
    )

    assert response.metadata["language"] == "en"
    assert response.metadata["answer_found"] is False

    assert "prices" in response.text.lower()


def test_faq_capability_returns_configured_answer():
    capability = FAQCapability()

    context = build_context(
        variables={
            "faq": {
                "prices": {
                    "keywords": [
                        "precio",
                        "precios",
                        "cuanto cuesta",
                    ],
                    "answer": (
                        "Las sesiones tienen un precio de 40 €."
                    ),
                },
            },
        },
    )

    response = capability.handle(
        context,
        "¿Cuánto cuesta una sesión?",
    )

    assert response.text == (
        "Las sesiones tienen un precio de 40 €."
    )

    assert response.metadata["answer_found"] is True


def test_faq_capability_ignores_invalid_faq_configuration():
    capability = FAQCapability()

    context = build_context(
        variables={
            "faq": {
                "invalid": {
                    "keywords": "precio",
                    "answer": None,
                },
            },
        },
    )

    response = capability.handle(
        context,
        "¿Cuál es el precio?",
    )

    assert response.metadata["answer_found"] is False