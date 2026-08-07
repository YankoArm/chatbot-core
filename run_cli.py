from __future__ import annotations

from chatbot.application import Bootstrap
from chatbot.booking import (
    BookingService,
    InMemoryBookingRepository,
    build_booking_configuration,
)
from chatbot.business_templates.tarot import (
    create_tarot_template,
)
from chatbot.capabilities.booking import (
    BookingCapability,
)
from chatbot.channels import (
    ApplicationChannel,
    CLIChannel,
)
from chatbot.clients.tarot_alvin import (
    create_tarot_alvin_definition,
)
from chatbot.instances import InstanceResolver
from run_google_calendar import (
    build_calendar_service,
)


def main() -> None:
    """
    Run Tarot Alvin through the interactive CLI channel.
    """

    template = create_tarot_template()
    definition = create_tarot_alvin_definition()

    instance = InstanceResolver().resolve(
        template=template,
        definition=definition,
    )

    booking_configuration = (
        build_booking_configuration(
            instance
        )
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
                business_hours=(
                    booking_configuration.business_hours
                ),
                booking_rules=(
                    booking_configuration.booking_rules
                ),
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
    print(" FlowForge CLI - Tarot Alvin")
    print("=" * 50)
    print(
        "Google Calendar integration enabled."
    )
    print(
        "Client booking configuration loaded."
    )
    print(
        "Type 'exit', 'quit' or 'salir' to close."
    )
    print()

    cli.run()


if __name__ == "__main__":
    main()