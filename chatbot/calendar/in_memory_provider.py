from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from chatbot.calendar.provider import CalendarProvider


class InMemoryCalendarProvider(CalendarProvider):
    """
    In-memory calendar provider for tests and local development.

    Bookings are stored only for the lifetime of the provider instance.
    """

    def __init__(self) -> None:
        self._bookings: dict[
            str,
            dict[str, Any],
        ] = {}

    def is_available(
        self,
        *,
        start: datetime,
        end: datetime,
    ) -> bool:
        """
        Return whether the requested time range does not overlap
        with an existing booking.
        """

        self._validate_time_range(
            start=start,
            end=end,
        )

        return not any(
            self._ranges_overlap(
                start=start,
                end=end,
                booking_start=booking["start"],
                booking_end=booking["end"],
            )
            for booking in self._bookings.values()
        )

    def create_booking(
        self,
        *,
        start: datetime,
        end: datetime,
        title: str,
        description: str | None = None,
        attendee: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        Store a booking and return its generated identifier.
        """

        self._validate_time_range(
            start=start,
            end=end,
        )

        normalized_title = title.strip()

        if not normalized_title:
            raise ValueError(
                "Booking title cannot be empty."
            )

        if not self.is_available(
            start=start,
            end=end,
        ):
            raise ValueError(
                "Requested time range is not available."
            )

        booking_id = str(
            uuid4()
        )

        self._bookings[booking_id] = {
            "id": booking_id,
            "start": start,
            "end": end,
            "title": normalized_title,
            "description": description,
            "attendee": attendee,
            "metadata": dict(
                metadata or {}
            ),
        }

        return booking_id

    def reschedule_booking(
        self,
        booking_id: str,
        *,
        start: datetime,
        end: datetime,
    ) -> None:
        """
        Change the time range of an existing booking.
        """

        self._validate_time_range(
            start=start,
            end=end,
        )

        normalized_booking_id = (
            booking_id.strip()
        )

        if not normalized_booking_id:
            raise ValueError(
                "Booking ID cannot be empty."
            )

        if normalized_booking_id not in self._bookings:
            raise KeyError(
                f"Booking not found: "
                f"{normalized_booking_id}"
            )

        overlaps_another_booking = any(
            self._ranges_overlap(
                start=start,
                end=end,
                booking_start=booking["start"],
                booking_end=booking["end"],
            )
            for existing_id, booking
            in self._bookings.items()
            if existing_id != normalized_booking_id
        )

        if overlaps_another_booking:
            raise ValueError(
                "Requested time range is not available."
            )

        self._bookings[
            normalized_booking_id
        ]["start"] = start

        self._bookings[
            normalized_booking_id
        ]["end"] = end

    def cancel_booking(
        self,
        booking_id: str,
    ) -> None:
        """
        Remove a booking by identifier.
        """

        normalized_booking_id = (
            booking_id.strip()
        )

        if not normalized_booking_id:
            raise ValueError(
                "Booking ID cannot be empty."
            )

        if normalized_booking_id not in self._bookings:
            raise KeyError(
                f"Booking not found: "
                f"{normalized_booking_id}"
            )

        del self._bookings[
            normalized_booking_id
        ]

    def list_bookings(
        self,
        *,
        start: datetime,
        end: datetime,
    ) -> list[dict[str, Any]]:
        """
        Return bookings that overlap the requested time range.
        """

        self._validate_time_range(
            start=start,
            end=end,
        )

        bookings = [
            dict(booking)
            for booking in self._bookings.values()
            if self._ranges_overlap(
                start=start,
                end=end,
                booking_start=booking["start"],
                booking_end=booking["end"],
            )
        ]

        return sorted(
            bookings,
            key=lambda booking: booking["start"],
        )

    @staticmethod
    def _validate_time_range(
        *,
        start: datetime,
        end: datetime,
    ) -> None:
        if end <= start:
            raise ValueError(
                "Booking end must be after start."
            )

    @staticmethod
    def _ranges_overlap(
        *,
        start: datetime,
        end: datetime,
        booking_start: datetime,
        booking_end: datetime,
    ) -> bool:
        return (
            start < booking_end
            and end > booking_start
        )