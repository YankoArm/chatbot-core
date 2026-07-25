from chatbot.application.bootstrap import Bootstrap
from chatbot.business_templates import create_tarot_template
from chatbot.clients import create_tarot_alvin_definition


def build_tarot_alvin_application():
    template = create_tarot_template()
    definition = create_tarot_alvin_definition()

    return Bootstrap().build_from_definition(
        template=template,
        definition=definition,
    )


def test_bootstrap_builds_tarot_alvin_from_business_template():
    app = build_tarot_alvin_application()

    assert app.instance.id == "tarot_alvin"
    assert app.instance.name == "Tarot Alvin"
    assert app.instance.template_id == "tarot"

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
        "knowledge/tarot_alvin"
    )

    assert app.instance.settings["business_type"] == (
        "tarot"
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
        app.instance.settings["branding"][
            "display_name"
        ]
        == "Tarot Alvin"
    )

    assert app.instance.metadata["category"] == (
        "spiritual_services"
    )

    assert app.instance.metadata["owner"] == (
        "Tarot Alvin"
    )


def test_tarot_alvin_answers_faq_from_json_knowledge():
    app = build_tarot_alvin_application()

    response = app.chat(
        session_id="faq-integration-session",
        message="¿Cuánto cuesta una sesión?",
    )

    assert response.text == (
        "El precio de las sesiones todavía "
        "no está configurado."
    )

    assert response.metadata["capability"] == "faq"
    assert response.metadata["handled"] is True
    assert response.metadata["answer_found"] is True
    assert response.metadata["language"] == "es"


def test_tarot_alvin_uses_english_faq_answer():
    app = build_tarot_alvin_application()

    response = app.chat(
        session_id="english-faq-session",
        message="How much does a session cost?",
    )

    assert response.text == (
        "Session pricing has not been configured yet."
    )

    assert response.metadata["capability"] == "faq"
    assert response.metadata["handled"] is True
    assert response.metadata["answer_found"] is True
    assert response.metadata["language"] == "en"


def test_tarot_alvin_persists_knowledge_service_in_session():
    app = build_tarot_alvin_application()

    session_id = "persistent-knowledge-session"

    app.chat(
        session_id=session_id,
        message="¿Cuánto cuesta una sesión?",
    )

    context = app.conversation_store.get(
        session_id
    )

    first_service = context.knowledge_service

    app.chat(
        session_id=session_id,
        message="¿Qué servicios ofrecéis?",
    )

    context = app.conversation_store.get(
        session_id
    )

    assert first_service is not None
    assert context.knowledge_service is first_service


def test_tarot_alvin_session_context_reads_company_knowledge():
    app = build_tarot_alvin_application()

    session_id = "company-knowledge-session"

    app.chat(
        session_id=session_id,
        message="¿Cuánto cuesta una sesión?",
    )

    context = app.conversation_store.get(
        session_id
    )

    assert context.knowledge_service is not None

    company = context.knowledge_service.get_section(
        "company",
    )

    assert company == {}