from datetime import datetime, timedelta, timezone

from chatbot.activation import (
    ActivationDecision,
    ActivationManager,
    ActivationState,
    ExactPhrasePolicy,
)


PROMPT_MESSAGE = (
    "Este número también se utiliza de forma personal. "
    "Para iniciar el asistente, escribe únicamente TAROT."
)


class MutableClock:
    def __init__(self, current: datetime) -> None:
        self.current = current

    def __call__(self) -> datetime:
        return self.current

    def advance(self, delta: timedelta) -> None:
        self.current += delta


def build_manager(
    clock: MutableClock,
    session_timeout: timedelta | None = None,
) -> ActivationManager:
    policy = ExactPhrasePolicy(
        phrases=["Tarot"],
        prompt_message=PROMPT_MESSAGE,
    )

    return ActivationManager(
        policy=policy,
        session_timeout=session_timeout,
        clock=clock,
    )


def test_handle_returns_continue_for_activation() -> None:
    clock = MutableClock(
        datetime(2026, 7, 20, 20, 0, tzinfo=timezone.utc)
    )

    manager = build_manager(clock)
    state = ActivationState()

    decision = manager.handle("Tarot", state)

    assert isinstance(decision, ActivationDecision)
    assert decision.continue_processing is True
    assert decision.response is None


def test_handle_returns_continue_for_active_session() -> None:
    clock = MutableClock(
        datetime(2026, 7, 20, 20, 0, tzinfo=timezone.utc)
    )

    manager = build_manager(clock)
    state = ActivationState()

    manager.handle("Tarot", state)

    clock.advance(timedelta(minutes=5))

    decision = manager.handle(
        "Quiero una lectura",
        state,
    )

    assert decision.continue_processing is True
    assert decision.response is None


def test_handle_returns_prompt_response() -> None:
    clock = MutableClock(
        datetime(2026, 7, 20, 20, 0, tzinfo=timezone.utc)
    )

    manager = build_manager(clock)
    state = ActivationState()

    decision = manager.handle(
        "Hola",
        state,
    )

    assert decision.continue_processing is False
    assert decision.response is not None
    assert decision.response.text == PROMPT_MESSAGE


def test_handle_returns_silent_response() -> None:
    clock = MutableClock(
        datetime(2026, 7, 20, 20, 0, tzinfo=timezone.utc)
    )

    manager = build_manager(clock)
    state = ActivationState()

    manager.handle("Hola", state)

    clock.advance(timedelta(seconds=5))

    decision = manager.handle(
        "Hola otra vez",
        state,
    )

    assert decision.continue_processing is False
    assert decision.response is not None
    assert decision.response.text == ""


def test_handle_allows_reactivation_after_timeout() -> None:
    clock = MutableClock(
        datetime(2026, 7, 20, 20, 0, tzinfo=timezone.utc)
    )

    manager = build_manager(
        clock,
        session_timeout=timedelta(minutes=30),
    )

    state = ActivationState()

    manager.handle("Tarot", state)

    clock.advance(timedelta(minutes=31))

    decision = manager.handle(
        "Tarot",
        state,
    )

    assert decision.continue_processing is True
    assert decision.response is None
    assert state.active is True