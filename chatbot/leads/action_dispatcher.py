from __future__ import annotations

import hashlib
import json
from typing import Any

from chatbot.leads.models import Lead
from chatbot.leads.repository import LeadRepository


class LeadCaptureActionDispatcher:
    """
    Persist lead-capture actions emitted by conversation capabilities.
    """

    def __init__(
        self,
        repository: LeadRepository,
    ) -> None:
        self._repository = repository

    def dispatch(
        self,
        *,
        instance: Any,
        session_id: str,
        action: dict,
    ) -> bool:
        if action.get("type") != "lead_capture":
            return False

        name = action.get("name")
        phone = action.get("phone")
        reason = action.get("reason")
        client_id = getattr(instance, "id", None)

        if not all(
            isinstance(value, str) and value.strip()
            for value in (
                client_id,
                session_id,
                name,
                phone,
                reason,
            )
        ):
            return False

        lead = Lead(
            action_id=self._action_id(
                client_id=client_id,
                session_id=session_id,
                name=name,
                phone=phone,
                reason=reason,
            ),
            client_id=client_id,
            session_id=session_id,
            name=name,
            phone=phone,
            reason=reason,
        )

        self._repository.save(lead)

        return True

    @staticmethod
    def _action_id(
        *,
        client_id: str,
        session_id: str,
        name: str,
        phone: str,
        reason: str,
    ) -> str:
        payload = json.dumps(
            {
                "client_id": client_id,
                "session_id": session_id,
                "name": name,
                "phone": phone,
                "reason": reason,
            },
            sort_keys=True,
            ensure_ascii=True,
        )

        return hashlib.sha256(
            payload.encode("utf-8")
        ).hexdigest()
