from __future__ import annotations

import re
import unicodedata
from typing import Any

from chatbot.capabilities.base_capability import BaseCapability
from chatbot.language import Language
from chatbot.responses import Response


_TRANSFER_KEYWORDS = {
    "hablar con una persona",
    "hablar con alguien",
    "hablar con un agente",
    "hablar con un humano",
    "atencion humana",
    "atencion personal",
    "quiero hablar con alguien",
    "quiero hablar con una persona",
    "speak to a person",
    "speak with a person",
    "speak to an agent",
    "speak with an agent",
    "speak to a human",
    "human support",
    "human assistance",
}

_STATE_KEY = "lead_capture"


class LeadCaptureCapability(BaseCapability):
    """
    Collect contact details before requesting human attention.
    """

    name = "lead_capture"
    version = "1.0"
    dependencies: list[str] = []

    def can_handle(
        self,
        context: Any,
        message: str,
    ) -> bool:
        return (
            self._normalize_text(message)
            in _TRANSFER_KEYWORDS
        )

    def has_active_flow(
        self,
        context: Any,
    ) -> bool:
        return isinstance(
            context.get_variable(_STATE_KEY),
            dict,
        )

    def handle(
        self,
        context: Any,
        message: str,
    ) -> Response:
        state = context.get_variable(_STATE_KEY)

        if not isinstance(state, dict):
            context.set_variable(
                _STATE_KEY,
                {"step": "name"},
            )

            return self._response(
                context=context,
                text=(
                    "Para que una persona pueda ayudarte mejor, "
                    "¿cómo te llamas?"
                ),
                step="name",
            )

        step = state["step"]
        value = message.strip()

        if step == "name":
            state["name"] = value
            state["step"] = "phone"
            context.set_variable(_STATE_KEY, state)

            return self._response(
                context=context,
                text=(
                    f"Gracias, {value}. "
                    "¿Cuál es tu número de teléfono?"
                ),
                step="phone",
            )

        if step == "phone":
            state["phone"] = value
            state["step"] = "reason"
            context.set_variable(_STATE_KEY, state)

            return self._response(
                context=context,
                text=(
                    "Perfecto. Cuéntame brevemente "
                    "qué necesitas."
                ),
                step="reason",
            )

        reason = value
        lead = {
            "type": "lead_capture",
            "status": "captured",
            "name": state["name"],
            "phone": state["phone"],
            "reason": reason,
        }

        context.add_pending_action(lead)
        context.add_pending_action(
            {
                "type": "human_transfer",
                "status": "pending",
                "message": reason,
            }
        )
        context.remove_variable(_STATE_KEY)
        context.clear_active_capability()

        return Response(
            text=(
                "Gracias. He enviado tus datos al equipo para "
                "que una persona continúe la conversación contigo."
            ),
            metadata={
                "capability": self.name,
                "handled": True,
                "lead_captured": True,
                "human_transfer_requested": True,
            },
        )

    def _response(
        self,
        *,
        context: Any,
        text: str,
        step: str,
    ) -> Response:
        language = getattr(
            context,
            "language",
            Language.ES,
        )

        return Response(
            text=text,
            metadata={
                "capability": self.name,
                "handled": True,
                "language": language.value,
                "lead_capture_step": step,
            },
        )

    @staticmethod
    def _normalize_text(
        message: str,
    ) -> str:
        normalized = unicodedata.normalize(
            "NFKD",
            message,
        )

        normalized = "".join(
            character
            for character in normalized
            if not unicodedata.combining(character)
        )

        normalized = normalized.casefold()

        normalized = re.sub(
            r"[^a-z0-9\s]",
            " ",
            normalized,
        )

        return re.sub(
            r"\s+",
            " ",
            normalized,
        ).strip()
