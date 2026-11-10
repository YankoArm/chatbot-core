from dataclasses import replace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatbot.api.web_chat import build_web_chat_router
from chatbot.clients.registry import build_client_definition
from run_flowforge import build_tenant_application


WIDGET_ID = "wf_tarot_real_engine_123456"


def test_web_chat_uses_real_flowforge_engine():
    original = build_client_definition("tarot_alvin")

    definition = replace(
        original,
        settings={
            **original.settings,
            "web_chat": {
                "enabled": True,
                "widget_id": WIDGET_ID,
            },
        },
        metadata={
            **original.metadata,
            "admin_status": "active",
        },
    )

    app = FastAPI()

    app.include_router(
        build_web_chat_router(
            resolve_widget=lambda widget_id: (
                definition
                if widget_id == WIDGET_ID
                else None
            ),
            build_application=lambda tenant: (
                build_tenant_application(
                    definition=tenant,
                    calendar_service=None,
                    booking_repository=None,
                    lead_repository=None,
                )
            ),
        )
    )

    client = TestClient(app)

    started = client.post(
        f"/webchat/api/{WIDGET_ID}/session"
    )

    assert started.status_code == 201

    token = started.json()["session_token"]

    greeting = client.post(
        f"/webchat/api/{WIDGET_ID}/message",
        json={
            "session_token": token,
            "message": "Hola",
        },
    )

    assert greeting.status_code == 200
    assert greeting.json()["response"].strip()

    activation = client.post(
        f"/webchat/api/{WIDGET_ID}/message",
        json={
            "session_token": token,
            "message": "TAROT",
        },
    )

    assert activation.status_code == 200
    assert activation.json()["response"].strip()

    print("\nRESPUESTA INICIAL:")
    print(greeting.json()["response"])

    print("\nRESPUESTA ACTIVACION:")
    print(activation.json()["response"])
