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
        activation=ActivationConfig(
            type="exact_phrase",
            phrases=[
                "servicios",
                "nexo servicios",
            ],
            prompt_message=(
                "Hola, estás hablando con el asistente "
                "automático de Nexo Servicios.\n\n"
                "Para iniciar la demostración, escribe SERVICIOS."
            ),
            activated_message=(
                "Demostración de servicios profesionales "
                "activada correctamente.\n\n"
                "Puedo ayudarte con:\n"
                "• Resolver dudas sobre los servicios\n"
                "• Explicar cómo trabajamos\n"
                "• Orientarte sobre presupuestos\n"
                "• Hablar con una persona\n\n"
                "Escríbeme directamente qué necesitas."
            ),
            prompt_cooldown=60,
            session_timeout=3600,
        ),
        metadata={
            "owner": "Demo comercial de FlowForge",
            "business_type": "professional_services",
            "version": "1.0",
        },
    )
