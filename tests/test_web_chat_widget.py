from dataclasses import replace
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatbot.api.web_chat_mount import mount_web_chat
from chatbot.clients.registry import build_client_definition


WIDGET = "wf_visual_test_123456"


def make_client(name="Empresa de prueba", enabled=True):
    original = build_client_definition("tarot_alvin")

    definition = replace(
        original,
        name=name,
        settings={
            **original.settings,
            "web_chat": {
                "enabled": enabled,
                "widget_id": WIDGET,
            },
        },
        metadata={
            **original.metadata,
            "admin_status": "active",
        },
    )

    class Repository:
        def list_all(self):
            return (definition,)

    class Application:
        def chat(self, *, session_id, message):
            return SimpleNamespace(text="Recibido: " + message)

    app = FastAPI()

    mount_web_chat(
        app,
        repository=Repository(),
        application_factory=lambda definition: Application(),
        enabled=True,
    )

    return TestClient(app)


def test_embed_script_is_available():
    client = make_client()

    response = client.get("/webchat/embed.js")

    assert response.status_code == 200
    assert "javascript" in response.headers["content-type"]
    assert "data-flowforge-widget" in response.text
    assert "iframe" in response.text


def test_widget_page_is_available():
    client = make_client()

    response = client.get(f"/webchat/widget/{WIDGET}")

    assert response.status_code == 200
    assert "Empresa de prueba" in response.text
    assert "/webchat/api/" in response.text
    assert WIDGET in response.text


def test_widget_escapes_business_name():
    client = make_client(
        name="<script>alert(1)</script>"
    )

    response = client.get(f"/webchat/widget/{WIDGET}")

    assert response.status_code == 200
    assert "&lt;script&gt;" in response.text
    assert "<script>alert(1)</script>" not in response.text


def test_disabled_widget_returns_404():
    client = make_client(enabled=False)

    response = client.get(f"/webchat/widget/{WIDGET}")

    assert response.status_code == 404


def test_widget_uses_existing_conversation_api():
    client = make_client()

    started = client.post(
        f"/webchat/api/{WIDGET}/session"
    )

    assert started.status_code == 201

    response = client.post(
        f"/webchat/api/{WIDGET}/message",
        json={
            "session_token": started.json()["session_token"],
            "message": "Hola",
        },
    )

    assert response.status_code == 200
    assert response.json()["response"] == "Recibido: Hola"
