from copy import deepcopy

import pytest

from chatbot.booking.services import build_bookable_services


def service_data(service_id="tarot"):
    return {
        "id": service_id,
        "name": {
            "es": "Servicio de prueba",
            "en": "Test service",
        },
        "duration_minutes": 30,
        "price": {
            "type": "fixed",
            "amount_cents": 2500,
            "currency": "EUR",
        },
    }


def test_existing_service_remains_bookable():
    result = build_bookable_services([service_data()])

    assert len(result) == 1
    assert result[0].id == "tarot"
    assert result[0].duration_minutes == 30


@pytest.mark.parametrize("service_type", ["project", "recurring"])
def test_non_appointment_services_are_excluded_from_booking(service_type):
    appointment = service_data()
    other = service_data("website_or_seo")
    other["service_type"] = service_type
    other.pop("duration_minutes")

    result = build_bookable_services([other, appointment])

    assert [service.id for service in result] == ["tarot"]


def test_unknown_service_type_is_rejected():
    service = service_data()
    service["service_type"] = "invalid"

    with pytest.raises(ValueError):
        build_bookable_services([service])


def test_duplicate_ids_are_rejected_across_service_types():
    appointment = service_data()
    project = deepcopy(appointment)
    project["service_type"] = "project"
    project.pop("duration_minutes")

    with pytest.raises(ValueError, match="Duplicate"):
        build_bookable_services([appointment, project])
