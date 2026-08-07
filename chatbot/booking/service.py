from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

from chatbot.availability import (
    BookingRules,
    BusinessHours,
    TimeSlot,
)
from chatbot.booking.models import Booking
from chatbot.booking.repository import BookingRepository
from chatbot.booking.state import BookingState
from chatbot.calendar import CalendarService


class BookingSlotUnavailableError(Exception):
    """
    Raised when the selected booking slot is no longer available.
    """


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
        *,
        business_hours: BusinessHours | None = None,
        rules: BookingRules | None = None,
        now: datetime | None = None,
    ) -> Booking:
        """
        Build and persist a booking from complete conversation state.

        When calendar integration and availability configuration are
        enabled, the selected time is checked again immediately before
        creating the external event.

        The external calendar event is created before the local booking
        is persisted.
        """

        if not state.has_required_data:
            raise ValueError(
                "Cannot create a booking from incomplete state."
            )

        if (
            self._calendar_service is not None
            and business_hours is not None
            and rules is not None
        ):
            self._ensure_slot_is_available(
                state,
                business_hours=business_hours,
                rules=rules,
                now=now,
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

        state.available_times = ()

        return booking

    def get_available_dates(
        self,
        *,
        start_date: date,
        days: int,
        business_hours: BusinessHours,
        rules: BookingRules,
        now: datetime,
    ) -> tuple[date, ...]:
        """
        Return dates containing at least one available booking slot.

        Calendar availability is delegated to CalendarService.
        """

        if self._calendar_service is None:
            return ()

        return (
            self._calendar_service
            .get_available_dates(
                start_date=start_date,
                days=days,
                business_hours=business_hours,
                rules=rules,
                now=now,
            )
        )

    def get_available_slots_for_date(
        self,
        target_date: date,
        *,
        business_hours: BusinessHours,
        rules: BookingRules,
        now: datetime,
    ) -> tuple[TimeSlot, ...]:
        """
        Return available booking slots for a date.

        Calendar availability is delegated to CalendarService.
        """

        if self._calendar_service is None:
            return ()

        return (
            self._calendar_service
            .get_available_slots_for_date(
                target_date,
                business_hours=business_hours,
                rules=rules,
                now=now,
            )
        )

    def _ensure_slot_is_available(
        self,
        state: BookingState,
        *,
        business_hours: BusinessHours,
        rules: BookingRules,
        now: datetime | None = None,
    ) -> None:
        """
        Check that the selected conversation slot is still available.

        Availability is recalculated immediately before the external
        calendar event is created to reduce double-booking risks.
        """

        date_value = self._require_value(
            state.date,
            "date",
        )

        time_value = self._require_value(
            state.time,
            "time",
        )

        target_date = datetime.strptime(
            date_value,
            "%d/%m/%Y",
        ).date()

        timezone = ZoneInfo(
            business_hours.timezone_name
        )

        current_time = (
            now
            if now is not None
            else datetime.now(timezone)
        )

        available_slots = (
            self.get_available_slots_for_date(
                target_date,
                business_hours=business_hours,
                rules=rules,
                now=current_time,
            )
        )

        available_times = {
            slot.start.strftime("%H:%M")
            for slot in available_slots
        }

        if time_value not in available_times:
            raise BookingSlotUnavailableError(
                "The selected booking slot is no longer available."
            )

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
        """
        Return a normalized required value.

        Raise ValueError when the value is missing or empty.
        """

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