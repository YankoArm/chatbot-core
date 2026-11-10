from dataclasses import replace
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatbot.api.web_chat_mount import mount_web_chat
from chatbot.clients.registry import build_client_definition
from chatbot.instances.sqlite_repository import (
    SQLiteInstanceDefinitionRepository,
)


WIDGET = "wf_mount_test_123456"


def make_definition(client_id, widget_id=WIDGET):
    original = build_client_definition("tarot_alvin")

    return replace(
        original,
        id=client_id,
        name=client_id,
        whatsapp_phone_number_id=None,
        settings={
            **original.settings,
            "web_chat": {
                "enabled": True,
                "widget_id": widget_id,
            },
        },
        metadata={
            **original.metadata,
            "admin_status": "active",
        },
    )


class FakeApplication:
    def __init__(self, client_id):
        self.client_id = client_id

    def chat(self, *, session_id, message):
        return SimpleNamespace(
            text=f"{self.client_id}: {message}"
        )


@pytest.fixture
def repo(tmp_path):
    repository = SQLiteInstanceDefinitionRepository(
        tmp_path / "mount_test.sqlite3"
    )
    try:
        yield repository
    finally:
        repository.close()


def build_app(repo, enabled=True):
    app = FastAPI()
    mount_web_chat(
        app,
        repository=repo,
        application_factory=lambda definition: (
            FakeApplication(definition.id)
        ),
        enabled=enabled,
    )
    return TestClient(app)


def test_web_chat_disabled_by_default(repo):
    repo.save(make_definition("empresa_a"))
    client = build_app(repo, enabled=False)

    response = client.post(
        f"/webchat/api/{WIDGET}/session"
    )

    assert response.status_code == 404


def test_web_chat_requires_repository_when_enabled():
    with pytest.raises(ValueError):
        mount_web_chat(
            FastAPI(),
            repository=None,
            application_factory=lambda definition: None,
            enabled=True,
        )


def test_web_chat_mount_uses_sqlite_client(repo):
    repo.save(make_definition("empresa_a"))
    client = build_app(repo)

    started = client.post(
        f"/webchat/api/{WIDGET}/session"
    )
    assert started.status_code == 201

    token = started.json()["session_token"]

    answered = client.post(
        f"/webchat/api/{WIDGET}/message",
        json={
            "session_token": token,
            "message": "Hola",
        },
    )

    assert answered.status_code == 200
    assert answered.json()["response"] == "empresa_a: Hola"


def test_session_rejected_after_widget_changes_owner(repo):
    original = make_definition("empresa_a")
    repo.save(original)

    client = build_app(repo)

    started = client.post(
        f"/webchat/api/{WIDGET}/session"
    )
    assert started.status_code == 201

    token = started.json()["session_token"]

    repo.save(
        replace(
            original,
            settings={
                **original.settings,
                "web_chat": {
                    "enabled": False,
                    "widget_id": "wf_previous_owner_123456",
                },
            },
        )
    )

    repo.save(make_definition("empresa_b"))

    response = client.post(
        f"/webchat/api/{WIDGET}/message",
        json={
            "session_token": token,
            "message": "Hola",
        },
    )

    assert response.status_code == 404
