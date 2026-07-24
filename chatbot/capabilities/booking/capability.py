from typing import Any

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
        context.booking.name = message.strip()

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

    def _handle_date(self, context: Any, message: str) -> Response:
        context.booking.date = message.strip()

        return self._response(
            context,
            "¿A qué hora quieres la cita?",
        )

    def _handle_time(self, context: Any, message: str) -> Response:
        context.booking.time = message.strip()

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