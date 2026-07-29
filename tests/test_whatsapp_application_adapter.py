from chatbot.connectors.whatsapp.application_adapter import (
    FlowForgeWhatsAppAdapter,
)
from chatbot.connectors.whatsapp.message_handler import (
    IncomingWhatsAppMessage,
)
from chatbot.responses import Response


class RecordingApplication:
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
            text="Hola, ¿en qué puedo ayudarte?",
        )


def test_whatsapp_application_adapter_delegates_to_flowforge() -> None:
    application = RecordingApplication()

    adapter = FlowForgeWhatsAppAdapter(
        application=application,
    )

    result = adapter.handle(
        IncomingWhatsAppMessage(
            user_id="34600000000",
            text="Hola",
        )
    )

    assert application.session_id == "34600000000"
    assert application.message == "Hola"
    assert result == "Hola, ¿en qué puedo ayudarte?"