from __future__ import annotations

from fastapi.testclient import TestClient

from chatbot.api.whatsapp_app import (
    build_whatsapp_api,
)
from chatbot.instances import (
    InstanceDefinition,
    SQLiteInstanceDefinitionRepository,
)


class NoOpMessageHandler:
    def handle(
        self,
        payload: dict,
    ) -> None:
        return None


def build_test_client(
) -> TestClient:
    app = build_whatsapp_api(
        message_handler=NoOpMessageHandler(),
    )

    return TestClient(
        app
    )


def test_admin_page_lists_registered_clients(
) -> None:
    client = build_test_client()

    response = client.get(
        "/admin"
    )

    assert response.status_code == 200
    assert response.headers[
        "content-type"
    ].startswith(
        "text/html"
    )

    assert "FlowForge Admin" in response.text
    assert "Salón Estilo" in response.text
    assert "Tarot Alvin" in response.text
    assert "hairdressing_demo" in response.text
    assert "tarot_alvin" in response.text

    assert (
        'href="/admin/clients/hairdressing_demo"'
        in response.text
    )
    assert (
        'href="/admin/clients/tarot_alvin"'
        in response.text
    )


def test_admin_client_page_shows_resolved_configuration(
) -> None:
    client = build_test_client()

    response = client.get(
        "/admin/clients/hairdressing_demo"
    )

    assert response.status_code == 200
    assert response.headers[
        "content-type"
    ].startswith(
        "text/html"
    )

    assert "Salón Estilo" in response.text
    assert "hairdressing" in response.text
    assert "hairdressing_demo" in response.text
    assert "booking" in response.text
    assert "whatsapp" in response.text


def test_admin_page_includes_stored_client_definition(
) -> None:
    repository = (
        SQLiteInstanceDefinitionRepository(
            database_path=":memory:",
        )
    )
    repository.save(
        InstanceDefinition(
            id="salon_norte",
            name="Salón Norte",
            template_id="hairdressing",
            settings={
                "branding": {
                    "display_name": "Salón Norte",
                },
            },
        )
    )

    app = build_whatsapp_api(
        message_handler=NoOpMessageHandler(),
        instance_definition_repository=repository,
    )
    client = TestClient(
        app
    )

    list_response = client.get(
        "/admin"
    )
    detail_response = client.get(
        "/admin/clients/salon_norte"
    )

    assert list_response.status_code == 200
    assert "Salón Norte" in list_response.text
    assert "salon_norte" in list_response.text

    assert detail_response.status_code == 200
    assert "Salón Norte" in detail_response.text
    assert "hairdressing" in detail_response.text
    assert "booking" in detail_response.text
    assert "whatsapp" in detail_response.text

    repository.close()


def test_admin_client_page_returns_not_found_for_unknown_client(
) -> None:
    client = build_test_client()

    response = client.get(
        "/admin/clients/missing-client"
    )

    assert response.status_code == 404

def test_admin_new_client_page_shows_creation_form(
) -> None:
    repository = (
        SQLiteInstanceDefinitionRepository(
            database_path=":memory:",
        )
    )

    app = build_whatsapp_api(
        message_handler=NoOpMessageHandler(),
        instance_definition_repository=repository,
    )
    client = TestClient(
        app
    )

    response = client.get(
        "/admin/clients/new"
    )

    assert response.status_code == 200
    assert "Crear nuevo bot" in response.text
    assert 'name="client_id"' in response.text
    assert 'name="name"' in response.text
    assert 'name="template_id"' in response.text
    assert 'value="hairdressing"' in response.text
    assert 'value="tarot"' in response.text
    assert (
        'action="/admin/clients"'
        in response.text
    )

    repository.close()


def test_admin_creates_client_definition_as_draft(
) -> None:
    repository = (
        SQLiteInstanceDefinitionRepository(
            database_path=":memory:",
        )
    )

    app = build_whatsapp_api(
        message_handler=NoOpMessageHandler(),
        instance_definition_repository=repository,
    )
    client = TestClient(
        app
    )

    response = client.post(
        "/admin/clients",
        data={
            "client_id": "salon_centro",
            "name": "Salón Centro",
            "template_id": "hairdressing",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers[
        "location"
    ] == (
        "/admin/clients/salon_centro"
    )

    stored_definition = repository.get(
        "salon_centro"
    )

    assert stored_definition is not None
    assert stored_definition.id == (
        "salon_centro"
    )
    assert stored_definition.name == (
        "Salón Centro"
    )
    assert stored_definition.template_id == (
        "hairdressing"
    )
    assert stored_definition.settings == {
        "branding": {
            "display_name": "Salón Centro",
        },
    }
    assert stored_definition.metadata[
        "admin_status"
    ] == "draft"

    repository.close()