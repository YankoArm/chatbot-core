# chatbot/services/intent_detector.py

from typing import Literal

Intent = Literal[
    "greeting",
    "sessions_info",
    "prices_info",
    "booking",
    "farewell",
    "unknown",
]


class IntentDetector:
    GREETING_KEYWORDS = {
        "hola", "buenas", "hello", "hi", "hey"
    }

    SESSIONS_KEYWORDS = {
        "sesión", "sesiones", "session", "sessions", "tarot", "reading", "consulta"
    }

    PRICES_KEYWORDS = {
        "precio", "precios", "price", "prices", "cost", "cuesta", "coste"
    }

    BOOKING_KEYWORDS = {
        "reservar", "reserva", "cita", "book", "booking", "appointment", "fecha"
    }

    FAREWELL_KEYWORDS = {
        "adiós", "adios", "hasta luego", "bye", "goodbye", "see you"
    }

    @classmethod
    def detect(cls, message: str) -> Intent:
        text = message.lower()

        if any(word in text for word in cls.GREETING_KEYWORDS):
            return "greeting"

        if any(word in text for word in cls.PRICES_KEYWORDS):
            return "prices_info"

        if any(word in text for word in cls.BOOKING_KEYWORDS):
            return "booking"

        if any(word in text for word in cls.SESSIONS_KEYWORDS):
            return "sessions_info"

        if any(word in text for word in cls.FAREWELL_KEYWORDS):
            return "farewell"

        return "unknown"