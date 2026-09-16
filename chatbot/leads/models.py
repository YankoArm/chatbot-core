from __future__ import annotations

from dataclasses import dataclass


@dataclass(
    frozen=True,
    slots=True,
)
class Lead:
    """
    One captured contact request from a FlowForge conversation.
    """

    action_id: str
    client_id: str
    session_id: str
    name: str
    phone: str
    reason: str
