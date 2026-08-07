from __future__ import annotations

from chatbot.activation import ActivationConfig
from chatbot.instances import InstanceDefinition


def create_tarot_alvin_definition() -> InstanceDefinition:
    """
    Create the client-specific configuration for Tarot Alvin.

    This definition only contains data that differs from the reusable
    tarot business template.
    """

    return InstanceDefinition(
        id="tarot_alvin",
        name="Tarot Alvin",
        template_id="tarot",
        knowledge_path="knowledge/tarot_alvin",
        settings={
            "branding": {
                "display_name": "Tarot Alvin",
            },
            "booking": {
                "timezone": "Europe/Madrid",
                "business_hours": {
                    "monday": [
                        ["10:00", "14:00"],
                        ["16:00", "20:00"],
                    ],
                    "tuesday": [
                        ["10:00", "14:00"],
                        ["16:00", "20:00"],
                    ],
                    "wednesday": [
                        ["10:00", "14:00"],
                        ["16:00", "20:00"],
                    ],
                    "thursday": [
                        ["10:00", "14:00"],
                        ["16:00", "20:00"],
                    ],
                    "friday": [
                        ["10:00", "14:00"],
                        ["16:00", "20:00"],
                    ],
                    "saturday": [],
                    "sunday": [],
                },
                "rules": {
                    "appointment_duration_minutes": 60,
                    "slot_interval_minutes": 60,
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
                "tarot",
            ],
            prompt_message=(
                "Hola, estás hablando con el asistente automático "
                "de Alvin.\n\n"
                "Para activar el servicio de tarot, escribe TAROT."
            ),
            activated_message=(
                "Servicio de tarot activado correctamente.\n\n"
                "¿En qué puedo ayudarte?"
            ),
            prompt_cooldown=60,
            session_timeout=3600,
        ),
        metadata={
            "owner": "Tarot Alvin",
            "business_type": "tarot",
            "version": "1.0",
            "booking_configuration_status": "provisional",
        },
    )
