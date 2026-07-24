from __future__ import annotations

from chatbot.capabilities.booking import BookingCapability
from chatbot.capabilities.greeting import GreetingCapability
from chatbot.registry import DefaultCapabilityRegistry


def test_default_registry_contains_builtin_capabilities() -> None:
    registry = DefaultCapabilityRegistry()

    available = registry.available()

    assert "greeting" in available
    assert "booking" in available


def test_default_registry_creates_greeting_capability() -> None:
    registry = DefaultCapabilityRegistry()

    capability = registry.create("greeting")

    assert isinstance(capability, GreetingCapability)
    assert capability.name == "greeting"


def test_default_registry_creates_booking_capability() -> None:
    registry = DefaultCapabilityRegistry()

    capability = registry.create("booking")

    assert isinstance(capability, BookingCapability)
    assert capability.name == "booking"


def test_registry_creates_new_instance_each_time() -> None:
    registry = DefaultCapabilityRegistry()

    first = registry.create("greeting")
    second = registry.create("greeting")

    assert first is not second