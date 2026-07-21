from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True, frozen=True)
class IncomingMessage:
    """
    Transport-independent message received from an external channel.
    """

    session_id: str
    text: str
    sender_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.session_id.strip():
            raise ValueError("session_id cannot be empty.")

        if not self.text.strip():
            raise ValueError("text cannot be empty.")