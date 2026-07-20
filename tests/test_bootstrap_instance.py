import pytest

from chatbot.application import Bootstrap
from chatbot.capabilities.booking.capability import BookingCapability
from chatbot.instances import Instance
from chatbot.registry import CapabilityRegistry


def build_registry() -> CapabilityRegistry:
    registry = CapabilityRegistry()
    registry.register(BookingCapability)
    return registry


def test_bootstrap_builds_application_from_instance():
    instance = Instance(
        id="tarot_esmeralda",
        name="Tarot Esmeralda",
        capabilities=["booking"],
    )

    bootstrap = Bootstrap(
        capability_registry=build_registry()
    )

    app = bootstrap.build_from_instance(instance)

    assert app.instance is instance
    assert app.capability_manager.all()[0].name == "booking"
    assert app.info()["capabilities"] == ["booking"]


def test_bootstrap_application_can_process_messages():
    instance = Instance(
        id="tarot_esmeralda",
        name="Tarot Esmeralda",
        capabilities=["booking"],
    )

    bootstrap = Bootstrap(
        capability_registry=build_registry()
    )

    app = bootstrap.build_from_instance(instance)

    response = app.chat(
        session_id="user_1",
        message="Quiero reservar una cita",
    )

    assert response.text == "Booking Capability handled the request."
    assert response.metadata["capability"] == "booking"


def test_bootstrap_builds_instance_without_capabilities():
    instance = Instance(
        id="empty",
        name="Empty Assistant",
    )

    bootstrap = Bootstrap(
        capability_registry=CapabilityRegistry()
    )

    app = bootstrap.build_from_instance(instance)

    assert app.capability_manager.all() == []
    assert app.info()["capabilities"] == []


def test_bootstrap_rejects_unknown_capability():
    instance = Instance(
        id="invalid",
        name="Invalid Assistant",
        capabilities=["unknown"],
    )

    bootstrap = Bootstrap(
        capability_registry=CapabilityRegistry()
    )

    with pytest.raises(
        ValueError,
        match="Unknown capability 'unknown'",
    ):
        bootstrap.build_from_instance(instance)