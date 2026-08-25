from __future__ import annotations

from chatbot.activation import ActivationConfig
from chatbot.instances import InstanceDefinition


def create_hairdressing_demo_definition() -> InstanceDefinition:
    """
    Create the generic hair salon demonstration configuration.

    This instance is intended for commercial presentations and can be
    copied and customized when onboarding a real hair salon.
    """

    return InstanceDefinition(
        id="hairdressing_demo",
        name="Salón Estilo",
        template_id="hairdressing",
        knowledge_path="knowledge/hairdressing_demo",
        settings={
            "branding": {
                "display_name": "Salón Estilo",
            },
            "booking": {
                "timezone": "Europe/Madrid",
                "business_hours": {
                    "monday": [
                        ["09:30", "13:30"],
                        ["16:00", "20:00"],
                    ],
                    "tuesday": [
                        ["09:30", "13:30"],
                        ["16:00", "20:00"],
                    ],
                    "wednesday": [
                        ["09:30", "13:30"],
                        ["16:00", "20:00"],
                    ],
                    "thursday": [
                        ["09:30", "13:30"],
                        ["16:00", "20:00"],
                    ],
                    "friday": [
                        ["09:30", "13:30"],
                        ["16:00", "20:00"],
                    ],
                    "saturday": [
                        ["09:30", "14:00"],
                    ],
                    "sunday": [],
                },
                "rules": {
                    "appointment_duration_minutes": 30,
                    "slot_interval_minutes": 30,
                    "buffer_before_minutes": 0,
                    "buffer_after_minutes": 0,
                    "minimum_notice_hours": 2,
                    "maximum_advance_days": 30,
                    "allow_past_bookings": False,
                },
            },
        },
        activation=ActivationConfig(
            type="exact_phrase",
            phrases=[
                "peluqueria",
                "peluquería",
            ],
            prompt_message=(
                "Hola, estás hablando con el asistente automático "
                "de Salón Estilo.\n\n"
                "Para iniciar la demostración, escribe PELUQUERÍA."
            ),
            activated_message=(
                "Demostración de peluquería activada correctamente.\n\n"
                "¿En qué puedo ayudarte?"
            ),
            prompt_cooldown=60,
            session_timeout=3600,
        ),
        metadata={
            "owner": "Demo comercial de FlowForge",
            "business_type": "hairdressing",
            "version": "1.0",
            "booking_configuration_status": "demo",
        },
    )
