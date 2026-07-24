from __future__ import annotations

from dataclasses import dataclass

from chatbot.booking.state import BookingStep


@dataclass(frozen=True, slots=True)
class Booking:
    """
    Complete booking request ready to be processed or persisted.
    """

    name: str
    phone: str
    date: str
    time: str


__all__ = [
    "Booking",
    "BookingStep",
]