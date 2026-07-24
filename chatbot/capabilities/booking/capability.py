from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from typing import Any, Callable

from chatbot.booking import BookingState, BookingStep
from chatbot.capabilities.base_capability import BaseCapability
from chatbot.language import Language
from chatbot.responses import Response


_BOOKING_KEYWORDS = {
    Language.ES: (
        "reserv",
        "cita",
        "pedir hora",
        "agendar",
    ),
    Language.EN: (
        "appointment",
        "book",
        "booking",
        "schedule",
        "reservation",
    ),
}

_CONFIRMATION_WORDS = {
    Language.ES: {
        "si",
        "confirmar",
        "confirmo",
        "confirmada",
        "correcto",
        "correcta",
        "vale",
        "de acuerdo",
        "adelante",
        "ok",
    },
    Language.EN: {
        "yes",
        "confirm",
        "confirmed",
        "correct",
        "okay",
        "go ahead",
        "proceed",
        "sure",
        "ok",
    },
}

_CANCELLATION_WORDS = {
    Language.ES: {
        "no",
        "cancelar",
        "cancelo",
        "cancelada",
        "anular",
        "anulo",
        "salir",
    },
    Language.EN: {
        "no",
        "cancel",
        "cancel it",
        "stop",
        "exit",
        "leave",
        "never mind",
        "nevermind",
    },
}

_TEXTS = {
    Language.ES: {
        "already_confirmed": "La reserva ya está confirmada.",
        "start": (
            "Perfecto. Vamos a reservar una cita. "
            "¿Cómo te llamas?"
        ),
        "invalid_name": (
            "Ese nombre no parece válido. "
            "¿Puedes escribirlo de nuevo?"
        ),
        "ask_phone": (
            "Encantado, {name}. "
            "¿Cuál es tu número de teléfono?"
        ),
        "invalid_phone": (
            "El teléfono no parece válido. "
            "Escribe únicamente entre 7 y 15 dígitos."
        ),
        "ask_date": "¿Para qué día quieres la cita?",
        "no_available_dates": (
            "Ahora mismo no tengo fechas disponibles. "
            "Inténtalo de nuevo más adelante."
        ),
        "available_dates": (
            "Tengo disponibilidad para los siguientes días: "
            "{dates}. ¿Qué día prefieres?"
        ),
        "invalid_date": (
            "La fecha no parece válida. "
            "Escríbela con el formato DD/MM/YYYY "
            "o pregúntame qué días hay disponibles."
        ),
        "ask_time": "¿A qué hora quieres la cita?",
        "invalid_time": (
            "La hora no parece válida. "
            "Escríbela con el formato HH:MM."
        ),
        "confirmation_summary": (
            "Estos son los datos de tu reserva:\n\n"
            "Nombre: {name}\n"
            "Teléfono: {phone}\n"
            "Fecha: {date}\n"
            "Hora: {time}\n\n"
            "¿Quieres confirmar la reserva? "
            "Responde «sí» para confirmar "
            "o «no» para cancelar."
        ),
        "confirmed": (
            "Reserva confirmada correctamente.\n\n"
            "Nombre: {name}\n"
            "Teléfono: {phone}\n"
            "Fecha: {date}\n"
            "Hora: {time}"
        ),
        "cancelled": (
            "La solicitud de reserva ha sido cancelada. "
            "Puedes empezar otra cuando quieras."
        ),
        "unknown_confirmation": (
            "No he entendido la respuesta. "
            "Escribe «sí» para confirmar "
            "o «no» para cancelar."
        ),
    },
    Language.EN: {
        "already_confirmed": (
            "The appointment has already been confirmed."
        ),
        "start": (
            "Perfect. Let's book an appointment. "
            "What's your name?"
        ),
        "invalid_name": (
            "That name doesn't seem valid. "
            "Could you enter it again?"
        ),
        "ask_phone": (
            "Nice to meet you, {name}. "
            "What's your phone number?"
        ),
        "invalid_phone": (
            "That phone number doesn't seem valid. "
            "Enter between 7 and 15 digits."
        ),
        "ask_date": (
            "What date would you like for your appointment?"
        ),
        "no_available_dates": (
            "There are currently no available dates. "
            "Please try again later."
        ),
        "available_dates": (
            "I have availability on the following dates: "
            "{dates}. Which date would you prefer?"
        ),
        "invalid_date": (
            "That date doesn't seem valid. "
            "Enter it using the DD/MM/YYYY format "
            "or ask which dates are available."
        ),
        "ask_time": (
            "What time would you like the appointment?"
        ),
        "invalid_time": (
            "That time doesn't seem valid. "
            "Enter it using the HH:MM format."
        ),
        "confirmation_summary": (
            "Here are your appointment details:\n\n"
            "Name: {name}\n"
            "Phone: {phone}\n"
            "Date: {date}\n"
            "Time: {time}\n\n"
            "Would you like to confirm the appointment? "
            "Reply “yes” to confirm "
            "or “no” to cancel."
        ),
        "confirmed": (
            "Your appointment has been confirmed.\n\n"
            "Name: {name}\n"
            "Phone: {phone}\n"
            "Date: {date}\n"
            "Time: {time}"
        ),
        "cancelled": (
            "The appointment request has been cancelled. "
            "You can start another one whenever you want."
        ),
        "unknown_confirmation": (
            "I didn't understand that response. "
            "Reply “yes” to confirm "
            "or “no” to cancel."
        ),
    },
}


