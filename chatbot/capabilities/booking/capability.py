from __future__ import annotations

import re

from dataclasses import replace

from chatbot.phone import (
    PhoneNumberError,
    PhoneNumberService,
)

from zoneinfo import ZoneInfo

from chatbot.availability import (
    BookingRules,
    BusinessHours,
)

import unicodedata
from datetime import datetime, timedelta
from typing import Any, Callable

from chatbot.booking.services import BookableService
from chatbot.booking import (
    BookingAlreadyCancelledError,
    BookingManagementAction,
    BookingManagementState,
    BookingManagementStep,
    BookingService,
    BookingSlotUnavailableError,
    BookingState,
    BookingStep,
)
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

_EXISTING_BOOKING_CANCELLATION_PHRASES = {
    Language.ES: (
        "cancelar mi cita",
        "cancelar una cita",
        "anular mi cita",
        "anular una cita",
        "cancelar mi reserva",
        "anular mi reserva",
    ),
    Language.EN: (
        "cancel my appointment",
        "cancel an appointment",
        "cancel my booking",
        "cancel my reservation",
    ),
}

_EXISTING_BOOKING_RESCHEDULE_PHRASES = {
    Language.ES: (
        "cambiar mi cita",
        "cambiar una cita",
        "reprogramar mi cita",
        "reprogramar una cita",
        "mover mi cita",
        "mover una cita",
        "cambiar mi reserva",
        "reprogramar mi reserva",
    ),
    Language.EN: (
        "reschedule my appointment",
        "reschedule an appointment",
        "change my appointment",
        "change an appointment",
        "move my appointment",
        "move an appointment",
        "reschedule my booking",
    ),
}

_BOOKING_RESCHEDULE_START_TEXTS = {
    Language.ES: (
        "Para cambiar tu cita, indícame el número "
        "de teléfono que usaste al reservar."
    ),
    Language.EN: (
        "To reschedule your appointment, please provide "
        "the phone number you used when booking."
    ),
}

_BOOKING_RESCHEDULE_DATE_TEXTS = {
    Language.ES: {
        "available_dates": (
            "Estas son las próximas fechas disponibles: "
            "{dates}. ¿Qué nueva fecha prefieres?"
        ),
        "no_available_dates": (
            "Ahora mismo no hay nuevas fechas disponibles "
            "para reprogramar esa cita. Puedes intentarlo "
            "más adelante o escribir «cancelar» para salir."
        ),
    },
    Language.EN: {
        "available_dates": (
            "These are the next available dates: "
            "{dates}. Which new date would you prefer?"
        ),
        "no_available_dates": (
            "There are currently no new dates available "
            "to reschedule that appointment. You can try "
            "again later or write “cancel” to exit."
        ),
    },
}

_BOOKING_RESCHEDULE_TIME_TEXTS = {
    Language.ES: {
        "available_times": (
            "Estas son las horas disponibles: "
            "{times}. ¿Qué nueva hora prefieres?"
        ),
        "invalid_date": (
            "Esa fecha no es válida. Elige una de las "
            "fechas disponibles usando el formato DD/MM/YYYY."
        ),
        "no_available_times": (
            "Ya no quedan horas disponibles para esa fecha. "
            "Elige otra de las fechas disponibles."
        ),
    },
    Language.EN: {
        "available_times": (
            "These times are available: "
            "{times}. Which new time would you prefer?"
        ),
        "invalid_date": (
            "That date is not valid. Choose one of the "
            "available dates using the DD/MM/YYYY format."
        ),
        "no_available_times": (
            "There are no available times left for that date. "
            "Choose another available date."
        ),
    },
}

_BOOKING_RESCHEDULE_CONFIRMATION_TEXTS = {
    Language.ES: {
        "summary": (
            "Estos son los datos del cambio:\n\n"
            "Servicio: {service}\n"
            "Fecha anterior: {old_date}\n"
            "Hora anterior: {old_time}\n\n"
            "Nueva fecha: {new_date}\n"
            "Nueva hora: {new_time}\n\n"
            "¿Quieres confirmar el cambio? Responde «sí» "
            "para confirmar o «no» para conservar la cita actual."
        ),
        "invalid_time": (
            "Esa hora no es válida. Elige una de las "
            "horas disponibles usando el formato HH:MM."
        ),
    },
    Language.EN: {
        "summary": (
            "Here are the reschedule details:\n\n"
            "Service: {service}\n"
            "Previous date: {old_date}\n"
            "Previous time: {old_time}\n\n"
            "New date: {new_date}\n"
            "New time: {new_time}\n\n"
            "Would you like to confirm the change? Reply “yes” "
            "to confirm or “no” to keep the current appointment."
        ),
        "invalid_time": (
            "That time is not valid. Choose one of the "
            "available times using the HH:MM format."
        ),
    },
}

_BOOKING_RESCHEDULE_RESULT_TEXTS = {
    Language.ES: {
        "complete": (
            "Tu cita se ha cambiado correctamente.\n\n"
            "{service_line}"
            "Nueva fecha: {date}\n"
            "Nueva hora: {time}"
        ),
        "rejected": (
            "No se ha realizado ningún cambio. "
            "Tu cita conserva la fecha y hora anteriores."
        ),
        "unknown_confirmation": (
            "No he entendido la respuesta. Responde «sí» "
            "para confirmar el cambio o «no» para conservar "
            "la cita actual."
        ),
    },
    Language.EN: {
        "complete": (
            "Your appointment has been rescheduled successfully.\n\n"
            "{service_line}"
            "New date: {date}\n"
            "New time: {time}"
        ),
        "rejected": (
            "No changes have been made. Your appointment "
            "keeps its previous date and time."
        ),
        "unknown_confirmation": (
            "I did not understand that response. Reply “yes” "
            "to confirm the change or “no” to keep the "
            "current appointment."
        ),
    },
}

