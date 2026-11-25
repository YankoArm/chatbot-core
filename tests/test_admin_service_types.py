from copy import deepcopy
from dataclasses import dataclass, field

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatbot.api.admin_services import build_admin_services_router


@dataclass
class DemoDefinition:
    id: str = "demo"
    name: str = "Demo"
    settings: dict = field(default_factory=dict)


class MemoryRepository:
    def __init__(self):
        self.definition = DemoDefinition(settings={
            "services": [{
                "id": "existing",
                "name": {"es": "Original", "en": "Original"},
                "duration_minutes": 30,
                "price": {
                    "type": "fixed",
                    "amount_cents": 2500,
                    "currency": "EUR",
                },
            }],
        })

    def get(self, client_id):
        if client_id == self.definition.id:
            return deepcopy(self.definition)
        return None

    def save(self, definition):
        self.definition = deepcopy(definition)


@pytest.fixture
def panel():
    repository = MemoryRepository()
    app = FastAPI()
    app.include_router(build_admin_services_router(
        instance_definition_repository=repository,
        definition_loader=repository.get,
        page_renderer=lambda **kwargs: kwargs["content"],
    ))
    with TestClient(app) as client:
        yield client, repository


def form_data(service_type):
    return {
        "name_es": "Desarrollo web",
        "name_en": "Web development",
        "service_type": service_type,
        "duration_minutes": "",
        "duration_text": "A consultar",
        "billing_period": "month" if service_type == "recurring" else "once",
        "price_type": "from",
        "price_amount": "200.00",
        "currency": "EUR",
    }


@pytest.mark.parametrize("service_type", ["project", "recurring"])
def test_create_non_appointment_without_minutes(panel, service_type):
    client, repository = panel
    values = form_data(service_type)

    response = client.post(
        "/admin/clients/demo/services",
        data=values,
        follow_redirects=False,
    )

    assert response.status_code == 303, response.text
    saved = repository.definition.settings["services"][-1]
    assert saved["service_type"] == service_type
    assert saved.get("duration_minutes") is None
    assert saved["duration_text"] == "A consultar"
    assert saved["price"]["billing_period"] == values["billing_period"]


@pytest.mark.parametrize("service_type", ["project", "recurring"])
def test_edit_appointment_into_non_appointment(panel, service_type):
    client, repository = panel
    values = form_data(service_type)

    response = client.post(
        "/admin/clients/demo/services/existing",
        data=values,
        follow_redirects=False,
    )

    assert response.status_code == 303, response.text
    saved = repository.definition.settings["services"][0]
    assert saved["id"] == "existing"
    assert saved["service_type"] == service_type
    assert saved.get("duration_minutes") is None
    assert saved["duration_text"] == "A consultar"
    assert saved["price"]["billing_period"] == values["billing_period"]
