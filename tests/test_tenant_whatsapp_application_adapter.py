from chatbot.connectors.whatsapp.application_adapter import (
    TenantFlowForgeWhatsAppAdapter,
)
from chatbot.connectors.whatsapp.message_handler import (
    IncomingWhatsAppMessage,
)


class RecordingTenantRouter:
    def __init__(
        self,
        client_id: str | None,
    ) -> None:
        self.client_id = client_id

    def resolve_client_id(
        self,
        message: IncomingWhatsAppMessage,
    ) -> str | None:
        return self.client_id


class RecordingApplication:
    def __init__(
        self,
    ) -> None:
        self.session_id: str | None = None
        self.message: str | None = None

    def chat(
        self,
        *,
        session_id: str,
        message: str,
    ) -> object:
        self.session_id = session_id
        self.message = message

        return type(
            "Response",
            (),
            {
                "text": "Respuesta del salón",
            },
        )()


class RecordingApplicationRegistry:
    def __init__(
        self,
        application: object | None,
    ) -> None:
        self.application = application
        self.client_id: str | None = None

    def get_application(
        self,
        client_id: str,
    ) -> object | None:
        self.client_id = client_id
        return self.application


def test_tenant_adapter_routes_message_to_resolved_application(
) -> None:
    application = RecordingApplication()
    registry = RecordingApplicationRegistry(
        application=application,
    )

    adapter = TenantFlowForgeWhatsAppAdapter(
        tenant_router=RecordingTenantRouter(
            client_id="hairdressing_demo",
        ),
        application_registry=registry,
    )

    response = adapter.handle(
        IncomingWhatsAppMessage(
            user_id="34600000000",
            text="Hola",
            phone_number_id=(
                "test-phone-number-id"
            ),
        )
    )

    assert response == "Respuesta del salón"
    assert registry.client_id == "hairdressing_demo"
    assert application.session_id == "34600000000"
    assert application.message == "Hola"