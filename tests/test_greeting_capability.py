from __future__ import annotations

import pytest

from chatbot.responses.response import Response
from chatbot.capabilities.greeting import GreetingCapability
from chatbot.conversation import ConversationContext


@pytest.fixture
def capability() -> GreetingCapability:
    return GreetingCapability()


@pytest.fixture
def context() -> ConversationContext:
    return ConversationContext(
        session_id="test-session",
    )


@pytest.mark.parametrize(
    "message",
    [
        "hola",
        "Hola",
        "HOLA",
        "hola!",
        "hola chatbot",
        "buenas",
        "buenos dias",
        "buenas tardes",
        "buenas noches",
        "hi",
        "hello",
        "hello there",
        "hey!",
    ],
)
def test_can_handle_common_greetings(
    capability: GreetingCapability,
    context: ConversationContext,
    message: str,
) -> None:
    assert capability.can_handle(context, message) is True


@pytest.mark.parametrize(
    "message",
    [
        "quiero reservar una cita",
        "cuanto cuesta",
        "necesito ayuda",
        "adios",
        "",
        "   ",
    ],
)
def test_cannot_handle_unrelated_messages(
    capability: GreetingCapability,
    context: ConversationContext,
    message: str,
) -> None:
    assert capability.can_handle(context, message) is False


def test_handle_returns_response(
    capability: GreetingCapability,
    context: ConversationContext,
) -> None:
    response = capability.handle(
        context,
        "hola",
    )

    assert isinstance(response, Response)
    assert response.text == "¡Hola! 👋 ¿En qué puedo ayudarte?"
    assert response.actions == []
    assert response.metadata == {}
    assert response.next_capability is None


def test_handle_sets_active_capability(
    capability: GreetingCapability,
    context: ConversationContext,
) -> None:
    capability.handle(
        context,
        "hola",
    )

    assert context.active_capability == "greeting"