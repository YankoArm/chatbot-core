from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from threading import Lock
from typing import Protocol


@dataclass(frozen=True)
class IncomingWhatsAppMessage:
    user_id: str
    text: str
    message_id: str | None = None


class WhatsAppParserProtocol(Protocol):
    def parse(
        self,
        payload: dict[str, object],
    ) -> IncomingWhatsAppMessage:
        ...


class WhatsAppOrchestratorProtocol(Protocol):
    def handle(
        self,
        message: object,
    ) -> object:
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
        max_processed_message_ids: int = 10_000,
    ) -> None:
        if max_processed_message_ids <= 0:
            raise ValueError(
                "max_processed_message_ids must be positive"
            )

        self._parser = parser
        self._orchestrator = orchestrator
        self._sender = sender
        self._max_processed_message_ids = (
            max_processed_message_ids
        )
        self._processed_message_ids: set[str] = set()
        self._processed_message_order: deque[str] = deque()
        self._processing_lock = Lock()

    def handle(
        self,
        payload: dict[str, object],
    ) -> object | None:
        if self._parser is None:
            return None

        parsed_message = self._parser.parse(
            payload
        )

        if self._orchestrator is None:
            return parsed_message

        with self._processing_lock:
            message_id = parsed_message.message_id

            if (
                message_id is not None
                and message_id
                in self._processed_message_ids
            ):
                return None

            response = self._orchestrator.handle(
                parsed_message
            )

            if self._sender is not None:
                self._sender.send_text(
                    recipient=parsed_message.user_id,
                    text=str(response),
                )

            if message_id is not None:
                self._remember_processed_message_id(
                    message_id
                )

            return response

    def _remember_processed_message_id(
        self,
        message_id: str,
    ) -> None:
        if message_id in self._processed_message_ids:
            return

        self._processed_message_ids.add(
            message_id
        )
        self._processed_message_order.append(
            message_id
        )

        while (
            len(self._processed_message_order)
            > self._max_processed_message_ids
        ):
            expired_message_id = (
                self._processed_message_order.popleft()
            )
            self._processed_message_ids.remove(
                expired_message_id
            )