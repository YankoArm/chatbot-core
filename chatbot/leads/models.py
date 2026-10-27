from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


def _utc_now_iso() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


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
    status: str = "pending"
    created_at: str = field(
        default_factory=_utc_now_iso
    )
    contacted_at: str | None = None
