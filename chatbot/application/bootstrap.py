from __future__ import annotations

from chatbot.application.application import FlowForgeApplication
from chatbot.capabilities.capability_manager import CapabilityManager
from chatbot.conversation import ConversationOrchestrator, ConversationStore
from chatbot.instances import Instance
from chatbot.registry import (
    CapabilityRegistry,
    DefaultCapabilityRegistry,
)
from chatbot.activation import ActivationFactory

class Bootstrap:
    """
    Builds FlowForge application runtimes.

    It can build an application from prepared runtime components or
    automatically from a declarative Instance.
    """

    def __init__(
        self,
        capability_registry: CapabilityRegistry | None = None,
    ) -> None:

        self._capability_registry = (
            capability_registry
            or DefaultCapabilityRegistry()
        )

    def build(
        self,
        instance,
        orchestrator,
        capability_manager,
        conversation_store=None,
        activation_manager=None,
        connector_manager=None,
    ) -> FlowForgeApplication:
        """
        Build an application from already prepared runtime components.

        This method remains available for compatibility and low-level use.
        """

        return FlowForgeApplication(
            instance=instance,
            orchestrator=orchestrator,
            capability_manager=capability_manager,
            conversation_store=conversation_store or ConversationStore(),
            activation_manager=activation_manager,
            connector_manager=connector_manager,
        )

    def build_from_instance(
        self,
        instance: Instance,
        conversation_store: ConversationStore | None = None,
    ) -> FlowForgeApplication:
        """
        Build a complete application from an Instance definition.
        """

        capability_manager = CapabilityManager()

        for capability_name in instance.capabilities:
            capability = self._capability_registry.create(
                capability_name
            )
            capability_manager.register(capability)

        orchestrator = ConversationOrchestrator(
            capability_manager
        )

        activation_factory = ActivationFactory()

        activation_manager = activation_factory.create(
            instance.activation,
        )

        return self.build(
            instance=instance,
            orchestrator=orchestrator,
            capability_manager=capability_manager,
            conversation_store=conversation_store,
            activation_manager=activation_manager,
        )