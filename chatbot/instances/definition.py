from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from chatbot.activation import ActivationConfig


@dataclass(slots=True)
class InstanceDefinition:
    """
    Client-specific FlowForge configuration.

    An InstanceDefinition references a reusable business template and
    declares only the values that differ for a particular client.
    """

    id: str
    name: str
    template_id: str

    default_language: str | None = None
    supported_languages: list[str] | None = None

    channels: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)
    disabled_capabilities: list[str] = field(
        default_factory=list
    )

    connectors: list[str] = field(default_factory=list)
    disabled_connectors: list[str] = field(
        default_factory=list
    )

    knowledge_path: str | None = None

    settings: dict[str, Any] = field(
        default_factory=dict
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    activation: ActivationConfig | None = None