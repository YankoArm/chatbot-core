from chatbot.business_templates import (
    create_hairdressing_template,
)


def test_create_hairdressing_template():
    template = create_hairdressing_template()

    assert template.id == "hairdressing"
    assert template.name == "Hairdressing Assistant"

    assert template.default_language == "es"
    assert template.supported_languages == [
        "es",
        "en",
    ]

    assert template.channels == [
        "web",
        "whatsapp",
    ]

    assert template.capabilities == [
        "greeting",
        "faq",
        "booking",
        "help",
        "human_transfer",
    ]

    assert template.connectors == []

    assert template.settings == {
        "business_type": "hairdressing",
        "booking": {
            "enabled": True,
            "requires_confirmation": True,
        },
        "faq": {
            "enabled": True,
        },
        "help": {
            "enabled": True,
        },
        "human_transfer": {
            "enabled": True,
        },
    }

    assert template.metadata == {
        "category": "beauty_and_personal_care",
        "template_version": "1.0",
    }

    assert template.activation is not None
