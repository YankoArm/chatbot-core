from __future__ import annotations

import re
import unicodedata
from typing import Any

from chatbot.capabilities.base_capability import BaseCapability
from chatbot.language import Language
from chatbot.phone import (
    PhoneNumberError,
    PhoneNumberService,
)
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

_FOLLOW_UP_KEY = "lead_capture_follow_up"

_FOLLOW_UP_KEYWORDS = {
    "genial",
    "perfecto",
    "perfecta",
    "estupendo",
    "estupenda",
    "gracias",
    "muchas gracias",
    "de acuerdo",
    "vale",
    "ok",
    "okay",
}



class LeadCaptureCapability(BaseCapability):
    """
    Collect contact details before requesting human attention.
    """

    name = "lead_capture"
    version = "1.0"
    dependencies: list[str] = []

    def __init__(
        self,
        phone_number_service: (
            PhoneNumberService | None
        ) = None,
    ) -> None:
        self._phone_number_service = (
            phone_number_service
            or PhoneNumberService(
                default_region="ES",
            )
        )

    def can_handle(
        self,
        context: Any,
        message: str,
    ) -> bool:
        normalized_message = self._normalize_text(
            message
        )

        if (
            context.get_variable(_FOLLOW_UP_KEY) is True
            and normalized_message in _FOLLOW_UP_KEYWORDS
        ):
            return True

        return (
            normalized_message
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
            if context.get_variable(_FOLLOW_UP_KEY) is True:
                context.remove_variable(_FOLLOW_UP_KEY)

                return Response(
                    text=(
                        "Me alegra que todo haya sido de tu agrado. "
                        "El equipo revisará tu solicitud y se pondrá en "
                        "contacto contigo lo antes posible."
                    ),
                    metadata={
                        "capability": self.name,
                        "handled": True,
                        "lead_capture_follow_up": True,
                    },
                )
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

        if self._normalize_text(value) in {
            "cancelar",
            "salir",
            "no",
            "cancel",
            "exit",
            "stop",
        }:
            context.remove_variable(_STATE_KEY)
            context.clear_active_capability()

            return Response(
                text=(
                    "De acuerdo. He cancelado la solicitud "
                    "de atención."
                ),
                metadata={
                    "capability": self.name,
                    "handled": True,
                    "lead_capture_cancelled": True,
                },
            )

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
            try:
                phone = self._phone_number_service.normalize(
                    value,
                )
            except PhoneNumberError:
                return self._response(
                    context=context,
                    text=(
                        "No parece un número de teléfono válido. "
                        "Inténtalo de nuevo, incluyendo el prefijo "
                        "si lo necesitas."
                    ),
                    step="phone",
                )

            state["phone"] = phone
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
        context.set_variable(
            _FOLLOW_UP_KEY,
            True,
        )
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
