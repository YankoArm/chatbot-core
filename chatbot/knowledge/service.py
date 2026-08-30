from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from chatbot.knowledge.loader import KnowledgeLoader


class KnowledgeService:
    """
    Provide high-level access to loaded FlowForge knowledge.

    File-based knowledge can be extended or overridden with
    instance-specific knowledge without modifying the loader cache.
    """

    def __init__(
        self,
        loader: KnowledgeLoader,
        knowledge_path: str | Path,
        *,
        knowledge_overrides: (
            dict[str, Any] | None
        ) = None,
        allow_missing_path: bool = False,
    ) -> None:
        self._loader = loader
        self._knowledge_path = knowledge_path
        self._knowledge_overrides = deepcopy(
            knowledge_overrides or {}
        )
        self._allow_missing_path = (
            allow_missing_path
        )
        self._knowledge: (
            dict[str, Any] | None
        ) = None

    def load(
        self,
        *,
        force_reload: bool = False,
    ) -> dict[str, Any]:
        """
        Load base knowledge and apply instance-specific overrides.
        """

        try:
            base_knowledge = self._loader.load(
                self._knowledge_path,
                force_reload=force_reload,
            )
        except FileNotFoundError:
            if not self._allow_missing_path:
                raise

            base_knowledge = {}

        self._knowledge = self._deep_merge(
            base_knowledge,
            self._knowledge_overrides,
        )

        return self._knowledge

    def get_section(
        self,
        section: str,
        default: Any = None,
    ) -> Any:
        """
        Return one complete knowledge section.
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
        """

        section_data = self.get_section(
            section,
            {},
        )

        if not isinstance(
            section_data,
            dict,
        ):
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
        Reload base knowledge and reapply overrides.
        """

        return self.load(
            force_reload=True,
        )

    def clear(
        self,
    ) -> None:
        """
        Clear cached base and merged knowledge.
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

    @classmethod
    def _deep_merge(
        cls,
        base: dict[str, Any],
        overrides: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Merge nested dictionaries without mutating either source.
        """

        merged = deepcopy(
            base
        )

        for key, override_value in overrides.items():
            base_value = merged.get(
                key
            )

            if (
                isinstance(base_value, dict)
                and isinstance(
                    override_value,
                    dict,
                )
            ):
                merged[key] = cls._deep_merge(
                    base_value,
                    override_value,
                )
                continue

            merged[key] = deepcopy(
                override_value
            )

        return merged