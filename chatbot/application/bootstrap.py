from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from chatbot.activation import ActivationFactory
from chatbot.application.application import FlowForgeApplication
from chatbot.capabilities.base_capability import BaseCapability
from chatbot.capabilities.capability_manager import CapabilityManager
from chatbot.conversation import (
    ConversationContextFactory,
    ConversationOrchestrator,
    ConversationStore,
)
from chatbot.instances import (
    Instance,
    InstanceDefinition,
    InstanceResolver,
    TemplateDefinition,
)
from chatbot.knowledge import KnowledgeServiceFactory
from chatbot.language import (
    BaseLanguageDetector,
    RuleBasedLanguageDetector,
)
from chatbot.registry import (
    CapabilityRegistry,
    DefaultCapabilityRegistry,
)


CapabilityFactory = Callable[[], BaseCapability]


class Bootstrap:
    """
    Build fully configured FlowForge application runtimes.

    Bootstrap is the application's composition root. It creates and connects
    infrastructure components, capabilities, conversation services, activation
    services, knowledge services and language detection.

    Capability factories may be supplied to inject dependencies into selected
    capabilities without coupling Bootstrap to concrete business services.

    It can build an application from either:

    - A fully resolved Instance.
    - A TemplateDefinition combined with an InstanceDefinition.

    Business logic must not be implemented here.
    """

    def __init__(
        self,
        capability_registry: CapabilityRegistry | None = None,
        language_detector: BaseLanguageDetector | None = None,
        activation_factory: ActivationFactory | None = None,
        instance_resolver: InstanceResolver | None = None,
        knowledge_service_factory: (
            KnowledgeServiceFactory | None
        ) = None,
        capability_factories: (
            Mapping[str, CapabilityFactory] | None
        ) = None,
        knowledge_root: str | Path = "knowledge",
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

        self._instance_resolver = (
            instance_resolver
            or InstanceResolver()
        )

        self._knowledge_service_factory = (
            knowledge_service_factory
            or KnowledgeServiceFactory(
                knowledge_root=knowledge_root,
            )
        )

        self._capability_factories = self._normalize_capability_factories(
            capability_factories
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
        context_factory: ConversationContextFactory | None = None,
    ) -> FlowForgeApplication:
        """
        Build an application from prepared runtime components.

        This low-level method is intended for tests, custom deployments and
        advanced integrations that supply their own runtime services.
        """

        self._validate_instance(instance)

        selected_language_detector = (
            language_detector
            or self._language_detector
        )

        selected_conversation_store = (
            conversation_store
            or ConversationStore()
        )

        selected_context_factory = (
            context_factory
            or self._build_context_factory()
        )

        return FlowForgeApplication(
            instance=instance,
            orchestrator=orchestrator,
            capability_manager=capability_manager,
            conversation_store=selected_conversation_store,
            activation_manager=activation_manager,
            connector_manager=connector_manager,
            language_detector=selected_language_detector,
            context_factory=selected_context_factory,
        )

    def build_from_instance(
        self,
        instance: Instance,
        conversation_store: ConversationStore | None = None,
        connector_manager: Any | None = None,
        language_detector: BaseLanguageDetector | None = None,
    ) -> FlowForgeApplication:
        """
        Build a complete application from a resolved Instance.

        Capabilities, orchestration, activation, knowledge access and language
        detection are created and connected automatically.
        """

        self._validate_instance(instance)

        capability_manager = self._build_capability_manager(
            instance
        )

        orchestrator = ConversationOrchestrator(
            capability_manager=capability_manager,
        )

        activation_manager = self._build_activation_manager(
            instance
        )

        context_factory = self._build_context_factory()

        return self.build(
            instance=instance,
            orchestrator=orchestrator,
            capability_manager=capability_manager,
            conversation_store=conversation_store,
            activation_manager=activation_manager,
            connector_manager=connector_manager,
            language_detector=language_detector,
            context_factory=context_factory,
        )

    def build_from_definition(
        self,
        template: TemplateDefinition,
        definition: InstanceDefinition,
        conversation_store: ConversationStore | None = None,
        connector_manager: Any | None = None,
        language_detector: BaseLanguageDetector | None = None,
    ) -> FlowForgeApplication:
        """
        Resolve a template and client definition, then build the application.

        This is the preferred entry point for client-specific deployments.
        The resolver combines template defaults with instance overrides and
        produces the final resolved Instance consumed by the runtime.
        """

        instance = self._instance_resolver.resolve(
            template=template,
            definition=definition,
        )

        return self.build_from_instance(
            instance=instance,
            conversation_store=conversation_store,
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

            capability = self._create_capability(
                normalized_name
            )

            capability_manager.register(capability)
            registered_names.add(normalized_name)

        return capability_manager

    def _create_capability(
        self,
        capability_name: str,
    ) -> BaseCapability:
        """
        Create a capability using an injected factory when available.

        Capabilities without a custom factory continue to be created through
        the configured capability registry.
        """

        capability_factory = self._capability_factories.get(
            capability_name
        )

        if capability_factory is None:
            return self._capability_registry.create(
                capability_name
            )

        capability = capability_factory()

        if not isinstance(
            capability,
            BaseCapability,
        ):
            raise TypeError(
                "Capability factory must return a BaseCapability "
                f"instance for {capability_name!r}."
            )

        if capability.name != capability_name:
            raise ValueError(
                "Capability factory returned an unexpected capability: "
                f"expected {capability_name!r}, "
                f"received {capability.name!r}."
            )

        return capability

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

    def _build_context_factory(
        self,
    ) -> ConversationContextFactory:
        """
        Create the conversation context factory.

        The factory assigns each conversation the knowledge service belonging
        to its active FlowForge instance.
        """

        return ConversationContextFactory(
            knowledge_service_factory=(
                self._knowledge_service_factory
            ),
        )

    @staticmethod
    def _normalize_capability_factories(
        capability_factories: (
            Mapping[str, CapabilityFactory] | None
        ),
    ) -> dict[str, CapabilityFactory]:
        """
        Validate and normalize injected capability factories.
        """

        if capability_factories is None:
            return {}

        normalized_factories: dict[
            str,
            CapabilityFactory,
        ] = {}

        for capability_name, capability_factory in (
            capability_factories.items()
        ):
            normalized_name = capability_name.strip()

            if not normalized_name:
                raise ValueError(
                    "Capability factory names cannot be empty."
                )

            if not callable(capability_factory):
                raise TypeError(
                    "Capability factory must be callable for "
                    f"{normalized_name!r}."
                )

            if normalized_name in normalized_factories:
                raise ValueError(
                    "Duplicate capability factory configured for "
                    f"{normalized_name!r}."
                )

            normalized_factories[
                normalized_name
            ] = capability_factory

        return normalized_factories

    @staticmethod
    def _validate_instance(
        instance: Instance,
    ) -> None:
        """
        Validate the minimum data required to build a runtime.
        """

        if not isinstance(instance, Instance):
            raise TypeError(
                "Bootstrap requires a resolved Instance object."
            )

        if not instance.id.strip():
            raise ValueError(
                "Instance id cannot be empty."
            )

        if not instance.name.strip():
            raise ValueError(
                "Instance name cannot be empty."
            )