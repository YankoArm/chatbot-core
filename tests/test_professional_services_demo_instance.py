from chatbot.application.bootstrap import Bootstrap
from chatbot.business_templates import (
    create_professional_services_template,
)
from chatbot.clients import (
    create_professional_services_demo_definition,
)


def build_professional_services_demo_application():
    template = create_professional_services_template()
    definition = create_professional_services_demo_definition()

    return Bootstrap().build_from_definition(
        template=template,
        definition=definition,
    )


def test_bootstrap_builds_professional_services_demo():
    app = build_professional_services_demo_application()

    assert app.instance.id == "professional_services_demo"
    assert app.instance.name == "Nexo Servicios"
    assert app.instance.template_id == (
        "professional_services"
    )

    assert app.instance.capabilities == [
        "greeting",
        "faq",
        "help",
        "human_transfer",
    ]

    assert app.instance.knowledge_path == (
        "knowledge/professional_services_demo"
    )

    assert app.instance.settings["business_type"] == (
        "professional_services"
    )

    assert app.instance.settings["branding"]["display_name"] == (
        "Nexo Servicios"
    )

    assert app.instance.metadata["category"] == (
        "professional_services"
    )

    assert app.instance.metadata["owner"] == (
        "Demo comercial de FlowForge"
    )


def test_professional_services_demo_answers_faq():
    app = build_professional_services_demo_application()

    app.chat(
        session_id="professional-services-faq",
        message="Servicios",
    )

    response = app.chat(
        session_id="professional-services-faq",
        message="¿Qué servicios ofrecéis?",
    )

    assert response.text == (
        "Ofrecemos asesoramiento, gestión de proyectos y "
        "servicios personalizados. Cuéntanos qué necesitas "
        "y una persona del equipo podrá orientarte."
    )
    assert response.metadata["capability"] == "faq"
    assert response.metadata["answer_found"] is True


def test_professional_services_demo_allows_human_transfer():
    app = build_professional_services_demo_application()

    app.chat(
        session_id="professional-services-transfer",
        message="Servicios",
    )

    response = app.chat(
        session_id="professional-services-transfer",
        message="Quiero hablar con una persona",
    )

    assert response.text == (
        "De acuerdo. Voy a solicitar que una persona "
        "continúe la conversación contigo."
    )
    assert response.metadata["capability"] == "human_transfer"
    assert response.metadata["human_transfer_requested"] is True
    assert response.metadata["transfer_registered"] is True
