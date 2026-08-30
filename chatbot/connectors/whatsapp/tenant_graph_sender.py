from __future__ import annotations

from typing import Protocol

from chatbot.connectors.whatsapp.graph_sender import (
    WhatsAppGraphClientProtocol,
)


class WhatsAppGraphClientProviderProtocol(Protocol):
    def get_client(
        self,
        phone_number_id: str,
    ) -> WhatsAppGraphClientProtocol | None:
        ...


class TenantWhatsAppGraphSender:
    """
    Send replies through the WhatsApp number that received the message.
    """

    def __init__(
        self,
        *,
        graph_client_provider: (
            WhatsAppGraphClientProviderProtocol
        ),
    ) -> None:
        self._graph_client_provider = (
            graph_client_provider
        )

    def send_text(
        self,
        *,
        recipient: str,
        text: str,
        phone_number_id: str | None,
    ) -> None:
        if phone_number_id is None:
            return

        graph_client = (
            self._graph_client_provider.get_client(
                phone_number_id
            )
        )

        if graph_client is None:
            return

        graph_client.send_text_message(
            to=recipient,
            text=text,
        )