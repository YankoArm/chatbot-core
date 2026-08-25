from chatbot.application.bootstrap import Bootstrap
from chatbot.business_templates import (
    create_hairdressing_template,
)
from chatbot.clients import (
    create_hairdressing_demo_definition,
)


def build_hairdressing_demo_application():
    template = create_hairdressing_template()
    definition = create_hairdressing_demo_definition()

    return Bootstrap().build_from_definition(
        template=template,
        definition=definition,
    )


def test_bootstrap_builds_hairdressing_demo():
    app = build_hairdressing_demo_application()

    assert app.instance.id == "hairdressing_demo"
    assert app.instance.name == "Salón Estilo"
    assert app.instance.template_id == "hairdressing"

    assert app.instance.default_language == "es"
    assert app.instance.supported_languages == [
        "es",
        "en",
    ]

    assert app.instance.capabilities == [
        "greeting",
        "faq",
        "booking",
        "human_transfer",
    ]

    assert app.instance.channels == [
        "web",
        "whatsapp",
    ]

    assert app.instance.knowledge_path == (
        "knowledge/hairdressing_demo"
    )

    assert app.instance.settings["business_type"] == (
        "hairdressing"
    )

    assert (
        app.instance.settings["booking"]["enabled"]
        is True
    )

    assert (
        app.instance.settings["booking"]["timezone"]
        == "Europe/Madrid"
    )

    assert (
        app.instance.settings["branding"]["display_name"]
        == "Salón Estilo"
    )

    assert app.instance.metadata["category"] == (
        "beauty_and_personal_care"
    )

    assert app.instance.metadata["owner"] == (
        "Demo comercial de FlowForge"
    )


def test_hairdressing_demo_answers_services_and_prices():
    app = build_hairdressing_demo_application()
    session_id = "hairdressing-services-session"

    app.chat(
        session_id=session_id,
        message="Peluquería",
    )

    response = app.chat(
        session_id=session_id,
        message="¿Qué servicios y precios tenéis?",
    )

    assert response.text == (
        "Estos son nuestros servicios:\n\n"
        "✂️ Corte de mujer — 25 €\n"
        "✂️ Corte de hombre — 18 €\n"
        "🧒 Corte infantil — 15 €\n"
        "💇 Peinado — 25 €\n"
        "🎨 Tinte — desde 45 €\n"
        "✨ Mechas — desde 65 €\n"
        "🌿 Tratamiento capilar — 30 €\n\n"
        "Los precios son orientativos y pueden variar "
        "según el largo y las características del cabello."
    )

    assert response.metadata["capability"] == "faq"
    assert response.metadata["handled"] is True
    assert response.metadata["answer_found"] is True
    assert response.metadata["language"] == "es"
