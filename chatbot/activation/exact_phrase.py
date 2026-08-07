from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timedelta

from chatbot.activation.action import ActivationAction
from chatbot.activation.policy import ActivationPolicy
from chatbot.activation.result import ActivationResult
from chatbot.activation.state import ActivationState


class ExactPhrasePolicy(ActivationPolicy):
    """
    Activate the assistant only when the complete message matches
    one of the configured phrases.

    Comparison ignores surrounding whitespace and differences
    between uppercase and lowercase characters.
    """

    def __init__(
        self,
        phrases: Iterable[str],
        prompt_message: str,
        activated_message: str,
        prompt_cooldown: timedelta | None = None,
    ) -> None:
        normalized_phrases = {
            self._normalize(phrase)
            for phrase in phrases
            if self._normalize(phrase)
        }

        if not normalized_phrases:
            raise ValueError(
                "ExactPhrasePolicy requires at least one non-empty phrase."
            )

        if not prompt_message.strip():
            raise ValueError(
                "prompt_message cannot be empty."
            )

        if not activated_message.strip():
            raise ValueError(
                "activated_message cannot be empty."
            )

        if (
            prompt_cooldown is not None
            and prompt_cooldown.total_seconds() < 0
        ):
            raise ValueError(
                "prompt_cooldown cannot be negative."
            )

        self._phrases = frozenset(
            normalized_phrases
        )
        self._prompt_message = (
            prompt_message
        )
        self._activated_message = (
            activated_message
        )
        self._prompt_cooldown = (
            prompt_cooldown
        )

    def evaluate(
        self,
        message: str,
        state: ActivationState,
    ) -> ActivationResult:
        if state.active:
            return ActivationResult(
                action=ActivationAction.CONTINUE,
            )

        normalized_message = self._normalize(
            message
        )

        if normalized_message in self._phrases:
            return ActivationResult(
                action=ActivationAction.ACTIVATE,
                message=self._activated_message,
            )

        if self._should_send_prompt(state):
            return ActivationResult(
                action=ActivationAction.PROMPT,
                message=self._prompt_message,
            )

        return ActivationResult(
            action=ActivationAction.SILENT,
        )

    def _should_send_prompt(
        self,
        state: ActivationState,
    ) -> bool:
        if state.prompt_sent_at is None:
            return True

        if self._prompt_cooldown is None:
            return False

        now = datetime.now(
            tz=state.prompt_sent_at.tzinfo
        )

        return (
            now - state.prompt_sent_at
            >= self._prompt_cooldown
        )

    @staticmethod
    def _normalize(
        value: str,
    ) -> str:
        return value.strip().casefold()