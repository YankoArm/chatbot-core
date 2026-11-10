import pytest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatbot.api.admin import build_admin_router
from chatbot.clients.registry import build_instance_from_definition
from chatbot.instances.channel_modes import channels_for_mode
from chatbot.instances.sqlite_repository import (
    SQLiteInstanceDefinitionRepository,
)


@pytest.fixture
def repository(tmp_path):
    repo = SQLiteInstanceDefinitionRepository(
        tmp_path / "channel_modes.sqlite3"
    )
    try:
        yield repo
    finally:
        repo.close()


def make_client(repository):
    app = FastAPI()
    app.include_router(build_admin_router(repository))
    return TestClient(app)


@pytest.mark.parametrize(
    "mode,expected",
    [
        ("whatsapp", ["whatsapp"]),
        ("web", ["web"]),
        ("both", ["whatsapp", "web"]),
    ],
)
def test_channel_modes(mode, expected):
    assert channels_for_mode(mode) == expected


def test_invalid_channel_mode_raises():
    with pytest.raises(ValueError):
        channels_for_mode("invalid")


def test_creation_form_shows_three_options(repository):
    client = make_client(repository)

    response = client.get("/admin/clients/new")

    assert response.status_code == 200
    assert 'name="channel_mode"' in response.text
    assert 'value="whatsapp"' in response.text
    assert 'value="web"' in response.text
    assert 'value="both"' in response.text


@pytest.mark.parametrize(
    "mode,expected",
    [
        ("whatsapp", ["whatsapp"]),
        ("web", ["web"]),
        ("both", ["whatsapp", "web"]),
    ],
)
def test_admin_creates_bot_with_selected_channels(
    repository, mode, expected
):
    client = make_client(repository)

    response = client.post(
        "/admin/clients",
        data={
            "name": f"Canal Demo {mode}",
            "template_id": "professional_services",
            "channel_mode": mode,
        },
        follow_redirects=False,
    )

    assert response.status_code == 303

    definitions = repository.list_all()
    assert len(definitions) == 1

    definition = definitions[0]

    assert definition.channels == expected
    assert definition.metadata["channel_mode"] == mode
    assert definition.metadata["admin_status"] == "draft"

    resolved = build_instance_from_definition(definition)
    assert resolved.channels == expected


def test_existing_form_submission_remains_compatible(repository):
    client = make_client(repository)

    response = client.post(
        "/admin/clients",
        data={
            "name": "Legacy Form Demo",
            "template_id": "professional_services",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert repository.list_all()[0].channels == ["whatsapp"]


def test_invalid_channel_is_rejected(repository):
    client = make_client(repository)

    response = client.post(
        "/admin/clients",
        data={
            "name": "Invalid Channel",
            "template_id": "professional_services",
            "channel_mode": "telegram",
        },
        follow_redirects=False,
    )

    assert response.status_code == 422
    assert repository.list_all() == ()
