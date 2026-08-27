from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from chatbot.activation import ActivationState
from chatbot.booking import (
    BookingManagementState,
    BookingState,
)
from chatbot.language import Language


@dataclass(slots=True)
class ConversationContext:
    """
    Runtime memory of an ongoing conversation.

    ConversationContext preserves the user's language, objective, active
    capability, booking state, booking-management state, temporary
    variables and delegation state across messages belonging to the same
    session.
    """

    session_id: str
    user_id: str | None = None

    objective: str | None = None
    active_capability: str | None = None
    language: Language | None = None
    booking: BookingState | None = None
    booking_management: BookingManagementState | None = None

    knowledge_service: Any | None = None

    previous_capabilities: list[str] = field(
        default_factory=list
    )
    variables: dict[str, Any] = field(
        default_factory=dict
    )
    pending_actions: list[dict[str, Any]] = field(
        default_factory=list
    )
    metadata: dict[str, Any] = field(
        default_factory=dict
    )
    activation_state: ActivationState = field(
        default_factory=ActivationState
    )

    @property
    def has_language(self) -> bool:
        """
        Return whether the conversation already has a selected language.
        """

        return self.language is not None

    def set_language(
        self,
        language: Language,
    ) -> None:
        """
        Set the language used throughout the current conversation.
        """

        self.language = language
        self.metadata["language"] = language.value

    def set_active_capability(
        self,
        capability_name: str,
    ) -> None:
        """
        Activate a capability and preserve the previous capability in history.

        Re-selecting the currently active capability does not create duplicate
        history entries.
        """

        if capability_name == self.active_capability:
            return

        if self.active_capability is not None:
            self.previous_capabilities.append(
                self.active_capability
            )

        self.active_capability = capability_name

    def clear_active_capability(self) -> None:
        """
        Clear the currently active capability.
        """

        self.active_capability = None

    def set_variable(
        self,
        key: str,
        value: Any,
    ) -> None:
        self.variables[key] = value

    def get_variable(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        return self.variables.get(key, default)

    def remove_variable(
        self,
        key: str,
    ) -> Any:
        """
        Remove and return a conversation variable.

        Return None when the variable does not exist.
        """

        return self.variables.pop(key, None)

    def add_pending_action(
        self,
        action: dict[str, Any],
    ) -> None:
        self.pending_actions.append(action)

    def clear_pending_actions(self) -> None:
        self.pending_actions.clear()

    def reset_booking(self) -> None:
        """
        Remove the current new-booking state.
        """

        self.booking = None

    def reset_booking_management(self) -> None:
        """
        Remove the current existing-booking management state.
        """

        self.booking_management = None

    def reset(self) -> None:
        """
        Restore the complete conversation context to its initial state.

        The session and user identifiers are preserved, while all transient
        conversational data is removed.
        """

        self.objective = None
        self.active_capability = None
        self.language = None
        self.booking = None
        self.booking_management = None

        self.previous_capabilities.clear()
        self.variables.clear()
        self.pending_actions.clear()
        self.metadata.clear()

        self.activation_state.reset()