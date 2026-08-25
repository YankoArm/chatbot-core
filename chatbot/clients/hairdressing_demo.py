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
            "services": [
                {
                    "id": "womens_haircut",
                    "name": {
                        "es": "Corte de mujer",
                        "en": "Women's haircut",
                    },
                    "duration_minutes": 45,
                    "price": {
                        "type": "fixed",
                        "amount_cents": 2500,
                        "currency": "EUR",
                    },
                },
                {
                    "id": "mens_haircut",
                    "name": {
                        "es": "Corte de hombre",
                        "en": "Men's haircut",
                    },
                    "duration_minutes": 30,
                    "price": {
                        "type": "fixed",
                        "amount_cents": 1800,
                        "currency": "EUR",
                    },
                },
                {
                    "id": "childrens_haircut",
                    "name": {
                        "es": "Corte infantil",
                        "en": "Children's haircut",
                    },
                    "duration_minutes": 30,
                    "price": {
                        "type": "fixed",
                        "amount_cents": 1500,
                        "currency": "EUR",
                    },
                },
                {
                    "id": "hairstyling",
                    "name": {
                        "es": "Peinado",
                        "en": "Hairstyling",
                    },
                    "duration_minutes": 45,
                    "price": {
                        "type": "fixed",
                        "amount_cents": 2500,
                        "currency": "EUR",
                    },
                },
                {
                    "id": "hair_coloring",
                    "name": {
                        "es": "Tinte",
                        "en": "Hair colouring",
                    },
                    "duration_minutes": 90,
                    "price": {
                        "type": "from",
                        "amount_cents": 4500,
                        "currency": "EUR",
                    },
                },
                {
                    "id": "highlights",
                    "name": {
                        "es": "Mechas",
                        "en": "Highlights",
                    },
                    "duration_minutes": 120,
                    "price": {
                        "type": "from",
                        "amount_cents": 6500,
                        "currency": "EUR",
                    },
                },
                {
                    "id": "hair_treatment",
                    "name": {
                        "es": "Tratamiento capilar",
                        "en": "Hair treatment",
                    },
                    "duration_minutes": 45,
                    "price": {
                        "type": "fixed",
                        "amount_cents": 3000,
                        "currency": "EUR",
                    },
                },
            ],
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