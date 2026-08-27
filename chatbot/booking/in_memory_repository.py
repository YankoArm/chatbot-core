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

    def update(
        self,
        booking: Booking,
    ) -> None:
        """
        Replace an existing booking while preserving its position.
        """

        for index, existing_booking in enumerate(
            self._bookings
        ):
            if self._is_same_booking(
                existing_booking,
                booking,
            ):
                self._bookings[index] = booking
                return

        raise ValueError(
            "Cannot update a booking that is not stored."
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

    def find_by_phone(
        self,
        phone: str,
    ) -> tuple[Booking, ...]:
        """
        Return bookings matching the normalized phone number.
        """

        normalized_phone = phone.strip()

        return tuple(
            booking
            for booking in self._bookings
            if booking.phone.strip() == normalized_phone
        )

    @staticmethod
    def _is_same_booking(
        existing_booking: Booking,
        updated_booking: Booking,
    ) -> bool:
        """
        Determine whether two records represent the same booking.
        """

        if (
            existing_booking.calendar_booking_id is not None
            and updated_booking.calendar_booking_id is not None
        ):
            return (
                existing_booking.calendar_booking_id
                == updated_booking.calendar_booking_id
            )

        return (
            existing_booking.phone
            == updated_booking.phone
            and existing_booking.date
            == updated_booking.date
            and existing_booking.time
            == updated_booking.time
        )