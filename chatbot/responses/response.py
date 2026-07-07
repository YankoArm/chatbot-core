from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Response:
    """
    Standard response object returned by FlowForge components.

    A Response represents what the assistant wants to send back to the user,
    plus optional metadata for orchestration, connectors or UI rendering.
    """

    text: str
    actions: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    next_capability: str | None = None

    def has_next_capability(self) -> bool:
        return self.next_capability is not None