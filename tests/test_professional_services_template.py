from chatbot.business_templates import (
    create_professional_services_template,
)


def test_create_professional_services_template():
    template = create_professional_services_template()

    assert template.id == "professional_services"
    assert template.name == "Professional Services Assistant"

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
        "help",
        "human_transfer",
    ]

    assert template.connectors == []

    assert template.settings == {
        "business_type": "professional_services",
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
        "category": "professional_services",
        "template_version": "1.0",
    }

    assert template.activation is not None
