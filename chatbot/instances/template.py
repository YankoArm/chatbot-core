from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from chatbot.activation import ActivationConfig


@dataclass(slots=True)
class TemplateDefinition:
    """
    Reusable configuration for a type of business.

    A template defines the common defaults shared by assistants belonging
    to the same business category, such as tarot readers, dental clinics
    or hotels.
    """

    id: str
    name: str

    default_language: str = "es"
    supported_languages: list[str] = field(
        default_factory=lambda: ["es"]
    )

    channels: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)
    connectors: list[str] = field(default_factory=list)

    knowledge_path: str | None = None

    settings: dict[str, Any] = field(
        default_factory=dict
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    activation: ActivationConfig = field(
        default_factory=ActivationConfig
    )