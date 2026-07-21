from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True, frozen=True)
class OutgoingMessage:
    """
    Transport-independent message returned to an external channel.
    """

    text: str
    metadata: dict[str, Any] = field(default_factory=dict)