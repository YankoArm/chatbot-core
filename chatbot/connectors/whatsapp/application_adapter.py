from __future__ import annotations

from collections.abc import Callable
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
        is_active: Callable[[], bool] | None = None,
    ) -> None:
        self._application = application
        self._is_active = is_active or (
            lambda: True
        )

    def handle(
        self,
        message: IncomingWhatsAppMessage,
    ) -> str | None:
        if not self._is_active():
            return None

        response = self._application.chat(
            session_id=message.user_id,
            message=message.text,
        )

        return response.text