from __future__ import annotations

from chatbot.capabilities.faq import FAQCapability
from chatbot.conversation.context import (
    ConversationContext,
)
from chatbot.conversation.context_factory import (
    ConversationContextFactory,
)
from chatbot.instances import Instance
from chatbot.language import Language


SERVICES = [
    {
        "id": "tarot_30min",
        "name": {
            "es": "Lectura de tarot 30 minutos",
            "en": "30-minute Tarot Reading",
        },
        "duration_minutes": 30,
        "price": {
            "type": "fixed",
            "amount_cents": 2500,
            "currency": "EUR",
        },
    },
    {
        "id": "tarot_60min",
        "name": {
            "es": "Lectura de tarot 1 hora",
            "en": "1-hour Tarot Reading",
        },
        "duration_minutes": 60,
        "price": {
            "type": "fixed",
            "amount_cents": 5000,
            "currency": "EUR",
        },
    },
]


class StaleKnowledgeService:
    def get_section(
        self,
        section: str,
        default: object = None,
    ) -> object:
        if section != "faq":
            return default

        return {
            "services": {
                "keywords": [
                    "servicios",
                    "sesiones",
                ],
                "answers": {
                    "es": (
                        "RESPUESTA ANTIGUA QUE NO DEBE USARSE"
                    ),
                    "en": (
                        "OLD ANSWER THAT MUST NOT BE USED"
                    ),
                },
            },
            "prices": {
                "keywords": [
                    "precio",
                    "precios",
                ],
                "answers": {
                    "es": (
                        "El precio todavia no esta configurado."
                    ),
                    "en": (
                        "The price is not configured yet."
                    ),
                },
            },
        }


class FakeKnowledgeServiceFactory:
    def build(
        self,
        instance: Instance,
    ) -> None:
        return None


def build_context(
    language: Language,
) -> ConversationContext:
    context = ConversationContext(
        session_id="catalog-test",
        language=language,
        knowledge_service=StaleKnowledgeService(),
    )

    context.variables["services"] = SERVICES

    return context


def test_spanish_service_question_uses_catalog() -> None:
    response = FAQCapability().handle(
        build_context(Language.ES),
        "Que sesiones hay",
    )

    assert (
        "Lectura de tarot 30 minutos"
        in response.text
    )
    assert "25,00 \u20ac" in response.text
    assert (
        "Lectura de tarot 1 hora"
        in response.text
    )
    assert "50,00 \u20ac" in response.text

    assert (
        "RESPUESTA ANTIGUA"
        not in response.text
    )


def test_spanish_price_question_uses_catalog() -> None:
    response = FAQCapability().handle(
        build_context(Language.ES),
        "Cuanto cuestan las sesiones",
    )

    assert "25,00 \u20ac" in response.text
    assert "50,00 \u20ac" in response.text

    assert (
        "todavia no esta configurado"
        not in response.text
    )


def test_english_service_question_uses_catalog() -> None:
    response = FAQCapability().handle(
        build_context(Language.EN),
        "What services do you offer?",
    )

    assert (
        "30-minute Tarot Reading"
        in response.text
    )
    assert "\u20ac25.00" in response.text

    assert (
        "1-hour Tarot Reading"
        in response.text
    )
    assert "\u20ac50.00" in response.text

    assert "OLD ANSWER" not in response.text


def test_context_factory_exposes_services() -> None:
    instance = Instance(
        id="tarot_test",
        name="Tarot Test",
        settings={
            "services": SERVICES,
        },
    )

    factory = ConversationContextFactory(
        knowledge_service_factory=(
            FakeKnowledgeServiceFactory()
        ),
    )

    context = factory.build(
        instance=instance,
        session_id="session-1",
        user_id="user-1",
    )

    assert (
        context.variables["services"]
        == SERVICES
    )
