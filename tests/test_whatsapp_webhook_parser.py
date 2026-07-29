from __future__ import annotations

from chatbot.channels import WhatsAppWebhookParser


def test_parser_extracts_text_message() -> None:
    parser = WhatsAppWebhookParser()

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

    message = parser.parse(payload)

    assert message.phone_number == "34600123123"
    assert message.message_id == "wamid-123"
    assert message.text == "Hola"

def test_parser_returns_none_when_payload_has_no_messages() -> None:
    parser = WhatsAppWebhookParser()

    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "statuses": [
                                {
                                    "id": "wamid-123",
                                    "status": "delivered",
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }

    message = parser.parse(payload)

    assert message is None

def test_parser_returns_none_for_non_text_message() -> None:
    parser = WhatsAppWebhookParser()

    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "from": "34600123123",
                                    "id": "wamid-456",
                                    "type": "image",
                                    "image": {
                                        "id": "media-123",
                                        "mime_type": "image/jpeg",
                                    },
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }

    message = parser.parse(payload)

    assert message is None

def test_parser_uses_first_message_when_multiple_exist() -> None:
    parser = WhatsAppWebhookParser()

    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "from": "34600123123",
                                    "id": "wamid-1",
                                    "type": "text",
                                    "text": {
                                        "body": "Primer mensaje",
                                    },
                                },
                                {
                                    "from": "34600123123",
                                    "id": "wamid-2",
                                    "type": "text",
                                    "text": {
                                        "body": "Segundo mensaje",
                                    },
                                },
                            ]
                        }
                    }
                ]
            }
        ]
    }

    message = parser.parse(payload)

    assert message.message_id == "wamid-1"
    assert message.text == "Primer mensaje"

def test_parser_extracts_provider_metadata() -> None:
    parser = WhatsAppWebhookParser()

    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "metadata": {
                                "phone_number_id": "business-456",
                            },
                            "contacts": [
                                {
                                    "profile": {
                                        "name": "Yanko",
                                    },
                                    "wa_id": "34600123123",
                                }
                            ],
                            "messages": [
                                {
                                    "from": "34600123123",
                                    "id": "wamid-123",
                                    "type": "text",
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

    message = parser.parse(payload)

    assert message is not None
    assert message.metadata == {
        "profile_name": "Yanko",
        "phone_number_id": "business-456",
    }