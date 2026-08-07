from typing import Protocol
from dataclasses import dataclass

@dataclass(frozen=True)
class IncomingWhatsAppMessage:
    user_id: str
    text: str

class WhatsAppParserProtocol(Protocol):
    def parse(
        self,
        payload: dict[str, object],
    ) -> IncomingWhatsAppMessage:
        ...

class WhatsAppOrchestratorProtocol(Protocol):
    def handle(self, message: object) -> object:
        ...

class WhatsAppSenderProtocol(Protocol):
    def send_text(
        self,
        recipient: str,
        text: str,
    ) -> None:
        ...

class WhatsAppMessageHandler:
    def __init__(
        self,
        parser: WhatsAppParserProtocol | None = None,
        orchestrator: WhatsAppOrchestratorProtocol | None = None,
        sender: WhatsAppSenderProtocol | None = None,
    ) -> None:
        self._parser = parser
        self._orchestrator = orchestrator
        self._sender = sender

    def handle(
        self,
        payload: dict[str, object],
    ) -> object | None:
        if self._parser is None:
            return None

        parsed_message = self._parser.parse(payload)

        if self._orchestrator is None:
            return parsed_message

        response = self._orchestrator.handle(parsed_message)

        if self._sender is not None:
            self._sender.send_text(
                recipient=parsed_message.user_id,
                text=str(response),
            )

        return response