class BookingCapability(BaseCapability):
    """
    Handle Spanish and English appointment booking conversations.

    The conversation language is detected and persisted by
    FlowForgeApplication before this capability is invoked.
    """

    name = "booking"
    version = "1.1"
    dependencies: list[str] = []

    def register(
        self,
        context: dict[str, Any],
    ) -> None:
        context.setdefault("flows", [])
        context.setdefault("actions", [])

        if "booking_flow" not in context["flows"]:
            context["flows"].append("booking_flow")

    def can_handle(
        self,
        context: Any,
        message: str,
    ) -> bool:
        text = self._normalize_text(message)

        return any(
            keyword in text
            for language_keywords in _BOOKING_KEYWORDS.values()
            for keyword in language_keywords
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
            context=context,
            text=self._text(
                context,
                "already_confirmed",
            ),
        )

    def _start_booking(
        self,
        context: Any,
    ) -> Response:
        context.booking = BookingState()

        return self._response(
            context=context,
            text=self._text(
                context,
                "start",
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
                context=context,
                text=self._text(
                    context,
                    "invalid_name",
                ),
            )

        context.booking.name = name

        return self._response(
            context=context,
            text=self._text(
                context,
                "ask_phone",
                name=name,
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
                context=context,
                text=self._text(
                    context,
                    "invalid_phone",
                ),
            )

        context.booking.phone = phone

        return self._response(
            context=context,
            text=self._text(
                context,
                "ask_date",
            ),
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
                    context=context,
                    text=self._text(
                        context,
                        "no_available_dates",
                    ),
                )

            return self._response(
                context=context,
                text=self._text(
                    context,
                    "available_dates",
                    dates=", ".join(available_dates),
                ),
            )

        if not self._is_valid_date(date):
            return self._response(
                context=context,
                text=self._text(
                    context,
                    "invalid_date",
                ),
            )

        context.booking.date = date

        return self._response(
            context=context,
            text=self._text(
                context,
                "ask_time",
            ),
        )

    def _handle_time(
        self,
        context: Any,
        message: str,
    ) -> Response:
        time = message.strip()

        if not self._is_valid_time(time):
            return self._response(
                context=context,
                text=self._text(
                    context,
                    "invalid_time",
                ),
            )

        context.booking.time = time

        return self._response(
            context=context,
            text=self._build_confirmation_summary(
                context
            ),
        )

    def _handle_confirmation(
        self,
        context: Any,
        message: str,
    ) -> Response:
        normalized = self._normalize_text(message)
        language = self._get_language(context)

        if normalized in _CONFIRMATION_WORDS[language]:
            context.booking.confirm()

            return self._response(
                context=context,
                text=self._text(
                    context,
                    "confirmed",
                    name=context.booking.name,
                    phone=context.booking.phone,
                    date=context.booking.date,
                    time=context.booking.time,
                ),
            )

        if normalized in _CANCELLATION_WORDS[language]:
            context.booking = None
            context.clear_active_capability()

            return Response(
                text=self._text(
                    context,
                    "cancelled",
                ),
                metadata={
                    "capability": self.name,
                    "handled": True,
                    "booking_step": "cancelled",
                    "language": language.value,
                },
            )

        return self._response(
            context=context,
            text=self._text(
                context,
                "unknown_confirmation",
            ),
        )

    def _get_step_handler(
        self,
        step: BookingStep,
    ) -> Callable[[Any, str], Response] | None:
        handlers: dict[
            BookingStep,
            Callable[[Any, str], Response],
        ] = {
            BookingStep.NAME: self._handle_name,
            BookingStep.PHONE: self._handle_phone,
            BookingStep.DATE: self._handle_date,
            BookingStep.TIME: self._handle_time,
            BookingStep.CONFIRMATION: (
                self._handle_confirmation
            ),
        }

        return handlers.get(step)

    def _build_confirmation_summary(
        self,
        context: Any,
    ) -> str:
        booking = context.booking

        return self._text(
            context,
            "confirmation_summary",
            name=booking.name,
            phone=booking.phone,
            date=booking.date,
            time=booking.time,
        )

    def _response(
        self,
        context: Any,
        text: str,
    ) -> Response:
        language = self._get_language(context)

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
                "language": language.value,
            },
        )

    @classmethod
    def _text(
        cls,
        context: Any,
        key: str,
        **values: Any,
    ) -> str:
        language = cls._get_language(context)

        template = _TEXTS[language][key]

        return template.format(**values)

    @staticmethod
    def _get_language(
        context: Any,
    ) -> Language:
        language = getattr(
            context,
            "language",
            None,
        )

        if language in _TEXTS:
            return language

        return Language.ES

    @staticmethod
    def _is_valid_name(
        name: str,
    ) -> bool:
        cleaned_name = name.strip()

        if len(cleaned_name) < 2:
            return False

        return any(
            character.isalpha()
            for character in cleaned_name
        )

    @staticmethod
    def _normalize_phone(
        phone: str,
    ) -> str:
        return re.sub(
            r"[\s()+-]",
            "",
            phone.strip(),
        )

    @staticmethod
    def _is_valid_phone(
        phone: str,
    ) -> bool:
        return (
            phone.isdigit()
            and 7 <= len(phone) <= 15
        )

    @staticmethod
    def _is_valid_date(
        date: str,
    ) -> bool:
        try:
            parsed_date = datetime.strptime(
                date,
                "%d/%m/%Y",
            )
        except ValueError:
            return False

        return (
            parsed_date.date()
            >= datetime.now().date()
        )

    @staticmethod
    def _is_valid_time(
        time: str,
    ) -> bool:
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
            "available",
            "availability",
            "free",
            "opening",
            "openings",
            "slot",
            "slots",
        }

        date_words = {
            "dia",
            "dias",
            "fecha",
            "fechas",
            "day",
            "days",
            "date",
            "dates",
        }

        question_patterns = (
            # Spanish
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

            # English
            "what days are available",
            "what dates are available",
            "which days are available",
            "which dates are available",
            "what days do you have",
            "what dates do you have",
            "when are you available",
            "when can i book",
            "when can i come",
            "show available dates",
            "show me the dates",
            "show me available dates",
            "do you have availability",
            "any available dates",
            "available appointments",
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
                "what ",
                "which ",
                "when ",
                "show ",
                "do ",
                "are ",
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

    def _get_available_dates(
        self,
    ) -> list[str]:
        """
        Temporary availability source.

        Google Calendar will replace this hardcoded implementation.
        """

        return [
            "28/07/2026",
            "29/07/2026",
            "30/07/2026",
        ]