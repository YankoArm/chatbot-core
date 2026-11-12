from dataclasses import replace
from html import unescape

import pytest
from fastapi.testclient import TestClient

from chatbot.clients.registry import build_client_definition
from chatbot.instances.sqlite_repository import (
    SQLiteInstanceDefinitionRepository,
)
from scripts.demo_web_chat import create_demo_app


@pytest.fixture
def client(tmp_path):
    database = tmp_path / "admin.sqlite3"
    original = build_client_definition("tarot_alvin")
    definition = replace(
        original,
        channels=["web"],
        metadata={**original.metadata, "admin_status": "active"},
        settings={
            **original.settings,
            "web_chat": {
                "enabled": True,
                "widget_id": "wf_visual_regression_test",
                "allowed_origins": ["http://testserver"],
            },
        },
    )

    repository = SQLiteInstanceDefinitionRepository(database_path=database)
    try:
        repository.save(definition)
    finally:
        repository.close()

    app = create_demo_app(database_path=database, client_id=definition.id)
    with TestClient(app) as test_client:
        yield test_client


def test_demo_page_has_correct_text(client):
    response = client.get("/")

    assert response.status_code == 200
    assert (
        "Prueba local del asistente con su configuraci\u00f3n guardada."
        in unescape(response.text)
    )


def test_embed_has_svg_chat_icon(client):
    response = client.get("/webchat/embed.js")

    assert response.status_code == 200
    assert "const chatIcon =" in response.text
    assert "<svg" in response.text
    assert "button.innerHTML = chatIcon;" in response.text
