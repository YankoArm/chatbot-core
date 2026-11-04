from dataclasses import replace

from chatbot.api.admin_preview import (
    build_client_definition,
    build_instance_from_definition,
)
from chatbot.application.bootstrap import Bootstrap


def make_app(enabled, reminders=None):
    definition = build_client_definition("tarot_alvin")
    instance = build_instance_from_definition(definition)
    instance = replace(
        instance,
        activation=replace(
            instance.activation,
            remind_on_cooldown=enabled,
            reminder_messages=reminders or {},
        ),
    )
    return Bootstrap().build_from_instance(instance)


def test_english_reminder():
    app = make_app(True)
    session = "english-reminder"

    first = app.chat(session_id=session, message="hello")
    second = app.chat(session_id=session, message="hola")
    third = app.chat(session_id=session, message="TAROT")

    assert first.text.startswith("Hello")
    assert second.text == "To continue, please type TAROT."
    assert third.text.startswith("Tarot service activated")


def test_spanish_reminder():
    app = make_app(True)
    session = "spanish-reminder"

    first = app.chat(session_id=session, message="hola")
    second = app.chat(session_id=session, message="hello")

    assert first.text.startswith("Hola")
    assert second.text == "Para continuar, escribe TAROT."


def test_cooldown_unchanged_by_default():
    app = make_app(False)
    session = "no-reminder"

    app.chat(session_id=session, message="hello")
    second = app.chat(session_id=session, message="hola")

    assert second.text == ""


def test_custom_english_reminder():
    app = make_app(
        True,
        {"en": "Please enter TAROT to continue."},
    )
    session = "custom-reminder"

    app.chat(session_id=session, message="hello")
    second = app.chat(session_id=session, message="hola")

    assert second.text == "Please enter TAROT to continue."

def test_english_activation_uses_real_line_breaks():
    app = make_app(True)
    session = "english-activation-newlines"

    first = app.chat(session_id=session, message="hello")
    activated = app.chat(
        session_id=session,
        message="TAROT",
    )

    assert chr(10) * 2 in first.text
    assert chr(10) * 2 in activated.text
    assert chr(92) + "n" not in activated.text
