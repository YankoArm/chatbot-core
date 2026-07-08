from __future__ import annotations

from chatbot.conversation.context import ConversationContext


class ConversationStore:
    """
    In-memory storage for ConversationContext objects.

    This store manages conversation sessions without leaking storage
    responsibilities into the Application layer.
    """

    def __init__(self):
        self._contexts: dict[str, ConversationContext] = {}

    def get(self, session_id: str) -> ConversationContext:
        if session_id not in self._contexts:
            self._contexts[session_id] = ConversationContext(session_id=session_id)

        return self._contexts[session_id]

    def reset(self, session_id: str) -> None:
        if session_id in self._contexts:
            self._contexts[session_id].reset()

    def delete(self, session_id: str) -> None:
        self._contexts.pop(session_id, None)

    def count(self) -> int:
        return len(self._contexts)