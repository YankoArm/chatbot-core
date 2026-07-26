from __future__ import annotations

from pathlib import Path

from chatbot.application.bootstrap import Bootstrap
from chatbot.booking.service import BookingService
from chatbot.calendar import (
    CalendarService,
    GoogleCalendarProvider,
)
from chatbot.calendar.google_auth import (
    build_google_calendar_service,
)
from chatbot.capabilities.booking.capability import (
    BookingCapability,
)
from chatbot.instances.instance import Instance


DEFAULT_CREDENTIALS_PATH = Path(
    "secrets/google_credentials.json"
)

DEFAULT_TOKEN_PATH = Path(
    "secrets/google_token.json"
)

DEFAULT_CALENDAR_ID = "primary"
DEFAULT_TIMEZONE = "Europe/Madrid"


def build_booking_service() -> BookingService:
    """
    Build the booking service backed by Google Calendar.
    """

    google_service = build_google_calendar_service(
        credentials_path=DEFAULT_CREDENTIALS_PATH,
        token_path=DEFAULT_TOKEN_PATH,
    )

    calendar_provider = GoogleCalendarProvider(
        service=google_service,
        calendar_id=DEFAULT_CALENDAR_ID,
        timezone=DEFAULT_TIMEZONE,
    )

    calendar_service = CalendarService(
        calendar_provider
    )

    return BookingService(
        calendar_service
    )


def build_application(
    booking_service: BookingService,
):
    """
    Build FlowForge with the Google-backed booking capability.
    """

    instance = Instance(
        id="flowforge-google-calendar",
        name="FlowForge Google Calendar",
        default_language="es",
        channels=[
            "cli",
        ],
        capabilities=[
            "greeting",
            "booking",
        ],
    )

    bootstrap = Bootstrap(
        capability_factories={
            "booking": lambda: BookingCapability(
                booking_service=booking_service,
            ),
        },
    )

    return bootstrap.build_from_instance(
        instance
    )


def main() -> None:
    print(
        "Google Calendar application composition "
        "loaded correctly."
    )


if __name__ == "__main__":
    main()