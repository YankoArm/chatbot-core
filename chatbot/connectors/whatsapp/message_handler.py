from typing import Protocol
from dataclasses import dataclass

class WhatsAppParserProtocol(Protocol):
    def parse(
        self,
        payload: dict[str, object],
    ) -> object:
        ...

class WhatsAppOrchestratorProtocol(Protocol):
    def handle(self, message: object) -> object:
        ...

@dataclass(frozen=True)
class IncomingWhatsAppMessage:
    user_id: str
    text: str

class WhatsAppMessageHandler:
    def __init__(
        self,
        parser: WhatsAppParserProtocol | None = None,
        orchestrator: WhatsAppOrchestratorProtocol | None = None,
    ) -> None:
        self._parser = parser
        self._orchestrator = orchestrator

    def handle(self, payload: dict[str, object]) -> object | None:
        if self._parser is None:
            return None

        parsed_message = self._parser.parse(payload)

        if self._orchestrator is None:
            return parsed_message

        return self._orchestrator.handle(parsed_message)


