from __future__ import annotations

from chatbot.channels import (
    ApplicationChannel,
    IncomingMessage,
)
from chatbot.responses import Response


class FakeApplication:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def chat(
        self,
        session_id: str,
        message: str,
    ) -> Response:

        self.calls.append(
            (session_id, message)
        )

        return Response(
            text=f"response:{message}",
            metadata={
                "capability": "fake",
            },
        )


def test_application_channel_sends_message_to_application() -> None:
    application = FakeApplication()
    channel = ApplicationChannel(application)

    outgoing = channel.receive(
        IncomingMessage(
            session_id="session-1",
            text="Hola",
            sender_id="user-1",
            metadata={
                "channel": "web",
            },
        )
    )

    assert application.calls == [
        ("session-1", "Hola")
    ]

    assert outgoing.text == "response:Hola"


def test_application_channel_preserves_response_metadata() -> None:
    application = FakeApplication()
    channel = ApplicationChannel(application)

    outgoing = channel.receive(
        IncomingMessage(
            session_id="session-1",
            text="Hola",
        )
    )

    assert outgoing.metadata["capability"] == "fake"


def test_application_channel_adds_sender_id() -> None:
    application = FakeApplication()
    channel = ApplicationChannel(application)

    outgoing = channel.receive(
        IncomingMessage(
            session_id="session-1",
            text="Hola",
            sender_id="user-123",
        )
    )

    assert outgoing.metadata["sender_id"] == "user-123"


def test_application_channel_preserves_incoming_metadata() -> None:
    application = FakeApplication()
    channel = ApplicationChannel(application)

    outgoing = channel.receive(
        IncomingMessage(
            session_id="session-1",
            text="Hola",
            metadata={
                "channel": "telegram",
                "chat_id": 123,
            },
        )
    )

    assert outgoing.metadata["incoming_metadata"] == {
        "channel": "telegram",
        "chat_id": 123,
    }