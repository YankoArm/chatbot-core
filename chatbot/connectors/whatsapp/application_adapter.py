from __future__ import annotations

from typing import Protocol

from chatbot.connectors.whatsapp.message_handler import (
    IncomingWhatsAppMessage,
)
from chatbot.responses import Response


class FlowForgeApplicationProtocol(Protocol):
    def chat(
        self,
        session_id: str,
        message: str,
    ) -> Response:
        ...


class FlowForgeWhatsAppAdapter:
    """
    Adapt WhatsApp messages to the FlowForge application interface.

    The WhatsApp user identifier is used as the conversation session
    identifier so subsequent messages from the same phone number reuse
    the same conversation context.
    """

    def __init__(
        self,
        application: FlowForgeApplicationProtocol,
    ) -> None:
        self._application = application

    def handle(
        self,
        message: IncomingWhatsAppMessage,
    ) -> str:
        response = self._application.chat(
            session_id=message.user_id,
            message=message.text,
        )

        return response.text