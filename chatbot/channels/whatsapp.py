from __future__ import annotations

from chatbot.channels.message import IncomingMessage
from chatbot.channels.result import OutgoingMessage


class WhatsAppChannel:
    def __init__(
        self,
        application_channel,
    ) -> None:
        self._application_channel = application_channel

    def process(
        self,
        *,
        phone_number: str,
        text: str,
        message_id: str,
        metadata: dict | None = None,
    ) -> OutgoingMessage:
        incoming_metadata = dict(
            metadata or {}
        )

        incoming_metadata.update({
            "channel": "whatsapp",
            "message_id": message_id,
            "phone_number": phone_number,
        })

        incoming = IncomingMessage(
            session_id=f"whatsapp:{phone_number}",
            text=text,
            sender_id=phone_number,
            metadata=incoming_metadata,
        )

        return self._application_channel.receive(
            incoming
        )