from typing import Protocol

from chatbot.connectors.whatsapp.application_adapter import (
    FlowForgeWhatsAppAdapter,
)
from chatbot.connectors.whatsapp.graph_sender import (
    WhatsAppGraphSender,
)
from chatbot.connectors.whatsapp.message_handler import (
    WhatsAppMessageHandler,
)
from chatbot.connectors.whatsapp.parser import (
    WhatsAppPayloadParser,
)


class FlowForgeApplicationProtocol(Protocol):
    def chat(
        self,
        *,
        session_id: str,
        message: str,
    ) -> object:
        ...


class WhatsAppGraphClientProtocol(Protocol):
    def send_text_message(
        self,
        *,
        recipient: str,
        text: str,
    ) -> object:
        ...


def build_whatsapp_message_handler(
    *,
    application: FlowForgeApplicationProtocol,
    graph_client: WhatsAppGraphClientProtocol,
) -> WhatsAppMessageHandler:
    parser = WhatsAppPayloadParser()

    orchestrator = FlowForgeWhatsAppAdapter(
        application=application,
    )

    sender = WhatsAppGraphSender(
        graph_client=graph_client,
    )

    return WhatsAppMessageHandler(
        parser=parser,
        orchestrator=orchestrator,
        sender=sender,
    )