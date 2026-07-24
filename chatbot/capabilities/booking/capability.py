from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from typing import Any, Callable

from chatbot.booking import BookingState, BookingStep
from chatbot.capabilities.base_capability import BaseCapability
from chatbot.responses import Response


_BOOKING_KEYWORDS = (
    "reserv",
    "cita",
    "appointment",
    "book",
    "booking",
)

_CONFIRMATION_WORDS = {
    "si",
    "confirmar",
    "confirmo",
    "confirmada",
    "correcto",
    "correcta",
    "vale",
    "ok",
    "de acuerdo",
    "adelante",
}

_CANCELLATION_WORDS = {
    "no",
    "cancelar",
    "cancelo",
    "cancelada",
    "anular",
    "anulo",
    "salir",
}


class BookingCapability(BaseCapability):
    name = "booking"
    version = "1.0"
    dependencies: list[str] = []

    def register(self, context: dict[str, Any]) -> None:
        context.setdefault("flows", [])
        context.setdefault("actions", [])

        context["flows"].append("booking_flow")

    def can_handle(
        self,
        context: Any,
        message: str,
    ) -> bool:
        text = self._normalize_text(message)

        return any(
            keyword in text
            for keyword in _BOOKING_KEYWORDS
        )

    def handle(
        self,
        context: Any,
        message: str,
    ) -> Response:
        if context.booking is None:
            return self._start_booking(context)

        handler = self._get_step_handler(
            context.booking.next_step
        )

        if handler is not None:
            return handler(context, message)

        return self._response(
            context,
            "La reserva ya está confirmada.",
        )

    def _start_booking(
        self,
        context: Any,
    ) -> Response:
        context.booking = BookingState()

        return self._response(
            context,
            (
                "Perfecto. Vamos a reservar una cita. "
                "¿Cómo te llamas?"
            ),
        )

    def _handle_name(
        self,
        context: Any,
        message: str,
    ) -> Response:
        name = message.strip()

        if not self._is_valid_name(name):
            return self._response(
                context,
                (
                    "Ese nombre no parece válido. "
                    "¿Puedes escribirlo de nuevo?"
                ),
            )

        context.booking.name = name

        return self._response(
            context,
            (
                f"Encantado, {context.booking.name}. "
                "¿Cuál es tu número de teléfono?"
            ),
        )

    def _handle_phone(
        self,
        context: Any,
        message: str,
    ) -> Response:
        phone = self._normalize_phone(message)

        if not self._is_valid_phone(phone):
            return self._response(
                context,
                (
                    "El teléfono no parece válido. "
                    "Escribe únicamente entre 7 y 15 dígitos."
                ),
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

    def _handle_time(
        self,
        context: Any,
        message: str,
    ) -> Response:
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
            self._build_confirmation_summary(
                context.booking
            ),
        )

    def _handle_confirmation(
        self,
        context: Any,
        message: str,
    ) -> Response:
        normalized = self._normalize_text(message)

        if normalized in _CONFIRMATION_WORDS:
            context.booking.confirm()

            return self._response(
                context,
                (
                    "Reserva confirmada correctamente.\n\n"
                    f"Nombre: {context.booking.name}\n"
                    f"Teléfono: {context.booking.phone}\n"
                    f"Fecha: {context.booking.date}\n"
                    f"Hora: {context.booking.time}"
                ),
            )

        if normalized in _CANCELLATION_WORDS:
            context.booking = None

            return Response(
                text=(
                    "La solicitud de reserva ha sido cancelada. "
                    "Puedes empezar otra cuando quieras."
                ),
                metadata={
                    "capability": self.name,
                    "handled": True,
                    "booking_step": "cancelled",
                },
            )

        return self._response(
            context,
            (
                "No he entendido la respuesta. "
                "Escribe «sí» para confirmar "
                "o «no» para cancelar."
            ),
        )

    def _get_step_handler(
        self,
        step: BookingStep,
    ) -> Callable[[Any, str], Response] | None:
        handlers = {
            BookingStep.NAME: self._handle_name,
            BookingStep.PHONE: self._handle_phone,
            BookingStep.DATE: self._handle_date,
            BookingStep.TIME: self._handle_time,
            BookingStep.CONFIRMATION: self._handle_confirmation,
        }

        return handlers.get(step)

    def _build_confirmation_summary(
        self,
        booking: BookingState,
    ) -> str:
        return (
            "Estos son los datos de tu reserva:\n\n"
            f"Nombre: {booking.name}\n"
            f"Teléfono: {booking.phone}\n"
            f"Fecha: {booking.date}\n"
            f"Hora: {booking.time}\n\n"
            "¿Quieres confirmar la reserva? "
            "Responde «sí» para confirmar "
            "o «no» para cancelar."
        )

    def _response(
        self,
        context: Any,
        text: str,
    ) -> Response:
        booking_step = (
            context.booking.next_step.value
            if context.booking is not None
            else "inactive"
        )

        return Response(
            text=text,
            metadata={
                "capability": self.name,
                "handled": True,
                "booking_step": booking_step,
            },
        )

    @staticmethod
    def _is_valid_name(name: str) -> bool:
        cleaned_name = name.strip()

        if len(cleaned_name) < 2:
            return False

        return any(
            character.isalpha()
            for character in cleaned_name
        )

    @staticmethod
    def _normalize_phone(phone: str) -> str:
        return re.sub(
            r"[\s()+-]",
            "",
            phone.strip(),
        )

    @staticmethod
    def _is_valid_phone(phone: str) -> bool:
        return (
            phone.isdigit()
            and 7 <= len(phone) <= 15
        )

    @staticmethod
    def _is_valid_date(date: str) -> bool:
        try:
            parsed_date = datetime.strptime(
                date,
                "%d/%m/%Y",
            )
        except ValueError:
            return False

        return parsed_date.date() >= datetime.now().date()

    @staticmethod
    def _is_valid_time(time: str) -> bool:
        try:
            datetime.strptime(
                time,
                "%H:%M",
            )
        except ValueError:
            return False

        return True

    @classmethod
    def _asks_for_available_dates(
        cls,
        message: str,
    ) -> bool:
        normalized = cls._normalize_text(message)

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

        starts_as_question = normalized.startswith(
            (
                "que ",
                "cuales ",
                "dime ",
                "cuando ",
            )
        )

        return (
            matches_question_pattern
            or has_availability_word
            or (
                has_date_word
                and starts_as_question
            )
        )

    @staticmethod
    def _normalize_text(message: str) -> str:
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

    def _get_available_dates(self) -> list[str]:
        return [
            "28/07/2026",
            "29/07/2026",
            "30/07/2026",
        ]