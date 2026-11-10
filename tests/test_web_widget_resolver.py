from dataclasses import replace
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatbot.api.web_chat import build_web_chat_router
from chatbot.api.web_widget_resolver import (
    resolve_web_widget_definition,
)
from chatbot.clients.registry import build_client_definition
from chatbot.instances.sqlite_repository import (
    SQLiteInstanceDefinitionRepository,
)


WIDGET_A = "wf_tenant_alpha_123456"
WIDGET_B = "wf_tenant_beta_123456"


@pytest.fixture
def repository(tmp_path):
    repo = SQLiteInstanceDefinitionRepository(
        tmp_path / "widget_clients.sqlite3"
    )

    try:
        yield repo
    finally:
        repo.close()


def save_client(repository, client_id, widget_id, enabled=True):
    original = build_client_definition("tarot_alvin")

    definition = replace(
        original,
        id=client_id,
        name=client_id,
        whatsapp_phone_number_id=None,
        settings={
            **original.settings,
            "web_chat": {
                "enabled": enabled,
                "widget_id": widget_id,
            },
        },
        metadata={
            **original.metadata,
            "admin_status": "active",
        },
    )

    repository.save(definition)
    return definition


def make_client(repository):
    class FakeApplication:
        def __init__(self, client_id):
            self.client_id = client_id

        def chat(self, *, session_id, message):
            return SimpleNamespace(
                text=f"{self.client_id}: {message}"
            )

    app = FastAPI()

    app.include_router(
        build_web_chat_router(
            resolve_widget=lambda widget_id: (
                resolve_web_widget_definition(
                    repository, widget_id
                )
            ),
            build_application=lambda definition: (
                FakeApplication(definition.id)
            ),
        )
    )

    return TestClient(app)


def test_resolves_correct_client(repository):
    save_client(repository, "empresa_a", WIDGET_A)
    save_client(repository, "empresa_b", WIDGET_B)

    resolved = resolve_web_widget_definition(
        repository, WIDGET_B
    )

    assert resolved is not None
    assert resolved.id == "empresa_b"


def test_rejects_unknown_widget(repository):
    save_client(repository, "empresa_a", WIDGET_A)

    assert resolve_web_widget_definition(
        repository, WIDGET_B
    ) is None


def test_rejects_invalid_widget_identifier(repository):
    assert resolve_web_widget_definition(
        repository, "../admin"
    ) is None


def test_rejects_duplicate_widget_identifiers(repository):
    save_client(repository, "empresa_a", WIDGET_A)
    save_client(repository, "empresa_b", WIDGET_A)

    assert resolve_web_widget_definition(
        repository, WIDGET_A
    ) is None


def test_web_chat_routes_to_correct_sqlite_client(repository):
    save_client(repository, "empresa_a", WIDGET_A)
    save_client(repository, "empresa_b", WIDGET_B)

    client = make_client(repository)

    session_a = client.post(
        f"/webchat/api/{WIDGET_A}/session"
    )
    session_b = client.post(
        f"/webchat/api/{WIDGET_B}/session"
    )

    assert session_a.status_code == 201
    assert session_b.status_code == 201

    token_a = session_a.json()["session_token"]
    token_b = session_b.json()["session_token"]

    response_a = client.post(
        f"/webchat/api/{WIDGET_A}/message",
        json={
            "session_token": token_a,
            "message": "Hola",
        },
    )

    response_b = client.post(
        f"/webchat/api/{WIDGET_B}/message",
        json={
            "session_token": token_b,
            "message": "Hola",
        },
    )

    assert response_a.status_code == 200
    assert response_b.status_code == 200
    assert response_a.json()["response"] == "empresa_a: Hola"
    assert response_b.json()["response"] == "empresa_b: Hola"

    cross_tenant = client.post(
        f"/webchat/api/{WIDGET_B}/message",
        json={
            "session_token": token_a,
            "message": "Acceso cruzado",
        },
    )

    assert cross_tenant.status_code == 404


def test_duplicate_widget_is_blocked_by_api(repository):
    save_client(repository, "empresa_a", WIDGET_A)
    save_client(repository, "empresa_b", WIDGET_A)

    client = make_client(repository)

    response = client.post(
        f"/webchat/api/{WIDGET_A}/session"
    )

    assert response.status_code == 404
