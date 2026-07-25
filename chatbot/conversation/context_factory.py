from __future__ import annotations

from chatbot.conversation.context import (
    ConversationContext,
)
from chatbot.instances import Instance
from chatbot.knowledge import (
    KnowledgeServiceFactory,
)


class ConversationContextFactory:
    """
    Build conversation contexts for FlowForge instances.

    Each context receives the KnowledgeService resolved from the active
    instance configuration.
    """

    def __init__(
        self,
        knowledge_service_factory: KnowledgeServiceFactory,
    ) -> None:
        self._knowledge_service_factory = (
            knowledge_service_factory
        )

    def build(
        self,
        *,
        instance: Instance,
        session_id: str,
        user_id: str,
    ) -> ConversationContext:
        """
        Build a conversation context for an instance.
        """

        normalized_session_id = session_id.strip()
        normalized_user_id = user_id.strip()

        if not normalized_session_id:
            raise ValueError(
                "Session ID cannot be empty."
            )

        if not normalized_user_id:
            raise ValueError(
                "User ID cannot be empty."
            )

        knowledge_service = (
            self._knowledge_service_factory.build(
                instance
            )
        )

        return ConversationContext(
            session_id=normalized_session_id,
            user_id=normalized_user_id,
            knowledge_service=knowledge_service,
        )