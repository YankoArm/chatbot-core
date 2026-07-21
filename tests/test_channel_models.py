import pytest

from chatbot.channels import IncomingMessage, OutgoingMessage


def test_incoming_message_stores_channel_data() -> None:
    message = IncomingMessage(
        session_id="session-1",
        text="Hola",
        sender_id="user-123",
        metadata={"channel": "web"},
    )

    assert message.session_id == "session-1"
    assert message.text == "Hola"
    assert message.sender_id == "user-123"
    assert message.metadata == {"channel": "web"}


@pytest.mark.parametrize(
    "session_id",
    ["", " ", "   "],
)
def test_incoming_message_rejects_empty_session_id(
    session_id: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="session_id cannot be empty",
    ):
        IncomingMessage(
            session_id=session_id,
            text="Hola",
        )


@pytest.mark.parametrize(
    "text",
    ["", " ", "   "],
)
def test_incoming_message_rejects_empty_text(
    text: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="text cannot be empty",
    ):
        IncomingMessage(
            session_id="session-1",
            text=text,
        )


def test_outgoing_message_stores_response_data() -> None:
    message = OutgoingMessage(
        text="Hola, ¿en qué puedo ayudarte?",
        metadata={"capability": "menu"},
    )

    assert message.text == "Hola, ¿en qué puedo ayudarte?"
    assert message.metadata == {"capability": "menu"}