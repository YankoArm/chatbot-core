from __future__ import annotations

import argparse
from collections.abc import Sequence

from chatbot.application import Bootstrap
from chatbot.booking import (
    BookingService,
    InMemoryBookingRepository,
    build_booking_configuration,
)
from chatbot.capabilities.booking import (
    BookingCapability,
)
from chatbot.channels import (
    ApplicationChannel,
    CLIChannel,
)
from chatbot.clients.registry import (
    build_client_instance,
    list_client_ids,
)
from run_google_calendar import (
    build_calendar_service,
)


def build_argument_parser() -> argparse.ArgumentParser:
    """
    Build the FlowForge CLI argument parser.
    """

    parser = argparse.ArgumentParser(
        description=(
            "Run a registered FlowForge client "
            "through the interactive CLI."
        ),
    )

    parser.add_argument(
        "--client",
        choices=list_client_ids(),
        default="tarot_alvin",
        help=(
            "Registered client to run. "
            "Defaults to tarot_alvin."
        ),
    )

    return parser


def main(
    argv: Sequence[str] | None = None,
) -> None:
    """
    Run a registered FlowForge client through the CLI channel.
    """

    arguments = build_argument_parser().parse_args(
        argv
    )

    instance = build_client_instance(
        arguments.client,
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
    print(f" FlowForge CLI - {instance.name}")
    print("=" * 50)
    print(f"Client: {instance.id}")
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