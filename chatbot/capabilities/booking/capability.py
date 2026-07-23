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
        context.set_active_capability(self.name)

        if context.booking is None:
            return self._start_booking(context)

        if context.booking.next_step is BookingStep.NAME:
            return self._handle_name(context, message)

        if context.booking.next_step is BookingStep.PHONE:
            return self._handle_phone(context, message)

        if context.booking.next_step is BookingStep.DATE:
            return self._handle_date(context, message)

        if context.booking.next_step is BookingStep.TIME:
            return self._handle_time(context, message)

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

        return Response(
            text="Perfecto. Vamos a reservar una cita. ¿Cómo te llamas?",
            metadata={
                "capability": self.name,
                "handled": True,
                "booking_step": context.booking.next_step.value,
            },
        )

    def _handle_name(self, context: Any, message: str) -> Response:
        context.booking.name = message.strip()

        return Response(
            text=(
                f"Encantado, {context.booking.name}. "
                "¿Cuál es tu número de teléfono?"
            ),
            metadata={
                "capability": self.name,
                "handled": True,
                "booking_step": context.booking.next_step.value,
            },
        )

    def _handle_phone(self, context: Any, message: str) -> Response:
        context.booking.phone = message.strip()

        return Response(
            text="¿Para qué día quieres la cita?",
            metadata={
                "capability": self.name,
                "handled": True,
                "booking_step": context.booking.next_step.value,
            },
        )

    def _handle_date(self, context: Any, message: str) -> Response:
        context.booking.date = message.strip()

        return Response(
            text="¿A qué hora quieres la cita?",
            metadata={
                "capability": self.name,
                "handled": True,
                "booking_step": context.booking.next_step.value,
            },
        )

    def _handle_time(self, context: Any, message: str) -> Response:
        context.booking.time = message.strip()

        return Response(
            text=(
                f"Perfecto, {context.booking.name}. "
                f"He registrado tu solicitud para "
                f"{context.booking.date} a las "
                f"{context.booking.time}."
            ),
            metadata={
                "capability": self.name,
                "handled": True,
                "booking_step": context.booking.next_step.value,
            },
        )