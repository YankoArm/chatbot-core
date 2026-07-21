from __future__ import annotations

from chatbot.responses.response import Response
from chatbot.capabilities.base_capability import BaseCapability


class GreetingCapability(BaseCapability):
    """
    Handles common greetings from the user.
    """

    name = "greeting"

    _GREETINGS = {
        "hola",
        "buenas",
        "buenos dias",
        "buenas tardes",
        "buenas noches",
        "hi",
        "hello",
        "hey",
    }

    def can_handle(self, context, message: str) -> bool:
        text = message.strip().lower()

        return any(
            text.startswith(greeting)
            for greeting in self._GREETINGS
        )

    def handle(self, context, message: str) -> Response:
        context.set_active_capability(self.name)

        return Response(
            text="¡Hola! 👋 ¿En qué puedo ayudarte?"
        )