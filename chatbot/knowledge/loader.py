from __future__ import annotations

from pathlib import Path
from typing import Any

from chatbot.knowledge.provider import KnowledgeProvider


class KnowledgeLoader:
    """
    Load and cache knowledge for FlowForge instances.

    Knowledge is cached by its normalized path so repeated requests do not
    reload the same files from disk.
    """

    def __init__(
        self,
        provider: KnowledgeProvider,
    ) -> None:
        self._provider = provider
        self._cache: dict[str, dict[str, Any]] = {}

    def load(
        self,
        knowledge_path: str | Path,
        *,
        force_reload: bool = False,
    ) -> dict[str, Any]:
        """
        Load knowledge from the configured provider.

        When force_reload is False, previously loaded knowledge is returned
        from the in-memory cache.
        """

        cache_key = self._build_cache_key(
            knowledge_path
        )

        if (
            not force_reload
            and cache_key in self._cache
        ):
            return self._cache[cache_key]

        knowledge = self._provider.load(
            knowledge_path
        )

        self._cache[cache_key] = knowledge

        return knowledge

    def clear(
        self,
        knowledge_path: str | Path | None = None,
    ) -> None:
        """
        Clear one cached knowledge entry or the complete cache.

        When knowledge_path is None, every cached entry is removed.
        """

        if knowledge_path is None:
            self._cache.clear()
            return

        cache_key = self._build_cache_key(
            knowledge_path
        )

        self._cache.pop(
            cache_key,
            None,
        )

    def is_cached(
        self,
        knowledge_path: str | Path,
    ) -> bool:
        """
        Return True when knowledge for the supplied path is cached.
        """

        cache_key = self._build_cache_key(
            knowledge_path
        )

        return cache_key in self._cache

    @staticmethod
    def _build_cache_key(
        knowledge_path: str | Path,
    ) -> str:
        """
        Normalize a knowledge path for consistent cache lookups.
        """

        return str(
            Path(knowledge_path).resolve()
        )