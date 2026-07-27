from __future__ import annotations

from chatbot.booking.models import Booking
from chatbot.booking.repository import BookingRepository
from chatbot.booking.state import BookingState
from chatbot.calendar import CalendarService


class BookingService:
    """
    Coordinate booking-related business operations.

    Booking persistence belongs to this service, while calendar-specific
    operations are delegated to CalendarService.
    """

    def __init__(
        self,
        repository: BookingRepository,
        calendar_service: CalendarService | None = None,
    ) -> None:
        self._repository = repository
        self._calendar_service = calendar_service

    def create_booking(
        self,
        booking: Booking,
    ) -> None:
        """
        Persist a completed booking.
        """

        self._repository.save(
            booking
        )

    def create_booking_from_state(
        self,
        state: BookingState,
    ) -> Booking:
        """
        Build and persist a booking from complete conversation state.

        When calendar integration is enabled, the external event is
        created before the local booking is persisted.
        """

        if not state.has_required_data:
            raise ValueError(
                "Cannot create a booking from incomplete state."
            )

        booking = Booking(
            name=self._require_value(
                state.name,
                "name",
            ),
            phone=self._require_value(
                state.phone,
                "phone",
            ),
            date=self._require_value(
                state.date,
                "date",
            ),
            time=self._require_value(
                state.time,
                "time",
            ),
        )

        calendar_booking_id = (
            self._create_calendar_booking(
                booking
            )
        )

        self.create_booking(
            booking
        )

        state.confirm(
            booking_id=calendar_booking_id
        )

        return booking

    def _create_calendar_booking(
        self,
        booking: Booking,
    ) -> str | None:
        """
        Create an external calendar event when integration is enabled.
        """

        if self._calendar_service is None:
            return None

        return self._calendar_service.create_booking(
            date=booking.date,
            time=booking.time,
            title=f"Booking - {booking.name}",
            description=(
                f"Client: {booking.name}\n"
                f"Phone: {booking.phone}"
            ),
            metadata={
                "client_name": booking.name,
                "client_phone": booking.phone,
                "booking_date": booking.date,
                "booking_time": booking.time,
            },
        )

    @staticmethod
    def _require_value(
        value: str | None,
        field_name: str,
    ) -> str:
        if value is None:
            raise ValueError(
                f"Booking field '{field_name}' is required."
            )

        normalized_value = value.strip()

        if not normalized_value:
            raise ValueError(
                f"Booking field '{field_name}' is required."
            )

        return normalized_value