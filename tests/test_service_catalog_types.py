import pytest

from chatbot.capabilities.faq.catalog import build_service_catalog_answer
from chatbot.language import Language


def catalog_services():
    return [
        {
            "id": "website",
            "service_type": "project",
            "name": {"es": "Pagina web", "en": "Website"},
            "duration_text": "5-10 dias",
            "price": {
                "type": "from",
                "amount_cents": 20000,
                "currency": "EUR",
                "billing_period": "once",
            },
        },
        {
            "id": "seo",
            "service_type": "recurring",
            "name": {"es": "Posicionamiento SEO", "en": "SEO"},
            "duration_text": "A consultar",
            "price": {
                "type": "from",
                "amount_cents": 10000,
                "currency": "EUR",
                "billing_period": "month",
            },
        },
    ]


@pytest.mark.parametrize(
    "language,message,website,period,amount",
    [
        (Language.ES, "Ver servicios y precios", "Pagina web", "/ mes", "100,00"),
        (Language.EN, "Services and prices", "Website", "/ month", "100.00"),
    ],
)
def test_catalog_includes_projects_and_recurring_prices(
    language, message, website, period, amount
):
    answer = build_service_catalog_answer(
        services=catalog_services(),
        message=message,
        language=language,
    )

    assert answer is not None
    assert website in answer
    assert "SEO" in answer
    assert "5-10 dias" in answer
    assert period in answer
    assert amount in answer
    assert "minutos" not in answer
    assert "minutes" not in answer


@pytest.mark.parametrize("language", [Language.ES, Language.EN])
def test_non_bookable_catalog_does_not_invite_booking(language):
    answer = build_service_catalog_answer(
        services=catalog_services(),
        message="servicios" if language is Language.ES else "services",
        language=language,
    )

    assert answer is not None
    if language is Language.ES:
        assert "reservar" not in answer.casefold()
        assert "informaci\u00f3n" in answer.casefold()
    else:
        assert "book" not in answer.casefold()
        assert "information" in answer.casefold()
