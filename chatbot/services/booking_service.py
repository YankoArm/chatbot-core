# chatbot/services/booking_service.py

class BookingService:

    AVAILABLE_DATES = [
        "2026-04-21 10:00",
        "2026-04-21 12:00",
        "2026-04-22 16:00",
    ]

    @classmethod
    def get_available_dates(cls):
        return cls.AVAILABLE_DATES