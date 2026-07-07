from __future__ import annotations

from chatbot.application.application import FlowForgeApplication


class Bootstrap:
    """
    Builds a FlowForgeApplication from already prepared runtime components.

    Bootstrap is responsible for construction, not conversation logic.
    """

    def build(
        self,
        instance,
        orchestrator,
        capability_manager,
        connector_manager=None,
    ) -> FlowForgeApplication:
        return FlowForgeApplication(
            instance=instance,
            orchestrator=orchestrator,
            capability_manager=capability_manager,
            connector_manager=connector_manager,
        )