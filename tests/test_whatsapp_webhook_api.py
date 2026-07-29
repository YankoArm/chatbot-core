from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatbot.api.whatsapp import create_whatsapp_router
from chatbot.connectors.whatsapp.signature import (
    WhatsAppSignatureVerifier,
)


class RecordingMessageHandler:
    def __init__(self) -> None:
        self.payloads: list[dict[str, Any]] = []

    def handle(
        self,
        payload: dict[str, Any],
    ) -> str:
        self.payloads.append(payload)
        return "Respuesta de FlowForge"


class RejectingSignatureVerifier:
    def verify(
        self,
        *,
        body: bytes,
        signature: str,
    ) -> bool:
        return False


def test_webhook_endpoint_returns_200() -> None:
    app = FastAPI()
    app.include_router(
        create_whatsapp_router()
    )

    client = TestClient(app)

    response = client.post(
        "/webhook",
        json={},
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
    }


def test_webhook_endpoint_passes_payload_to_message_handler() -> None:
    handler = RecordingMessageHandler()

    app = FastAPI()
    app.include_router(
        create_whatsapp_router(
            message_handler=handler,
        )
    )

    client = TestClient(app)

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

    response = client.post(
        "/webhook",
        json=payload,
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
    }
    assert handler.payloads == [payload]


def test_webhook_verification_returns_challenge() -> None:
    app = FastAPI()
    app.include_router(
        create_whatsapp_router()
    )

    client = TestClient(app)

    response = client.get(
        "/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "test-token",
            "hub.challenge": "123456789",
        },
    )

    assert response.status_code == 200
    assert response.text == "123456789"


def test_webhook_verification_rejects_invalid_token() -> None:
    app = FastAPI()
    app.include_router(
        create_whatsapp_router(
            verify_token="secret-token",
        )
    )

    client = TestClient(app)

    response = client.get(
        "/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong-token",
            "hub.challenge": "123456789",
        },
    )

    assert response.status_code == 403


def test_webhook_endpoint_rejects_invalid_signature() -> None:
    app = FastAPI()
    app.include_router(
        create_whatsapp_router(
            signature_verifier=RejectingSignatureVerifier(),
        )
    )

    client = TestClient(app)

    response = client.post(
        "/webhook",
        content=b'{"entry":[]}',
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": "sha256=invalid",
        },
    )

    assert response.status_code == 403


def test_webhook_endpoint_accepts_real_signature_verifier() -> None:
    app = FastAPI()
    app.include_router(
        create_whatsapp_router(
            signature_verifier=WhatsAppSignatureVerifier(
                app_secret="secret",
            ),
        )
    )

    client = TestClient(app)

    response = client.post(
        "/webhook",
        content=b'{"message":"hola"}',
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": (
                "sha256="
                "bed02614ab68b29c8524e86ce4f70c92"
                "e7abca6796e9e988aad45309a2593fc6"
            ),
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
    }


def test_webhook_endpoint_rejects_missing_signature() -> None:
    app = FastAPI()
    app.include_router(
        create_whatsapp_router(
            signature_verifier=RejectingSignatureVerifier(),
        )
    )

    client = TestClient(app)

    response = client.post(
        "/webhook",
        content=b'{"entry":[]}',
        headers={
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == 403


def test_webhook_endpoint_processes_message_with_valid_signature() -> None:
    handler = RecordingMessageHandler()

    app = FastAPI()
    app.include_router(
        create_whatsapp_router(
            message_handler=handler,
            signature_verifier=WhatsAppSignatureVerifier(
                app_secret="secret",
            ),
        )
    )

    client = TestClient(app)

    response = client.post(
        "/webhook",
        content=b'{"entry":[]}',
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": (
                "sha256="
                "97f0eaf4fb539301c758929abea22432"
                "a8fed44f5ce20d65c6af41ff15dfb115"
            ),
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
    }
    assert handler.payloads == [
        {
            "entry": [],
        }
    ]