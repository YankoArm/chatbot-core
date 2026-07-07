from abc import ABC, abstractmethod
from typing import Any


class BaseCapability(ABC):
    name: str
    version: str = "1.0"
    dependencies: list[str] = []

    @abstractmethod
    def register(self, context: dict[str, Any]) -> None:
        """
        Register flows, actions, connectors or configuration needed by this capability.
        """
        pass