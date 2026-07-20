from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Instance:
    """
    Declarative description of a FlowForge assistant.

    An Instance describes what the assistant is, not how it runs.
    Runtime objects are created later by Bootstrap.
    """

    id: str
    name: str
    default_language: str = "es"
    channels: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)
    connectors: list[str] = field(default_factory=list)
    knowledge_path: str | None = None
    settings: dict[str, Any] = field(default_factory=dict)