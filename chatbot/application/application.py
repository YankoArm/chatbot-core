from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class FlowForgeApplication:
    """
    Runtime representation of a configured FlowForge Instance.

    The Application is the main entry point of the framework.
    It coordinates the core components required to process
    conversations but contains no business-specific logic.

    Responsibilities:
        - Expose the public FlowForge API.
        - Own the runtime components.
        - Delegate conversation processing.

    It never implements business behaviour directly.
    """

    instance: Any
    orchestrator: Any
    capability_manager: Any
    connector_manager: Any | None = None

    def chat(self, session_id: str, message: str):
        """
        Process an incoming user message.
        """
        raise NotImplementedError

    def reset_session(self, session_id: str):
        """
        Reset a conversation session.
        """
        raise NotImplementedError

    def reload(self):
        """
        Reload the current instance configuration.
        """
        raise NotImplementedError

    def info(self) -> dict:
        """
        Return runtime information about the application.
        """
        raise NotImplementedError