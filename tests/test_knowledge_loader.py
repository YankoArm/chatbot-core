from __future__ import annotations

from pathlib import Path
from typing import Any

from chatbot.knowledge import (
    KnowledgeLoader,
    KnowledgeProvider,
)


class FakeKnowledgeProvider(KnowledgeProvider):
    def __init__(self) -> None:
        self.load_calls: list[str] = []

    def load(
        self,
        knowledge_path: str | Path,
    ) -> dict[str, Any]:
        self.load_calls.append(
            str(knowledge_path)
        )

        return {
            "company": {
                "name": "Tarot Alvin",
            },
        }


def test_knowledge_loader_loads_from_provider(
    tmp_path,
):
    provider = FakeKnowledgeProvider()
    loader = KnowledgeLoader(provider)

    knowledge = loader.load(tmp_path)

    assert knowledge == {
        "company": {
            "name": "Tarot Alvin",
        },
    }

    assert provider.load_calls == [
        str(tmp_path),
    ]


def test_knowledge_loader_caches_loaded_knowledge(
    tmp_path,
):
    provider = FakeKnowledgeProvider()
    loader = KnowledgeLoader(provider)

    first_result = loader.load(tmp_path)
    second_result = loader.load(tmp_path)

    assert first_result is second_result
    assert len(provider.load_calls) == 1


def test_knowledge_loader_force_reload_calls_provider_again(
    tmp_path,
):
    provider = FakeKnowledgeProvider()
    loader = KnowledgeLoader(provider)

    loader.load(tmp_path)

    loader.load(
        tmp_path,
        force_reload=True,
    )

    assert len(provider.load_calls) == 2


def test_knowledge_loader_reports_cached_path(
    tmp_path,
):
    provider = FakeKnowledgeProvider()
    loader = KnowledgeLoader(provider)

    assert not loader.is_cached(tmp_path)

    loader.load(tmp_path)

    assert loader.is_cached(tmp_path)


def test_knowledge_loader_clears_specific_cached_path(
    tmp_path,
):
    provider = FakeKnowledgeProvider()
    loader = KnowledgeLoader(provider)

    loader.load(tmp_path)

    loader.clear(tmp_path)

    assert not loader.is_cached(tmp_path)


def test_knowledge_loader_clear_ignores_unknown_path(
    tmp_path,
):
    provider = FakeKnowledgeProvider()
    loader = KnowledgeLoader(provider)

    loader.clear(
        tmp_path / "missing",
    )

    assert not loader.is_cached(tmp_path)


def test_knowledge_loader_clears_complete_cache(
    tmp_path,
):
    provider = FakeKnowledgeProvider()
    loader = KnowledgeLoader(provider)

    first_path = tmp_path / "first"
    second_path = tmp_path / "second"

    loader.load(first_path)
    loader.load(second_path)

    assert loader.is_cached(first_path)
    assert loader.is_cached(second_path)

    loader.clear()

    assert not loader.is_cached(first_path)
    assert not loader.is_cached(second_path)


def test_knowledge_loader_normalizes_string_and_path_keys(
    tmp_path,
):
    provider = FakeKnowledgeProvider()
    loader = KnowledgeLoader(provider)

    loader.load(
        str(tmp_path),
    )

    loader.load(
        Path(tmp_path),
    )

    assert len(provider.load_calls) == 1