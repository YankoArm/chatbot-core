from __future__ import annotations

import pytest

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
    assert (
        "/admin/clients/hairdressing_demo/schedule"
        in response.text
    )
    assert "Horarios y reservas" in response.text
    assert (
        "/admin/clients/hairdressing_demo/business"
        in response.text
    )
    assert "Información del negocio" in response.text
    assert (
        "/admin/clients/hairdressing_demo/faq"
        in response.text
    )
    assert "Preguntas frecuentes" in response.text


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

def test_admin_edit_client_page_shows_stored_values(
) -> None:
    repository = (
        SQLiteInstanceDefinitionRepository(
            database_path=":memory:",
        )
    )
    repository.save(
        InstanceDefinition(
            id="salon_centro",
            name="Salón Centro",
            template_id="hairdressing",
            default_language="es",
            supported_languages=[
                "es",
                "en",
            ],
            settings={
                "branding": {
                    "display_name": "Salón Centro",
                },
                "booking": {
                    "timezone": "Europe/Madrid",
                },
            },
            metadata={
                "admin_status": "draft",
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

    response = client.get(
        "/admin/clients/salon_centro/edit"
    )

    assert response.status_code == 200
    assert "Editar bot" in response.text
    assert 'value="Salón Centro"' in response.text
    assert 'name="default_language"' in response.text
    assert 'value="es" selected' in response.text
    assert 'name="timezone"' in response.text
    assert 'value="Europe/Madrid"' in response.text
    assert (
        'action="/admin/clients/salon_centro"'
        in response.text
    )

    repository.close()


def test_admin_updates_basic_client_configuration(
) -> None:
    repository = (
        SQLiteInstanceDefinitionRepository(
            database_path=":memory:",
        )
    )
    repository.save(
        InstanceDefinition(
            id="salon_centro",
            name="Salón Centro",
            template_id="hairdressing",
            default_language="es",
            supported_languages=[
                "es",
                "en",
            ],
            settings={
                "branding": {
                    "display_name": "Salón Centro",
                },
                "booking": {
                    "timezone": "Europe/Madrid",
                },
                "services": [
                    {
                        "id": "haircut",
                        "name": {
                            "es": "Corte",
                        },
                    },
                ],
            },
            metadata={
                "admin_status": "draft",
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

    response = client.post(
        "/admin/clients/salon_centro",
        data={
            "name": "Salón Centro Renovado",
            "default_language": "en",
            "timezone": "Atlantic/Canary",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers[
        "location"
    ] == (
        "/admin/clients/salon_centro"
    )

    updated_definition = repository.get(
        "salon_centro"
    )

    assert updated_definition is not None
    assert updated_definition.name == (
        "Salón Centro Renovado"
    )
    assert updated_definition.default_language == "en"
    assert updated_definition.settings[
        "branding"
    ]["display_name"] == (
        "Salón Centro Renovado"
    )
    assert updated_definition.settings[
        "booking"
    ]["timezone"] == (
        "Atlantic/Canary"
    )

    assert updated_definition.settings[
        "services"
    ] == [
        {
            "id": "haircut",
            "name": {
                "es": "Corte",
            },
        },
    ]

    repository.close()

def test_admin_can_edit_builtin_client_into_repository(
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

    edit_response = client.get(
        "/admin/clients/hairdressing_demo/edit"
    )

    assert edit_response.status_code == 200
    assert "Salón Estilo" in edit_response.text
    assert "Europe/Madrid" in edit_response.text

    update_response = client.post(
        "/admin/clients/hairdressing_demo",
        data={
            "name": "Salón Estilo Renovado",
            "default_language": "es",
            "timezone": "Europe/Madrid",
        },
        follow_redirects=False,
    )

    assert update_response.status_code == 303

    stored_definition = repository.get(
        "hairdressing_demo"
    )

    assert stored_definition is not None
    assert stored_definition.name == (
        "Salón Estilo Renovado"
    )
    assert stored_definition.settings[
        "services"
    ]
    assert stored_definition.metadata[
        "business_type"
    ] == "hairdressing"

    repository.close()

def test_admin_services_page_lists_configured_services(
) -> None:
    repository = (
        SQLiteInstanceDefinitionRepository(
            database_path=":memory:",
        )
    )
    repository.save(
        InstanceDefinition(
            id="salon_centro",
            name="Salón Centro",
            template_id="hairdressing",
            settings={
                "services": [
                    {
                        "id": "haircut",
                        "name": {
                            "es": "Corte",
                            "en": "Haircut",
                        },
                        "duration_minutes": 30,
                        "price": {
                            "type": "fixed",
                            "amount_cents": 2000,
                            "currency": "EUR",
                        },
                    },
                ],
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

    response = client.get(
        "/admin/clients/salon_centro/services"
    )

    assert response.status_code == 200
    assert "Servicios y precios" in response.text
    assert "Corte" in response.text
    assert "30 minutos" in response.text
    assert "20,00 €" in response.text
    assert (
        "/admin/clients/salon_centro/services/new"
        in response.text
    )
    assert (
        "/admin/clients/salon_centro/services/haircut/edit"
        in response.text
    )
    assert (
        "/admin/clients/salon_centro/services/haircut/delete"
        in response.text
    )

    repository.close()


def test_admin_adds_service_to_client_definition(
) -> None:
    repository = (
        SQLiteInstanceDefinitionRepository(
            database_path=":memory:",
        )
    )
    repository.save(
        InstanceDefinition(
            id="salon_centro",
            name="Salón Centro",
            template_id="hairdressing",
            settings={
                "services": [],
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

    form_response = client.get(
        "/admin/clients/salon_centro/services/new"
    )

    assert form_response.status_code == 200
    assert "Añadir servicio" in form_response.text
    assert 'name="service_id"' in form_response.text
    assert 'name="name_es"' in form_response.text
    assert 'name="duration_minutes"' in form_response.text
    assert 'name="price_type"' in form_response.text
    assert 'name="price_amount"' in form_response.text

    create_response = client.post(
        "/admin/clients/salon_centro/services",
        data={
            "service_id": "highlights",
            "name_es": "Mechas",
            "name_en": "Highlights",
            "duration_minutes": "120",
            "price_type": "from",
            "price_amount": "65.50",
            "currency": "EUR",
        },
        follow_redirects=False,
    )

    assert create_response.status_code == 303
    assert create_response.headers[
        "location"
    ] == (
        "/admin/clients/salon_centro/services"
    )

    updated_definition = repository.get(
        "salon_centro"
    )

    assert updated_definition is not None
    assert updated_definition.settings[
        "services"
    ] == [
        {
            "id": "highlights",
            "name": {
                "es": "Mechas",
                "en": "Highlights",
            },
            "duration_minutes": 120,
            "price": {
                "type": "from",
                "amount_cents": 6550,
                "currency": "EUR",
            },
        },
    ]

    repository.close()

def test_admin_edits_existing_service(
) -> None:
    repository = (
        SQLiteInstanceDefinitionRepository(
            database_path=":memory:",
        )
    )
    repository.save(
        InstanceDefinition(
            id="salon_centro",
            name="Salón Centro",
            template_id="hairdressing",
            settings={
                "services": [
                    {
                        "id": "highlights",
                        "name": {
                            "es": "Mechas",
                            "en": "Highlights",
                        },
                        "duration_minutes": 120,
                        "price": {
                            "type": "from",
                            "amount_cents": 6500,
                            "currency": "EUR",
                        },
                    },
                    {
                        "id": "haircut",
                        "name": {
                            "es": "Corte",
                        },
                        "duration_minutes": 30,
                        "price": {
                            "type": "fixed",
                            "amount_cents": 2000,
                            "currency": "EUR",
                        },
                    },
                ],
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

    form_response = client.get(
        "/admin/clients/salon_centro/services/highlights/edit"
    )

    assert form_response.status_code == 200
    assert "Editar servicio" in form_response.text
    assert 'value="Mechas"' in form_response.text
    assert 'value="120"' in form_response.text
    assert 'value="65.00"' in form_response.text

    update_response = client.post(
        "/admin/clients/salon_centro/services/highlights",
        data={
            "name_es": "Mechas premium",
            "name_en": "Premium highlights",
            "duration_minutes": "150",
            "price_type": "fixed",
            "price_amount": "80.00",
            "currency": "EUR",
        },
        follow_redirects=False,
    )

    assert update_response.status_code == 303
    assert update_response.headers[
        "location"
    ] == (
        "/admin/clients/salon_centro/services"
    )

    updated_definition = repository.get(
        "salon_centro"
    )

    assert updated_definition is not None

    services = updated_definition.settings[
        "services"
    ]

    assert len(services) == 2
    assert services[0] == {
        "id": "highlights",
        "name": {
            "es": "Mechas premium",
            "en": "Premium highlights",
        },
        "duration_minutes": 150,
        "price": {
            "type": "fixed",
            "amount_cents": 8000,
            "currency": "EUR",
        },
    }
    assert services[1]["id"] == "haircut"

    repository.close()


def test_admin_deletes_service_after_confirmation(
) -> None:
    repository = (
        SQLiteInstanceDefinitionRepository(
            database_path=":memory:",
        )
    )
    repository.save(
        InstanceDefinition(
            id="salon_centro",
            name="Salón Centro",
            template_id="hairdressing",
            settings={
                "services": [
                    {
                        "id": "haircut",
                        "name": {
                            "es": "Corte",
                        },
                        "duration_minutes": 30,
                        "price": {
                            "type": "fixed",
                            "amount_cents": 2000,
                            "currency": "EUR",
                        },
                    },
                ],
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

    confirmation_response = client.get(
        "/admin/clients/salon_centro/services/haircut/delete"
    )

    assert confirmation_response.status_code == 200
    assert "Eliminar servicio" in confirmation_response.text
    assert "Corte" in confirmation_response.text
    assert (
        'action="/admin/clients/salon_centro/services/haircut/delete"'
        in confirmation_response.text
    )

    delete_response = client.post(
        "/admin/clients/salon_centro/services/haircut/delete",
        follow_redirects=False,
    )

    assert delete_response.status_code == 303
    assert delete_response.headers[
        "location"
    ] == (
        "/admin/clients/salon_centro/services"
    )

    updated_definition = repository.get(
        "salon_centro"
    )

    assert updated_definition is not None
    assert updated_definition.settings[
        "services"
    ] == []

    repository.close()

def test_admin_schedule_page_shows_booking_configuration(
) -> None:
    repository = (
        SQLiteInstanceDefinitionRepository(
            database_path=":memory:",
        )
    )
    repository.save(
        InstanceDefinition(
            id="salon_centro",
            name="Salón Centro",
            template_id="hairdressing",
            settings={
                "booking": {
                    "timezone": "Europe/Madrid",
                    "business_hours": {
                        "monday": [
                            ["09:30", "13:30"],
                            ["16:00", "20:00"],
                        ],
                        "tuesday": [],
                    },
                    "rules": {
                        "appointment_duration_minutes": 30,
                        "slot_interval_minutes": 30,
                        "buffer_before_minutes": 0,
                        "buffer_after_minutes": 10,
                        "minimum_notice_hours": 2,
                        "maximum_advance_days": 30,
                        "allow_past_bookings": False,
                    },
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

    response = client.get(
        "/admin/clients/salon_centro/schedule"
    )

    assert response.status_code == 200
    assert "Horarios y reservas" in response.text
    assert 'value="Europe/Madrid"' in response.text
    assert 'name="monday_enabled"' in response.text
    assert 'value="09:30"' in response.text
    assert 'value="13:30"' in response.text
    assert 'value="16:00"' in response.text
    assert 'value="20:00"' in response.text
    assert 'name="slot_interval_minutes"' in response.text
    assert 'value="30"' in response.text
    assert 'name="maximum_advance_days"' in response.text

    repository.close()


def test_admin_updates_booking_schedule_and_rules(
) -> None:
    repository = (
        SQLiteInstanceDefinitionRepository(
            database_path=":memory:",
        )
    )
    repository.save(
        InstanceDefinition(
            id="salon_centro",
            name="Salón Centro",
            template_id="hairdressing",
            settings={
                "booking": {
                    "timezone": "Europe/Madrid",
                    "business_hours": {},
                    "rules": {
                        "appointment_duration_minutes": 30,
                        "slot_interval_minutes": 30,
                        "buffer_before_minutes": 0,
                        "buffer_after_minutes": 0,
                        "minimum_notice_hours": 2,
                        "maximum_advance_days": 30,
                        "allow_past_bookings": False,
                    },
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

    response = client.post(
        "/admin/clients/salon_centro/schedule",
        data={
            "timezone": "Europe/Madrid",
            "monday_enabled": "on",
            "monday_start_1": "09:00",
            "monday_end_1": "14:00",
            "monday_start_2": "16:00",
            "monday_end_2": "20:00",
            "tuesday_enabled": "on",
            "tuesday_start_1": "10:00",
            "tuesday_end_1": "18:00",
            "appointment_duration_minutes": "45",
            "slot_interval_minutes": "15",
            "buffer_before_minutes": "5",
            "buffer_after_minutes": "10",
            "minimum_notice_hours": "4",
            "maximum_advance_days": "60",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == (
        "/admin/clients/salon_centro"
    )

    stored_definition = repository.get(
        "salon_centro"
    )

    assert stored_definition is not None

    booking = stored_definition.settings[
        "booking"
    ]

    assert booking["timezone"] == "Europe/Madrid"
    assert booking["business_hours"]["monday"] == [
        ["09:00", "14:00"],
        ["16:00", "20:00"],
    ]
    assert booking["business_hours"]["tuesday"] == [
        ["10:00", "18:00"],
    ]
    assert booking["business_hours"]["wednesday"] == []
    assert booking["rules"] == {
        "appointment_duration_minutes": 45,
        "slot_interval_minutes": 15,
        "buffer_before_minutes": 5,
        "buffer_after_minutes": 10,
        "minimum_notice_hours": 4,
        "maximum_advance_days": 60,
        "allow_past_bookings": False,
    }

    repository.close()

@pytest.mark.parametrize(
    (
        "overrides",
        "removed_fields",
        "expected_message",
    ),
    [
        (
            {
                "timezone": "Invalid/Timezone",
            },
            (),
            "zona horaria indicada no es válida",
        ),
        (
            {
                "monday_start_1": "",
                "monday_end_1": "",
            },
            (),
            "Cada día abierto necesita",
        ),
        (
            {
                "monday_end_1": "08:00",
            },
            (),
            "hora de cierre debe ser posterior",
        ),
        (
            {
                "monday_start_2": "13:00",
                "monday_end_2": "16:00",
            },
            (),
            "franjas de un mismo día no pueden solaparse",
        ),
        (
            {
                "slot_interval_minutes": "0",
            },
            (),
            "intervalo entre horas debe ser igual o mayor que 1",
        ),
        (
            {},
            (
                "monday_enabled",
            ),
            "Debes abrir al menos un día",
        ),
    ],
)
def test_admin_rejects_invalid_booking_schedule(
    overrides: dict[str, str],
    removed_fields: tuple[str, ...],
    expected_message: str,
) -> None:
    original_settings = {
        "booking": {
            "timezone": "Europe/Madrid",
            "business_hours": {
                "monday": [
                    ["09:00", "14:00"],
                ],
            },
            "rules": {
                "appointment_duration_minutes": 30,
                "slot_interval_minutes": 30,
                "buffer_before_minutes": 0,
                "buffer_after_minutes": 0,
                "minimum_notice_hours": 2,
                "maximum_advance_days": 30,
                "allow_past_bookings": False,
            },
        },
    }

    repository = (
        SQLiteInstanceDefinitionRepository(
            database_path=":memory:",
        )
    )
    repository.save(
        InstanceDefinition(
            id="salon_centro",
            name="Salón Centro",
            template_id="hairdressing",
            settings=original_settings,
        )
    )

    app = build_whatsapp_api(
        message_handler=NoOpMessageHandler(),
        instance_definition_repository=repository,
    )
    client = TestClient(
        app
    )

    submitted_data = {
        "timezone": "Europe/Madrid",
        "monday_enabled": "on",
        "monday_start_1": "09:00",
        "monday_end_1": "14:00",
        "monday_start_2": "",
        "monday_end_2": "",
        "appointment_duration_minutes": "30",
        "slot_interval_minutes": "30",
        "buffer_before_minutes": "0",
        "buffer_after_minutes": "0",
        "minimum_notice_hours": "2",
        "maximum_advance_days": "30",
    }
    submitted_data.update(
        overrides
    )

    for field_name in removed_fields:
        submitted_data.pop(
            field_name,
            None,
        )

    response = client.post(
        "/admin/clients/salon_centro/schedule",
        data=submitted_data,
        follow_redirects=False,
    )

    assert response.status_code == 400
    assert expected_message in response.text

    stored_definition = repository.get(
        "salon_centro"
    )

    assert stored_definition is not None
    assert stored_definition.settings == (
        original_settings
    )

    repository.close()

def test_admin_faq_page_lists_configured_entries(
) -> None:
    repository = (
        SQLiteInstanceDefinitionRepository(
            database_path=":memory:",
        )
    )
    repository.save(
        InstanceDefinition(
            id="salon_centro",
            name="Salón Centro",
            template_id="hairdressing",
            settings={
                "knowledge": {
                    "faq": {
                        "location": {
                            "question": "¿Dónde estamos?",
                            "keywords": [
                                "donde estais",
                                "direccion",
                            ],
                            "answers": {
                                "es": (
                                    "Estamos en Calle Mayor, 10."
                                ),
                                "en": (
                                    "We are at 10 Calle Mayor."
                                ),
                            },
                        },
                    },
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

    response = client.get(
        "/admin/clients/salon_centro/faq"
    )

    assert response.status_code == 200
    assert "Preguntas frecuentes" in response.text
    assert "¿Dónde estamos?" in response.text
    assert "Estamos en Calle Mayor, 10." in response.text
    assert "donde estais" in response.text
    assert (
        "/admin/clients/salon_centro/faq/new"
        in response.text
    )
    assert (
        "/admin/clients/salon_centro/faq/location/edit"
        in response.text
    )
    assert (
        "/admin/clients/salon_centro/faq/location/delete"
        in response.text
    )

    repository.close()


def test_admin_adds_faq_entry_to_client_definition(
) -> None:
    repository = (
        SQLiteInstanceDefinitionRepository(
            database_path=":memory:",
        )
    )
    repository.save(
        InstanceDefinition(
            id="salon_centro",
            name="Salón Centro",
            template_id="hairdressing",
            settings={
                "knowledge": {
                    "company": {
                        "name": "Salón Centro",
                    },
                    "faq": {},
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

    form_response = client.get(
        "/admin/clients/salon_centro/faq/new"
    )

    assert form_response.status_code == 200
    assert "Añadir pregunta frecuente" in (
        form_response.text
    )

    response = client.post(
        "/admin/clients/salon_centro/faq",
        data={
            "faq_id": "payment_methods",
            "question": "¿Cómo puedo pagar?",
            "keywords": (
                "formas de pago\n"
                "pagar con tarjeta\n"
                "aceptais bizum"
            ),
            "answer_es": (
                "Aceptamos tarjeta, efectivo y Bizum."
            ),
            "answer_en": (
                "We accept card, cash and Bizum."
            ),
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == (
        "/admin/clients/salon_centro/faq"
    )

    stored_definition = repository.get(
        "salon_centro"
    )

    assert stored_definition is not None

    knowledge = stored_definition.settings[
        "knowledge"
    ]

    assert knowledge["company"] == {
        "name": "Salón Centro",
    }
    assert knowledge["faq"]["payment_methods"] == {
        "question": "¿Cómo puedo pagar?",
        "keywords": [
            "formas de pago",
            "pagar con tarjeta",
            "aceptais bizum",
        ],
        "answers": {
            "es": (
                "Aceptamos tarjeta, efectivo y Bizum."
            ),
            "en": (
                "We accept card, cash and Bizum."
            ),
        },
    }

    repository.close()

def test_admin_edits_existing_faq_entry(
) -> None:
    repository = (
        SQLiteInstanceDefinitionRepository(
            database_path=":memory:",
        )
    )
    repository.save(
        InstanceDefinition(
            id="salon_centro",
            name="Salón Centro",
            template_id="hairdressing",
            settings={
                "knowledge": {
                    "company": {
                        "name": "Salón Centro",
                    },
                    "faq": {
                        "location": {
                            "question": "¿Dónde estamos?",
                            "keywords": [
                                "direccion",
                            ],
                            "answers": {
                                "es": "Dirección anterior.",
                            },
                        },
                        "payment_methods": {
                            "question": "¿Cómo puedo pagar?",
                            "keywords": [
                                "formas de pago",
                            ],
                            "answers": {
                                "es": "Aceptamos tarjeta.",
                            },
                        },
                    },
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

    form_response = client.get(
        "/admin/clients/salon_centro/faq/location/edit"
    )

    assert form_response.status_code == 200
    assert "Editar pregunta frecuente" in (
        form_response.text
    )
    assert "¿Dónde estamos?" in form_response.text
    assert "Dirección anterior." in form_response.text

    response = client.post(
        "/admin/clients/salon_centro/faq/location",
        data={
            "question": "¿Dónde está el salón?",
            "keywords": (
                "donde estais\n"
                "direccion\n"
                "como llegar"
            ),
            "answer_es": (
                "Estamos en Calle Mayor, 10."
            ),
            "answer_en": (
                "We are at 10 Calle Mayor."
            ),
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == (
        "/admin/clients/salon_centro/faq"
    )

    stored_definition = repository.get(
        "salon_centro"
    )

    assert stored_definition is not None

    knowledge = stored_definition.settings[
        "knowledge"
    ]

    assert knowledge["company"] == {
        "name": "Salón Centro",
    }
    assert knowledge["faq"]["location"] == {
        "question": "¿Dónde está el salón?",
        "keywords": [
            "donde estais",
            "direccion",
            "como llegar",
        ],
        "answers": {
            "es": "Estamos en Calle Mayor, 10.",
            "en": "We are at 10 Calle Mayor.",
        },
    }
    assert "payment_methods" in knowledge["faq"]

    repository.close()


def test_admin_deletes_faq_entry_after_confirmation(
) -> None:
    repository = (
        SQLiteInstanceDefinitionRepository(
            database_path=":memory:",
        )
    )
    repository.save(
        InstanceDefinition(
            id="salon_centro",
            name="Salón Centro",
            template_id="hairdressing",
            settings={
                "knowledge": {
                    "company": {
                        "name": "Salón Centro",
                    },
                    "faq": {
                        "location": {
                            "question": "¿Dónde estamos?",
                            "keywords": [
                                "direccion",
                            ],
                            "answers": {
                                "es": "Estamos en Madrid.",
                            },
                        },
                        "payment_methods": {
                            "question": "¿Cómo puedo pagar?",
                            "keywords": [
                                "formas de pago",
                            ],
                            "answers": {
                                "es": "Aceptamos tarjeta.",
                            },
                        },
                    },
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

    confirmation_response = client.get(
        "/admin/clients/salon_centro/faq/location/delete"
    )

    assert confirmation_response.status_code == 200
    assert "Eliminar pregunta frecuente" in (
        confirmation_response.text
    )
    assert "¿Dónde estamos?" in (
        confirmation_response.text
    )

    response = client.post(
        "/admin/clients/salon_centro/faq/location/delete",
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == (
        "/admin/clients/salon_centro/faq"
    )

    stored_definition = repository.get(
        "salon_centro"
    )

    assert stored_definition is not None

    knowledge = stored_definition.settings[
        "knowledge"
    ]

    assert "location" not in knowledge["faq"]
    assert "payment_methods" in knowledge["faq"]
    assert knowledge["company"] == {
        "name": "Salón Centro",
    }

    repository.close()

@pytest.mark.parametrize(
    (
        "overrides",
        "expected_message",
    ),
    [
        (
            {
                "faq_id": "Payment Methods",
            },
            "identificador debe comenzar por una letra",
        ),
        (
            {
                "faq_id": "location",
            },
            "Ya existe una pregunta con ese identificador",
        ),
        (
            {
                "question": "",
            },
            "La pregunta es obligatoria",
        ),
        (
            {
                "keywords": "   ",
            },
            "Añade al menos una palabra",
        ),
        (
            {
                "answer_es": "",
            },
            "respuesta en español es obligatoria",
        ),
    ],
)
def test_admin_rejects_invalid_faq_entry(
    overrides: dict[str, str],
    expected_message: str,
) -> None:
    original_settings = {
        "knowledge": {
            "company": {
                "name": "Salón Centro",
            },
            "faq": {
                "location": {
                    "question": "¿Dónde estamos?",
                    "keywords": [
                        "direccion",
                    ],
                    "answers": {
                        "es": "Estamos en Madrid.",
                    },
                },
            },
        },
    }

    repository = (
        SQLiteInstanceDefinitionRepository(
            database_path=":memory:",
        )
    )
    repository.save(
        InstanceDefinition(
            id="salon_centro",
            name="Salón Centro",
            template_id="hairdressing",
            settings=original_settings,
        )
    )

    app = build_whatsapp_api(
        message_handler=NoOpMessageHandler(),
        instance_definition_repository=repository,
    )
    client = TestClient(
        app
    )

    submitted_data = {
        "faq_id": "payment_methods",
        "question": "¿Cómo puedo pagar?",
        "keywords": (
            "formas de pago\n"
            "pagar con tarjeta"
        ),
        "answer_es": "Aceptamos tarjeta.",
        "answer_en": "We accept cards.",
    }
    submitted_data.update(
        overrides
    )

    response = client.post(
        "/admin/clients/salon_centro/faq",
        data=submitted_data,
        follow_redirects=False,
    )

    assert response.status_code == 400
    assert expected_message in response.text

    stored_definition = repository.get(
        "salon_centro"
    )

    assert stored_definition is not None
    assert stored_definition.settings == (
        original_settings
    )

    repository.close()

def test_admin_faq_page_includes_and_edits_file_based_entry(
    tmp_path,
) -> None:
    (
        tmp_path / "faq.json"
    ).write_text(
        """
        {
          "location": {
            "keywords": [
              "donde estais",
              "direccion"
            ],
            "answers": {
              "es": "Dirección original.",
              "en": "Original address."
            }
          }
        }
        """,
        encoding="utf-8",
    )

    repository = (
        SQLiteInstanceDefinitionRepository(
            database_path=":memory:",
        )
    )
    repository.save(
        InstanceDefinition(
            id="salon_centro",
            name="Salón Centro",
            template_id="hairdressing",
            knowledge_path=str(
                tmp_path
            ),
            settings={},
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
        "/admin/clients/salon_centro/faq"
    )

    assert list_response.status_code == 200
    assert "location" in list_response.text
    assert "Dirección original." in list_response.text
    assert (
        "/admin/clients/salon_centro/faq/location/edit"
        in list_response.text
    )

    form_response = client.get(
        "/admin/clients/salon_centro/faq/location/edit"
    )

    assert form_response.status_code == 200
    assert "Dirección original." in form_response.text

    response = client.post(
        "/admin/clients/salon_centro/faq/location",
        data={
            "question": "¿Dónde está el salón?",
            "keywords": (
                "donde estais\n"
                "direccion\n"
                "como llegar"
            ),
            "answer_es": "Estamos en Calle Mayor, 10.",
            "answer_en": "We are at 10 Calle Mayor.",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303

    stored_definition = repository.get(
        "salon_centro"
    )

    assert stored_definition is not None

    stored_entry = stored_definition.settings[
        "knowledge"
    ]["faq"]["location"]

    assert stored_entry["answers"]["es"] == (
        "Estamos en Calle Mayor, 10."
    )

    delete_response = client.post(
        "/admin/clients/salon_centro/faq/location/delete",
        follow_redirects=False,
    )

    assert delete_response.status_code == 303

    deleted_definition = repository.get(
        "salon_centro"
    )

    assert deleted_definition is not None
    assert deleted_definition.settings[
        "knowledge"
    ]["faq"]["location"] is None

    updated_list_response = client.get(
        "/admin/clients/salon_centro/faq"
    )

    assert "Dirección original." not in (
        updated_list_response.text
    )

    repository.close()

def test_admin_business_page_shows_company_and_messages(
) -> None:
    repository = (
        SQLiteInstanceDefinitionRepository(
            database_path=":memory:",
        )
    )
    repository.save(
        InstanceDefinition(
            id="salon_centro",
            name="Salón Centro",
            template_id="hairdressing",
            settings={
                "knowledge": {
                    "company": {
                        "name": "Salón Centro",
                        "description": "Peluquería en Madrid.",
                        "phone": "+34600123123",
                        "email": "hola@saloncentro.es",
                        "address": "Calle Mayor, 10",
                        "website": "https://saloncentro.es",
                    },
                    "greetings": {
                        "welcome": {
                            "es": "¡Hola! ¿En qué podemos ayudarte?",
                            "en": "Hello! How can we help you?",
                        },
                    },
                    "human_transfer": {
                        "response": {
                            "es": "Te pondremos en contacto con el salón.",
                            "en": "We will connect you with the salon.",
                        },
                    },
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

    response = client.get(
        "/admin/clients/salon_centro/business"
    )

    assert response.status_code == 200
    assert "Información del negocio" in response.text
    assert 'value="Salón Centro"' in response.text
    assert "Peluquería en Madrid." in response.text
    assert 'value="+34600123123"' in response.text
    assert 'value="hola@saloncentro.es"' in response.text
    assert 'value="Calle Mayor, 10"' in response.text
    assert 'value="https://saloncentro.es"' in response.text
    assert "¡Hola! ¿En qué podemos ayudarte?" in (
        response.text
    )
    assert "Te pondremos en contacto con el salón." in (
        response.text
    )

    repository.close()


def test_admin_updates_company_and_custom_messages(
) -> None:
    repository = (
        SQLiteInstanceDefinitionRepository(
            database_path=":memory:",
        )
    )
    repository.save(
        InstanceDefinition(
            id="salon_centro",
            name="Salón Centro",
            template_id="hairdressing",
            settings={
                "knowledge": {
                    "faq": {
                        "location": {
                            "keywords": [
                                "direccion",
                            ],
                            "answers": {
                                "es": "Estamos en Madrid.",
                            },
                        },
                    },
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

    response = client.post(
        "/admin/clients/salon_centro/business",
        data={
            "company_name": "Salón Centro Renovado",
            "description": "Especialistas en color y corte.",
            "phone": "+34600987654",
            "email": "contacto@saloncentro.es",
            "address": "Gran Vía, 20, Madrid",
            "website": "https://saloncentro.es",
            "greeting_es": (
                "¡Hola! Bienvenido a Salón Centro."
            ),
            "greeting_en": (
                "Hello! Welcome to Salón Centro."
            ),
            "human_transfer_es": (
                "Avisaremos al equipo para que te atienda."
            ),
            "human_transfer_en": (
                "We will notify the team to assist you."
            ),
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == (
        "/admin/clients/salon_centro"
    )

    stored_definition = repository.get(
        "salon_centro"
    )

    assert stored_definition is not None

    knowledge = stored_definition.settings[
        "knowledge"
    ]

    assert knowledge["faq"]["location"]["answers"]["es"] == (
        "Estamos en Madrid."
    )
    assert knowledge["company"] == {
        "name": "Salón Centro Renovado",
        "description": "Especialistas en color y corte.",
        "phone": "+34600987654",
        "email": "contacto@saloncentro.es",
        "address": "Gran Vía, 20, Madrid",
        "website": "https://saloncentro.es",
    }
    assert knowledge["greetings"]["welcome"] == {
        "es": "¡Hola! Bienvenido a Salón Centro.",
        "en": "Hello! Welcome to Salón Centro.",
    }
    assert knowledge["human_transfer"]["response"] == {
        "es": "Avisaremos al equipo para que te atienda.",
        "en": "We will notify the team to assist you.",
    }

    repository.close()

@pytest.mark.parametrize(
    (
        "overrides",
        "expected_message",
    ),
    [
        (
            {
                "company_name": "",
            },
            "nombre comercial es obligatorio",
        ),
        (
            {
                "email": "correo-invalido",
            },
            "correo electrónico no es válido",
        ),
        (
            {
                "website": "saloncentro.es",
            },
            "sitio web debe ser una URL completa",
        ),
        (
            {
                "greeting_es": "",
            },
            "saludo en español es obligatorio",
        ),
        (
            {
                "human_transfer_es": "",
            },
            "mensaje de transferencia en español es obligatorio",
        ),
    ],
)
def test_admin_rejects_invalid_business_information(
    overrides: dict[str, str],
    expected_message: str,
) -> None:
    original_settings = {
        "knowledge": {
            "faq": {
                "location": {
                    "keywords": [
                        "direccion",
                    ],
                    "answers": {
                        "es": "Estamos en Madrid.",
                    },
                },
            },
        },
    }

    repository = (
        SQLiteInstanceDefinitionRepository(
            database_path=":memory:",
        )
    )
    repository.save(
        InstanceDefinition(
            id="salon_centro",
            name="Salón Centro",
            template_id="hairdressing",
            settings=original_settings,
        )
    )

    app = build_whatsapp_api(
        message_handler=NoOpMessageHandler(),
        instance_definition_repository=repository,
    )
    client = TestClient(
        app
    )

    submitted_data = {
        "company_name": "Salón Centro",
        "description": "Peluquería en Madrid.",
        "phone": "+34600123123",
        "email": "hola@saloncentro.es",
        "address": "Calle Mayor, 10",
        "website": "https://saloncentro.es",
        "greeting_es": "¡Hola! ¿En qué podemos ayudarte?",
        "greeting_en": "Hello! How can we help you?",
        "human_transfer_es": (
            "Avisaremos al equipo para que te atienda."
        ),
        "human_transfer_en": (
            "We will notify the team to assist you."
        ),
    }
    submitted_data.update(
        overrides
    )

    response = client.post(
        "/admin/clients/salon_centro/business",
        data=submitted_data,
        follow_redirects=False,
    )

    assert response.status_code == 400
    assert expected_message in response.text

    stored_definition = repository.get(
        "salon_centro"
    )

    assert stored_definition is not None
    assert stored_definition.settings == (
        original_settings
    )

    repository.close()

def test_admin_preview_uses_current_bot_messages_safely(
) -> None:
    repository = (
        SQLiteInstanceDefinitionRepository(
            database_path=":memory:",
        )
    )
    repository.save(
        InstanceDefinition(
            id="salon_centro",
            name="Salón Centro",
            template_id="hairdressing",
            settings={
                "knowledge": {
                    "greetings": {
                        "welcome": {
                            "es": (
                                "¡Hola! Bienvenido a Salón Centro."
                            ),
                        },
                    },
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

    page_response = client.get(
        "/admin/clients/salon_centro/preview"
    )

    response = client.post(
        "/admin/clients/salon_centro/preview",
        data={
            "message": "hola",
            "history": "[]",
        },
    )

    assert page_response.status_code == 200
    assert "Prueba el asistente" in page_response.text
    assert "Las reservas están desactivadas" in page_response.text

    assert response.status_code == 200
    assert "hola" in response.text
    assert (
        "¡Hola! Bienvenido a Salón Centro."
        in response.text
    )

    repository.close()

def test_admin_preview_explains_that_booking_is_disabled(
) -> None:
    repository = (
        SQLiteInstanceDefinitionRepository(
            database_path=":memory:",
        )
    )
    repository.save(
        InstanceDefinition(
            id="salon_centro",
            name="Salón Centro",
            template_id="hairdressing",
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
        "/admin/clients/salon_centro/preview",
        data={
            "message": "Quiero reservar una cita",
            "history": "[]",
        },
    )

    assert response.status_code == 200
    assert (
        "Las reservas no se pueden probar aquí"
        in response.text
    )

    repository.close()

def test_admin_changes_stored_bot_lifecycle_status(
) -> None:
    repository = (
        SQLiteInstanceDefinitionRepository(
            database_path=":memory:",
        )
    )
    repository.save(
        InstanceDefinition(
            id="salon_centro",
            name="Salón Centro",
            template_id="hairdressing",
            metadata={
                "admin_status": "draft",
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

    response = client.post(
        "/admin/clients/salon_centro/status",
        data={
            "status": "active",
        },
        follow_redirects=False,
    )

    updated_definition = repository.get(
        "salon_centro"
    )

    assert response.status_code == 303
    assert response.headers["location"] == (
        "/admin/clients/salon_centro"
    )
    assert updated_definition is not None
    assert updated_definition.metadata[
        "admin_status"
    ] == "active"

    repository.close()
def test_admin_client_detail_links_to_bot_status(
) -> None:
    client = build_test_client()

    response = client.get(
        "/admin/clients/hairdressing_demo"
    )

    assert response.status_code == 200
    assert (
        'href="/admin/clients/hairdressing_demo/status"'
        in response.text
    )
    assert "Estado del bot" in response.text
def test_admin_requires_login_when_credentials_are_configured(
) -> None:
    app = build_whatsapp_api(
        message_handler=NoOpMessageHandler(),
        admin_password="test-admin-password",
        admin_session_secret="test-session-secret",
    )
    client = TestClient(app)

    response = client.get(
        "/admin",
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == (
        "/admin/login"
    )


def test_admin_login_grants_access_to_admin_routes(
) -> None:
    app = build_whatsapp_api(
        message_handler=NoOpMessageHandler(),
        admin_password="test-admin-password",
        admin_session_secret="test-session-secret",
    )
    client = TestClient(app)

    login_response = client.post(
        "/admin/login",
        data={
            "password": "test-admin-password",
        },
        follow_redirects=False,
    )

    assert login_response.status_code == 303
    assert login_response.headers["location"] == "/admin"

    admin_response = client.get("/admin")

    assert admin_response.status_code == 200
    assert "FlowForge Admin" in admin_response.text


def test_admin_login_rejects_invalid_password(
) -> None:
    app = build_whatsapp_api(
        message_handler=NoOpMessageHandler(),
        admin_password="test-admin-password",
        admin_session_secret="test-session-secret",
    )
    client = TestClient(app)

    response = client.post(
        "/admin/login",
        data={
            "password": "incorrect-password",
        },
        follow_redirects=False,
    )

    assert response.status_code == 401
    assert "Contraseña incorrecta" in response.text
def test_authenticated_admin_post_requires_same_origin(
) -> None:
    app = build_whatsapp_api(
        message_handler=NoOpMessageHandler(),
        admin_password="test-admin-password",
        admin_session_secret="test-session-secret",
    )
    client = TestClient(app)

    client.post(
        "/admin/login",
        data={
            "password": "test-admin-password",
        },
    )

    response = client.post(
        "/admin/logout",
        follow_redirects=False,
    )

    assert response.status_code == 403
    assert "Solicitud no autorizada" in response.text


def test_authenticated_admin_post_accepts_same_origin(
) -> None:
    app = build_whatsapp_api(
        message_handler=NoOpMessageHandler(),
        admin_password="test-admin-password",
        admin_session_secret="test-session-secret",
    )
    client = TestClient(app)

    client.post(
        "/admin/login",
        data={
            "password": "test-admin-password",
        },
    )

    response = client.post(
        "/admin/logout",
        headers={
            "Origin": "http://testserver",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == (
        "/admin/login"
    )
def test_admin_updates_tenant_provisioning_identifiers(
) -> None:
    repository = SQLiteInstanceDefinitionRepository(
        database_path=":memory:",
    )
    repository.save(
        InstanceDefinition(
            id="salon_centro",
            name="Salón Centro",
            template_id="hairdressing",
            default_language="es",
            supported_languages=[
                "es",
                "en",
            ],
            settings={
                "branding": {
                    "display_name": "Salón Centro",
                },
                "booking": {
                    "timezone": "Europe/Madrid",
                },
            },
        )
    )

    app = build_whatsapp_api(
        message_handler=NoOpMessageHandler(),
        instance_definition_repository=repository,
    )
    client = TestClient(app)

    response = client.post(
        "/admin/clients/salon_centro",
        data={
            "name": "Salón Centro",
            "default_language": "es",
            "timezone": "Europe/Madrid",
            "whatsapp_phone_number_id": (
                "phone-number-centro"
            ),
            "calendar_id": "calendar-centro",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303

    definition = repository.get("salon_centro")

    assert definition is not None
    assert definition.whatsapp_phone_number_id == (
        "phone-number-centro"
    )
    assert definition.calendar_id == "calendar-centro"

    repository.close()
def test_admin_rejects_reused_whatsapp_phone_number_id(
) -> None:
    repository = SQLiteInstanceDefinitionRepository(
        database_path=":memory:",
    )

    for client_id, phone_number_id in (
        ("salon_norte", "phone-norte"),
        ("salon_sur", "phone-sur"),
    ):
        repository.save(
            InstanceDefinition(
                id=client_id,
                name=client_id.replace("_", " ").title(),
                template_id="hairdressing",
                default_language="es",
                supported_languages=[
                    "es",
                    "en",
                ],
                whatsapp_phone_number_id=phone_number_id,
                settings={
                    "branding": {
                        "display_name": client_id,
                    },
                    "booking": {
                        "timezone": "Europe/Madrid",
                    },
                },
            )
        )

    app = build_whatsapp_api(
        message_handler=NoOpMessageHandler(),
        instance_definition_repository=repository,
    )
    client = TestClient(app)

    response = client.post(
        "/admin/clients/salon_sur",
        data={
            "name": "Salón Sur",
            "default_language": "es",
            "timezone": "Europe/Madrid",
            "whatsapp_phone_number_id": "phone-norte",
            "calendar_id": "calendar-sur",
        },
        follow_redirects=False,
    )

    assert response.status_code == 422
    assert "asociado a otro bot" in response.text

    definition = repository.get("salon_sur")

    assert definition is not None
    assert definition.whatsapp_phone_number_id == (
        "phone-sur"
    )

    repository.close()
def test_admin_rejects_reused_google_calendar_id(
) -> None:
    repository = SQLiteInstanceDefinitionRepository(
        database_path=":memory:",
    )

    for client_id, calendar_id in (
        ("salon_norte", "calendar-norte"),
        ("salon_sur", "calendar-sur"),
    ):
        repository.save(
            InstanceDefinition(
                id=client_id,
                name=client_id.replace("_", " ").title(),
                template_id="hairdressing",
                default_language="es",
                supported_languages=[
                    "es",
                    "en",
                ],
                calendar_id=calendar_id,
                settings={
                    "branding": {
                        "display_name": client_id,
                    },
                    "booking": {
                        "timezone": "Europe/Madrid",
                    },
                },
            )
        )

    app = build_whatsapp_api(
        message_handler=NoOpMessageHandler(),
        instance_definition_repository=repository,
    )
    client = TestClient(app)

    response = client.post(
        "/admin/clients/salon_sur",
        data={
            "name": "Salón Sur",
            "default_language": "es",
            "timezone": "Europe/Madrid",
            "whatsapp_phone_number_id": "phone-sur",
            "calendar_id": "calendar-norte",
        },
        follow_redirects=False,
    )

    assert response.status_code == 422
    assert "Google Calendar ID ya está asociado" in (
        response.text
    )

    definition = repository.get("salon_sur")

    assert definition is not None
    assert definition.calendar_id == "calendar-sur"

    repository.close()