from __future__ import annotations

import pytest

from chatbot.connectors.whatsapp.message_handler import (
    WhatsAppMessageHandler,
)
from chatbot.connectors.whatsapp.parser import (
    WhatsAppPayloadParser,
)


class FailIfCalledOrchestrator:
    def handle(
        self,
        message: object,
    ) -> object:
        raise AssertionError(
            "Status webhook must not reach the orchestrator."
        )


class FailIfCalledSender:
    def send_text(
        self,
        recipient: str,
        text: str,
        phone_number_id: str | None = None,
    ) -> None:
        raise AssertionError(
            "Status webhook must not send a message."
        )


def build_status_payload(
    status: str,
) -> dict[str, object]:
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "test-waba-id",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": (
                                    "+15550000000"
                                ),
                                "phone_number_id": (
                                    "test-phone-number-id"
                                ),
                            },
                            "statuses": [
                                {
                                    "id": "wamid.TEST_STATUS",
                                    "status": status,
                                    "timestamp": "0",
                                    "recipient_id": (
                                        "34600000000"
                                    ),
                                }
                            ],
                        },
                    }
                ],
            }
        ],
    }


@pytest.mark.parametrize(
    "status",
    [
        "sent",
        "delivered",
        "read",
        "failed",
    ],
)
def test_whatsapp_status_webhook_is_ignored(
    status: str,
) -> None:
    handler = WhatsAppMessageHandler(
        parser=WhatsAppPayloadParser(),
        orchestrator=FailIfCalledOrchestrator(),
        sender=FailIfCalledSender(),
    )

    result = handler.handle(
        build_status_payload(status)
    )

    assert result is None
