
from chatbot.connectors.whatsapp.message_handler import (
    IncomingWhatsAppMessage,
    WhatsAppMessageHandler,
)

def test_whatsapp_message_handler_can_be_created() -> None:
    handler = WhatsAppMessageHandler()

    assert handler is not None

def test_whatsapp_message_handler_accepts_payload() -> None:
    handler = WhatsAppMessageHandler()

    result = handler.handle(
        {
            "entry": [],
        }
    )

    assert result is None

class RecordingParser:
    def __init__(self) -> None:
        self.received_payload: dict[str, object] | None = None

    def parse(self, payload: dict[str, object]) -> None:
        self.received_payload = payload


def test_whatsapp_message_handler_uses_parser() -> None:
    parser = RecordingParser()
    handler = WhatsAppMessageHandler(parser=parser)

    payload = {
        "entry": [],
    }

    handler.handle(payload)

    assert parser.received_payload == payload

class ReturningParser:
    def parse(
        self,
        payload: dict[str, object],
    ) -> dict[str, object]:
        return {
            "user_id": "123",
            "text": "Hola",
        }


def test_whatsapp_message_handler_returns_parser_result() -> None:
    parser = ReturningParser()
    handler = WhatsAppMessageHandler(parser=parser)

    result = handler.handle(
        {
            "entry": [],
        }
    )

    assert result == {
        "user_id": "123",
        "text": "Hola",
    }

class RecordingOrchestrator:
    def __init__(self) -> None:
        self.received_message: object | None = None

    def handle(self, message: object) -> str:
        self.received_message = message
        return "OK"


def test_whatsapp_message_handler_passes_parsed_message_to_orchestrator() -> None:
    parser = ReturningParser()
    orchestrator = RecordingOrchestrator()

    handler = WhatsAppMessageHandler(
        parser=parser,
        orchestrator=orchestrator,
    )

    handler.handle(
        {
            "entry": [],
        }
    )

    assert orchestrator.received_message == {
        "user_id": "123",
        "text": "Hola",
    }

def test_whatsapp_message_handler_returns_orchestrator_response() -> None:
    parser = ReturningParser()
    orchestrator = RecordingOrchestrator()

    handler = WhatsAppMessageHandler(
        parser=parser,
        orchestrator=orchestrator,
    )

    result = handler.handle(
        {
            "entry": [],
        }
    )

    assert result == "OK"

def test_incoming_whatsapp_message_stores_user_id_and_text() -> None:
    message = IncomingWhatsAppMessage(
        user_id="123",
        text="Hola",
    )

    assert message.user_id == "123"
    assert message.text == "Hola"