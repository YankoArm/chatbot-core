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
        raise NotImplementedError

    @abstractmethod
    def update(
        self,
        booking: Booking,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def find_by_phone(
        self,
        phone: str,
    ) -> tuple[Booking, ...]:
        raise NotImplementedError

    @abstractmethod
    def find_by_client_and_phone(
        self,
        *,
        client_id: str,
        phone: str,
    ) -> tuple[Booking, ...]:
        raise NotImplementedError