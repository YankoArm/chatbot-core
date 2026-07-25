from __future__ import annotations

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
            },
        },

        metadata={
            "owner": "Tarot Alvin",
            "business_type": "tarot",
            "version": "1.0",
        },
    )