from chatbot.connectors.whatsapp.tenant_graph_sender import (
    TenantWhatsAppGraphSender,
)


class RecordingGraphClient:
    def __init__(
        self,
    ) -> None:
        self.to: str | None = None
        self.text: str | None = None

    def send_text_message(
        self,
        *,
        to: str,
        text: str,
    ) -> object:
        self.to = to
        self.text = text
        return object()


class RecordingGraphClientProvider:
    def __init__(
        self,
        graph_client: object | None,
    ) -> None:
        self.graph_client = graph_client
        self.phone_number_id: str | None = None

    def get_client(
        self,
        phone_number_id: str,
    ) -> object | None:
        self.phone_number_id = phone_number_id
        return self.graph_client


def test_tenant_graph_sender_uses_incoming_phone_number(
) -> None:
    graph_client = RecordingGraphClient()
    provider = RecordingGraphClientProvider(
        graph_client=graph_client,
    )
    sender = TenantWhatsAppGraphSender(
        graph_client_provider=provider,
    )

    sender.send_text(
        recipient="34600000000",
        text="Respuesta del salón",
        phone_number_id="test-phone-number-id",
    )

    assert provider.phone_number_id == (
        "test-phone-number-id"
    )
    assert graph_client.to == "34600000000"
    assert graph_client.text == "Respuesta del salón"