from chatbot.connectors.whatsapp.message_handler import (
    IncomingWhatsAppMessage,
)
from chatbot.connectors.whatsapp.tenant_router import (
    WhatsAppTenantRouter,
)
from chatbot.instances import (
    InstanceDefinition,
    SQLiteInstanceDefinitionRepository,
)


def test_tenant_router_resolves_active_client_by_phone_number(
) -> None:
    repository = SQLiteInstanceDefinitionRepository(
        database_path=":memory:",
    )
    repository.save(
        InstanceDefinition(
            id="hairdressing_demo",
            name="Salón Estilo",
            template_id="hairdressing",
            whatsapp_phone_number_id=(
                "test-phone-number-id"
            ),
            metadata={
                "admin_status": "active",
            },
        )
    )

    router = WhatsAppTenantRouter(
        instance_definition_repository=repository,
    )

    client_id = router.resolve_client_id(
        IncomingWhatsAppMessage(
            user_id="34600000000",
            text="Hola",
            phone_number_id=(
                "test-phone-number-id"
            ),
        )
    )

    assert client_id == "hairdressing_demo"

    repository.close()
def test_tenant_router_rejects_unknown_phone_number(
) -> None:
    repository = SQLiteInstanceDefinitionRepository(
        database_path=":memory:",
    )
    router = WhatsAppTenantRouter(
        instance_definition_repository=repository,
    )

    client_id = router.resolve_client_id(
        IncomingWhatsAppMessage(
            user_id="34600000000",
            text="Hola",
            phone_number_id="unknown-phone-number-id",
        )
    )

    assert client_id is None

    repository.close()


def test_tenant_router_rejects_paused_client(
) -> None:
    repository = SQLiteInstanceDefinitionRepository(
        database_path=":memory:",
    )
    repository.save(
        InstanceDefinition(
            id="hairdressing_demo",
            name="Salón Estilo",
            template_id="hairdressing",
            whatsapp_phone_number_id=(
                "test-phone-number-id"
            ),
            metadata={
                "admin_status": "paused",
            },
        )
    )

    router = WhatsAppTenantRouter(
        instance_definition_repository=repository,
    )

    client_id = router.resolve_client_id(
        IncomingWhatsAppMessage(
            user_id="34600000000",
            text="Hola",
            phone_number_id=(
                "test-phone-number-id"
            ),
        )
    )

    assert client_id is None

    repository.close()