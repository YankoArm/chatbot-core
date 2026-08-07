from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True, frozen=True)
class ActivationConfig:
    """
    Declarative activation configuration for an Instance.
    """

    type: str = "always_active"

    phrases: list[str] = field(
        default_factory=list
    )

    prompt_message: str = (
        "This assistant is not active yet."
    )

    activated_message: str = (
        "Assistant activated."
    )

    prompt_cooldown: int = 60

    session_timeout: int | None = None