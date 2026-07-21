from __future__ import annotations

from collections.abc import Callable

from chatbot.channels.application_channel import ApplicationChannel
from chatbot.channels.message import IncomingMessage
from chatbot.channels.result import OutgoingMessage


InputReader = Callable[[str], str]
OutputWriter = Callable[[str], None]


class CLIChannel:
    """
    Interactive command-line channel for FlowForge applications.
    """

    def __init__(
        self,
        application_channel: ApplicationChannel,
        input_reader: InputReader = input,
        output_writer: OutputWriter = print,
    ) -> None:
        self._application_channel = application_channel
        self._input_reader = input_reader
        self._output_writer = output_writer

    def process(
        self,
        *,
        session_id: str,
        text: str,
        sender_id: str | None = None,
    ) -> OutgoingMessage:
        """
        Process a single CLI message without starting an interactive loop.
        """

        incoming = IncomingMessage(
            session_id=session_id,
            text=text,
            sender_id=sender_id,
            metadata={
                "channel": "cli",
            },
        )

        return self._application_channel.receive(incoming)

    def run(
        self,
        *,
        session_id: str = "cli-session",
        sender_id: str = "cli-user",
        prompt: str = "> ",
        exit_commands: tuple[str, ...] = (
            "exit",
            "quit",
            "salir",
        ),
    ) -> None:
        """
        Run an interactive CLI loop until the user enters an exit command.
        """

        normalized_exit_commands = {
            command.strip().casefold()
            for command in exit_commands
        }

        while True:
            text = self._input_reader(prompt)

            if text.strip().casefold() in normalized_exit_commands:
                break

            if not text.strip():
                continue

            outgoing = self.process(
                session_id=session_id,
                text=text,
                sender_id=sender_id,
            )

            self._output_writer(outgoing.text)