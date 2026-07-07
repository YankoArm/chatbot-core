from chatbot.capabilities.base_capability import BaseCapability


class BookingCapability(BaseCapability):
    name = "booking"
    version = "1.0"
    dependencies = []

    def register(self, context: dict) -> None:
        context.setdefault("flows", [])
        context.setdefault("actions", [])

        context["flows"].append("booking_flow")