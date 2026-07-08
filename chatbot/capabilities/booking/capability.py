from typing import Any
from chatbot.responses import Response
from chatbot.capabilities.base_capability import BaseCapability


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

        keywords = (
            "reserv",
            "cita",
            "appointment",
            "book",
            "booking",
        )

        return any(keyword in text for keyword in keywords)

    def handle(self, context: Any, message: str) -> Response:
        return Response(
            text="Booking Capability handled the request.",
            metadata={
                "capability": self.name,
                "handled": True,
            },
        )