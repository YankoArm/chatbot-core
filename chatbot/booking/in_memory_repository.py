from __future__ import annotations

from chatbot.booking.models import Booking
from chatbot.booking.repository import BookingRepository


class InMemoryBookingRepository(
    BookingRepository
):
    """
    Store completed bookings in memory.

    Intended for tests, demos and local development.
    """

    def __init__(self) -> None:
        self._bookings: list[Booking] = []

    def save(
        self,
        booking: Booking,
    ) -> None:
        self._bookings.append(
            booking
        )

    def list_all(
        self,
    ) -> list[Booking]:
        """
        Return a copy of all stored bookings.
        """

        return list(
            self._bookings
        )