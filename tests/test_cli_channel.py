from __future__ import annotations

from chatbot.channels import CLIChannel, OutgoingMessage


class FakeApplicationChannel:
    def __init__(self) -> None:
        self.messages = []

    def receive(self, message) -> OutgoingMessage:
        self.messages.append(message)

        return OutgoingMessage(
            text=f"response:{message.text}",
        )


def test_process_creates_cli_incoming_message() -> None:
    application_channel = FakeApplicationChannel()
    channel = CLIChannel(application_channel)

    outgoing = channel.process(
        session_id="session-1",
        text="Hola",
        sender_id="user-1",
    )

    assert outgoing.text == "response:Hola"

    assert len(application_channel.messages) == 1

    incoming = application_channel.messages[0]

    assert incoming.session_id == "session-1"
    assert incoming.text == "Hola"
    assert incoming.sender_id == "user-1"
    assert incoming.metadata == {
        "channel": "cli",
    }


def test_run_reads_messages_and_writes_responses() -> None:
    inputs = iter([
        "Hola",
        "Quiero información",
        "salir",
    ])

    outputs: list[str] = []

    application_channel = FakeApplicationChannel()

    channel = CLIChannel(
        application_channel,
        input_reader=lambda prompt: next(inputs),
        output_writer=outputs.append,
    )

    channel.run(
        session_id="session-1",
        sender_id="user-1",
    )

    assert outputs == [
        "response:Hola",
        "response:Quiero información",
    ]

    assert [
        message.text
        for message in application_channel.messages
    ] == [
        "Hola",
        "Quiero información",
    ]


def test_run_ignores_empty_messages() -> None:
    inputs = iter([
        "",
        "   ",
        "Hola",
        "exit",
    ])

    outputs: list[str] = []

    application_channel = FakeApplicationChannel()

    channel = CLIChannel(
        application_channel,
        input_reader=lambda prompt: next(inputs),
        output_writer=outputs.append,
    )

    channel.run()

    assert outputs == [
        "response:Hola",
    ]

    assert len(application_channel.messages) == 1


def test_run_accepts_case_insensitive_exit_command() -> None:
    inputs = iter([
        "SALIR",
    ])

    outputs: list[str] = []

    application_channel = FakeApplicationChannel()

    channel = CLIChannel(
        application_channel,
        input_reader=lambda prompt: next(inputs),
        output_writer=outputs.append,
    )

    channel.run()

    assert outputs == []
    assert application_channel.messages == []