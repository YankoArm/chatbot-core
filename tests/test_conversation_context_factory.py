from pathlib import Path

import pytest

from chatbot.conversation import (
    ConversationContextFactory,
)
from chatbot.instances import Instance
from chatbot.knowledge import (
    KnowledgeService,
    KnowledgeServiceFactory,
)


def build_context_factory(
    knowledge_root: Path,
) -> ConversationContextFactory:
    knowledge_factory = KnowledgeServiceFactory(
        knowledge_root=knowledge_root,
    )

    return ConversationContextFactory(
        knowledge_service_factory=knowledge_factory,
    )


def test_context_factory_builds_context_with_knowledge_service(
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
        knowledge_path=str(instance_path),
    )

    context_factory = build_context_factory(
        tmp_path
    )

    context = context_factory.build(
        instance=instance,
        session_id="session-001",
        user_id="user-001",
    )

    assert context.session_id == "session-001"
    assert context.user_id == "user-001"

    assert isinstance(
        context.knowledge_service,
        KnowledgeService,
    )

    assert context.knowledge_service.get(
        "company",
        "name",
    ) == "Tarot Alvin"


def test_context_factory_uses_explicit_knowledge_path(
    tmp_path: Path,
):
    custom_path = (
        tmp_path
        / "clients"
        / "alvin_knowledge"
    )

    custom_path.mkdir(
        parents=True
    )

    (
        custom_path / "company.json"
    ).write_text(
        '{"name": "Custom Tarot Alvin"}',
        encoding="utf-8",
    )

    instance = Instance(
        id="tarot_alvin",
        name="Tarot Alvin",
        capabilities=[],
        knowledge_path=str(custom_path),
    )

    context_factory = build_context_factory(
        tmp_path
    )

    context = context_factory.build(
        instance=instance,
        session_id="session-001",
        user_id="user-001",
    )

    assert context.knowledge_service.get(
        "company",
        "name",
    ) == "Custom Tarot Alvin"


def test_context_factory_uses_default_instance_path(
    tmp_path: Path,
):
    instance_path = (
        tmp_path / "tarot_alvin"
    )

    instance_path.mkdir()

    (
        instance_path / "company.json"
    ).write_text(
        '{"name": "Default Tarot Alvin"}',
        encoding="utf-8",
    )

    instance = Instance(
        id="tarot_alvin",
        name="Tarot Alvin",
        capabilities=[],
    )

    context_factory = build_context_factory(
        tmp_path
    )

    context = context_factory.build(
        instance=instance,
        session_id="session-001",
        user_id="user-001",
    )

    assert context.knowledge_service.get(
        "company",
        "name",
    ) == "Default Tarot Alvin"


def test_context_factory_strips_session_and_user_ids(
    tmp_path: Path,
):
    instance_path = (
        tmp_path / "tarot_alvin"
    )

    instance_path.mkdir()

    (
        instance_path / "company.json"
    ).write_text(
        "{}",
        encoding="utf-8",
    )

    instance = Instance(
        id="tarot_alvin",
        name="Tarot Alvin",
        capabilities=[],
        knowledge_path=str(instance_path),
    )

    context_factory = build_context_factory(
        tmp_path
    )

    context = context_factory.build(
        instance=instance,
        session_id="  session-001  ",
        user_id="  user-001  ",
    )

    assert context.session_id == "session-001"
    assert context.user_id == "user-001"


def test_context_factory_rejects_empty_session_id(
    tmp_path: Path,
):
    instance = Instance(
        id="tarot_alvin",
        name="Tarot Alvin",
        capabilities=[],
    )

    context_factory = build_context_factory(
        tmp_path
    )

    with pytest.raises(
        ValueError,
        match="Session ID cannot be empty",
    ):
        context_factory.build(
            instance=instance,
            session_id="",
            user_id="user-001",
        )


def test_context_factory_rejects_empty_user_id(
    tmp_path: Path,
):
    instance = Instance(
        id="tarot_alvin",
        name="Tarot Alvin",
        capabilities=[],
    )

    context_factory = build_context_factory(
        tmp_path
    )

    with pytest.raises(
        ValueError,
        match="User ID cannot be empty",
    ):
        context_factory.build(
            instance=instance,
            session_id="session-001",
            user_id="",
        )