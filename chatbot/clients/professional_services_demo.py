from __future__ import annotations

from chatbot.activation import ActivationConfig
from chatbot.instances import InstanceDefinition


def create_professional_services_demo_definition() -> InstanceDefinition:
    """
    Create a commercial demonstration for professional-services bots.

    This instance can be copied and customized for consultancies,
    local services, agencies, real-estate businesses or similar teams.
    """

    return InstanceDefinition(
        id="professional_services_demo",
        name="Nexo Servicios",
        template_id="professional_services",
        knowledge_path="knowledge/professional_services_demo",
        settings={
            "branding": {
                "display_name": "Nexo Servicios",
            },
        },
        activation=ActivationConfig(),
        metadata={
            "owner": "Demo comercial de FlowForge",
            "business_type": "professional_services",
            "version": "1.0",
        },
    )
