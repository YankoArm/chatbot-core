from pathlib import Path

import pytest

from chatbot.instances import Instance
from chatbot.knowledge import (
    KnowledgeService,
    KnowledgeServiceFactory,
)


def test_factory_builds_knowledge_service(
    tmp_path: Path,
):
    instance_path = (
        tmp_path / "tarot_alvin"
    )

    instance_path.mkdir()

    (
        instance_path / "company.json"
    ).write_text(
        '{"name": "Tarot Alvin"}',
        encoding="utf-8",
    )

    instance = Instance(
        id="tarot_alvin",
        name="Tarot Alvin",
        capabilities=[],
    )

    factory = KnowledgeServiceFactory(
        knowledge_root=tmp_path,
    )

    service = factory.build(
        instance
    )

    assert isinstance(
        service,
        KnowledgeService,
    )

    assert service.get(
        "company",
        "name",
    ) == "Tarot Alvin"


def test_factory_uses_instance_directory(
    tmp_path: Path,
):
    factory = KnowledgeServiceFactory(
        knowledge_root=tmp_path,
    )

    result = factory.knowledge_path_for(
        "tarot_alvin"
    )

    assert result == (
        tmp_path / "tarot_alvin"
    )


def test_factory_strips_instance_id(
    tmp_path: Path,
):
    factory = KnowledgeServiceFactory(
        knowledge_root=tmp_path,
    )

    result = factory.knowledge_path_for(
        "  tarot_alvin  "
    )

    assert result == (
        tmp_path / "tarot_alvin"
    )


def test_factory_rejects_empty_instance_id(
    tmp_path: Path,
):
    factory = KnowledgeServiceFactory(
        knowledge_root=tmp_path,
    )

    with pytest.raises(
        ValueError,
        match="Instance id cannot be empty",
    ):
        factory.knowledge_path_for("")


def test_factory_rejects_blank_instance_id(
    tmp_path: Path,
):
    factory = KnowledgeServiceFactory(
        knowledge_root=tmp_path,
    )

    with pytest.raises(
        ValueError,
        match="Instance id cannot be empty",
    ):
        factory.knowledge_path_for("   ")


def test_factory_service_raises_when_instance_directory_does_not_exist(
    tmp_path: Path,
):
    instance = Instance(
        id="missing_instance",
        name="Missing Instance",
        capabilities=[],
    )

    factory = KnowledgeServiceFactory(
        knowledge_root=tmp_path,
    )

    service = factory.build(
        instance
    )

    with pytest.raises(
        FileNotFoundError,
        match="Knowledge path does not exist",
    ):
        service.load()


def test_factory_builds_service_from_explicit_path(
    tmp_path: Path,
):
    custom_path = (
        tmp_path / "custom_knowledge"
    )

    custom_path.mkdir()

    (
        custom_path / "company.json"
    ).write_text(
        '{"name": "Custom Client"}',
        encoding="utf-8",
    )

    factory = KnowledgeServiceFactory()

    service = factory.build_from_path(
        custom_path
    )

    assert service.get(
        "company",
        "name",
    ) == "Custom Client"


def test_factory_explicit_path_does_not_use_knowledge_root(
    tmp_path: Path,
):
    configured_root = (
        tmp_path / "default_root"
    )

    explicit_path = (
        tmp_path / "external_client"
    )

    explicit_path.mkdir()

    (
        explicit_path / "company.json"
    ).write_text(
        '{"name": "External Client"}',
        encoding="utf-8",
    )

    factory = KnowledgeServiceFactory(
        knowledge_root=configured_root,
    )

    service = factory.build_from_path(
        explicit_path
    )

    assert service.get(
        "company",
        "name",
    ) == "External Client"


def test_factory_prefers_explicit_instance_knowledge_path(
    tmp_path: Path,
):
    default_path = (
        tmp_path / "tarot_alvin"
    )

    explicit_path = (
        tmp_path / "custom_tarot_data"
    )

    default_path.mkdir()
    explicit_path.mkdir()

    (
        default_path / "company.json"
    ).write_text(
        '{"name": "Default Tarot Alvin"}',
        encoding="utf-8",
    )

    (
        explicit_path / "company.json"
    ).write_text(
        '{"name": "Explicit Tarot Alvin"}',
        encoding="utf-8",
    )

    instance = Instance(
        id="tarot_alvin",
        name="Tarot Alvin",
        capabilities=[],
        knowledge_path=str(explicit_path),
    )

    factory = KnowledgeServiceFactory(
        knowledge_root=tmp_path,
    )

    service = factory.build(
        instance
    )

    assert service.get(
        "company",
        "name",
    ) == "Explicit Tarot Alvin"


def test_factory_resolves_default_path_when_instance_has_no_explicit_path(
    tmp_path: Path,
):
    instance = Instance(
        id="tarot_alvin",
        name="Tarot Alvin",
        capabilities=[],
    )

    factory = KnowledgeServiceFactory(
        knowledge_root=tmp_path,
    )

    result = factory.resolve_path(
        instance
    )

    assert result == (
        tmp_path / "tarot_alvin"
    )


def test_factory_resolves_explicit_instance_path(
    tmp_path: Path,
):
    explicit_path = (
        tmp_path / "external_knowledge"
    )

    instance = Instance(
        id="tarot_alvin",
        name="Tarot Alvin",
        capabilities=[],
        knowledge_path=str(explicit_path),
    )

    factory = KnowledgeServiceFactory(
        knowledge_root=tmp_path,
    )

    result = factory.resolve_path(
        instance
    )

    assert result == explicit_path