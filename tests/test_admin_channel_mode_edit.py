from dataclasses import replace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatbot.api.admin import build_admin_router
from chatbot.clients.registry import (
    build_client_definition,
    build_instance_from_definition,
)
from chatbot.instances.sqlite_repository import (
    SQLiteInstanceDefinitionRepository,
)


@pytest.fixture
def environment(tmp_path):
    repository = SQLiteInstanceDefinitionRepository(
        tmp_path / "edit_channels.sqlite3"
    )

    app = FastAPI()
    app.include_router(build_admin_router(repository))

    try:
        yield TestClient(app), repository
    finally:
        repository.close()


def create_bot(client, repository, mode="whatsapp"):
    response = client.post(
        "/admin/clients",
        data={
            "name": "Demo Canales",
            "template_id": "professional_services",
            "channel_mode": mode,
        },
        follow_redirects=False,
    )

    assert response.status_code == 303

    return repository.list_all()[0]


def update_bot(client, definition, **overrides):
    instance = build_instance_from_definition(definition)

    data = {
        "name": definition.name,
        "default_language": instance.default_language,
        "timezone": "Europe/Madrid",
        "whatsapp_phone_number_id": (
            definition.whatsapp_phone_number_id or ""
        ),
        "calendar_id": definition.calendar_id or "",
    }

    data.update(overrides)

    return client.post(
        f"/admin/clients/{definition.id}",
        data=data,
        follow_redirects=False,
    )


def test_edit_form_shows_three_modes(environment):
    client, repository = environment
    definition = create_bot(client, repository)

    response = client.get(
        f"/admin/clients/{definition.id}/edit"
    )

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
def test_bot_can_change_channel(
    environment, mode, expected
):
    client, repository = environment
    definition = create_bot(client, repository)

    response = update_bot(
        client,
        definition,
        channel_mode=mode,
    )

    assert response.status_code == 303

    saved = repository.get(definition.id)

    assert saved.channels == expected
    assert saved.metadata["channel_mode"] == mode
    assert build_instance_from_definition(
        saved
    ).channels == expected


def test_existing_mode_is_preserved(environment):
    client, repository = environment

    definition = create_bot(
        client, repository, mode="both"
    )

    response = update_bot(
        client,
        definition,
        name="Nombre actualizado",
    )

    assert response.status_code == 303

    saved = repository.get(definition.id)

    assert saved.name == "Nombre actualizado"
    assert saved.channels == ["whatsapp", "web"]
    assert saved.metadata["channel_mode"] == "both"


def test_invalid_mode_is_rejected(environment):
    client, repository = environment
    definition = create_bot(client, repository)

    response = update_bot(
        client,
        definition,
        channel_mode="telegram",
    )

    assert response.status_code == 422

    saved = repository.get(definition.id)

    assert saved.channels == ["whatsapp"]
    assert saved.metadata["channel_mode"] == "whatsapp"


def test_legacy_configuration_is_preserved(environment):
    client, repository = environment

    original = build_client_definition("tarot_alvin")

    legacy = replace(
        original,
        id="legacy_edit_demo",
        name="Legacy Edit Demo",
        whatsapp_phone_number_id=None,
    )

    repository.save(legacy)

    before = repository.get(legacy.id)

    response = client.get(
        f"/admin/clients/{legacy.id}/edit"
    )

    assert response.status_code == 200
    assert 'value="legacy"' in response.text

    updated = update_bot(client, before)

    assert updated.status_code == 303

    saved = repository.get(legacy.id)

    assert saved.channels == before.channels
    assert saved.metadata == before.metadata


def test_legacy_bot_can_enable_both(environment):
    client, repository = environment

    original = build_client_definition("tarot_alvin")

    legacy = replace(
        original,
        id="legacy_upgrade_demo",
        name="Legacy Upgrade Demo",
        whatsapp_phone_number_id=None,
    )

    repository.save(legacy)

    response = update_bot(
        client,
        legacy,
        channel_mode="both",
    )

    assert response.status_code == 303

    saved = repository.get(legacy.id)

    assert saved.channels == ["whatsapp", "web"]
    assert saved.metadata["channel_mode"] == "both"
