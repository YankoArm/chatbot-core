from __future__ import annotations

from pathlib import Path
from typing import Any

from chatbot.knowledge.loader import KnowledgeLoader


class KnowledgeService:
    """
    Provide high-level access to loaded FlowForge knowledge.

    Capabilities should use this service instead of reading files or
    interacting directly with providers.
    """

    def __init__(
        self,
        loader: KnowledgeLoader,
        knowledge_path: str | Path,
    ) -> None:
        self._loader = loader
        self._knowledge_path = knowledge_path
        self._knowledge: dict[str, Any] | None = None

    def load(
        self,
        *,
        force_reload: bool = False,
    ) -> dict[str, Any]:
        """
        Load and retain the knowledge associated with this service.
        """

        self._knowledge = self._loader.load(
            self._knowledge_path,
            force_reload=force_reload,
        )

        return self._knowledge

    def get_section(
        self,
        section: str,
        default: Any = None,
    ) -> Any:
        """
        Return one complete knowledge section.

        Example:

            service.get_section("faq")
        """

        knowledge = self._ensure_loaded()

        return knowledge.get(
            section,
            default,
        )

    def get(
        self,
        section: str,
        key: str,
        default: Any = None,
    ) -> Any:
        """
        Return one value from a dictionary-based section.

        Example:

            service.get("company", "name")
        """

        section_data = self.get_section(
            section,
            {},
        )

        if not isinstance(section_data, dict):
            return default

        return section_data.get(
            key,
            default,
        )

    def has_section(
        self,
        section: str,
    ) -> bool:
        """
        Return True when a knowledge section exists.
        """

        knowledge = self._ensure_loaded()

        return section in knowledge

    def reload(
        self,
    ) -> dict[str, Any]:
        """
        Reload knowledge from the underlying provider.
        """

        return self.load(
            force_reload=True,
        )

    def clear(
        self,
    ) -> None:
        """
        Clear cached knowledge for this service.
        """

        self._loader.clear(
            self._knowledge_path
        )

        self._knowledge = None

    def _ensure_loaded(
        self,
    ) -> dict[str, Any]:
        """
        Load knowledge lazily on first access.
        """

        if self._knowledge is None:
            return self.load()

        return self._knowledge