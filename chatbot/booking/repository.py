from __future__ import annotations

from abc import ABC, abstractmethod

from chatbot.booking.models import Booking


class BookingRepository(ABC):
    """
    Persistence contract for completed bookings.
    """

    @abstractmethod
    def save(self, booking: Booking) -> None:
        """
        Persist a completed booking.
        """

        raise NotImplementedError