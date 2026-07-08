from __future__ import annotations

from typing import Any

from chatbot.capabilities.capability_manager import CapabilityManager
from chatbot.conversation.context import ConversationContext
from chatbot.responses import Response


class ConversationOrchestrator:
    """
    Coordinates conversation processing between Context, Capabilities and Responses.

    The Orchestrator does not contain business-specific logic.
    It delegates messages to the first Capability able to handle them.
    """

    def __init__(self, capability_manager: CapabilityManager):
        self.capability_manager = capability_manager

    def process(self, context: ConversationContext, message: str) -> Response:
        for capability in self.capability_manager.all():
            if capability.can_handle(context, message):
                context.set_active_capability(capability.name)
                return capability.handle(context, message)

        return Response(
            text="I'm sorry, I don't know how to handle that request.",
            metadata={
                "handled": False,
            },
        )