from __future__ import annotations

from chatbot.activation import ActivationConfig
from chatbot.instances import TemplateDefinition


def create_professional_services_template() -> TemplateDefinition:
    """
    Create reusable defaults for professional-services assistants.

    Client-specific services, prices, locations and contact details
    belong in InstanceDefinition and its knowledge base.
    """

    return TemplateDefinition(
        id="professional_services",
        name="Professional Services Assistant",
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
            "help",
            "human_transfer",
        ],
        connectors=[],
        settings={
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
        },
        metadata={
            "category": "professional_services",
            "template_version": "1.0",
        },
        activation=ActivationConfig(),
    )