_BOOKING_RESCHEDULE_CONFLICT_TEXTS = {
    Language.ES: (
        "El horario elegido ya no está disponible. "
        "Tu cita original no se ha modificado. Puedes iniciar "
        "de nuevo el cambio para elegir otro horario."
    ),
    Language.EN: (
        "The selected date and time are no longer available. "
        "Your original appointment has not been changed. You "
        "can start the reschedule again to choose another time."
    ),
}

_BOOKING_MANAGEMENT_CONFLICT_TEXTS = {
    Language.ES: (
        "Esa cita ya no está activa. Es posible que se haya "
        "cancelado desde otro canal."
    ),
    Language.EN: (
        "That appointment is no longer active. It may have "
        "been cancelled through another channel."
    ),
}


_BOOKING_MANAGEMENT_EXIT_TEXTS = {
    Language.ES: (
        "La gestión de tu cita ha finalizado "
        "sin realizar cambios."
    ),
    Language.EN: (
        "Appointment management has ended "
        "without making any changes."
    ),
}


_BOOKING_MANAGEMENT_TEXTS = {
    Language.ES: {
        "ask_phone": (
            "Para localizar tu cita, indícame el número "
            "de teléfono que usaste al reservar."
        ),
        "no_active_bookings": (
            "No he encontrado ninguna cita activa asociada "
            "a ese teléfono. Comprueba el número e inténtalo "
            "de nuevo o escribe «cancelar» para salir."
        ),
        "multiple_bookings": (
            "He encontrado varias citas activas:\n\n"
            "{bookings}\n\n"
            "Escribe el número de la cita que quieres cancelar."
        ),
        "invalid_selection": (
            "Esa opción no es válida. Escribe un número "
            "entre 1 y {count}."
        ),
        "cancellation_confirmation": (
            "He encontrado esta cita:\n\n"
            "{service_line}"
            "Fecha: {date}\n"
            "Hora: {time}\n\n"
            "¿Quieres cancelarla? Responde «sí» para "
            "confirmar o «no» para conservarla."
        ),
        "cancellation_complete": (
            "Tu cita ha sido cancelada correctamente.\n\n"
            "{service_line}"
            "Fecha: {date}\n"
            "Hora: {time}\n\n"
            "Si necesitas otra cita, puedes reservarla "
            "cuando quieras."
        ),
        "cancellation_rejected": (
            "De acuerdo. Tu cita se mantiene sin cambios."
        ),
        "unknown_confirmation": (
            "No he entendido la respuesta. Escribe «sí» "
            "para cancelar la cita o «no» para conservarla."
        ),
    },
    Language.EN: {
        "ask_phone": (
            "To find your appointment, please provide the "
            "phone number you used when booking."
        ),
        "no_active_bookings": (
            "I couldn't find any active appointments associated "
            "with that phone number. Check the number and try "
            "again, or write “cancel” to exit."
        ),
        "multiple_bookings": (
            "I found several active appointments:\n\n"
            "{bookings}\n\n"
            "Enter the number of the appointment you want to cancel."
        ),
        "invalid_selection": (
            "That option is not valid. Enter a number "
            "between 1 and {count}."
        ),
        "cancellation_confirmation": (
            "I found this appointment:\n\n"
            "{service_line}"
            "Date: {date}\n"
            "Time: {time}\n\n"
            "Would you like to cancel it? Reply “yes” to "
            "confirm or “no” to keep it."
        ),
        "cancellation_complete": (
            "Your appointment has been cancelled successfully.\n\n"
            "{service_line}"
            "Date: {date}\n"
            "Time: {time}\n\n"
            "If you need another appointment, you can book "
            "one whenever you want."
        ),
        "cancellation_rejected": (
            "Understood. Your appointment remains unchanged."
        ),
        "unknown_confirmation": (
            "I didn't understand your response. Reply “yes” "
            "to cancel the appointment or “no” to keep it."
        ),
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
            "¿Cuál es tu número de teléfono? "
            "Puedes incluir el prefijo internacional, "
            "por ejemplo +34."
        ),
        "invalid_phone": (
            "El teléfono no parece válido. "
            "Comprueba el número y su prefijo internacional."
        ),
        "ask_date": "¿Para qué día quieres la cita?",
        "no_available_dates": (
            "Ahora mismo no tengo fechas disponibles. "
            "Inténtalo de nuevo más adelante."
        ),
        "available_dates": (
            "Tengo disponibilidad para las próximas fechas: "
            "{dates}. ¿Qué día prefieres? "
            "Si necesitas una fecha posterior, dímelo."
        ),
        "selected_date_unavailable": (
            "Lo siento, esa fecha no está disponible. "
            "Ahora mismo tengo disponibles estos días: "
            "{dates}. ¿Cuál prefieres?"
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
            "{service_line}"
            "Nombre: {name}\n"
            "Teléfono: {phone}\n"
            "Fecha: {date}\n"
            "Hora: {time}\n\n"
            "¿Quieres confirmar la reserva? "
            "Responde «sí» para confirmar "
            "o «no» para cancelar."
        ),
        "confirmed": (
            "Tu reserva se ha realizado correctamente.\n\n"
            "{service_line}"
            "Nombre: {name}\n"
            "Teléfono: {phone}\n"
            "Fecha: {date}\n"
            "Hora: {time}\n\n"
            "Ya tienes tu cita reservada.\n\n"
            "Si necesitas algo más, escríbeme directamente "
            "qué deseas consultar."
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
        "available_times": (
            "Tengo disponibles estas horas: "
            "{times}. ¿Cuál prefieres?"
        ),
        "no_available_times": (
            "No quedan horas disponibles para ese día. "
            "Prueba con otra fecha."
        ),
        "selected_time_unavailable": (
            "Lo siento, esa hora acaba de dejar de estar disponible. "
            "Ahora tengo libres estas horas: {times}. "
            "Elige otra hora."
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
            "What's your phone number? "
            "You may include the international prefix, "
            "for example +34."
        ),
        "invalid_phone": (
            "That phone number doesn't seem valid. "
            "Check the number and its international prefix."
        ),
        "ask_date": (
            "What date would you like for your appointment?"
        ),
        "no_available_dates": (
            "There are currently no available dates. "
            "Please try again later."
        ),
        "available_dates": (
            "My next available dates are: "
            "{dates}. Which date would you prefer? "
            "If you need a later date, let me know."
        ),
        "selected_date_unavailable": (
            "Sorry, that date is not available. "
            "These dates are currently available: "
            "{dates}. Which one would you prefer?"
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
            "{service_line}"
            "Name: {name}\n"
            "Phone: {phone}\n"
            "Date: {date}\n"
            "Time: {time}\n\n"
            "Would you like to confirm the appointment? "
            "Reply “yes” to confirm "
            "or “no” to cancel."
        ),
        "confirmed": (
            "Your appointment has been booked successfully.\n\n"
            "{service_line}"
            "Name: {name}\n"
            "Phone: {phone}\n"
            "Date: {date}\n"
            "Time: {time}\n\n"
            "Your appointment is now confirmed.\n\n"
            "If you need anything else, write directly "
            "what you would like help with."
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
        "available_times": (
            "These times are available: "
            "{times}. Which one would you prefer?"
        ),
        "no_available_times": (
            "There are no available times left for that date. "
            "Please choose another date."
        ),
        "selected_time_unavailable": (
            "Sorry, that time has just become unavailable. "
            "These times are still available: {times}. "
            "Please choose another time."
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

    def __init__(
        self,
        booking_service: BookingService | None = None,
        phone_service: PhoneNumberService | None = None,
        business_hours: BusinessHours | None = None,
        booking_rules: BookingRules | None = None,
        services: tuple[BookableService, ...] = (),
    ) -> None:
        self._booking_service = booking_service
        self._business_hours = business_hours
        self._booking_rules = booking_rules
        self._services = tuple(services)

        self._phone_service = (
            phone_service
            or PhoneNumberService(
                default_region="ES",
            )
        )

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

        return (
            self._asks_for_available_dates(message)
            or any(
                keyword in text
                for language_keywords in _BOOKING_KEYWORDS.values()
                for keyword in language_keywords
            )
        )
    def handle(
        self,
        context: Any,
        message: str,
    ) -> Response:
        if context.booking is None:
            if context.booking_management is not None:
                return self._handle_booking_management(
                    context,
                    message,
                )

            if self._is_existing_booking_cancellation(
                message
            ):
                return (
                    self._start_existing_booking_cancellation(
                        context
                    )
                )

            if self._is_existing_booking_reschedule(
                message
            ):
                return (
                    self._start_existing_booking_reschedule(
                        context
                    )
                )

            if self._asks_for_available_dates(
                message
            ):
                return self._handle_initial_availability(
                    context
                )

            return self._start_booking(
                context,
                message,
            )

        language = self._get_language(context)
        normalized_message = self._normalize_text(
            message
        )
        early_cancellation_words = (
            _CANCELLATION_WORDS[language]
            - {"no"}
        )

        if normalized_message in early_cancellation_words:
            return self._cancel_booking(
                context
            )

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

    def _is_existing_booking_reschedule(
        self,
        message: str,
    ) -> bool:
        normalized_message = self._normalize_text(
            message
        )

        return any(
            phrase in normalized_message
            for language_phrases
            in _EXISTING_BOOKING_RESCHEDULE_PHRASES.values()
            for phrase in language_phrases
        )

    def _start_existing_booking_reschedule(
        self,
        context: Any,
    ) -> Response:
        language = self._get_language(context)

        context.booking_management = (
            BookingManagementState(
                action=BookingManagementAction.RESCHEDULE,
            )
        )

        return Response(
            text=_BOOKING_RESCHEDULE_START_TEXTS[
                language
            ],
            metadata={
                "capability": self.name,
                "handled": True,
                "booking_management_step": (
                    BookingManagementStep.PHONE.value
                ),
                "language": language.value,
            },
        )

    def _is_existing_booking_cancellation(
        self,
        message: str,
    ) -> bool:
        normalized_message = self._normalize_text(
            message
        )

        return any(
            phrase in normalized_message
            for language_phrases
            in _EXISTING_BOOKING_CANCELLATION_PHRASES.values()
            for phrase in language_phrases
        )

    def _start_existing_booking_cancellation(
        self,
        context: Any,
    ) -> Response:
        language = self._get_language(context)

        context.booking_management = (
            BookingManagementState(
                action=BookingManagementAction.CANCEL,
            )
        )

        return Response(
            text=(
                _BOOKING_MANAGEMENT_TEXTS[
                    language
                ]["ask_phone"]
            ),
            metadata={
                "capability": self.name,
                "handled": True,
                "booking_management_step": (
                    BookingManagementStep.PHONE.value
                ),
                "language": language.value,
            },
        )

    def _handle_booking_management(
        self,
        context: Any,
        message: str,
    ) -> Response:
        """
        Continue management of an existing booking.
        """

        management = context.booking_management

        if management is None:
            raise ValueError(
                "Cannot handle missing booking management state."
            )

        language = self._get_language(context)
        normalized_message = self._normalize_text(
            message
        )
        exit_words = (
            _CANCELLATION_WORDS[language]
            - {"no"}
        )

        if normalized_message in exit_words:
            return self._exit_booking_management(
                context
            )

        if (
            management.next_step
            is BookingManagementStep.PHONE
        ):
            return self._handle_booking_management_phone(
                context,
                message,
            )

        if (
            management.next_step
            is BookingManagementStep.SELECTION
        ):
            return self._handle_booking_management_selection(
                context,
                message,
            )

        if (
            management.next_step
            is BookingManagementStep.DATE
        ):
            return self._handle_booking_management_date(
                context,
                message,
            )

        if (
            management.next_step
            is BookingManagementStep.TIME
        ):
            return self._handle_booking_management_time(
                context,
                message,
            )

        if (
            management.next_step
            is BookingManagementStep.CONFIRMATION
        ):
            if (
                management.action
                is BookingManagementAction.RESCHEDULE
            ):
                return (
                    self._handle_booking_reschedule_confirmation(
                        context,
                        message,
                    )
                )

            return self._handle_booking_management_confirmation(
                context,
                message,
            )

        raise ValueError(
            "Cannot continue completed booking management."
        )

    def _exit_booking_management(
        self,
        context: Any,
    ) -> Response:
        """
        End existing-booking management without making changes.
        """

        language = self._get_language(context)

        context.reset_booking_management()
        context.clear_active_capability()

        return Response(
            text=_BOOKING_MANAGEMENT_EXIT_TEXTS[
                language
            ],
            metadata={
                "capability": self.name,
                "handled": True,
                "booking_management_step": (
                    BookingManagementStep.COMPLETE.value
                ),
                "booking_cancelled": False,
                "language": language.value,
            },
        )

    def _handle_booking_management_phone(
        self,
        context: Any,
        message: str,
    ) -> Response:
        """
        Parse the phone and locate active bookings.
        """

        management = context.booking_management

        if management is None:
            raise ValueError(
                "Cannot locate bookings without management state."
            )

        language = self._get_language(context)

        try:
            phone = self._phone_service.parse(
                message
            )
        except PhoneNumberError:
            return Response(
                text=self._text(
                    context,
                    "invalid_phone",
                ),
                metadata={
                    "capability": self.name,
                    "handled": True,
                    "booking_management_step": (
                        BookingManagementStep.PHONE.value
                    ),
                    "language": language.value,
                },
            )

        active_bookings = (
            self._booking_service.find_active_bookings_by_phone(
                phone.e164
            )
            if self._booking_service is not None
            else ()
        )

        if not active_bookings:
            management.phone = None
            management.matching_bookings = ()
            management.selected_booking = None

            return Response(
                text=(
                    _BOOKING_MANAGEMENT_TEXTS[
                        language
                    ]["no_active_bookings"]
                ),
                metadata={
                    "capability": self.name,
                    "handled": True,
                    "booking_management_step": (
                        BookingManagementStep.PHONE.value
                    ),
                    "language": language.value,
                },
            )

        management.phone = phone.e164
        management.matching_bookings = tuple(
            active_bookings
        )

        if len(active_bookings) == 1:
            management.selected_booking = (
                active_bookings[0]
            )

            if (
                management.action
                is BookingManagementAction.RESCHEDULE
            ):
                return (
                    self._start_booking_reschedule_date_selection(
                        context
                    )
                )

            return Response(
                text=(
                    self._build_booking_cancellation_confirmation(
                        context
                    )
                ),
                metadata={
                    "capability": self.name,
                    "handled": True,
                    "booking_management_step": (
                        BookingManagementStep.CONFIRMATION.value
                    ),
                    "language": language.value,
                },
            )

        management.selected_booking = None

        return Response(
            text=self._build_booking_selection_message(
                context
            ),
            metadata={
                "capability": self.name,
                "handled": True,
                "booking_management_step": (
                    BookingManagementStep.SELECTION.value
                ),
                "language": language.value,
            },
        )

    def _start_booking_reschedule_date_selection(
        self,
        context: Any,
    ) -> Response:
        """
        Load and present dates for an existing booking reschedule.
        """

        management = context.booking_management

        if (
            management is None
            or management.selected_booking is None
        ):
            raise ValueError(
                "Cannot offer dates without a selected booking."
            )

        language = self._get_language(context)
        available_dates = tuple(
            self._get_available_dates(
                context=context,
            )
        )
        management.available_dates = available_dates
        management.new_date = None
        management.new_time = None
        management.available_times = ()

        if available_dates:
            text = (
                _BOOKING_RESCHEDULE_DATE_TEXTS[
                    language
                ]["available_dates"].format(
                    dates=", ".join(
                        available_dates[:5]
                    ),
                )
            )
        else:
            text = (
                _BOOKING_RESCHEDULE_DATE_TEXTS[
                    language
                ]["no_available_dates"]
            )

        return Response(
            text=text,
            metadata={
                "capability": self.name,
                "handled": True,
                "booking_management_step": (
                    BookingManagementStep.DATE.value
                ),
                "language": language.value,
            },
        )

    def _handle_booking_management_selection(
        self,
        context: Any,
        message: str,
    ) -> Response:
        """
        Select one active booking using its displayed number.
        """

        management = context.booking_management

        if management is None:
            raise ValueError(
                "Cannot select a booking without management state."
            )

        language = self._get_language(context)
        normalized_selection = message.strip()

        try:
            selected_index = int(
                normalized_selection
            ) - 1
        except ValueError:
            selected_index = -1

        if (
            selected_index < 0
            or selected_index
            >= len(management.matching_bookings)
        ):
            return Response(
                text=(
                    _BOOKING_MANAGEMENT_TEXTS[
                        language
                    ]["invalid_selection"].format(
                        count=len(
                            management.matching_bookings
                        ),
                    )
                ),
                metadata={
                    "capability": self.name,
                    "handled": True,
                    "booking_management_step": (
                        BookingManagementStep.SELECTION.value
                    ),
                    "language": language.value,
                },
            )

        management.selected_booking = (
            management.matching_bookings[
                selected_index
            ]
        )

        if (
            management.action
            is BookingManagementAction.RESCHEDULE
        ):
            return (
                self._start_booking_reschedule_date_selection(
                    context
                )
            )

        return Response(
            text=(
                self._build_booking_cancellation_confirmation(
                    context
                )
            ),
            metadata={
                "capability": self.name,
                "handled": True,
                "booking_management_step": (
                    BookingManagementStep.CONFIRMATION.value
                ),
                "language": language.value,
            },
        )

    def _build_booking_selection_message(
        self,
        context: Any,
    ) -> str:
        """
        Build the numbered list of active bookings.
        """

        management = context.booking_management

        if management is None:
            raise ValueError(
                "Cannot list bookings without management state."
            )

        language = self._get_language(context)
        appointment_name = (
            "Cita"
            if language is Language.ES
            else "Appointment"
        )
        time_connector = (
            "a las"
            if language is Language.ES
            else "at"
        )

        booking_lines = []

        for index, booking in enumerate(
            management.matching_bookings,
            start=1,
        ):
            service_name = (
                booking.service_name
                or appointment_name
            )

            booking_lines.append(
                f"{index}. {service_name} — "
                f"{booking.date} {time_connector} "
                f"{booking.time}"
            )

        return (
            _BOOKING_MANAGEMENT_TEXTS[
                language
            ]["multiple_bookings"].format(
                bookings="\n".join(
                    booking_lines
                ),
            )
        )

    def _handle_booking_management_date(
        self,
        context: Any,
        message: str,
    ) -> Response:
        """
        Select a new date and present its available times.
        """

        management = context.booking_management

        if (
            management is None
            or management.action
            is not BookingManagementAction.RESCHEDULE
            or management.selected_booking is None
        ):
            raise ValueError(
                "Cannot select a date without a reschedule state."
            )

        language = self._get_language(context)
        date_value = message.strip()

        try:
            normalized_date = datetime.strptime(
                date_value,
                "%d/%m/%Y",
            ).strftime(
                "%d/%m/%Y"
            )
        except ValueError:
            normalized_date = None

        if (
            normalized_date is None
            or normalized_date
            not in management.available_dates
        ):
            return Response(
                text=(
                    _BOOKING_RESCHEDULE_TIME_TEXTS[
                        language
                    ]["invalid_date"]
                ),
                metadata={
                    "capability": self.name,
                    "handled": True,
                    "booking_management_step": (
                        BookingManagementStep.DATE.value
                    ),
                    "language": language.value,
                },
            )

        available_times = self._get_available_times(
            normalized_date,
            context=context,
        )

        if not available_times:
            management.new_date = None
            management.new_time = None
            management.available_times = ()

            return Response(
                text=(
                    _BOOKING_RESCHEDULE_TIME_TEXTS[
                        language
                    ]["no_available_times"]
                ),
                metadata={
                    "capability": self.name,
                    "handled": True,
                    "booking_management_step": (
                        BookingManagementStep.DATE.value
                    ),
                    "language": language.value,
                },
            )

        management.new_date = normalized_date
        management.new_time = None
        management.available_times = tuple(
            available_times
        )

        return Response(
            text=(
                _BOOKING_RESCHEDULE_TIME_TEXTS[
                    language
                ]["available_times"].format(
                    times=", ".join(
                        available_times
                    ),
                )
            ),
            metadata={
                "capability": self.name,
                "handled": True,
                "booking_management_step": (
                    BookingManagementStep.TIME.value
                ),
                "language": language.value,
            },
        )

    def _handle_booking_management_time(
        self,
        context: Any,
        message: str,
    ) -> Response:
        """
        Select a new time and request reschedule confirmation.
        """

        management = context.booking_management

        if (
            management is None
            or management.action
            is not BookingManagementAction.RESCHEDULE
            or management.selected_booking is None
            or management.new_date is None
        ):
            raise ValueError(
                "Cannot select a time without a reschedule date."
            )

        language = self._get_language(context)
        time_value = message.strip()

        try:
            normalized_time = datetime.strptime(
                time_value,
                "%H:%M",
            ).strftime(
                "%H:%M"
            )
        except ValueError:
            normalized_time = None

        if (
            normalized_time is None
            or normalized_time
            not in management.available_times
        ):
            return Response(
                text=(
                    _BOOKING_RESCHEDULE_CONFIRMATION_TEXTS[
                        language
                    ]["invalid_time"]
                ),
                metadata={
                    "capability": self.name,
                    "handled": True,
                    "booking_management_step": (
                        BookingManagementStep.TIME.value
                    ),
                    "language": language.value,
                },
            )

        management.new_time = normalized_time

        return Response(
            text=(
                self._build_booking_reschedule_confirmation(
                    context
                )
            ),
            metadata={
                "capability": self.name,
                "handled": True,
                "booking_management_step": (
                    BookingManagementStep.CONFIRMATION.value
                ),
                "language": language.value,
            },
        )

    def _build_booking_reschedule_confirmation(
        self,
        context: Any,
    ) -> str:
        """
        Build the old-versus-new booking confirmation summary.
        """

        management = context.booking_management

        if (
            management is None
            or management.selected_booking is None
            or management.new_date is None
            or management.new_time is None
        ):
            raise ValueError(
                "Cannot build an incomplete reschedule summary."
            )

        language = self._get_language(context)
        booking = management.selected_booking

        default_service = (
            "Cita"
            if language is Language.ES
            else "Appointment"
        )

        return (
            _BOOKING_RESCHEDULE_CONFIRMATION_TEXTS[
                language
            ]["summary"].format(
                service=(
                    booking.service_name
                    or default_service
                ),
                old_date=booking.date,
                old_time=booking.time,
                new_date=management.new_date,
                new_time=management.new_time,
            )
        )

    def _handle_booking_reschedule_confirmation(
        self,
        context: Any,
        message: str,
    ) -> Response:
        """
        Confirm or reject an existing booking reschedule.
        """

        management = context.booking_management

        if (
            management is None
            or management.action
            is not BookingManagementAction.RESCHEDULE
            or management.selected_booking is None
            or management.new_date is None
            or management.new_time is None
        ):
            raise ValueError(
                "Cannot confirm an incomplete reschedule."
            )

        language = self._get_language(context)
        normalized_message = self._normalize_text(
            message
        )

        if normalized_message in _CONFIRMATION_WORDS[language]:
            if self._booking_service is None:
                raise ValueError(
                    "Cannot reschedule without BookingService."
                )

            try:
                updated_booking = (
                    self._booking_service.reschedule_booking(
                        management.selected_booking,
                        date=management.new_date,
                        time=management.new_time,
                    )
                )
            except BookingSlotUnavailableError:
                context.reset_booking_management()
                context.clear_active_capability()

                return Response(
                    text=(
                        _BOOKING_RESCHEDULE_CONFLICT_TEXTS[
                            language
                        ]
                    ),
                    metadata={
                        "capability": self.name,
                        "handled": True,
                        "booking_management_step": (
                            BookingManagementStep.COMPLETE.value
                        ),
                        "booking_rescheduled": False,
                        "booking_conflict": True,
                        "language": language.value,
                    },
                )

            management.complete()

            response = Response(
                text=self._build_rescheduled_booking_message(
                    context,
                    updated_booking,
                ),
                metadata={
                    "capability": self.name,
                    "handled": True,
                    "booking_management_step": (
                        BookingManagementStep.COMPLETE.value
                    ),
                    "booking_rescheduled": True,
                    "booking_conflict": False,
                    "language": language.value,
                },
            )

            context.reset_booking_management()
            context.clear_active_capability()

            return response

        if normalized_message in _CANCELLATION_WORDS[language]:
            context.reset_booking_management()
            context.clear_active_capability()

            return Response(
                text=(
                    _BOOKING_RESCHEDULE_RESULT_TEXTS[
                        language
                    ]["rejected"]
                ),
                metadata={
                    "capability": self.name,
                    "handled": True,
                    "booking_management_step": (
                        BookingManagementStep.COMPLETE.value
                    ),
                    "booking_rescheduled": False,
                    "booking_conflict": False,
                    "language": language.value,
                },
            )

        return Response(
            text=(
                _BOOKING_RESCHEDULE_RESULT_TEXTS[
                    language
                ]["unknown_confirmation"]
            ),
            metadata={
                "capability": self.name,
                "handled": True,
                "booking_management_step": (
                    BookingManagementStep.CONFIRMATION.value
                ),
                "language": language.value,
            },
        )

    def _build_rescheduled_booking_message(
        self,
        context: Any,
        booking: Any,
    ) -> str:
        """
        Build the successful reschedule response.
        """

        language = self._get_language(context)
        service_line = ""

        if booking.service_name:
            service_label = (
                "Servicio"
                if language is Language.ES
                else "Service"
            )
            service_line = (
                f"{service_label}: "
                f"{booking.service_name}\n"
            )

        return (
            _BOOKING_RESCHEDULE_RESULT_TEXTS[
                language
            ]["complete"].format(
                service_line=service_line,
                date=booking.date,
                time=booking.time,
            )
        )

    def _handle_booking_management_confirmation(
        self,
        context: Any,
        message: str,
    ) -> Response:
        """
        Confirm or reject cancellation of the selected booking.
        """

        management = context.booking_management

        if (
            management is None
            or management.selected_booking is None
        ):
            raise ValueError(
                "Cannot confirm cancellation without "
                "a selected booking."
            )

        language = self._get_language(context)
        normalized_message = self._normalize_text(
            message
        )

        if normalized_message in _CONFIRMATION_WORDS[language]:
            if self._booking_service is None:
                raise ValueError(
                    "Cannot cancel a booking without BookingService."
                )

            selected_booking = (
                management.selected_booking
            )

            try:
                cancelled_booking = (
                    self._booking_service.cancel_booking(
                        selected_booking
                    )
                )
            except BookingAlreadyCancelledError:
                context.reset_booking_management()
                context.clear_active_capability()

                return Response(
                    text=(
                        _BOOKING_MANAGEMENT_CONFLICT_TEXTS[
                            language
                        ]
                    ),
                    metadata={
                        "capability": self.name,
                        "handled": True,
                        "booking_management_step": (
                            BookingManagementStep.COMPLETE.value
                        ),
                        "booking_cancelled": False,
                        "booking_conflict": True,
                        "language": language.value,
                    },
                )

            management.complete()

            response = Response(
                text=self._build_cancelled_booking_message(
                    context,
                    cancelled_booking,
                ),
                metadata={
                    "capability": self.name,
                    "handled": True,
                    "booking_management_step": (
                        BookingManagementStep.COMPLETE.value
                    ),
                    "booking_cancelled": True,
                    "booking_conflict": False,
                    "language": language.value,
                },
            )

            context.reset_booking_management()
            context.clear_active_capability()

            return response

        if normalized_message in _CANCELLATION_WORDS[language]:
            context.reset_booking_management()
            context.clear_active_capability()

            return Response(
                text=(
                    _BOOKING_MANAGEMENT_TEXTS[
                        language
                    ]["cancellation_rejected"]
                ),
                metadata={
                    "capability": self.name,
                    "handled": True,
                    "booking_management_step": (
                        BookingManagementStep.COMPLETE.value
                    ),
                    "booking_cancelled": False,
                    "booking_conflict": False,
                    "language": language.value,
                },
            )

        return Response(
            text=(
                _BOOKING_MANAGEMENT_TEXTS[
                    language
                ]["unknown_confirmation"]
            ),
            metadata={
                "capability": self.name,
                "handled": True,
                "booking_management_step": (
                    BookingManagementStep.CONFIRMATION.value
                ),
                "language": language.value,
            },
        )

    def _build_cancelled_booking_message(
        self,
        context: Any,
        booking: Any,
    ) -> str:
        """
        Build the successful cancellation response.
        """

        language = self._get_language(context)
        service_line = ""

        if booking.service_name:
            service_label = (
                "Servicio"
                if language is Language.ES
                else "Service"
            )
            service_line = (
                f"{service_label}: "
                f"{booking.service_name}\n"
            )

        return (
            _BOOKING_MANAGEMENT_TEXTS[
                language
            ]["cancellation_complete"].format(
                service_line=service_line,
                date=booking.date,
                time=booking.time,
            )
        )

    def _build_booking_cancellation_confirmation(
        self,
        context: Any,
    ) -> str:
        """
        Build the confirmation summary for the selected booking.
        """

        management = context.booking_management

        if (
            management is None
            or management.selected_booking is None
        ):
            raise ValueError(
                "Cannot build cancellation confirmation "
                "without a selected booking."
            )

        language = self._get_language(context)
        booking = management.selected_booking

        service_line = ""

        if booking.service_name:
            service_label = (
                "Servicio"
                if language is Language.ES
                else "Service"
            )
            service_line = (
                f"{service_label}: "
                f"{booking.service_name}\n"
            )

        return (
            _BOOKING_MANAGEMENT_TEXTS[
                language
            ]["cancellation_confirmation"].format(
                service_line=service_line,
                date=booking.date,
                time=booking.time,
            )
        )

    def _cancel_booking(
        self,
        context: Any,
    ) -> Response:
        language = self._get_language(context)

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

    def _handle_initial_availability(
        self,
        context: Any,
    ) -> Response:
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
                dates=", ".join(
                    available_dates[:5]
                ),
            ),
        )
    def _start_booking(
        self,
        context: Any,
        message: str,
    ) -> Response:
        context.booking = BookingState(
            requires_service_selection=bool(
                self._services
            ),
        )

        if not self._services:
            return self._response(
                context=context,
                text=self._text(
                    context,
                    "start",
                ),
            )

        service = self._find_service(message)

        if service is not None:
            self._select_service(
                context,
                service,
            )

            return self._response(
                context=context,
                text=self._service_selected_text(
                    context,
                    service,
                ),
            )

        return self._response(
            context=context,
            text=self._build_service_menu(
                context
            ),
        )

    def _handle_service(
        self,
        context: Any,
        message: str,
    ) -> Response:
        service = self._find_service(message)

        if service is None:
            return self._response(
                context=context,
                text=self._build_service_menu(
                    context
                ),
            )

        self._select_service(
            context,
            service,
        )

        return self._response(
            context=context,
            text=self._service_selected_text(
                context,
                service,
            ),
        )

    def _find_service(
        self,
        message: str,
    ) -> BookableService | None:
        normalized_message = self._normalize_text(
            message
        )

        for service in self._services:
            candidates = (
                service.id,
                service.name_es,
                service.name_en,
            )

            for candidate in candidates:
                normalized_candidate = (
                    self._normalize_text(candidate)
                )

                if (
                    normalized_candidate
                    and normalized_candidate
                    in normalized_message
                ):
                    return service

        return None

    @staticmethod
    def _select_service(
        context: Any,
        service: BookableService,
    ) -> None:
        booking = context.booking

        booking.service_id = service.id
        booking.service_name = service.name_es
        booking.service_duration_minutes = (
            service.duration_minutes
        )
        booking.service_price_cents = (
            service.price_cents
        )
        booking.service_price_type = (
            service.price_type
        )
        booking.service_currency = (
            service.currency
        )

    def _build_service_menu(
        self,
        context: Any,
    ) -> str:
        language = self._get_language(context)

        if language is Language.EN:
            heading = "Which service would you like to book?"
        else:
            heading = "¿Qué servicio quieres reservar?"

        lines = [
            heading,
            "",
        ]

        for service in self._services:
            if language is Language.EN:
                service_name = service.name_en
                price_prefix = (
                    "from "
                    if service.price_type == "from"
                    else ""
                )
            else:
                service_name = service.name_es
                price_prefix = (
                    "desde "
                    if service.price_type == "from"
                    else ""
                )

            lines.append(
                "- "
                f"{service_name}: "
                f"{price_prefix}"
                f"{self._format_service_price(service)}"
            )

        return "\n".join(lines)

    def _service_selected_text(
        self,
        context: Any,
        service: BookableService,
    ) -> str:
        if self._get_language(context) is Language.EN:
            return (
                f"Perfect. You have selected {service.name_en}. "
                "What is your name?"
            )

        return (
            f"Perfecto. Has elegido {service.name_es}. "
            "¿Cómo te llamas?"
        )

    @staticmethod
    def _format_service_price(
        service: BookableService,
    ) -> str:
        amount = service.price_cents / 100

        if amount.is_integer():
            formatted_amount = str(int(amount))
        else:
            formatted_amount = (
                f"{amount:.2f}".replace(".", ",")
            )

        if service.currency == "EUR":
            return f"{formatted_amount} €"

        return (
            f"{formatted_amount} "
            f"{service.currency}"
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
        try:
            phone = self._phone_service.parse(
                message,
            )
        except PhoneNumberError:
            return self._response(
                context=context,
                text=self._text(
                    context,
                    "invalid_phone",
                ),
            )

        context.booking.phone = phone.e164

        return self._response(
            context=context,
            text=self._build_available_dates_message(
                context
            ),
        )

    def _handle_date(
        self,
        context: Any,
        message: str,
    ) -> Response:
        date = message.strip()

        if self._asks_for_available_dates(date):
            available_dates = self._get_available_dates(
                context=context,
            )

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
                    dates=", ".join(
                    available_dates[:5]
                ),
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

        available_dates = (
            context.booking.available_dates
        )

        if (
            available_dates
            and date not in available_dates
        ):
            return self._response(
                context=context,
                text=self._text(
                    context,
                    "selected_date_unavailable",
                    dates=", ".join(
                    available_dates[:5]
                ),
                ),
            )

        context.booking.date = date

        available_times = self._get_available_times(
            date,
            context=context,
        )

        if available_times is None:
            return self._response(
                context=context,
                text=self._text(
                    context,
                    "ask_time",
                ),
            )

        if not available_times:
            context.booking.date = None

            return self._response(
                context=context,
                text=self._text(
                    context,
                    "no_available_times",
                ),
            )

        context.booking.available_times = available_times
        context.booking.available_times_page = 0

        return self._response(
            context=context,
            text=self._build_available_times_page(
                context
            ),
        )

    def _build_available_times_page(
        self,
        context: Any,
        *,
        advance: bool = False,
    ) -> str:
        booking = context.booking

        if booking is None:
            raise ValueError(
                "Cannot paginate times without a booking state."
            )

        page_size = 8
        total_times = len(
            booking.available_times
        )
        last_page = max(
            0,
            (total_times - 1) // page_size,
        )

        if advance:
            booking.available_times_page = min(
                booking.available_times_page + 1,
                last_page,
            )

        page_start = (
            booking.available_times_page
            * page_size
        )
        page_end = page_start + page_size
        page_times = booking.available_times[
            page_start:page_end
        ]

        message = self._text(
            context,
            "available_times",
            times=", ".join(page_times),
        )

        if page_end < total_times:
            if self._get_language(context) is Language.EN:
                message += (
                    " Write “more times” to see the next options."
                )
            else:
                message += (
                    " Escribe «más horas» para ver las siguientes."
                )

        return message

    def _handle_time(
        self,
        context: Any,
        message: str,
    ) -> Response:
        time = message.strip()
        normalized_message = self._normalize_text(
            message
        )

        if normalized_message in {
            "mas horas",
            "siguientes horas",
            "more times",
            "next times",
        }:
            return self._response(
                context=context,
                text=self._build_available_times_page(
                    context,
                    advance=True,
                ),
            )

        if not self._is_valid_time(time):
            return self._response(
                context=context,
                text=self._text(
                    context,
                    "invalid_time",
                ),
            )

        available_times = context.booking.available_times

        if (
            available_times
            and time not in available_times
        ):
            return self._response(
                context=context,
                text=self._text(
                    context,
                    "invalid_available_time",
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
            return self._confirm_booking(
                context
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

    def _confirm_booking(
        self,
        context: Any,
    ) -> Response:
        booking = context.booking

        if booking is None:
            raise ValueError(
                "Cannot confirm a missing booking state."
            )

        if self._booking_service is None:
            booking.confirm()
            booking.available_times = ()
        else:
            try:
                self._booking_service.create_booking_from_state(
                    booking,
                    business_hours=self._business_hours,
                    rules=self._get_effective_booking_rules(
                        context
                    ),
                )
            except BookingSlotUnavailableError:
                date_value = booking.date

                if date_value is None:
                    raise ValueError(
                        "Cannot recalculate availability without a booking date."
                    )

                available_times = self._get_available_times(
                    date_value,
                    context=context,
                )

                booking.time = None

                if not available_times:
                    booking.date = None
                    booking.available_times = ()

                    return self._response(
                        context=context,
                        text=self._text(
                            context,
                            "no_available_times",
                        ),
                    )

                booking.available_times = available_times

                return self._response(
                    context=context,
                    text=self._text(
                        context,
                        "selected_time_unavailable",
                        times=", ".join(
                            available_times
                        ),
                    ),
                )

        response = self._response(
            context=context,
            text=self._text(
                context,
                "confirmed",
                name=booking.name,
                phone=booking.phone,
                date=booking.date,
                time=booking.time,
            ),
        )

        context.clear_active_capability()
        context.reset_booking()

        return response

    def _get_step_handler(
        self,
        step: BookingStep,
    ) -> Callable[[Any, str], Response] | None:
        handlers: dict[
            BookingStep,
            Callable[[Any, str], Response],
        ] = {
            BookingStep.SERVICE: self._handle_service,
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
        booking = getattr(
            context,
            "booking",
            None,
        )
        service_name = getattr(
            booking,
            "service_name",
            None,
        )

        if service_name:
            service_label = (
                "Service"
                if language is Language.EN
                else "Servicio"
            )

            values.setdefault(
                "service_line",
                f"{service_label}: {service_name}\n",
            )
        else:
            values.setdefault(
                "service_line",
                "",
            )

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

    def _get_effective_booking_rules(
        self,
        context: Any | None,
    ) -> BookingRules | None:
        """
        Return booking rules adjusted to the selected service duration.

        New bookings obtain their duration from BookingState. Existing
        bookings being rescheduled obtain it from the selected Booking.
        """

        if self._booking_rules is None:
            return None

        booking = getattr(
            context,
            "booking",
            None,
        )
        duration_minutes = getattr(
            booking,
            "service_duration_minutes",
            None,
        )

        if duration_minutes is None:
            management = getattr(
                context,
                "booking_management",
                None,
            )
            selected_booking = getattr(
                management,
                "selected_booking",
                None,
            )
            duration_minutes = getattr(
                selected_booking,
                "duration_minutes",
                None,
            )

        if duration_minutes is None:
            return self._booking_rules

        return replace(
            self._booking_rules,
            appointment_duration=timedelta(
                minutes=duration_minutes,
            ),
        )

    def _get_available_dates(
        self,
        context: Any | None = None,
        *,
        days: int = 30,
    ) -> list[str]:
        """
        Return formatted dates containing a slot long enough for the
        selected service.

        When no service has been selected, the configured default
        appointment duration is used.
        """

        effective_rules = (
            self._get_effective_booking_rules(
                context
            )
        )

        if (
            self._booking_service is None
            or self._business_hours is None
            or effective_rules is None
        ):
            return []

        timezone = ZoneInfo(
            self._business_hours.timezone_name
        )
        now = datetime.now(timezone)

        available_dates = (
            self._booking_service.get_available_dates(
                start_date=now.date(),
                days=days,
                business_hours=self._business_hours,
                rules=effective_rules,
                now=now,
            )
        )

        return [
            available_date.strftime(
                "%d/%m/%Y",
            )
            for available_date in available_dates
        ]

    def _build_available_dates_message(
        self,
        context: Any,
    ) -> str:
        available_dates = self._get_available_dates(
            context=context,
        )

        context.booking.available_dates = tuple(
            available_dates
        )

        if not available_dates:
            return self._text(
                context,
                "no_available_dates",
            )

        return self._text(
            context,
            "available_dates",
            dates=", ".join(
                    available_dates[:5]
                ),
        )

    def _get_available_times(
        self,
        date_value: str,
        *,
        context: Any | None = None,
    ) -> tuple[str, ...] | None:
        """
        Return formatted available times for the selected service.

        None means that availability integration is disabled.
        """

        effective_rules = (
            self._get_effective_booking_rules(
                context
            )
        )

        if (
            self._booking_service is None
            or self._business_hours is None
            or effective_rules is None
        ):
            return None

        target_date = datetime.strptime(
            date_value,
            "%d/%m/%Y",
        ).date()

        timezone = ZoneInfo(
            self._business_hours.timezone_name
        )

        slots = (
            self._booking_service
            .get_available_slots_for_date(
                target_date,
                business_hours=self._business_hours,
                rules=effective_rules,
                now=datetime.now(timezone),
            )
        )

        return tuple(
            slot.start.strftime("%H:%M")
            for slot in slots
        )
