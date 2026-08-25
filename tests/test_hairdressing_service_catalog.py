from chatbot.clients import (
    create_hairdressing_demo_definition,
)


def test_hairdressing_demo_has_structured_service_catalog():
    definition = create_hairdressing_demo_definition()

    services = definition.settings["services"]

    assert services == [
        {
            "id": "womens_haircut",
            "name": {
                "es": "Corte de mujer",
                "en": "Women's haircut",
            },
            "duration_minutes": 45,
            "price": {
                "type": "fixed",
                "amount_cents": 2500,
                "currency": "EUR",
            },
        },
        {
            "id": "mens_haircut",
            "name": {
                "es": "Corte de hombre",
                "en": "Men's haircut",
            },
            "duration_minutes": 30,
            "price": {
                "type": "fixed",
                "amount_cents": 1800,
                "currency": "EUR",
            },
        },
        {
            "id": "childrens_haircut",
            "name": {
                "es": "Corte infantil",
                "en": "Children's haircut",
            },
            "duration_minutes": 30,
            "price": {
                "type": "fixed",
                "amount_cents": 1500,
                "currency": "EUR",
            },
        },
        {
            "id": "hairstyling",
            "name": {
                "es": "Peinado",
                "en": "Hairstyling",
            },
            "duration_minutes": 45,
            "price": {
                "type": "fixed",
                "amount_cents": 2500,
                "currency": "EUR",
            },
        },
        {
            "id": "hair_coloring",
            "name": {
                "es": "Tinte",
                "en": "Hair colouring",
            },
            "duration_minutes": 90,
            "price": {
                "type": "from",
                "amount_cents": 4500,
                "currency": "EUR",
            },
        },
        {
            "id": "highlights",
            "name": {
                "es": "Mechas",
                "en": "Highlights",
            },
            "duration_minutes": 120,
            "price": {
                "type": "from",
                "amount_cents": 6500,
                "currency": "EUR",
            },
        },
        {
            "id": "hair_treatment",
            "name": {
                "es": "Tratamiento capilar",
                "en": "Hair treatment",
            },
            "duration_minutes": 45,
            "price": {
                "type": "fixed",
                "amount_cents": 3000,
                "currency": "EUR",
            },
        },
    ]