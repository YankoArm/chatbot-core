from __future__ import annotations

from chatbot.activation import ActivationConfig
from chatbot.instances import TemplateDefinition


def create_hairdressing_template() -> TemplateDefinition:
    """
    Create the default business template for hairdressing assistants.

    The template contains reusable defaults shared by hair salons.
    Client-specific information such as the salon name, services,
    prices, professionals and availability must be provided through
    InstanceDefinition.
    """

    return TemplateDefinition(
        id="hairdressing",
        name="Hairdressing Assistant",
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
            "help",
            "human_transfer",
        ],
        connectors=[],
        settings={
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
        },
        metadata={
            "category": "beauty_and_personal_care",
            "template_version": "1.0",
        },
        activation=ActivationConfig(),
    )
