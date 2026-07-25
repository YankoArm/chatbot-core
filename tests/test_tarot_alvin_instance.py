from chatbot.application.bootstrap import Bootstrap
from chatbot.business_templates import create_tarot_template
from chatbot.clients import create_tarot_alvin_definition


def test_bootstrap_builds_tarot_alvin_from_business_template():
    template = create_tarot_template()
    definition = create_tarot_alvin_definition()

    app = Bootstrap().build_from_definition(
        template=template,
        definition=definition,
    )

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

    assert app.instance.settings["business_type"] == "tarot"
    assert app.instance.settings["booking"]["enabled"] is True
    assert (
        app.instance.settings["booking"]["timezone"]
        == "Europe/Madrid"
    )

    assert (
        app.instance.settings["branding"]["display_name"]
        == "Tarot Alvin"
    )

    assert app.instance.metadata["category"] == (
        "spiritual_services"
    )
    assert app.instance.metadata["owner"] == "Tarot Alvin"