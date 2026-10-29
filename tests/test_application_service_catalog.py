from chatbot.application.bootstrap import Bootstrap
from chatbot.clients.registry import (
    build_instance_from_definition,
)
from chatbot.clients.tarot_alvin import (
    create_tarot_alvin_definition,
)


SERVICES = [
    {
        "id": "lectura_tarot_30_minutos",
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
        "id": "lectura_tarot_1_hora",
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


def test_application_exposes_service_catalog_to_faq():
    definition = create_tarot_alvin_definition()

    definition.settings["services"] = SERVICES

    instance = build_instance_from_definition(
        definition
    )

    application = Bootstrap().build_from_instance(
        instance
    )

    application.chat(
        session_id="catalog-integration-test",
        message="TAROT",
    )

    response = application.chat(
        session_id="catalog-integration-test",
        message="quiero saber que sesiones hay",
    )

    assert "Lectura de tarot 30 minutos" in response.text
    assert "25,00" in response.text
    assert "Lectura de tarot 1 hora" in response.text
    assert "50,00" in response.text

    response = application.chat(
        session_id="catalog-integration-test",
        message="y que precios?",
    )

    assert "25,00" in response.text
    assert "50,00" in response.text
    assert (
        "todavia no esta configurado"
        not in response.text.lower()
    )
