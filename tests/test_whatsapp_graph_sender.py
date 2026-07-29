from chatbot.connectors.whatsapp.graph_client import WhatsAppMessageResponse
from chatbot.connectors.whatsapp.graph_sender import WhatsAppGraphSender


class RecordingGraphClient:
    def __init__(self) -> None:
        self.to: str | None = None
        self.text: str | None = None

    def send_text_message(
        self,
        *,
        to: str,
        text: str,
    ) -> WhatsAppMessageResponse:
        self.to = to
        self.text = text

        return WhatsAppMessageResponse(
            message_id="message-123",
        )


def test_whatsapp_graph_sender_delegates_to_graph_client() -> None:
    graph_client = RecordingGraphClient()
    sender = WhatsAppGraphSender(
        graph_client=graph_client,
    )

    sender.send_text(
        recipient="34600000000",
        text="Hola",
    )

    assert graph_client.to == "34600000000"
    assert graph_client.text == "Hola"