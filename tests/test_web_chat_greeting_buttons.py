from types import SimpleNamespace

import pytest

from chatbot.api.web_chat import _format_web_chat_reply_text
from chatbot.capabilities.greeting import GreetingCapability
from chatbot.language import Language


@pytest.mark.parametrize("language", [Language.ES, Language.EN])
def test_web_greeting_keeps_welcome_and_removes_text_menu(language):
    greetings = {
        "menu": {
            "enabled": True,
            "items": {"services": True, "human_transfer": True},
        },
    }
    definition = SimpleNamespace(settings={
        "knowledge": {"greetings": greetings},
    })
    welcome = "Welcome" if language is Language.EN else "Hola"
    result = SimpleNamespace(
        text=GreetingCapability._append_guided_menu(
            response_text=welcome,
            greetings=greetings,
            language=language,
        ),
        metadata={
            "capability": "greeting",
            "language": language.value,
        },
    )

    assert result.text != welcome
    assert _format_web_chat_reply_text(definition, result) == welcome


def test_web_contact_question_is_preserved():
    definition = SimpleNamespace(settings={})
    result = SimpleNamespace(
        text="Your phone number?",
        metadata={"capability": "lead_capture"},
    )

    assert _format_web_chat_reply_text(definition, result) == result.text
