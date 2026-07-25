from __future__ import annotations

from pathlib import Path
from typing import Any

from chatbot.knowledge import (
    KnowledgeLoader,
    KnowledgeProvider,
    KnowledgeService,
)


class FakeKnowledgeProvider(KnowledgeProvider):
    def __init__(self) -> None:
        self.load_count = 0

    def load(
        self,
        knowledge_path: str | Path,
    ) -> dict[str, Any]:
        self.load_count += 1

        return {
            "company": {
                "name": "Tarot Alvin",
                "language": "es",
            },
            "services": {
                "tarot_session": {
                    "price": 40,
                },
            },
            "faq": {
                "prices": {
                    "answer": (
                        "Las sesiones cuestan 40 €."
                    ),
                },
            },
        }


def build_service(
    tmp_path,
) -> tuple[
    KnowledgeService,
    FakeKnowledgeProvider,
]:
    provider = FakeKnowledgeProvider()
    loader = KnowledgeLoader(provider)

    service = KnowledgeService(
        loader=loader,
        knowledge_path=tmp_path,
    )

    return service, provider


def test_knowledge_service_loads_knowledge(
    tmp_path,
):
    service, provider = build_service(
        tmp_path
    )

    knowledge = service.load()

    assert knowledge["company"]["name"] == (
        "Tarot Alvin"
    )
    assert provider.load_count == 1


def test_knowledge_service_loads_lazily(
    tmp_path,
):
    service, provider = build_service(
        tmp_path
    )

    assert provider.load_count == 0

    name = service.get(
        "company",
        "name",
    )

    assert name == "Tarot Alvin"
    assert provider.load_count == 1


def test_knowledge_service_gets_complete_section(
    tmp_path,
):
    service, _ = build_service(
        tmp_path
    )

    company = service.get_section(
        "company"
    )

    assert company == {
        "name": "Tarot Alvin",
        "language": "es",
    }


def test_knowledge_service_returns_default_for_missing_section(
    tmp_path,
):
    service, _ = build_service(
        tmp_path
    )

    result = service.get_section(
        "missing",
        {},
    )

    assert result == {}


def test_knowledge_service_gets_value_from_section(
    tmp_path,
):
    service, _ = build_service(
        tmp_path
    )

    result = service.get(
        "services",
        "tarot_session",
    )

    assert result == {
        "price": 40,
    }


def test_knowledge_service_returns_default_for_missing_key(
    tmp_path,
):
    service, _ = build_service(
        tmp_path
    )

    result = service.get(
        "company",
        "phone",
        "not configured",
    )

    assert result == "not configured"


def test_knowledge_service_returns_default_for_non_dict_section(
    tmp_path,
):
    class NonDictionaryProvider(
        KnowledgeProvider
    ):
        def load(
            self,
            knowledge_path: str | Path,
        ) -> dict[str, Any]:
            return {
                "greetings": [
                    "Hola",
                    "Buenas",
                ],
            }

    provider = NonDictionaryProvider()
    loader = KnowledgeLoader(provider)

    service = KnowledgeService(
        loader=loader,
        knowledge_path=tmp_path,
    )

    result = service.get(
        "greetings",
        "welcome",
        "Hola",
    )

    assert result == "Hola"


def test_knowledge_service_reports_existing_section(
    tmp_path,
):
    service, _ = build_service(
        tmp_path
    )

    assert service.has_section("faq")
    assert not service.has_section("missing")


def test_knowledge_service_does_not_reload_on_repeated_access(
    tmp_path,
):
    service, provider = build_service(
        tmp_path
    )

    service.get_section("company")
    service.get_section("faq")
    service.get("company", "name")

    assert provider.load_count == 1


def test_knowledge_service_reload_forces_provider_call(
    tmp_path,
):
    service, provider = build_service(
        tmp_path
    )

    service.load()
    service.reload()

    assert provider.load_count == 2


def test_knowledge_service_clear_removes_cached_knowledge(
    tmp_path,
):
    service, provider = build_service(
        tmp_path
    )

    service.get_section("company")
    service.clear()
    service.get_section("company")

    assert provider.load_count == 2