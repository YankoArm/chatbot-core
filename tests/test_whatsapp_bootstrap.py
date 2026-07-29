from chatbot.connectors.whatsapp.bootstrap import (
    build_whatsapp_message_handler,
)
from chatbot.connectors.whatsapp.message_handler import (
    WhatsAppMessageHandler,
)


def test_build_whatsapp_message_handler_returns_handler() -> None:
    handler = build_whatsapp_message_handler(
        application=object(),
        graph_client=object(),
    )

    assert isinstance(
        handler,
        WhatsAppMessageHandler,
    )