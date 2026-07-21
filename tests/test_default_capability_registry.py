from __future__ import annotations

from chatbot.capabilities.greeting import GreetingCapability
from chatbot.registry import DefaultCapabilityRegistry


def test_default_registry_contains_greeting() -> None:
    registry = DefaultCapabilityRegistry()

    assert "greeting" in registry.available()


def test_default_registry_creates_greeting_capability() -> None:
    registry = DefaultCapabilityRegistry()

    capability = registry.create("greeting")

    assert isinstance(capability, GreetingCapability)
    assert capability.name == "greeting"


def test_registry_creates_new_instance_each_time() -> None:
    registry = DefaultCapabilityRegistry()

    first = registry.create("greeting")
    second = registry.create("greeting")

    assert first is not second