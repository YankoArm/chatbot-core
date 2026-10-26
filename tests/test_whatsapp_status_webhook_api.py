from __future__ import annotations

import hashlib
import hmac
import json

from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatbot.api.whatsapp import create_whatsapp_router
from chatbot.connectors.whatsapp.message_handler import (
    WhatsAppMessageHandler,
)
from chatbot.connectors.whatsapp.parser import (
    WhatsAppPayloadParser,
)
from chatbot.connectors.whatsapp.signature import (
    WhatsAppSignatureVerifier,
)


APP_SECRET = "test-app-secret"


class FailIfCalledOrchestrator:
    def handle(
        self,
        message: object,
    ) -> object:
        raise AssertionError(
            "Status webhook must not reach FlowForge."
        )


class FailIfCalledSender:
    def send_text(
        self,
        recipient: str,
        text: str,
        phone_number_id: str | None = None,
    ) -> None:
        raise AssertionError(
            "Status webhook must not send a WhatsApp message."
        )


def test_status_webhook_returns_200_without_processing_message() -> None:
    payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "test-waba-id",
            "changes": [{
                "field": "messages",
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {
                        "display_phone_number": "+15550000000",
                        "phone_number_id": "test-phone-number-id",
                    },
                    "statuses": [{
                        "id": "wamid.STATUS_TEST",
                        "status": "delivered",
                        "timestamp": "0",
                        "recipient_id": "34600000000",
                    }],
                },
            }],
        }],
    }

    body = json.dumps(
        payload,
        separators=(",", ":"),
    ).encode("utf-8")

    signature = (
        "sha256="
        + hmac.new(
            APP_SECRET.encode("utf-8"),
            body,
            hashlib.sha256,
        ).hexdigest()
    )

    handler = WhatsAppMessageHandler(
        parser=WhatsAppPayloadParser(),
        orchestrator=FailIfCalledOrchestrator(),
        sender=FailIfCalledSender(),
    )

    app = FastAPI()
    app.include_router(
        create_whatsapp_router(
            message_handler=handler,
            signature_verifier=WhatsAppSignatureVerifier(
                app_secret=APP_SECRET,
            ),
        )
    )

    client = TestClient(app)

    response = client.post(
        "/webhook",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": signature,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
    }
