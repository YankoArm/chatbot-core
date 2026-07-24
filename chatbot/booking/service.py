from __future__ import annotations

from chatbot.booking.models import Booking
from chatbot.booking.repository import BookingRepository
from chatbot.booking.state import BookingState


class BookingService:
    """
    Coordinates booking-related business operations.
    """

    def __init__(self, repository: BookingRepository) -> None:
        self._repository = repository

    def create_booking(self, booking: Booking) -> None:
        """
        Persist a completed booking.
        """

        self._repository.save(booking)

    def create_booking_from_state(
        self,
        state: BookingState,
    ) -> Booking:
        """
        Build and persist a booking from completed conversation state.
        """

        if not state.is_complete:
            raise ValueError(
                "Cannot create a booking from incomplete state."
            )

        booking = Booking(
            name=self._require_value(state.name, "name"),
            phone=self._require_value(state.phone, "phone"),
            date=self._require_value(state.date, "date"),
            time=self._require_value(state.time, "time"),
        )

        self.create_booking(booking)

        return booking

    @staticmethod
    def _require_value(
        value: str | None,
        field_name: str,
    ) -> str:
        if value is None:
            raise ValueError(
                f"Booking field '{field_name}' is required."
            )

        return value