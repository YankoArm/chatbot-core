from dataclasses import replace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatbot.api.web_chat import build_web_chat_router
from chatbot.clients.registry import build_client_definition
from chatbot.instances.sqlite_repository import (
    SQLiteInstanceDefinitionRepository,
)
from run_flowforge import build_tenant_application


WIDGET_ID = "wf_sqlite_tarot_123456"


def test_web_chat_loads_real_client_from_sqlite(tmp_path):
    database = tmp_path / "web_chat_clients.sqlite3"

    repository = SQLiteInstanceDefinitionRepository(
        database_path=database,
    )

    try:
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

        repository.save(definition)

        stored = repository.get("tarot_alvin")

        assert stored is not None
        assert stored.settings["web_chat"]["enabled"] is True

        app = FastAPI()

        app.include_router(
            build_web_chat_router(
                resolve_widget=lambda widget_id: (
                    repository.get("tarot_alvin")
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
        assert "Alvin" in greeting.json()["response"]

        activation = client.post(
            f"/webchat/api/{WIDGET_ID}/message",
            json={
                "session_token": token,
                "message": "TAROT",
            },
        )

        assert activation.status_code == 200
        assert activation.json()["response"].strip()

        disabled = replace(
            stored,
            settings={
                **stored.settings,
                "web_chat": {
                    "enabled": False,
                    "widget_id": WIDGET_ID,
                },
            },
        )

        repository.save(disabled)

        blocked = client.post(
            f"/webchat/api/{WIDGET_ID}/message",
            json={
                "session_token": token,
                "message": "Hola otra vez",
            },
        )

        assert blocked.status_code == 404

        print("\nSQLite: configuracion recuperada")
        print("Motor real: conversacion correcta")
        print("Desactivacion: acceso bloqueado")

    finally:
        close = getattr(repository, "close", None)
        if callable(close):
            close()
