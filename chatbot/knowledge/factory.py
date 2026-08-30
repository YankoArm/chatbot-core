from __future__ import annotations

from pathlib import Path
from typing import Any

from chatbot.instances import Instance
from chatbot.knowledge.json_provider import (
    JsonKnowledgeProvider,
)
from chatbot.knowledge.loader import KnowledgeLoader
from chatbot.knowledge.service import KnowledgeService


class KnowledgeServiceFactory:
    """
    Build knowledge services for FlowForge instances.

    Instance knowledge stored in settings is merged over optional
    file-based knowledge.
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
        """

        knowledge_path = self.resolve_path(
            instance
        )
        knowledge_overrides = (
            self._get_instance_knowledge(
                instance
            )
        )

        return KnowledgeService(
            loader=self._loader,
            knowledge_path=knowledge_path,
            knowledge_overrides=(
                knowledge_overrides
            ),
            allow_missing_path=bool(
                knowledge_overrides
            ),
        )

    def build_from_path(
        self,
        knowledge_path: str | Path,
    ) -> KnowledgeService:
        """
        Build a file-only service from an explicit path.
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

    @staticmethod
    def _get_instance_knowledge(
        instance: Instance,
    ) -> dict[str, Any]:
        """
        Return validated knowledge stored in instance settings.
        """

        knowledge = instance.settings.get(
            "knowledge",
            {},
        )

        if not isinstance(
            knowledge,
            dict,
        ):
            raise ValueError(
                "Instance knowledge settings "
                "must be a dictionary."
            )

        return knowledge