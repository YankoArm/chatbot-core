from __future__ import annotations

from typing import Any

from chatbot.activation import ActivationFactory
from chatbot.application.application import FlowForgeApplication
from chatbot.capabilities.capability_manager import CapabilityManager
from chatbot.conversation import (
    ConversationOrchestrator,
    ConversationStore,
)
from chatbot.instances import Instance
from chatbot.language import (
    BaseLanguageDetector,
    RuleBasedLanguageDetector,
)
from chatbot.registry import (
    CapabilityRegistry,
    DefaultCapabilityRegistry,
)


class Bootstrap:
    """
    Build fully configured FlowForge application runtimes.

    Bootstrap acts as the composition root of the application. It creates and
    connects infrastructure components, capability instances, conversation
    services, activation services and language detection.

    Business logic must not be implemented here.
    """

    def __init__(
        self,
        capability_registry: CapabilityRegistry | None = None,
        language_detector: BaseLanguageDetector | None = None,
        activation_factory: ActivationFactory | None = None,
    ) -> None:
        self._capability_registry = (
            capability_registry
            or DefaultCapabilityRegistry()
        )

        self._language_detector = (
            language_detector
            or RuleBasedLanguageDetector()
        )

        self._activation_factory = (
            activation_factory
            or ActivationFactory()
        )

    def build(
        self,
        instance: Instance,
        orchestrator: ConversationOrchestrator,
        capability_manager: CapabilityManager,
        conversation_store: ConversationStore | None = None,
        activation_manager: Any | None = None,
        connector_manager: Any | None = None,
        language_detector: BaseLanguageDetector | None = None,
    ) -> FlowForgeApplication:
        """
        Build an application from prepared runtime components.

        This low-level method is useful for tests, custom deployments and
        advanced integrations that need to supply their own runtime services.
        """

        selected_language_detector = (
            language_detector
            or self._language_detector
        )

        selected_conversation_store = (
            conversation_store
            or ConversationStore()
        )

        return FlowForgeApplication(
            instance=instance,
            orchestrator=orchestrator,
            capability_manager=capability_manager,
            conversation_store=selected_conversation_store,
            activation_manager=activation_manager,
            connector_manager=connector_manager,
            language_detector=selected_language_detector,
        )

    def build_from_instance(
        self,
        instance: Instance,
        conversation_store: ConversationStore | None = None,
        connector_manager: Any | None = None,
        language_detector: BaseLanguageDetector | None = None,
    ) -> FlowForgeApplication:
        """
        Build a complete application from a declarative Instance definition.

        Capabilities, orchestration, activation and language detection are
        created and connected automatically.
        """

        capability_manager = self._build_capability_manager(
            instance
        )

        orchestrator = ConversationOrchestrator(
            capability_manager=capability_manager,
        )

        activation_manager = self._build_activation_manager(
            instance
        )

        return self.build(
            instance=instance,
            orchestrator=orchestrator,
            capability_manager=capability_manager,
            conversation_store=conversation_store,
            activation_manager=activation_manager,
            connector_manager=connector_manager,
            language_detector=language_detector,
        )

    def _build_capability_manager(
        self,
        instance: Instance,
    ) -> CapabilityManager:
        """
        Create and populate the capability manager for an instance.
        """

        capability_manager = CapabilityManager()

        registered_names: set[str] = set()

        for capability_name in instance.capabilities:
            normalized_name = capability_name.strip()

            if not normalized_name:
                raise ValueError(
                    "Instance capability names cannot be empty."
                )

            if normalized_name in registered_names:
                raise ValueError(
                    "Duplicate capability configured in instance: "
                    f"{normalized_name!r}."
                )

            capability = self._capability_registry.create(
                normalized_name
            )

            capability_manager.register(capability)
            registered_names.add(normalized_name)

        return capability_manager

    def _build_activation_manager(
        self,
        instance: Instance,
    ) -> Any:
        """
        Create the activation manager configured for an instance.
        """

        return self._activation_factory.create(
            instance.activation
        )