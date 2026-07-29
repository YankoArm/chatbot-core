from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatbot.api.whatsapp_app import (
    build_whatsapp_api,
)


class RecordingMessageHandler:
    def __init__(self) -> None:
        self.payloads: list[dict] = []

    def handle(
        self,
        payload: dict,
    ) -> str:
        self.payloads.append(payload)
        return "Respuesta de FlowForge"


def test_build_whatsapp_api_returns_fastapi_application() -> None:
    handler = RecordingMessageHandler()

    app = build_whatsapp_api(
        message_handler=handler,
        verify_token="test-token",
    )

    assert isinstance(
        app,
        FastAPI,
    )


def test_whatsapp_api_routes_payload_to_handler() -> None:
    handler = RecordingMessageHandler()

    app = build_whatsapp_api(
        message_handler=handler,
        verify_token="test-token",
    )

    client = TestClient(app)

    payload = {
        "entry": [],
    }

    response = client.post(
        "/webhook",
        json=payload,
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
    }
    assert handler.payloads == [
        payload,
    ]


def test_whatsapp_api_exposes_health_endpoint() -> None:
    handler = RecordingMessageHandler()

    app = build_whatsapp_api(
        message_handler=handler,
        verify_token="test-token",
    )

    client = TestClient(app)

    response = client.get(
        "/health",
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "flowforge-whatsapp",
    }