from __future__ import annotations

from typing import Type

from chatbot.capabilities.base_capability import BaseCapability


class CapabilityRegistry:
    """
    Registry responsible for discovering and creating capabilities.

    It stores capability classes (not instances) and creates a new
    instance whenever requested.
    """

    def __init__(self) -> None:
        self._capabilities: dict[str, Type[BaseCapability]] = {}

    def register(self, capability_class: Type[BaseCapability]) -> None:
        """
        Register a capability class.
        """

        name = capability_class.name

        if name in self._capabilities:
            raise ValueError(
                f"Capability '{name}' is already registered."
            )

        self._capabilities[name] = capability_class

    def create(self, name: str) -> BaseCapability:
        """
        Create a new capability instance.
        """

        capability_class = self._capabilities.get(name)

        if capability_class is None:
            raise ValueError(
                f"Unknown capability '{name}'."
            )

        return capability_class()

    def available(self) -> list[str]:
        """
        Return all registered capability names.
        """

        return sorted(self._capabilities.keys())