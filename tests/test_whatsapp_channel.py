from __future__ import annotations

from chatbot.channels import (
    OutgoingMessage,
    WhatsAppChannel,
)


class FakeApplicationChannel:
    def __init__(self) -> None:
        self.messages = []

    def receive(self, message) -> OutgoingMessage:
        self.messages.append(message)

        return OutgoingMessage(
            text=f"response:{message.text}",
        )


def test_process_creates_whatsapp_incoming_message() -> None:
    application_channel = FakeApplicationChannel()
    channel = WhatsAppChannel(application_channel)

    outgoing = channel.process(
        phone_number="34600123123",
        text="Hola",
        message_id="wamid-123",
    )

    assert outgoing.text == "response:Hola"

    assert len(application_channel.messages) == 1

    incoming = application_channel.messages[0]

    assert incoming.session_id == "whatsapp:34600123123"
    assert incoming.sender_id == "34600123123"
    assert incoming.text == "Hola"
    assert incoming.metadata == {
        "channel": "whatsapp",
        "message_id": "wamid-123",
        "phone_number": "34600123123",
    }

def test_process_creates_whatsapp_metadata() -> None:
    application_channel = FakeApplicationChannel()
    channel = WhatsAppChannel(application_channel)

    channel.process(
        phone_number="34600123123",
        text="Hola",
        message_id="wamid-999",
    )

    incoming = application_channel.messages[0]

    assert incoming.metadata["channel"] == "whatsapp"
    assert incoming.metadata["phone_number"] == "34600123123"
    assert incoming.metadata["message_id"] == "wamid-999"

def test_process_preserves_provider_metadata() -> None:
    application_channel = FakeApplicationChannel()
    channel = WhatsAppChannel(application_channel)

    channel.process(
        phone_number="34600123123",
        text="Hola",
        message_id="wamid-123",
        metadata={
            "profile_name": "Yanko",
            "phone_number_id": "business-456",
        },
    )

    incoming = application_channel.messages[0]

    assert incoming.metadata == {
        "profile_name": "Yanko",
        "phone_number_id": "business-456",
        "channel": "whatsapp",
        "message_id": "wamid-123",
        "phone_number": "34600123123",
    }

def test_process_protects_required_metadata() -> None:
    application_channel = FakeApplicationChannel()
    channel = WhatsAppChannel(application_channel)

    channel.process(
        phone_number="34600123123",
        text="Hola",
        message_id="wamid-123",
        metadata={
            "channel": "fake",
            "message_id": "fake-id",
            "phone_number": "000000000",
        },
    )

    incoming = application_channel.messages[0]

    assert incoming.metadata["channel"] == "whatsapp"
    assert incoming.metadata["message_id"] == "wamid-123"
    assert incoming.metadata["phone_number"] == "34600123123"