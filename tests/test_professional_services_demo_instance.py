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
        "lead_capture",
        "human_transfer",
    ]
    assert app.instance.activation.type == "always_active"
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


def test_professional_services_demo_answers_faq_without_activation_phrase():
    app = build_professional_services_demo_application()

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


def test_professional_services_demo_captures_lead_without_activation_phrase():
    app = build_professional_services_demo_application()
    session_id = "professional-services-lead"

    start_response = app.chat(
        session_id=session_id,
        message="Quiero hablar con una persona",
    )
    name_response = app.chat(
        session_id=session_id,
        message="Yanko",
    )
    phone_response = app.chat(
        session_id=session_id,
        message="600123123",
    )
    final_response = app.chat(
        session_id=session_id,
        message="Necesito un presupuesto.",
    )

    assert start_response.metadata["capability"] == (
        "lead_capture"
    )
    assert start_response.text == (
        "Para que una persona pueda ayudarte mejor, "
        "¿cómo te llamas?"
    )
    assert name_response.text == (
        "Gracias, Yanko. ¿Cuál es tu número de teléfono?"
    )
    assert phone_response.text == (
        "Perfecto. Cuéntame brevemente qué necesitas."
    )
    assert final_response.metadata["lead_captured"] is True
    assert (
        final_response.metadata["human_transfer_requested"]
        is True
    )
