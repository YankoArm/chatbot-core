from __future__ import annotations

from typing import Any
import re
import unicodedata

from chatbot.booking import BookingState, BookingStep
from chatbot.capabilities.base_capability import BaseCapability
from chatbot.responses import Response
from datetime import datetime

_BOOKING_KEYWORDS = (
    "reserv",
    "cita",
    "appointment",
    "book",
    "booking",
)


class BookingCapability(BaseCapability):
    name = "booking"
    version = "1.0"
    dependencies = []

    def register(self, context: dict[str, Any]) -> None:
        context.setdefault("flows", [])
        context.setdefault("actions", [])

        context["flows"].append("booking_flow")

    def can_handle(self, context: Any, message: str) -> bool:
        text = message.lower().strip()

        return any(
            keyword in text
            for keyword in _BOOKING_KEYWORDS
        )

    def handle(self, context: Any, message: str) -> Response:
        if context.booking is None:
            return self._start_booking(context)

        handler = self._get_step_handler(context.booking.next_step)

        if handler is not None:
            return handler(context, message)

        return Response(
            text="La reserva ya está en curso.",
            metadata={
                "capability": self.name,
                "handled": True,
                "booking_step": context.booking.next_step.value,
            },
        )

    def _start_booking(self, context: Any) -> Response:
        context.booking = BookingState()

        return self._response(
            context,
            "Perfecto. Vamos a reservar una cita. ¿Cómo te llamas?",
        )

    def _handle_name(self, context: Any, message: str) -> Response:
        name = message.strip()

        if not self._is_valid_name(name):
            return self._response(
                context,
                "Ese nombre no parece válido. ¿Puedes escribirlo de nuevo?",
            )

        context.booking.name = name

        return self._response(
            context,
            (
                f"Encantado, {context.booking.name}. "
                "¿Cuál es tu número de teléfono?"
            ),
        )

    def _handle_phone(self, context: Any, message: str) -> Response:
        phone = message.strip()

        if not phone.isdigit():
            return self._response(
                context,
                "El teléfono no parece válido. ¿Puedes escribirlo de nuevo?"
            )
            
        context.booking.phone = phone

        return self._response(
            context,
            "¿Para qué día quieres la cita?",
        )

    def _handle_date(
        self,
        context: Any,
        message: str,
    ) -> Response:
        date = message.strip()

        if self._asks_for_available_dates(date):
            available_dates = self._get_available_dates()

            if not available_dates:
                return self._response(
                    context,
                    (
                        "Ahora mismo no tengo fechas disponibles. "
                        "Inténtalo de nuevo más adelante."
                    ),
                )

            formatted_dates = ", ".join(available_dates)

            return self._response(
                context,
                (
                    "Tengo disponibilidad para los siguientes días: "
                    f"{formatted_dates}. "
                    "¿Qué día prefieres?"
                ),
            )

        if not self._is_valid_date(date):
            return self._response(
                context,
                (
                    "La fecha no parece válida. "
                    "Escríbela con el formato DD/MM/YYYY "
                    "o pregúntame qué días hay disponibles."
                ),
            )

        context.booking.date = date

        return self._response(
            context,
            "¿A qué hora quieres la cita?",
        )
    
    def _handle_time(self, context: Any, message: str) -> Response:
        time = message.strip()

        if not self._is_valid_time(time):
            return self._response(
                context,
                (
                    "La hora no parece válida. "
                    "Escríbela con el formato HH:MM."
                ),
            )

        context.booking.time = time

        return self._response(
            context,
            (
                f"Perfecto, {context.booking.name}. "
                f"He registrado tu solicitud para "
                f"{context.booking.date} a las "
                f"{context.booking.time}."
            ),
        )

    def _get_step_handler(self, step: BookingStep):
        if step is BookingStep.NAME:
            return self._handle_name

        if step is BookingStep.PHONE:
            return self._handle_phone

        if step is BookingStep.DATE:
            return self._handle_date

        if step is BookingStep.TIME:
            return self._handle_time

        return None

    def _response(
        self,
        context: Any,
        text: str,
    ) -> Response:
        return Response(
            text=text,
            metadata={
                "capability": self.name,
                "handled": True,
                "booking_step": context.booking.next_step.value,
            },
        )

    def _is_valid_name(self, name: str) -> bool:
        return len(name) >= 2 and not name.isdigit()

    def _is_valid_date(self, date: str) -> bool:
        try:
            datetime.strptime(date, "%d/%m/%Y")
        except ValueError:
            return False

        return True

    def _is_valid_time(self, time: str) -> bool:
        try:
            datetime.strptime(time, "%H:%M")
        except ValueError:
            return False

        return True

    @staticmethod
    def _asks_for_available_dates(message: str) -> bool:
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

        normalized = re.sub(
            r"\s+",
            " ",
            normalized,
        ).strip()

        availability_words = {
            "disponible",
            "disponibles",
            "disponibilidad",
            "libre",
            "libres",
            "hueco",
            "huecos",
        }

        date_words = {
            "dia",
            "dias",
            "fecha",
            "fechas",
        }

        question_patterns = (
            "que dias hay",
            "que fechas hay",
            "que dias tienes",
            "que fechas tienes",
            "que dias quedan",
            "que fechas quedan",
            "cuando hay",
            "cuando tienes",
            "cuando puedo",
            "cuando se puede",
            "dime los dias",
            "dime las fechas",
            "mostrar dias",
            "mostrar fechas",
            "ver dias",
            "ver fechas",
        )

        words = set(normalized.split())

        has_availability_word = bool(
            words & availability_words
        )

        has_date_word = bool(
            words & date_words
        )

        matches_question_pattern = any(
            pattern in normalized
            for pattern in question_patterns
        )

        return (
            matches_question_pattern
            or has_availability_word
            or (
                has_date_word
                and normalized.startswith(
                    (
                        "que ",
                        "cuales ",
                        "dime ",
                        "cuando ",
                    )
                )
            )
        )

    def _get_available_dates(self) -> list[str]:
        return [
            "28/07/2026",
            "29/07/2026",
            "30/07/2026",
        ]