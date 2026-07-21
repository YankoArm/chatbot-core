from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from chatbot.activation import ActivationState
from chatbot.language import Language

@dataclass(slots=True)
class ConversationContext:
    """
    Runtime memory of an ongoing conversation.

    ConversationContext preserves the user's objective, active capability,
    temporary variables and delegation state across messages.
    """

    session_id: str
    user_id: str | None = None
    objective: str | None = None
    active_capability: str | None = None
    language: Language | None = None
    previous_capabilities: list[str] = field(default_factory=list)
    variables: dict[str, Any] = field(default_factory=dict)
    pending_actions: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    activation_state: ActivationState = field(
        default_factory=ActivationState
    )

    def set_active_capability(self, capability_name: str) -> None:
        if self.active_capability:
            self.previous_capabilities.append(self.active_capability)

        self.active_capability = capability_name

    def set_variable(self, key: str, value: Any) -> None:
        self.variables[key] = value

    def get_variable(self, key: str, default: Any = None) -> Any:
        return self.variables.get(key, default)

    def add_pending_action(self, action: dict[str, Any]) -> None:
        self.pending_actions.append(action)

    def clear_pending_actions(self) -> None:
        self.pending_actions.clear()

    def reset(self) -> None:
        self.objective = None
        self.active_capability = None
        self.previous_capabilities.clear()
        self.variables.clear()
        self.pending_actions.clear()
        self.metadata.clear()
        self.activation_state.reset()