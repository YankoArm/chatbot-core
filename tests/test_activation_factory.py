from __future__ import annotations

import pytest

from chatbot.activation import (
    ActivationConfig,
    ActivationFactory,
    ActivationManager,
    ActivationState,
)


def test_create_always_active_manager() -> None:
    factory = ActivationFactory()

    manager = factory.create(
        ActivationConfig(
            type="always_active",
        )
    )

    state = ActivationState()

    decision = manager.handle(
        message="Hola",
        state=state,
    )

    assert isinstance(manager, ActivationManager)
    assert decision.continue_processing is True
    assert decision.response is None


def test_create_exact_phrase_manager_blocks_inactive_session() -> None:
    factory = ActivationFactory()

    manager = factory.create(
        ActivationConfig(
            type="exact_phrase",
            phrases=["Tarot", "Consulta"],
            prompt_message="Escribe TAROT para comenzar.",
            prompt_cooldown=90,
            session_timeout=1800,
        )
    )

    state = ActivationState()

    decision = manager.handle(
        message="Hola",
        state=state,
    )

    assert isinstance(manager, ActivationManager)
    assert decision.continue_processing is False
    assert decision.response is not None
    assert decision.response.text == "Escribe TAROT para comenzar."


def test_exact_phrase_configuration_allows_activation() -> None:
    factory = ActivationFactory()

    manager = factory.create(
        ActivationConfig(
            type="exact_phrase",
            phrases=["Tarot"],
            prompt_message="Activa el asistente.",
            prompt_cooldown=45,
        )
    )

    state = ActivationState()

    decision = manager.handle(
        message="Tarot",
        state=state,
    )

    assert decision.continue_processing is False
    assert decision.response is not None
    assert decision.response.text == "Assistant activated."
    assert state.active is True


def test_session_timeout_zero_raises_value_error() -> None:
    factory = ActivationFactory()

    with pytest.raises(
        ValueError,
        match="session_timeout must be greater than zero",
    ):
        factory.create(
            ActivationConfig(
                session_timeout=0,
            )
        )


def test_unknown_activation_type_raises_value_error() -> None:
    factory = ActivationFactory()

    config = ActivationConfig(
        type="unknown_policy",
    )

    with pytest.raises(
        ValueError,
        match="Unknown activation type: unknown_policy",
    ):
        factory.create(config)