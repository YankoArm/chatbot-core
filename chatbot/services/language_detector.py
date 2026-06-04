# chatbot/services/language_detector.py

from typing import Literal

Language = Literal["es", "en"]


class LanguageDetector:
    ES_KEYWORDS = {
        "hola", "buenas", "precio", "precios", "sesión", "sesiones",
        "cita", "reservar", "reserva", "tarot", "quiero", "información",
        "ayuda", "gracias", "adiós", "hasta luego"
    }

    EN_KEYWORDS = {
        "hello", "hi", "price", "prices", "session", "sessions",
        "appointment", "book", "booking", "tarot", "i want", "information",
        "help", "thanks", "bye", "goodbye"
    }

    @classmethod
    def detect(cls, message: str) -> Language:
        text = message.lower()

        es_score = sum(1 for word in cls.ES_KEYWORDS if word in text)
        en_score = sum(1 for word in cls.EN_KEYWORDS if word in text)

        if en_score > es_score:
            return "en"

        return "es"