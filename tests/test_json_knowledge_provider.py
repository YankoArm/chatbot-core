import json

import pytest

from chatbot.knowledge import JsonKnowledgeProvider


def test_json_provider_loads_all_json_sections(
    tmp_path,
):
    company_data = {
        "name": "Tarot Alvin",
        "language": "es",
    }

    faq_data = {
        "prices": {
            "answer": "Las sesiones cuestan 40 €.",
        },
    }

    (
        tmp_path / "company.json"
    ).write_text(
        json.dumps(company_data),
        encoding="utf-8",
    )

    (
        tmp_path / "faq.json"
    ).write_text(
        json.dumps(faq_data),
        encoding="utf-8",
    )

    provider = JsonKnowledgeProvider()

    knowledge = provider.load(tmp_path)

    assert knowledge == {
        "company": company_data,
        "faq": faq_data,
    }


def test_json_provider_accepts_string_path(
    tmp_path,
):
    (
        tmp_path / "company.json"
    ).write_text(
        '{"name": "Tarot Alvin"}',
        encoding="utf-8",
    )

    provider = JsonKnowledgeProvider()

    knowledge = provider.load(
        str(tmp_path),
    )

    assert knowledge["company"]["name"] == (
        "Tarot Alvin"
    )


def test_json_provider_ignores_non_json_files(
    tmp_path,
):
    (
        tmp_path / "company.json"
    ).write_text(
        '{"name": "Tarot Alvin"}',
        encoding="utf-8",
    )

    (
        tmp_path / "notes.txt"
    ).write_text(
        "This file must not be loaded.",
        encoding="utf-8",
    )

    provider = JsonKnowledgeProvider()

    knowledge = provider.load(tmp_path)

    assert list(knowledge) == ["company"]


def test_json_provider_returns_empty_dictionary_for_empty_file(
    tmp_path,
):
    (
        tmp_path / "company.json"
    ).write_text(
        "",
        encoding="utf-8",
    )

    provider = JsonKnowledgeProvider()

    knowledge = provider.load(tmp_path)

    assert knowledge == {
        "company": {},
    }


def test_json_provider_returns_empty_knowledge_for_empty_directory(
    tmp_path,
):
    provider = JsonKnowledgeProvider()

    knowledge = provider.load(tmp_path)

    assert knowledge == {}


def test_json_provider_raises_when_path_does_not_exist(
    tmp_path,
):
    missing_path = tmp_path / "missing"

    provider = JsonKnowledgeProvider()

    with pytest.raises(
        FileNotFoundError,
        match="Knowledge path does not exist",
    ):
        provider.load(missing_path)


def test_json_provider_raises_when_path_is_not_directory(
    tmp_path,
):
    file_path = tmp_path / "company.json"

    file_path.write_text(
        "{}",
        encoding="utf-8",
    )

    provider = JsonKnowledgeProvider()

    with pytest.raises(
        NotADirectoryError,
        match="Knowledge path is not a directory",
    ):
        provider.load(file_path)


def test_json_provider_raises_for_invalid_json(
    tmp_path,
):
    (
        tmp_path / "faq.json"
    ).write_text(
        '{"invalid": }',
        encoding="utf-8",
    )

    provider = JsonKnowledgeProvider()

    with pytest.raises(
        ValueError,
        match="Invalid JSON knowledge file",
    ):
        provider.load(tmp_path)