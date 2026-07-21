from __future__ import annotations

from chatbot.capabilities.greeting import GreetingCapability
from chatbot.registry.capability_registry import CapabilityRegistry


class DefaultCapabilityRegistry(CapabilityRegistry):
    """
    Registry containing all built-in FlowForge capabilities.
    """

    def __init__(self) -> None:
        super().__init__()

        self.register(GreetingCapability)