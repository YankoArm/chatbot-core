from __future__ import annotations

from chatbot.application import Bootstrap
from chatbot.booking import (
    BookingService,
    InMemoryBookingRepository,
)
from chatbot.capabilities.booking import (
    BookingCapability,
)
from chatbot.channels import (
    ApplicationChannel,
    CLIChannel,
)
from chatbot.instances import Instance
from run_google_calendar import (
    build_calendar_service,
)


def main() -> None:
    """
    Run FlowForge using the interactive CLI channel.
    """

    instance = Instance(
        id="demo",
        name="FlowForge Demo",
        capabilities=[
            "greeting",
            "booking",
        ],
    )

    calendar_service = build_calendar_service()

    booking_repository = (
        InMemoryBookingRepository()
    )

    booking_service = BookingService(
        repository=booking_repository,
        calendar_service=calendar_service,
    )

    bootstrap = Bootstrap(
        capability_factories={
            "booking": lambda: BookingCapability(
                booking_service=booking_service,
            ),
        },
    )

    application = bootstrap.build_from_instance(
        instance,
    )

    application_channel = ApplicationChannel(
        application,
    )

    cli = CLIChannel(
        application_channel,
    )

    print("=" * 50)
    print(" FlowForge CLI")
    print("=" * 50)
    print(
        "Google Calendar integration enabled."
    )
    print(
        "Type 'exit', 'quit' or 'salir' to close."
    )
    print()

    cli.run()


if __name__ == "__main__":
    main()