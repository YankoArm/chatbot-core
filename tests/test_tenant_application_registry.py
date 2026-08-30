from chatbot.application.tenant_registry import (
    TenantApplicationRegistry,
)
from chatbot.instances import (
    InstanceDefinition,
    SQLiteInstanceDefinitionRepository,
)


def test_tenant_application_registry_builds_and_caches_client_runtime(
) -> None:
    repository = SQLiteInstanceDefinitionRepository(
        database_path=":memory:",
    )
    definition = InstanceDefinition(
        id="hairdressing_demo",
        name="Salón Estilo",
        template_id="hairdressing",
    )
    repository.save(
        definition
    )

    built_definitions: list[
        InstanceDefinition
    ] = []
    application = object()

    def build_application(
        received_definition: InstanceDefinition,
    ) -> object:
        built_definitions.append(
            received_definition
        )
        return application

    registry = TenantApplicationRegistry(
        instance_definition_repository=repository,
        application_factory=build_application,
    )

    first_application = registry.get_application(
        "hairdressing_demo"
    )
    second_application = registry.get_application(
        "hairdressing_demo"
    )

    assert first_application is application
    assert second_application is application
    assert built_definitions == [
        definition,
    ]

    repository.close()
def test_tenant_application_registry_returns_none_for_unknown_client(
) -> None:
    repository = SQLiteInstanceDefinitionRepository(
        database_path=":memory:",
    )
    built_definitions: list[
        InstanceDefinition
    ] = []

    def build_application(
        definition: InstanceDefinition,
    ) -> object:
        built_definitions.append(
            definition
        )
        return object()

    registry = TenantApplicationRegistry(
        instance_definition_repository=repository,
        application_factory=build_application,
    )

    assert registry.get_application(
        "unknown-client"
    ) is None
    assert built_definitions == []

    repository.close()


def test_tenant_application_registry_isolates_client_runtimes(
) -> None:
    repository = SQLiteInstanceDefinitionRepository(
        database_path=":memory:",
    )
    repository.save(
        InstanceDefinition(
            id="salon_norte",
            name="Salón Norte",
            template_id="hairdressing",
        )
    )
    repository.save(
        InstanceDefinition(
            id="salon_sur",
            name="Salón Sur",
            template_id="hairdressing",
        )
    )

    applications_by_client: dict[
        str,
        object,
    ] = {}

    def build_application(
        definition: InstanceDefinition,
    ) -> object:
        application = object()
        applications_by_client[
            definition.id
        ] = application
        return application

    registry = TenantApplicationRegistry(
        instance_definition_repository=repository,
        application_factory=build_application,
    )

    norte = registry.get_application(
        "salon_norte"
    )
    sur = registry.get_application(
        "salon_sur"
    )

    assert norte is applications_by_client[
        "salon_norte"
    ]
    assert sur is applications_by_client[
        "salon_sur"
    ]
    assert norte is not sur

    repository.close()