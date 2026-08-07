from datetime import datetime, timedelta

import pytest

from chatbot.activation import (
    ActivationAction,
    ActivationState,
    AlwaysActivePolicy,
    ExactPhrasePolicy,
)


def build_policy(
    prompt_cooldown: timedelta | None = None,
) -> ExactPhrasePolicy:
    return ExactPhrasePolicy(
        phrases=["Tarot"],
        prompt_message=(
            "Este número también se utiliza de forma personal. "
            "Para iniciar el asistente, escribe únicamente TAROT."
        ),
        activated_message=(
            "Asistente activado."
        ),
        prompt_cooldown=prompt_cooldown,
    )

def test_always_active_policy_continues() -> None:
    policy = AlwaysActivePolicy()
    state = ActivationState()

    result = policy.evaluate(
        message="Hola",
        state=state,
    )

    assert result.action == ActivationAction.CONTINUE
    assert result.should_process_message is True
    assert result.message is None
    assert result.should_respond is False


@pytest.mark.parametrize(
    "message",
    [
        "Tarot",
        "tarot",
        "TAROT",
        "  Tarot  ",
    ],
)
def test_exact_phrase_activates_for_exact_normalized_match(
    message: str,
) -> None:
    policy = build_policy()
    state = ActivationState(active=False)

    result = policy.evaluate(
        message=message,
        state=state,
    )

    assert result.action == ActivationAction.ACTIVATE
    assert result.should_process_message is False
    assert result.message == "Asistente activado."
    assert result.should_respond is False


@pytest.mark.parametrize(
    "message",
    [
        "Hola Tarot",
        "Quiero tarot",
        "¿Cómo va tu negocio del tarot?",
        "tarot por favor",
        "",
        "   ",
    ],
)
def test_exact_phrase_does_not_activate_partial_matches(
    message: str,
) -> None:
    policy = build_policy()
    state = ActivationState(active=False)

    result = policy.evaluate(
        message=message,
        state=state,
    )

    assert result.action == ActivationAction.PROMPT
    assert result.should_process_message is False
    assert result.should_respond is True
    assert result.message is not None


def test_active_state_continues_without_rechecking_phrase() -> None:
    policy = build_policy()
    state = ActivationState(active=True)

    result = policy.evaluate(
        message="Cualquier mensaje",
        state=state,
    )

    assert result.action == ActivationAction.CONTINUE
    assert result.should_process_message is True
    assert result.should_respond is False


def test_policy_is_silent_after_prompt_without_cooldown() -> None:
    policy = build_policy()
    state = ActivationState(
        active=False,
        prompt_sent_at=datetime.now(),
    )

    result = policy.evaluate(
        message="Hola",
        state=state,
    )

    assert result.action == ActivationAction.SILENT
    assert result.should_process_message is False
    assert result.should_respond is False


def test_policy_repeats_prompt_after_cooldown() -> None:
    policy = build_policy(
        prompt_cooldown=timedelta(hours=12),
    )
    state = ActivationState(
        active=False,
        prompt_sent_at=datetime.now() - timedelta(hours=13),
    )

    result = policy.evaluate(
        message="Hola",
        state=state,
    )

    assert result.action == ActivationAction.PROMPT
    assert result.should_respond is True


def test_policy_is_silent_during_cooldown() -> None:
    policy = build_policy(
        prompt_cooldown=timedelta(hours=12),
    )
    state = ActivationState(
        active=False,
        prompt_sent_at=datetime.now() - timedelta(hours=2),
    )

    result = policy.evaluate(
        message="Hola",
        state=state,
    )

    assert result.action == ActivationAction.SILENT
    assert result.should_respond is False


def test_policy_rejects_empty_phrases() -> None:
    with pytest.raises(ValueError):
        ExactPhrasePolicy(
            phrases=["", "   "],
            prompt_message="Escribe TAROT.",
            activated_message="Asistente activado.",
        )


def test_policy_rejects_empty_prompt_message() -> None:
    with pytest.raises(ValueError):
        ExactPhrasePolicy(
            phrases=["Tarot"],
            prompt_message="   ",
            activated_message="Asistente activado.",
        )


def test_policy_rejects_negative_cooldown() -> None:
    with pytest.raises(ValueError):
        ExactPhrasePolicy(
            phrases=["Tarot"],
            prompt_message="Escribe TAROT.",
            prompt_cooldown=timedelta(seconds=-1),
            activated_message="Asistente activado.",
        )