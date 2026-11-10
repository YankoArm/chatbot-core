from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from chatbot.clients.registry import build_client_definition
from chatbot.instances.sqlite_repository import (
    SQLiteInstanceDefinitionRepository,
)
from scripts.demo_web_chat import create_demo_app


WIDGET_ID = "wf_easy_app_code_test_2026"


def test_demo_uses_stored_widget_and_real_engine(tmp_path):
    database = tmp_path / "admin.sqlite3"
    repository = SQLiteInstanceDefinitionRepository(database_path=database)

    try:
        original = build_client_definition("tarot_alvin")
        definition = replace(
            original,
            id="easy_app_code",
            name="Easy App Code",
            channels=["web"],
            settings={
                **original.settings,
                "web_chat": {
                    "enabled": True,
                    "widget_id": WIDGET_ID,
                    "allowed_origins": ["http://testserver"],
                },
            },
            metadata={
                **original.metadata,
                "admin_status": "active",
            },
        )
        repository.save(definition)
    finally:
        repository.close()

    app = create_demo_app(
        database_path=database,
        client_id="easy_app_code",
    )

    with TestClient(app) as client:
        page = client.get("/")
        assert page.status_code == 200
        assert "Easy App Code" in page.text
        assert f'data-flowforge-widget="{WIDGET_ID}"' in page.text
        assert "wf_local_tarot_demo_2026" not in page.text

        started = client.post(
            f"/webchat/api/{WIDGET_ID}/session",
            headers={"Origin": "http://testserver"},
        )
        assert started.status_code == 201

        reply = client.post(
            f"/webchat/api/{WIDGET_ID}/message",
            headers={"Origin": "http://testserver"},
            json={
                "session_token": started.json()["session_token"],
                "message": "Hola",
            },
        )
        assert reply.status_code == 200
        assert reply.json()["response"].strip()

        unknown = client.post(
            "/webchat/api/wf_unknown_widget_2026/session"
        )
        assert unknown.status_code == 404


def test_demo_rejects_missing_database_without_creating_it(tmp_path):
    database = tmp_path / "missing.sqlite3"

    with pytest.raises(FileNotFoundError):
        create_demo_app(
            database_path=database,
            client_id="easy_app_code",
        )

    assert not database.exists()


def test_demo_rejects_unknown_client(tmp_path):
    database = tmp_path / "admin.sqlite3"
    repository = SQLiteInstanceDefinitionRepository(database_path=database)
    repository.close()

    with pytest.raises(ValueError, match="easy_app_code"):
        create_demo_app(
            database_path=database,
            client_id="easy_app_code",
        )
