from __future__ import annotations

from pathlib import Path

from chatbot.instances import Instance
from chatbot.knowledge.json_provider import (
    JsonKnowledgeProvider,
)
from chatbot.knowledge.loader import KnowledgeLoader
from chatbot.knowledge.service import KnowledgeService


class KnowledgeServiceFactory:
    """
    Build knowledge services for FlowForge instances.

    An instance may provide an explicit knowledge path. When no explicit path
    is configured, the conventional ``knowledge/<instance_id>`` directory is
    used automatically.
    """

    def __init__(
        self,
        knowledge_root: str | Path = "knowledge",
    ) -> None:
        self._knowledge_root = Path(
            knowledge_root
        )

        self._provider = JsonKnowledgeProvider()

        self._loader = KnowledgeLoader(
            self._provider
        )

    def build(
        self,
        instance: Instance,
    ) -> KnowledgeService:
        """
        Build the KnowledgeService associated with an instance.

        Explicit instance knowledge paths take precedence over the default
        directory convention.
        """

        knowledge_path = self.resolve_path(
            instance
        )

        return self.build_from_path(
            knowledge_path
        )

    def build_from_path(
        self,
        knowledge_path: str | Path,
    ) -> KnowledgeService:
        """
        Build a KnowledgeService from an explicit knowledge path.
        """

        normalized_path = Path(
            knowledge_path
        )

        return KnowledgeService(
            loader=self._loader,
            knowledge_path=normalized_path,
        )

    def resolve_path(
        self,
        instance: Instance,
    ) -> Path:
        """
        Resolve the knowledge directory configured for an instance.
        """

        explicit_path = getattr(
            instance,
            "knowledge_path",
            None,
        )

        if explicit_path:
            return Path(
                explicit_path
            )

        return self.knowledge_path_for(
            instance.id
        )

    def knowledge_path_for(
        self,
        instance_id: str,
    ) -> Path:
        """
        Return the conventional knowledge directory for an instance.
        """

        normalized_instance_id = (
            instance_id.strip()
        )

        if not normalized_instance_id:
            raise ValueError(
                "Instance id cannot be empty."
            )

        return (
            self._knowledge_root
            / normalized_instance_id
        )