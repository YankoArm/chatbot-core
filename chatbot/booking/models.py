from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from chatbot.booking.state import BookingStep


class BookingStatus(str, Enum):
    """
    Current lifecycle status of a completed booking.
    """

    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class Booking:
    """
    Complete booking request ready to be processed or persisted.

    Service information is optional so generic appointment businesses
    remain compatible with the original booking model.
    """

    name: str
    phone: str
    date: str
    time: str
    client_id: str = "legacy"

    service_id: str | None = None
    service_name: str | None = None
    duration_minutes: int | None = None
    price_cents: int | None = None
    price_type: str | None = None
    currency: str | None = None

    calendar_booking_id: str | None = None
    status: BookingStatus = BookingStatus.CONFIRMED


__all__ = [
    "Booking",
    "BookingStatus",
    "BookingStep",
]