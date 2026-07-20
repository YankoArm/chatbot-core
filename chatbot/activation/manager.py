from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta, timezone

from chatbot.activation.action import ActivationAction
from chatbot.activation.policy import ActivationPolicy
from chatbot.activation.result import ActivationResult
from chatbot.activation.state import ActivationState
from chatbot.responses import Response
from chatbot.activation.decision import ActivationDecision


Clock = Callable[[], datetime]


class ActivationManager:
    """
    Coordinates an ActivationPolicy with its mutable runtime state.

    Policies decide what should happen.
    ActivationManager applies that decision to ActivationState.
    """

    def __init__(
        self,
        policy: ActivationPolicy,
        session_timeout: timedelta | None = None,
        clock: Clock | None = None,
    ) -> None:
        if (
            session_timeout is not None
            and session_timeout.total_seconds() <= 0
        ):
            raise ValueError("session_timeout must be greater than zero.")

        self._policy = policy
        self._session_timeout = session_timeout
        self._clock = clock or self._utc_now

    def evaluate(
        self,
        message: str,
        state: ActivationState,
    ) -> ActivationResult:
        now = self._clock()
        self._expire_if_required(state, now)

        result = self._policy.evaluate(
            message=message,
            state=state,
        )

        self._apply_result(
            result=result,
            state=state,
            now=now,
        )

        return result

    def reset(self, state: ActivationState) -> None:
        state.reset()

    def _apply_result(
        self,
        result: ActivationResult,
        state: ActivationState,
        now: datetime,
    ) -> None:
        if result.action == ActivationAction.ACTIVATE:
            state.activate(
                activated_at=now,
                expires_at=self._calculate_expiration(now),
            )
            return

        if result.action == ActivationAction.CONTINUE:
            if state.active:
                state.refresh(
                    expires_at=self._calculate_expiration(now),
                )
            return

        if result.action == ActivationAction.PROMPT:
            state.register_prompt(now)

    def _expire_if_required(
        self,
        state: ActivationState,
        now: datetime,
    ) -> None:
        if not state.active:
            return

        if state.expires_at is None:
            return

        if now >= state.expires_at:
            state.deactivate()

    def _calculate_expiration(
        self,
        now: datetime,
    ) -> datetime | None:
        if self._session_timeout is None:
            return None

        return now + self._session_timeout

    @staticmethod
    def _utc_now() -> datetime:
        return datetime.now(timezone.utc)
    
    def handle(
        self,
        message: str,
        state: ActivationState,
    ) -> ActivationDecision:
        result = self.evaluate(message, state)

        if result.action in {
            ActivationAction.ACTIVATE,
            ActivationAction.CONTINUE,
        }:
            return ActivationDecision(
                continue_processing=True,
            )

        return ActivationDecision(
            continue_processing=False,
            response=Response(
                text=result.message or "",
            ),
        )