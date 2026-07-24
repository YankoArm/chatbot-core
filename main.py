from __future__ import annotations

from chatbot.application.bootstrap import Bootstrap
from chatbot.channels import ApplicationChannel, CLIChannel
from chatbot.instances.instance import Instance


def main() -> None:
    instance = Instance(
        id="flowforge-cli",
        name="FlowForge CLI",
        default_language="es",
        channels=[
            "cli",
        ],
        capabilities=[
            "greeting",
            "booking",
        ],
    )

    application = Bootstrap().build_from_instance(instance)

    application_channel = ApplicationChannel(application)
    cli_channel = CLIChannel(application_channel)

    cli_channel.run(
        session_id="cli-session",
        sender_id="cli-user",
        prompt="Tú: ",
    )


if __name__ == "__main__":
    main()