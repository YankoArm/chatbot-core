from abc import ABC, abstractmethod
from typing import Any


class BaseCapability(ABC):
    """
    Base class for every FlowForge Capability.

    A Capability describes reusable business behavior.
    It can register framework resources and handle conversation messages.
    """

    name: str
    version: str = "1.0"
    dependencies: list[str] = []

    def register(self, context: dict[str, Any]) -> None:
        """
        Register flows, actions, connectors or configuration needed by this capability.

        This method is optional because not every Capability needs to register resources.
        """
        return None

    @abstractmethod
    def can_handle(self, context: Any, message: str) -> bool:
        """
        Return True if this Capability can handle the incoming message.
        """
        pass

    @abstractmethod
    def handle(self, context: Any, message: str) -> Any:
        """
        Process the incoming message and return a response.
        """
        pass