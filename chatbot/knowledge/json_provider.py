from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from chatbot.knowledge.provider import KnowledgeProvider


class JsonKnowledgeProvider(KnowledgeProvider):
    """
    Load FlowForge knowledge from a directory of JSON files.

    Each JSON filename becomes a knowledge section.

    Example:

        knowledge/tarot_alvin/company.json
        knowledge/tarot_alvin/faq.json

    becomes:

        {
            "company": {...},
            "faq": {...},
        }
    """

    def load(
        self,
        knowledge_path: str | Path,
    ) -> dict[str, Any]:
        path = Path(knowledge_path)

        self._validate_path(path)

        knowledge: dict[str, Any] = {}

        for json_file in sorted(path.glob("*.json")):
            section_name = json_file.stem

            knowledge[section_name] = self._load_file(
                json_file
            )

        return knowledge

    @staticmethod
    def _validate_path(
        path: Path,
    ) -> None:
        """
        Ensure the supplied knowledge path exists and is a directory.
        """

        if not path.exists():
            raise FileNotFoundError(
                f"Knowledge path does not exist: {path}"
            )

        if not path.is_dir():
            raise NotADirectoryError(
                f"Knowledge path is not a directory: {path}"
            )

    @staticmethod
    def _load_file(
        file_path: Path,
    ) -> Any:
        """
        Read and decode one JSON file.

        Empty files are temporarily interpreted as empty dictionaries.
        This allows a client knowledge structure to be created
        incrementally without breaking the complete provider.
        """

        content = file_path.read_text(
            encoding="utf-8",
        ).strip()

        if not content:
            return {}

        try:
            return json.loads(content)
        except json.JSONDecodeError as error:
            raise ValueError(
                f"Invalid JSON knowledge file: {file_path}"
            ) from error