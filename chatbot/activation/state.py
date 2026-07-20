from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class ActivationState:
    """
    Runtime activation state associated with a conversation session.
    """

    active: bool = False
    activated_at: datetime | None = None
    expires_at: datetime | None = None
    prompt_sent_at: datetime | None = None

    def activate(
        self,
        *,
        activated_at: datetime,
        expires_at: datetime | None = None,
    ) -> None:
        self.active = True
        self.activated_at = activated_at
        self.expires_at = expires_at
        self.prompt_sent_at = None

    def refresh(
        self,
        *,
        expires_at: datetime | None,
    ) -> None:
        if self.active:
            self.expires_at = expires_at

    def register_prompt(self, sent_at: datetime) -> None:
        self.prompt_sent_at = sent_at

    def deactivate(self) -> None:
        self.active = False
        self.activated_at = None
        self.expires_at = None

    def reset(self) -> None:
        self.active = False
        self.activated_at = None
        self.expires_at = None
        self.prompt_sent_at = None