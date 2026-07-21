from __future__ import annotations

from chatbot.application.application import FlowForgeApplication
from chatbot.channels.channel import Channel
from chatbot.channels.message import IncomingMessage
from chatbot.channels.result import OutgoingMessage


class ApplicationChannel(Channel):
    """
    Channel adapter that connects transport-independent messages
    with FlowForgeApplication.
    """

    def __init__(
        self,
        application: FlowForgeApplication,
    ) -> None:
        self._application = application

    def receive(
        self,
        message: IncomingMessage,
    ) -> OutgoingMessage:

        response = self._application.chat(
            session_id=message.session_id,
            message=message.text,
        )

        return OutgoingMessage(
            text=response.text,
            metadata={
                **response.metadata,
                "sender_id": message.sender_id,
                "incoming_metadata": message.metadata,
            },
        )