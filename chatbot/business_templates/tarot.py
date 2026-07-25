from __future__ import annotations

from chatbot.activation import ActivationConfig
from chatbot.instances import TemplateDefinition


def create_tarot_template() -> TemplateDefinition:
    """
    Create the default business template for tarot assistants.

    The template contains reusable defaults shared by tarot businesses.
    Client-specific information such as the professional's name, prices,
    services and availability must be provided through InstanceDefinition.
    """

    return TemplateDefinition(
        id="tarot",
        name="Tarot Assistant",
        default_language="es",
        supported_languages=[
            "es",
            "en",
        ],
        channels=[
            "web",
            "whatsapp",
        ],
        capabilities=[
            "greeting",
            "faq",
            "booking",
            "human_transfer",
        ],
        connectors=[],
        settings={
            "business_type": "tarot",
            "booking": {
                "enabled": True,
                "requires_confirmation": True,
            },
            "faq": {
                "enabled": True,
            },
            "human_transfer": {
                "enabled": True,
            },
        },
        metadata={
            "category": "spiritual_services",
            "template_version": "1.0",
        },
        activation=ActivationConfig(),
    )