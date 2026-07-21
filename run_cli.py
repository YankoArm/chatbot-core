from __future__ import annotations

from chatbot.application import Bootstrap
from chatbot.channels import (
    ApplicationChannel,
    CLIChannel,
)
from chatbot.instances import Instance


def main() -> None:
    """
    Run FlowForge using the interactive CLI channel.
    """

    instance = Instance(
        id="demo",
        name="FlowForge Demo",
        capabilities=[
            "greeting",
        ],
    )

    bootstrap = Bootstrap()

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
    print("Type 'exit', 'quit' or 'salir' to close.")
    print()

    cli.run()


if __name__ == "__main__":
    main()