
from chatbot.connectors.whatsapp.message_handler import (
    IncomingWhatsAppMessage,
    WhatsAppMessageHandler,
)

from chatbot.application import Bootstrap
from chatbot.capabilities.booking.capability import BookingCapability
from chatbot.instances import Instance
from chatbot.registry import CapabilityRegistry

from chatbot.connectors.whatsapp.application_adapter import (
    FlowForgeWhatsAppAdapter,
)
from chatbot.responses import Response

from chatbot.connectors.whatsapp.graph_sender import WhatsAppGraphSender
from chatbot.connectors.whatsapp.graph_client import WhatsAppMessageResponse
from chatbot.connectors.whatsapp.parser import WhatsAppPayloadParser

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
    ) -> IncomingWhatsAppMessage:
        return IncomingWhatsAppMessage(
            user_id="123",
            text="Hola",
        )

def test_whatsapp_message_handler_returns_parser_result() -> None:
    parser = ReturningParser()
    handler = WhatsAppMessageHandler(parser=parser)

    result = handler.handle(
        {
            "entry": [],
        }
    )

    assert result == IncomingWhatsAppMessage(
        user_id="123",
        text="Hola",
    )

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

    assert orchestrator.received_message == IncomingWhatsAppMessage(
        user_id="123",
        text="Hola",
    )

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

def test_whatsapp_message_handler_passes_typed_message_to_orchestrator() -> None:
    parser = ReturningParser()
    orchestrator = RecordingOrchestrator()

    handler = WhatsAppMessageHandler(
        parser=parser,
        orchestrator=orchestrator,
    )

    handler.handle({"entry": []})

    assert isinstance(
        orchestrator.received_message,
        IncomingWhatsAppMessage,
    )

class RecordingSender:
    def __init__(self) -> None:
        self.recipient: str | None = None
        self.text: str | None = None

    def send_text(
        self,
        recipient: str,
        text: str,
    ) -> None:
        self.recipient = recipient
        self.text = text

def test_whatsapp_message_handler_sends_orchestrator_response() -> None:
    parser = ReturningParser()
    orchestrator = RecordingOrchestrator()
    sender = RecordingSender()

    handler = WhatsAppMessageHandler(
        parser=parser,
        orchestrator=orchestrator,
        sender=sender,
    )

    handler.handle({"entry": []})

    assert sender.recipient == "123"
    assert sender.text == "OK"

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

def test_whatsapp_message_handler_sends_response_through_graph_sender() -> None:
    parser = ReturningParser()
    orchestrator = RecordingOrchestrator()
    graph_client = RecordingGraphClient()

    sender = WhatsAppGraphSender(
        graph_client=graph_client,
    )

    handler = WhatsAppMessageHandler(
        parser=parser,
        orchestrator=orchestrator,
        sender=sender,
    )

    result = handler.handle({"entry": []})

    assert result == "OK"
    assert graph_client.to == "123"
    assert graph_client.text == "OK"

def test_whatsapp_message_handler_processes_real_meta_payload() -> None:
    parser = WhatsAppPayloadParser()
    orchestrator = RecordingOrchestrator()
    graph_client = RecordingGraphClient()

    sender = WhatsAppGraphSender(
        graph_client=graph_client,
    )

    handler = WhatsAppMessageHandler(
        parser=parser,
        orchestrator=orchestrator,
        sender=sender,
    )

    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "from": "34600000000",
                                    "text": {
                                        "body": "Hola",
                                    },
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }

    result = handler.handle(payload)

    assert result == "OK"
    assert orchestrator.received_message == IncomingWhatsAppMessage(
        user_id="34600000000",
        text="Hola",
    )
    assert graph_client.to == "34600000000"
    assert graph_client.text == "OK"

class RecordingFlowForgeApplication:
    def __init__(self) -> None:
        self.session_id: str | None = None
        self.message: str | None = None

    def chat(
        self,
        session_id: str,
        message: str,
    ) -> Response:
        self.session_id = session_id
        self.message = message

        return Response(
            text="Respuesta real de FlowForge",
        )

def test_whatsapp_message_handler_uses_flowforge_application() -> None:
    application = RecordingFlowForgeApplication()
    graph_client = RecordingGraphClient()

    handler = WhatsAppMessageHandler(
        parser=WhatsAppPayloadParser(),
        orchestrator=FlowForgeWhatsAppAdapter(
            application=application,
        ),
        sender=WhatsAppGraphSender(
            graph_client=graph_client,
        ),
    )

    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "from": "34600000000",
                                    "text": {
                                        "body": "Quiero reservar una cita",
                                    },
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }

    result = handler.handle(payload)

    assert application.session_id == "34600000000"
    assert application.message == "Quiero reservar una cita"

    assert result == "Respuesta real de FlowForge"

    assert graph_client.to == "34600000000"
    assert graph_client.text == "Respuesta real de FlowForge"

def build_booking_application():
    registry = CapabilityRegistry()
    registry.register(BookingCapability)

    instance = Instance(
        id="tarot_esmeralda",
        name="Tarot Esmeralda",
        capabilities=["booking"],
    )

    bootstrap = Bootstrap(
        capability_registry=registry,
    )

    return bootstrap.build_from_instance(instance)

def test_whatsapp_message_handler_processes_message_with_real_flowforge() -> None:
    application = build_booking_application()
    graph_client = RecordingGraphClient()

    handler = WhatsAppMessageHandler(
        parser=WhatsAppPayloadParser(),
        orchestrator=FlowForgeWhatsAppAdapter(
            application=application,
        ),
        sender=WhatsAppGraphSender(
            graph_client=graph_client,
        ),
    )

    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "from": "34600000000",
                                    "text": {
                                        "body": "Quiero reservar una cita",
                                    },
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }

    result = handler.handle(payload)

    expected_response = (
        "Perfecto. Vamos a reservar una cita. "
        "¿Cómo te llamas?"
    )

    assert result == expected_response
    assert graph_client.to == "34600000000"
    assert graph_client.text == expected_response