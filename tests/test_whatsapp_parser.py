from chatbot.connectors.whatsapp.message_handler import (
    IncomingWhatsAppMessage,
)

from chatbot.connectors.whatsapp.parser import (
    WhatsAppPayloadParser,
    WhatsAppPayloadError,
)

import pytest

def test_whatsapp_payload_parser_extracts_text_message() -> None:
    parser = WhatsAppPayloadParser()

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

    result = parser.parse(payload)

    assert result == IncomingWhatsAppMessage(
        user_id="34600000000",
        text="Hola",
    )

def test_whatsapp_payload_parser_rejects_empty_entry() -> None:
    parser = WhatsAppPayloadParser()

    payload = {
        "entry": [],
    }

    with pytest.raises(
        WhatsAppPayloadError,
        match="WhatsApp payload does not contain a message",
    ):
        parser.parse(payload)

def test_whatsapp_payload_parser_rejects_non_text_message() -> None:
    parser = WhatsAppPayloadParser()

    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "from": "34600000000",
                                    "type": "image",
                                    "image": {
                                        "id": "image-123",
                                    },
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }

    with pytest.raises(
        WhatsAppPayloadError,
        match="WhatsApp message is not a text message",
    ):
        parser.parse(payload)
def test_whatsapp_payload_parser_preserves_receiver_phone_number_id(
) -> None:
    parser = WhatsAppPayloadParser()

    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "metadata": {
                                "phone_number_id": (
                                    "test-phone-number-id"
                                ),
                            },
                            "messages": [
                                {
                                    "from": "34600000000",
                                    "text": {
                                        "body": "Hola",
                                    },
                                }
                            ],
                        }
                    }
                ]
            }
        ]
    }

    result = parser.parse(payload)

    assert result == IncomingWhatsAppMessage(
        user_id="34600000000",
        text="Hola",
        phone_number_id="test-phone-number-id",
    )