import pytest

from chatbot.capabilities.booking.capability import BookingCapability
from chatbot.registry import CapabilityRegistry


def test_register_capability():
    registry = CapabilityRegistry()

    registry.register(BookingCapability)

    assert registry.available() == ["booking"]


def test_create_capability_instance():
    registry = CapabilityRegistry()

    registry.register(BookingCapability)

    capability = registry.create("booking")

    assert isinstance(capability, BookingCapability)


def test_register_duplicate_capability_raises_error():
    registry = CapabilityRegistry()

    registry.register(BookingCapability)

    with pytest.raises(ValueError):
        registry.register(BookingCapability)


def test_create_unknown_capability_raises_error():
    registry = CapabilityRegistry()

    with pytest.raises(ValueError):
        registry.create("unknown")


def test_available_returns_sorted_capabilities():
    registry = CapabilityRegistry()

    registry.register(BookingCapability)

    assert registry.available() == ["booking"]