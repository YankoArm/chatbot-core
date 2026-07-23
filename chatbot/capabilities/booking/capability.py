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
            context.booking = BookingState()

            return Response(
                text="Perfecto. Vamos a reservar una cita. ¿Cómo te llamas?",
                metadata={
                    "capability": self.name,
                    "handled": True,
                    "booking_step": context.booking.next_step.value,
                },
            )

        if context.booking.next_step is BookingStep.NAME:
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

        if context.booking.next_step is BookingStep.PHONE:
            context.booking.phone = message.strip()

            return Response(
                text="¿Para qué día quieres la cita?",
                metadata={
                    "capability": self.name,
                    "handled": True,
                    "booking_step": context.booking.next_step.value,
                },
            )

        return Response(
            text="La reserva ya está en curso.",
            metadata={
                "capability": self.name,
                "handled": True,
                "booking_step": context.booking.next_step.value,
            },
        )