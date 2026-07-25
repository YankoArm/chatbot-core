from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class KnowledgeProvider(ABC):
    """
    Base interface for every FlowForge knowledge provider.

    A provider is responsible for loading raw knowledge data from a
    specific source, such as JSON files, a database or an external API.
    """

    @abstractmethod
    def load(
        self,
        knowledge_path: str | Path,
    ) -> dict[str, Any]:
        """
        Load all available knowledge from the given path.

        The returned dictionary must use section names as keys.

        Example:

        {
            "company": {...},
            "services": {...},
            "faq": {...},
        }
        """
        raise NotImplementedError