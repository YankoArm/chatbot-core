from __future__ import annotations

from datetime import timedelta

from chatbot.activation.always_active import AlwaysActivePolicy
from chatbot.activation.config import ActivationConfig
from chatbot.activation.exact_phrase import ExactPhrasePolicy
from chatbot.activation.manager import ActivationManager


class ActivationFactory:
    """
    Factory responsible for creating activation managers from
    declarative activation configuration.
    """

    def create(
        self,
        config: ActivationConfig,
    ) -> ActivationManager:

        if config.type == "always_active":
            policy = AlwaysActivePolicy()

        elif config.type == "exact_phrase":
            policy = ExactPhrasePolicy(
                phrases=config.phrases,
                prompt_message=config.prompt_message,
                activated_message=config.activated_message,
                prompt_cooldown=timedelta(
                    seconds=config.prompt_cooldown,
                ),
            )

        else:
            raise ValueError(
                f"Unknown activation type: {config.type}"
            )

        timeout = (
            timedelta(seconds=config.session_timeout)
            if config.session_timeout is not None
            else None
        )

        return ActivationManager(
            policy=policy,
            session_timeout=timeout,
        )