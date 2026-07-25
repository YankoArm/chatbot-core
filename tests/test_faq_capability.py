from pathlib import Path
from types import SimpleNamespace
from typing import Any

from chatbot.capabilities.faq import FAQCapability
from chatbot.knowledge import (
    KnowledgeLoader,
    KnowledgeProvider,
    KnowledgeService,
)
from chatbot.language import Language


class FakeFAQKnowledgeProvider(
    KnowledgeProvider
):
    def load(
        self,
        knowledge_path: str | Path,
    ) -> dict[str, Any]:
        return {
            "faq": {
                "prices": {
                    "keywords": [
                        "precio",
                        "precios",
                        "cuanto cuesta",
                        "how much",
                        "cost",
                        "price",
                        "prices",
                    ],
                    "answers": {
                        "es": (
                            "Las sesiones tienen un precio "
                            "de 40 €."
                        ),
                        "en": "Sessions cost €40.",
                    },
                },
            },
        }


class InvalidFAQKnowledgeProvider(
    KnowledgeProvider
):
    def load(
        self,
        knowledge_path: str | Path,
    ) -> dict[str, Any]:
        return {
            "faq": {
                "invalid": {
                    "keywords": "precio",
                    "answers": None,
                },
            },
        }


def build_context(
    *,
    language: Language = Language.ES,
    knowledge_service: KnowledgeService | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        language=language,
        knowledge_service=knowledge_service,
    )


def build_knowledge_service(
    tmp_path: Path,
    provider: KnowledgeProvider | None = None,
) -> KnowledgeService:
    knowledge_provider = (
        provider
        if provider is not None
        else FakeFAQKnowledgeProvider()
    )

    loader = KnowledgeLoader(
        knowledge_provider
    )

    return KnowledgeService(
        loader=loader,
        knowledge_path=tmp_path,
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


def test_faq_capability_returns_spanish_knowledge_answer(
    tmp_path: Path,
):
    capability = FAQCapability()

    service = build_knowledge_service(
        tmp_path
    )

    context = build_context(
        language=Language.ES,
        knowledge_service=service,
    )

    response = capability.handle(
        context,
        "¿Cuánto cuesta una sesión?",
    )

    assert response.text == (
        "Las sesiones tienen un precio de 40 €."
    )

    assert response.metadata[
        "answer_found"
    ] is True

    assert response.metadata[
        "language"
    ] == "es"


def test_faq_capability_returns_english_knowledge_answer(
    tmp_path: Path,
):
    capability = FAQCapability()

    service = build_knowledge_service(
        tmp_path
    )

    context = build_context(
        language=Language.EN,
        knowledge_service=service,
    )

    response = capability.handle(
        context,
        "How much does a session cost?",
    )

    assert response.text == (
        "Sessions cost €40."
    )

    assert response.metadata[
        "answer_found"
    ] is True

    assert response.metadata[
        "language"
    ] == "en"


def test_faq_capability_returns_spanish_fallback_without_service():
    capability = FAQCapability()

    context = build_context(
        language=Language.ES,
        knowledge_service=None,
    )

    response = capability.handle(
        context,
        "¿Cuál es el precio?",
    )

    assert response.metadata[
        "language"
    ] == "es"

    assert response.metadata[
        "answer_found"
    ] is False

    assert "precios" in response.text.lower()


def test_faq_capability_returns_english_fallback_without_service():
    capability = FAQCapability()

    context = build_context(
        language=Language.EN,
        knowledge_service=None,
    )

    response = capability.handle(
        context,
        "What are your prices?",
    )

    assert response.metadata[
        "language"
    ] == "en"

    assert response.metadata[
        "answer_found"
    ] is False

    assert "prices" in response.text.lower()


def test_faq_capability_returns_fallback_when_no_keyword_matches(
    tmp_path: Path,
):
    capability = FAQCapability()

    service = build_knowledge_service(
        tmp_path
    )

    context = build_context(
        knowledge_service=service,
    )

    response = capability.handle(
        context,
        "¿Dónde está vuestro local?",
    )

    assert response.metadata[
        "answer_found"
    ] is False


def test_faq_capability_ignores_invalid_faq_configuration(
    tmp_path: Path,
):
    capability = FAQCapability()

    service = build_knowledge_service(
        tmp_path,
        provider=InvalidFAQKnowledgeProvider(),
    )

    context = build_context(
        knowledge_service=service,
    )

    response = capability.handle(
        context,
        "¿Cuál es el precio?",
    )

    assert response.metadata[
        "answer_found"
    ] is False