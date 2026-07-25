from __future__ import annotations

from datetime import datetime, timedelta

from chatbot.booking.models import Booking
from chatbot.booking.repository import BookingRepository
from chatbot.booking.state import BookingState
from chatbot.calendar import CalendarProvider


class BookingService:
    """
    Coordinate booking-related business operations.

    The calendar provider is optional so the booking domain can still be
    used without an external calendar integration.
    """

    def __init__(
        self,
        repository: BookingRepository,
        calendar_provider: CalendarProvider | None = None,
        duration_minutes: int = 60,
    ) -> None:
        if duration_minutes <= 0:
            raise ValueError(
                "Booking duration must be greater than zero."
            )

        self._repository = repository
        self._calendar_provider = calendar_provider
        self._duration_minutes = duration_minutes

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
        Build and persist a booking from completed conversation state.

        When a calendar provider is configured, availability is checked
        before the booking is persisted and a corresponding calendar event
        is created.
        """

        if not state.is_complete:
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

        self._create_calendar_booking(
            booking
        )

        self.create_booking(
            booking
        )

        return booking

    def _create_calendar_booking(
        self,
        booking: Booking,
    ) -> str | None:
        """
        Create the external calendar event when integration is enabled.
        """

        if self._calendar_provider is None:
            return None

        start = self._parse_start_datetime(
            booking
        )

        end = start + timedelta(
            minutes=self._duration_minutes
        )

        if not self._calendar_provider.is_available(
            start=start,
            end=end,
        ):
            raise ValueError(
                "Requested booking time is not available."
            )

        return self._calendar_provider.create_booking(
            start=start,
            end=end,
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
    def _parse_start_datetime(
        booking: Booking,
    ) -> datetime:
        """
        Convert the booking date and time strings to a datetime.

        The current booking conversation uses the Spanish date format
        DD/MM/YYYY and a 24-hour HH:MM time.
        """

        raw_datetime = (
            f"{booking.date} {booking.time}"
        )

        try:
            return datetime.strptime(
                raw_datetime,
                "%d/%m/%Y %H:%M",
            )
        except ValueError as exc:
            raise ValueError(
                "Booking date and time must use "
                "DD/MM/YYYY and HH:MM formats."
            ) from exc

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