from datetime import datetime, timedelta, timezone

import pytest

from chatbot.activation import (
    ActivationAction,
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


def test_manager_activates_state() -> None:
    now = datetime(2026, 7, 20, 20, 0, tzinfo=timezone.utc)
    clock = MutableClock(now)
    manager = build_manager(clock)
    state = ActivationState()

    result = manager.evaluate("Tarot", state)

    assert result.action == ActivationAction.ACTIVATE
    assert state.active is True
    assert state.activated_at == now
    assert state.expires_at is None


def test_manager_sets_session_expiration() -> None:
    now = datetime(2026, 7, 20, 20, 0, tzinfo=timezone.utc)
    clock = MutableClock(now)
    timeout = timedelta(minutes=30)
    manager = build_manager(clock, session_timeout=timeout)
    state = ActivationState()

    manager.evaluate("Tarot", state)

    assert state.expires_at == now + timeout


def test_manager_registers_prompt_time() -> None:
    now = datetime(2026, 7, 20, 20, 0, tzinfo=timezone.utc)
    clock = MutableClock(now)
    manager = build_manager(clock)
    state = ActivationState()

    result = manager.evaluate("Hola", state)

    assert result.action == ActivationAction.PROMPT
    assert state.active is False
    assert state.prompt_sent_at == now


def test_manager_refreshes_active_session_expiration() -> None:
    now = datetime(2026, 7, 20, 20, 0, tzinfo=timezone.utc)
    clock = MutableClock(now)
    timeout = timedelta(minutes=30)
    manager = build_manager(clock, session_timeout=timeout)
    state = ActivationState()

    manager.evaluate("Tarot", state)

    clock.advance(timedelta(minutes=20))
    manager.evaluate("Quiero hacer una consulta", state)

    assert state.expires_at == clock.current + timeout


def test_manager_expires_inactive_session() -> None:
    now = datetime(2026, 7, 20, 20, 0, tzinfo=timezone.utc)
    clock = MutableClock(now)
    manager = build_manager(
        clock,
        session_timeout=timedelta(minutes=30),
    )
    state = ActivationState()

    manager.evaluate("Tarot", state)

    clock.advance(timedelta(minutes=31))
    result = manager.evaluate("Quiero una consulta", state)

    assert state.active is False
    assert result.action == ActivationAction.PROMPT
    assert state.activated_at is None
    assert state.expires_at is None


def test_manager_can_reactivate_expired_session() -> None:
    now = datetime(2026, 7, 20, 20, 0, tzinfo=timezone.utc)
    clock = MutableClock(now)
    timeout = timedelta(minutes=30)
    manager = build_manager(clock, session_timeout=timeout)
    state = ActivationState()

    manager.evaluate("Tarot", state)

    clock.advance(timedelta(minutes=31))
    result = manager.evaluate("Tarot", state)

    assert result.action == ActivationAction.ACTIVATE
    assert state.active is True
    assert state.activated_at == clock.current
    assert state.expires_at == clock.current + timeout


def test_manager_reset_clears_activation_state() -> None:
    now = datetime(2026, 7, 20, 20, 0, tzinfo=timezone.utc)
    clock = MutableClock(now)
    manager = build_manager(clock)
    state = ActivationState()

    manager.evaluate("Tarot", state)
    manager.reset(state)

    assert state == ActivationState()


def test_manager_rejects_zero_session_timeout() -> None:
    now = datetime(2026, 7, 20, 20, 0, tzinfo=timezone.utc)
    clock = MutableClock(now)

    with pytest.raises(ValueError):
        build_manager(
            clock,
            session_timeout=timedelta(seconds=0),
        )


def test_manager_rejects_negative_session_timeout() -> None:
    now = datetime(2026, 7, 20, 20, 0, tzinfo=timezone.utc)
    clock = MutableClock(now)

    with pytest.raises(ValueError):
        build_manager(
            clock,
            session_timeout=timedelta(seconds=-1),
        )