from __future__ import annotations

from chatbot.capabilities.booking.capability import BookingCapability
from chatbot.capabilities.faq import FAQCapability
from chatbot.capabilities.greeting import GreetingCapability
from chatbot.capabilities.help import HelpCapability
from chatbot.capabilities.human_transfer import (
    HumanTransferCapability,
)
from chatbot.registry.capability_registry import CapabilityRegistry


class DefaultCapabilityRegistry(CapabilityRegistry):
    """
    Registry containing all built-in FlowForge capabilities.
    """

    def __init__(self) -> None:
        super().__init__()

        self.register(GreetingCapability)
        self.register(FAQCapability)
        self.register(BookingCapability)
        self.register(HelpCapability)
        self.register(HumanTransferCapability)
