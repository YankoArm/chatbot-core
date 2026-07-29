from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatbot.api.whatsapp import create_whatsapp_router
from dataclasses import dataclass
from chatbot.connectors.whatsapp.signature import (
    WhatsAppSignatureVerifier,
)

class FakeWhatsAppWebhookParser:
    def __init__(self) -> None:
        self.payloads: list[dict[str, Any]] = []

    def parse(self, payload: dict[str, Any]) -> None:
        self.payloads.append(payload)


def test_webhook_endpoint_returns_200() -> None:
    app = FastAPI()
    app.include_router(create_whatsapp_router())

    client = TestClient(app)

    response = client.post(
        "/webhook",
        json={},
    )

    assert response.status_code == 200


def test_webhook_endpoint_passes_payload_to_parser() -> None:
    parser = FakeWhatsAppWebhookParser()

    app = FastAPI()
    app.include_router(
        create_whatsapp_router(parser=parser)
    )

    client = TestClient(app)

    payload = {
        "entry": [
            {
                "changes": [],
            }
        ]
    }

    response = client.post(
        "/webhook",
        json=payload,
    )

    assert response.status_code == 200
    assert parser.payloads == [payload]

@dataclass(frozen=True)
class FakeWebhookMessage:
    phone_number: str
    message_id: str
    text: str
    metadata: dict[str, Any]

class FakeParserWithMessage:
    def parse(self, payload: dict[str, Any]) -> FakeWebhookMessage:
        return FakeWebhookMessage(
            phone_number="34600123123",
            message_id="wamid-123",
            text="Hola",
            metadata={
                "profile_name": "Yanko",
                "phone_number_id": "business-456",
            },
        )
    
class FakeWhatsAppChannel:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def process(
        self,
        *,
        phone_number: str,
        text: str,
        message_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.calls.append(
            {
                "phone_number": phone_number,
                "text": text,
                "message_id": message_id,
                "metadata": metadata,
            }
        )

def test_webhook_endpoint_forwards_parsed_message_to_channel() -> None:
    parser = FakeParserWithMessage()
    channel = FakeWhatsAppChannel()

    app = FastAPI()
    app.include_router(
        create_whatsapp_router(
            parser=parser,
            channel=channel,
        )
    )

    client = TestClient(app)

    response = client.post(
        "/webhook",
        json={"entry": []},
    )

    assert response.status_code == 200
    assert channel.calls == [
        {
            "phone_number": "34600123123",
            "text": "Hola",
            "message_id": "wamid-123",
            "metadata": {
                "profile_name": "Yanko",
                "phone_number_id": "business-456",
            },
        }
    ]

class FakeParserWithoutMessage:
    def parse(self, payload: dict[str, Any]) -> None:
        return None


def test_webhook_endpoint_does_not_call_channel_without_message() -> None:
    parser = FakeParserWithoutMessage()
    channel = FakeWhatsAppChannel()

    app = FastAPI()
    app.include_router(
        create_whatsapp_router(
            parser=parser,
            channel=channel,
        )
    )

    client = TestClient(app)

    response = client.post(
        "/webhook",
        json={"entry": []},
    )

    assert response.status_code == 200
    assert channel.calls == []

def test_webhook_verification_returns_challenge() -> None:
    app = FastAPI()
    app.include_router(create_whatsapp_router())

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

class RejectingSignatureVerifier:
    def verify(
        self,
        *,
        body: bytes,
        signature: str,
    ) -> bool:
        return False


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
class RecordingParser:
    def __init__(self) -> None:
        self.payload: dict[str, Any] | None = None

    def parse(
        self,
        payload: dict[str, Any],
    ) -> None:
        self.payload = payload
        return None


class RecordingChannel:
    def process(
        self,
        *,
        phone_number: str,
        text: str,
        message_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> object:
        return object()

def test_webhook_endpoint_processes_message_with_valid_signature() -> None:
    parser = RecordingParser()
    channel = RecordingChannel()

    app = FastAPI()
    app.include_router(
        create_whatsapp_router(
            parser=parser,
            channel=channel,
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
    assert parser.payload == {"entry": []}