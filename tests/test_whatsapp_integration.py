from chatbot.channels import (
    WhatsAppChannel,
    WhatsAppWebhookParser,
)
from chatbot.channels.message import IncomingMessage
from chatbot.channels.result import OutgoingMessage


class FakeApplicationChannel:
    def __init__(self) -> None:
        self.messages: list[IncomingMessage] = []

    def receive(self, message: IncomingMessage) -> OutgoingMessage:
        self.messages.append(message)
        return OutgoingMessage(text="OK")


def test_webhook_message_is_forwarded_to_application() -> None:
    parser = WhatsAppWebhookParser()
    application = FakeApplicationChannel()
    channel = WhatsAppChannel(application)

    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "from": "34600123123",
                                    "id": "wamid-123",
                                    "type": "text",
                                    "text": {
                                        "body": "Hola FlowForge",
                                    },
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }

    webhook_message = parser.parse(payload)

    assert webhook_message is not None

    channel.process(
        phone_number=webhook_message.phone_number,
        text=webhook_message.text,
        message_id=webhook_message.message_id,
    )

    assert len(application.messages) == 1

    incoming = application.messages[0]

    assert incoming.sender_id == "34600123123"
    assert incoming.text == "Hola FlowForge"