from __future__ import annotations

from chatbot.application.application import FlowForgeApplication
from chatbot.conversation import ConversationStore


class Bootstrap:
    """
    Builds a FlowForgeApplication from already prepared runtime components.
    """

    def build(
        self,
        instance,
        orchestrator,
        capability_manager,
        conversation_store=None,
        connector_manager=None,
    ) -> FlowForgeApplication:
        return FlowForgeApplication(
            instance=instance,
            orchestrator=orchestrator,
            capability_manager=capability_manager,
            conversation_store=conversation_store or ConversationStore(),
            connector_manager=connector_manager,
        )