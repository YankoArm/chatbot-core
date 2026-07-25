from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class CalendarProvider(ABC):
    """
    Abstract calendar integration used by booking services.

    Concrete providers may connect FlowForge to Google Calendar,
    Microsoft Outlook, CalDAV or an in-memory test implementation.
    """

    @abstractmethod
    def is_available(
        self,
        *,
        start: datetime,
        end: datetime,
    ) -> bool:
        """
        Return whether the requested time range is available.
        """

        raise NotImplementedError

    @abstractmethod
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
        Create a calendar booking and return its external identifier.
        """

        raise NotImplementedError

    @abstractmethod
    def cancel_booking(
        self,
        booking_id: str,
    ) -> None:
        """
        Cancel an existing booking.
        """

        raise NotImplementedError

    @abstractmethod
    def list_bookings(
        self,
        *,
        start: datetime,
        end: datetime,
    ) -> list[dict[str, Any]]:
        """
        Return bookings within the requested time range.
        """

        raise NotImplementedError