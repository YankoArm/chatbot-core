from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from chatbot.conversation import ConversationStore
from chatbot.responses import Response


@dataclass(slots=True)
class FlowForgeApplication:
    """
    Runtime representation of a configured FlowForge Instance.
    """

    instance: Any
    orchestrator: Any
    capability_manager: Any
    conversation_store: ConversationStore
    connector_manager: Any | None = None

    def chat(self, session_id: str, message: str) -> Response:
        context = self.conversation_store.get(session_id)
        return self.orchestrator.process(context, message)

    def reset_session(self, session_id: str) -> None:
        self.conversation_store.reset(session_id)

    def reload(self) -> None:
        raise NotImplementedError

    def info(self) -> dict:
        return {
            "instance": self.instance,
            "capabilities": [
                capability.name
                for capability in self.capability_manager.all()
            ],
            "active_sessions": self.conversation_store.count(),
        }