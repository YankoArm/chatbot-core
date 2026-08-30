from typing import Protocol

from chatbot.connectors.whatsapp.graph_client import WhatsAppMessageResponse


class WhatsAppGraphClientProtocol(Protocol):
    def send_text_message(
        self,
        *,
        to: str,
        text: str,
    ) -> WhatsAppMessageResponse:
        ...


class WhatsAppGraphSender:
    def __init__(
        self,
        *,
        graph_client: WhatsAppGraphClientProtocol,
    ) -> None:
        self._graph_client = graph_client

    def send_text(
        self,
        recipient: str,
        text: str,
        phone_number_id: str | None = None,
    ) -> None:
        self._graph_client.send_text_message(
            to=recipient,
            text=text,
        )