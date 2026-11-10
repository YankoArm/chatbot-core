import pytest

from chatbot.capabilities.human_transfer.capability import (
    HumanTransferCapability,
)
from chatbot.api.admin_preview import (
    build_client_definition,
    build_instance_from_definition,
)
from chatbot.application.bootstrap import Bootstrap


@pytest.mark.parametrize("message", [
    "Quiero hablar directamente con una persona",
    "Necesito hablar ahora mismo con alguien",
    "Me gustaria hablar personalmente con un agente",
    "I want to speak directly to a person",
    "Can I talk directly with an agent?",
])
def test_natural_human_transfer_requests(message):
    capability = HumanTransferCapability()
    assert capability.can_handle(None, message)


@pytest.mark.parametrize("message", [
    "Me gustaria saber que sesiones tiene",
    "Que precios hay",
    "Puedo hacer una consulta por telefono?",
    "Podrias explicarme las sesiones?",
])
def test_commercial_questions_do_not_request_transfer(message):
    capability = HumanTransferCapability()
    assert not capability.can_handle(None, message)


def test_tarot_routes_natural_request_to_human_transfer():
    definition = build_client_definition("tarot_alvin")
    instance = build_instance_from_definition(definition)
    app = Bootstrap().build_from_instance(instance)

    session = "tarot-natural-human-transfer"

    app.chat(session_id=session, message="hola")
    app.chat(session_id=session, message="TAROT")

    response = app.chat(
        session_id=session,
        message="Quiero hablar directamente con una persona",
    )

    assert response.metadata.get("human_transfer_step") == "reason"

@pytest.mark.parametrize("reason", [
    "Quiero consultar un problema con una reserva",
    "Tengo un problema con mi cita",
    "Necesito ayuda con mi reserva",
])
def test_human_transfer_preserves_booking_related_reason(reason):
    definition = build_client_definition("tarot_alvin")
    instance = build_instance_from_definition(definition)
    app = Bootstrap().build_from_instance(instance)

    session = "transfer-reason-" + str(
        ["Quiero consultar un problema con una reserva",
         "Tengo un problema con mi cita",
         "Necesito ayuda con mi reserva"].index(reason)
    )

    app.chat(session_id=session, message="hola")
    app.chat(session_id=session, message="TAROT")

    start = app.chat(
        session_id=session,
        message="Quiero hablar directamente con una persona",
    )

    assert start.metadata.get("human_transfer_step") == "reason"

    response = app.chat(
        session_id=session,
        message=reason,
    )

    assert response.metadata.get("human_transfer_requested") is True
    assert response.metadata.get("capability") == "human_transfer"


def test_explicit_booking_still_offers_switch_from_human_transfer():
    definition = build_client_definition("tarot_alvin")
    instance = build_instance_from_definition(definition)
    app = Bootstrap().build_from_instance(instance)

    session = "transfer-explicit-booking-switch"

    app.chat(session_id=session, message="hola")
    app.chat(session_id=session, message="TAROT")
    app.chat(
        session_id=session,
        message="Quiero hablar directamente con una persona",
    )

    response = app.chat(
        session_id=session,
        message="Quiero reservar una cita",
    )

    assert response.metadata.get("flow_switch_confirmation") is True
    assert response.metadata.get("flow_switch_to") == "booking"
