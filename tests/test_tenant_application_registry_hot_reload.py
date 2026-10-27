from __future__ import annotations

from copy import deepcopy

from chatbot.application.tenant_registry import (
    TenantApplicationRegistry,
)
from chatbot.instances import InstanceDefinition


class MutableDefinitionRepository:
    def __init__(
        self,
        definition: InstanceDefinition | None,
    ) -> None:
        self.definition = definition

    def get(
        self,
        client_id: str,
    ) -> InstanceDefinition | None:
        if self.definition is None:
            return None

        if self.definition.id != client_id:
            return None

        return deepcopy(
            self.definition
        )


def build_definition(
    *,
    greeting: str = "Hola original",
) -> InstanceDefinition:
    return InstanceDefinition(
        id="salon_centro",
        name="Salon Centro",
        template_id="hairdressing",
        settings={
            "knowledge": {
                "greetings": {
                    "welcome": {
                        "es": greeting,
                    },
                },
            },
        },
    )


def test_registry_reuses_runtime_when_definition_is_unchanged(
) -> None:
    repository = MutableDefinitionRepository(
        build_definition()
    )
    built_applications: list[object] = []

    def factory(
        definition: InstanceDefinition,
    ) -> object:
        application = object()
        built_applications.append(
            application
        )
        return application

    registry = TenantApplicationRegistry(
        instance_definition_repository=repository,
        application_factory=factory,
    )

    first = registry.get_application(
        "salon_centro"
    )
    second = registry.get_application(
        "salon_centro"
    )

    assert first is second
    assert len(built_applications) == 1


def test_registry_rebuilds_only_changed_tenant_definition(
) -> None:
    repository = MutableDefinitionRepository(
        build_definition(
            greeting="Hola original"
        )
    )
    built_definitions: list[
        InstanceDefinition
    ] = []

    def factory(
        definition: InstanceDefinition,
    ) -> object:
        built_definitions.append(
            deepcopy(definition)
        )
        return object()

    registry = TenantApplicationRegistry(
        instance_definition_repository=repository,
        application_factory=factory,
    )

    first = registry.get_application(
        "salon_centro"
    )

    repository.definition = build_definition(
        greeting="Hola actualizado"
    )

    second = registry.get_application(
        "salon_centro"
    )

    assert first is not second
    assert len(built_definitions) == 2
    assert (
        built_definitions[1]
        .settings["knowledge"]
        ["greetings"]["welcome"]["es"]
        == "Hola actualizado"
    )


def test_registry_detects_in_place_definition_changes(
) -> None:
    definition = build_definition()
    repository = MutableDefinitionRepository(
        definition
    )
    build_count = 0

    def factory(
        definition: InstanceDefinition,
    ) -> object:
        nonlocal build_count
        build_count += 1
        return object()

    registry = TenantApplicationRegistry(
        instance_definition_repository=repository,
        application_factory=factory,
    )

    first = registry.get_application(
        "salon_centro"
    )

    assert repository.definition is not None

    repository.definition.settings[
        "knowledge"
    ]["greetings"]["welcome"]["es"] = (
        "Cambio directo"
    )

    second = registry.get_application(
        "salon_centro"
    )

    assert first is not second
    assert build_count == 2


def test_registry_discards_runtime_when_definition_disappears(
) -> None:
    repository = MutableDefinitionRepository(
        build_definition()
    )
    build_count = 0

    def factory(
        definition: InstanceDefinition,
    ) -> object:
        nonlocal build_count
        build_count += 1
        return object()

    registry = TenantApplicationRegistry(
        instance_definition_repository=repository,
        application_factory=factory,
    )

    first = registry.get_application(
        "salon_centro"
    )

    repository.definition = None

    assert (
        registry.get_application(
            "salon_centro"
        )
        is None
    )

    repository.definition = build_definition(
        greeting="Tenant restaurado"
    )

    restored = registry.get_application(
        "salon_centro"
    )

    assert restored is not first
    assert build_count == 2
