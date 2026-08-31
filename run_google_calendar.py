from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from chatbot.calendar import (
    CalendarService,
    GoogleCalendarProvider,
)
from chatbot.calendar.google_auth import (
    build_google_calendar_service,
)


DEFAULT_CREDENTIALS_PATH = Path(
    "secrets/google_credentials.json"
)

DEFAULT_TOKEN_PATH = Path(
    "secrets/google_token.json"
)

DEFAULT_CALENDAR_ID = "primary"
DEFAULT_TIMEZONE = "Europe/Madrid"
DEFAULT_SEARCH_DAYS = 30


def build_calendar_service_factory():
    """
    Build CalendarService instances sharing one Google authentication.
    """

    google_service = build_google_calendar_service(
        credentials_path=DEFAULT_CREDENTIALS_PATH,
        token_path=DEFAULT_TOKEN_PATH,
    )

    def build_for_calendar(
        calendar_id: str,
    ) -> CalendarService:
        calendar_provider = GoogleCalendarProvider(
            service=google_service,
            calendar_id=calendar_id,
            timezone=DEFAULT_TIMEZONE,
        )

        return CalendarService(
            calendar_provider
        )

    return build_for_calendar


def build_calendar_service() -> CalendarService:
    """
    Build the legacy default CalendarService.
    """

    return build_calendar_service_factory()(
        DEFAULT_CALENDAR_ID
    )

def list_upcoming_bookings(
    calendar_service: CalendarService,
    *,
    days: int = DEFAULT_SEARCH_DAYS,
) -> list[dict[str, Any]]:
    """
    Return timed calendar events occurring during the next days.
    """

    if days <= 0:
        raise ValueError(
            "Search days must be greater than zero."
        )

    timezone = ZoneInfo(
        DEFAULT_TIMEZONE
    )

    start = datetime.now(
        timezone
    )

    end = start + timedelta(
        days=days
    )

    return calendar_service.list_bookings(
        start=start,
        end=end,
    )


def print_bookings(
    bookings: list[dict[str, Any]],
) -> None:
    """
    Print bookings returned by CalendarService.
    """

    if not bookings:
        print(
            "No timed events found in the requested period."
        )
        return

    print(
        f"Found {len(bookings)} timed event(s):"
    )

    for index, booking in enumerate(
        bookings,
        start=1,
    ):
        print()
        print(
            f"{index}. {booking['title'] or '(untitled event)'}"
        )
        print(
            f"   ID: {booking['id']}"
        )
        print(
            f"   Start: {booking['start'].isoformat()}"
        )
        print(
            f"   End: {booking['end'].isoformat()}"
        )

        description = booking.get(
            "description"
        )

        if description:
            print(
                f"   Description: {description}"
            )

        attendee = booking.get(
            "attendee"
        )

        if attendee:
            print(
                f"   Attendee: {attendee}"
            )


def main() -> None:
    print(
        "Connecting FlowForge to Google Calendar..."
    )

    calendar_service = build_calendar_service()

    print(
        "Google Calendar authentication completed successfully."
    )

    print(
        f"Reading events from the next "
        f"{DEFAULT_SEARCH_DAYS} days..."
    )

    bookings = list_upcoming_bookings(
        calendar_service
    )

    print_bookings(
        bookings
    )

    check_test_availability(
        calendar_service
    )

    booking_id = create_test_booking(
        calendar_service
    )

    delete_test_booking(
        calendar_service,
        booking_id,
    )

def check_test_availability(
    calendar_service: CalendarService,
) -> None:
    """
    Check whether a test time slot is available.
    """

    test_date = "30/07/2026"
    test_time = "10:00"

    available = calendar_service.is_available(
        date=test_date,
        time=test_time,
        duration_minutes=60,
    )

    status = (
        "AVAILABLE"
        if available
        else "NOT AVAILABLE"
    )

    print()
    print("Availability test:")
    print(
        f"Date: {test_date}"
    )
    print(
        f"Time: {test_time}"
    )
    print(
        f"Duration: 60 minutes"
    )
    print(
        f"Result: {status}"
    )

def create_test_booking(
    calendar_service: CalendarService,
) -> str:
    """
    Create a temporary booking in Google Calendar.
    """

    booking_id = calendar_service.create_booking(
        date="31/07/2099",
        time="10:00",
        title="FlowForge Integration Test",
        description=(
            "Temporary booking created "
            "by FlowForge sandbox."
        ),
        metadata={
            "source": "flowforge",
            "environment": "sandbox",
        },
    )

    print()
    print("Booking created successfully.")
    print(f"Booking id: {booking_id}")

    return booking_id

def delete_test_booking(
    calendar_service: CalendarService,
    booking_id: str,
) -> None:
    """
    Delete the temporary booking.
    """

    calendar_service.cancel_booking(
        booking_id
    )

    print()
    print("Booking deleted successfully.")

if __name__ == "__main__":
    main()