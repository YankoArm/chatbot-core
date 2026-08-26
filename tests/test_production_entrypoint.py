from __future__ import annotations

from fastapi.testclient import TestClient

from chatbot.infrastructure.config import (
    FlowForgeConfig,
    ServerConfig,
    WhatsAppConfig,
)
from run_flowforge import create_app


class FakeCalendarService:
    def is_available(
        self,
        *,
        date: str,
        time: str,
        duration_minutes: int,
    ) -> bool:
        return True

    def create_booking(
        self,
        *,
        date: str,
        time: str,
        title: str,
        description: str | None = None,
        attendee: str | None = None,
        metadata: dict | None = None,
    ) -> str:
        return "booking-test-id"

    def cancel_booking(
        self,
        booking_id: str,
    ) -> None:
        return None


class FakeWhatsAppGraphClient:
    def send_text_message(
        self,
        *,
        to: str,
        text: str,
    ) -> object:
        return object()


def test_create_app_builds_production_whatsapp_api() -> None:
    config = FlowForgeConfig(
        whatsapp=WhatsAppConfig(
            access_token="test-access-token",
            phone_number_id="test-phone-number-id",
            verify_token="test-verify-token",
            app_secret="test-app-secret",
        ),
        server=ServerConfig(
            host="127.0.0.1",
            port=8000,
        ),
    )

    app = create_app(
        config=config,
        calendar_service=FakeCalendarService(),
        graph_client=FakeWhatsAppGraphClient(),
    )

    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "flowforge-whatsapp",
    }

def test_create_app_verifies_whatsapp_webhook() -> None:
    config = FlowForgeConfig(
        whatsapp=WhatsAppConfig(
            access_token="test-access-token",
            phone_number_id="test-phone-number-id",
            verify_token="my-secret-token",
            app_secret="test-app-secret",
        ),
        server=ServerConfig(
            host="127.0.0.1",
            port=8000,
        ),
    )

    app = create_app(
        config=config,
        calendar_service=FakeCalendarService(),
        graph_client=FakeWhatsAppGraphClient(),
    )

    client = TestClient(app)

    response = client.get(
        "/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "my-secret-token",
            "hub.challenge": "123456",
        },
    )

    assert response.status_code == 200
    assert response.text == "123456"

def test_create_app_uses_configured_client_instance() -> None:
    config = FlowForgeConfig(
        whatsapp=WhatsAppConfig(
            access_token="test-access-token",
            phone_number_id="test-phone-number-id",
            verify_token="test-verify-token",
            app_secret="test-app-secret",
        ),
        server=ServerConfig(
            host="127.0.0.1",
            port=8000,
        ),
        client_id="hairdressing_demo",
    )

    app = create_app(
        config=config,
        calendar_service=FakeCalendarService(),
        graph_client=FakeWhatsAppGraphClient(),
    )

    assert app.state.flowforge_instance.id == (
        "hairdressing_demo"
    )
    assert app.state.flowforge_instance.name == (
        "Salón Estilo"
    )
    assert app.state.flowforge_instance.template_id == (
        "hairdressing"
    )
    assert app.state.flowforge_instance.capabilities == [
        "greeting",
        "faq",
        "booking",
        "help",
        "human_transfer",
    ]