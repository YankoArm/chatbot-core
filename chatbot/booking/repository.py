from __future__ import annotations

from abc import ABC, abstractmethod

from chatbot.booking.models import Booking


class BookingRepository(ABC):
    """
    Persistence contract for completed bookings.
    """

    @abstractmethod
    def save(
        self,
        booking: Booking,
    ) -> None:
        """
        Persist a completed booking.
        """

        raise NotImplementedError

    @abstractmethod
    def update(
        self,
        booking: Booking,
    ) -> None:
        """
        Replace a previously persisted booking.
        """

        raise NotImplementedError

    @abstractmethod
    def find_by_phone(
        self,
        phone: str,
    ) -> tuple[Booking, ...]:
        """
        Return bookings associated with a phone number.
        """

        raise NotImplementedError