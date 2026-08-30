from __future__ import annotations

from pathlib import Path

from chatbot.activation import ActivationConfig
from chatbot.instances import (
    InstanceDefinition,
    SQLiteInstanceDefinitionRepository,
)


def make_definition(
    *,
    client_id: str = "salon_norte",
    name: str = "Salón Norte",
) -> InstanceDefinition:
    return InstanceDefinition(
        id=client_id,
        name=name,
        template_id="hairdressing",
        default_language="es",
        supported_languages=[
            "es",
            "en",
        ],
        channels=[
            "web",
            "whatsapp",
        ],
        capabilities=[
            "booking",
        ],
        disabled_capabilities=[
            "human_transfer",
        ],
        connectors=[
            "google_calendar",
        ],
        disabled_connectors=[],
        knowledge_path=(
            f"knowledge/{client_id}"
        ),
        settings={
            "branding": {
                "display_name": name,
            },
            "services": [
                {
                    "id": "haircut",
                    "name": {
                        "es": "Corte",
                        "en": "Haircut",
                    },
                    "duration_minutes": 30,
                    "price": {
                        "type": "fixed",
                        "amount_cents": 2000,
                        "currency": "EUR",
                    },
                },
            ],
            "booking": {
                "timezone": "Europe/Madrid",
            },
        },
        metadata={
            "owner": "Jona",
            "status": "draft",
        },
        activation=ActivationConfig(
            type="exact_phrase",
            phrases=[
                "peluqueria",
                "peluquería",
            ],
            prompt_message="Escribe PELUQUERÍA.",
            activated_message="Asistente activado.",
            prompt_cooldown=45,
            session_timeout=3600,
        ),
    )


def test_repository_creates_database_file(
    tmp_path: Path,
) -> None:
    database_path = (
        tmp_path
        / "flowforge-admin.sqlite3"
    )

    repository = (
        SQLiteInstanceDefinitionRepository(
            database_path=database_path,
        )
    )

    assert database_path.exists()

    repository.close()


def test_repository_saves_and_loads_complete_definition(
    tmp_path: Path,
) -> None:
    database_path = (
        tmp_path
        / "flowforge-admin.sqlite3"
    )
    definition = make_definition()

    repository = (
        SQLiteInstanceDefinitionRepository(
            database_path=database_path,
        )
    )
    repository.save(
        definition
    )
    repository.close()

    reopened_repository = (
        SQLiteInstanceDefinitionRepository(
            database_path=database_path,
        )
    )

    stored_definition = (
        reopened_repository.get(
            definition.id
        )
    )

    assert stored_definition == definition

    reopened_repository.close()


def test_repository_returns_none_for_unknown_definition(
    tmp_path: Path,
) -> None:
    repository = (
        SQLiteInstanceDefinitionRepository(
            database_path=(
                tmp_path
                / "flowforge-admin.sqlite3"
            ),
        )
    )

    assert repository.get(
        "missing-client"
    ) is None

    repository.close()


def test_repository_lists_definitions_by_name(
    tmp_path: Path,
) -> None:
    repository = (
        SQLiteInstanceDefinitionRepository(
            database_path=(
                tmp_path
                / "flowforge-admin.sqlite3"
            ),
        )
    )

    repository.save(
        make_definition(
            client_id="salon_zeta",
            name="Salón Zeta",
        )
    )
    repository.save(
        make_definition(
            client_id="salon_alba",
            name="Salón Alba",
        )
    )

    definitions = repository.list_all()

    assert [
        definition.id
        for definition in definitions
    ] == [
        "salon_alba",
        "salon_zeta",
    ]

    repository.close()


def test_repository_updates_existing_definition(
    tmp_path: Path,
) -> None:
    repository = (
        SQLiteInstanceDefinitionRepository(
            database_path=(
                tmp_path
                / "flowforge-admin.sqlite3"
            ),
        )
    )

    repository.save(
        make_definition()
    )
    repository.save(
        make_definition(
            name="Salón Norte Renovado",
        )
    )

    definitions = repository.list_all()

    assert len(definitions) == 1
    assert definitions[0].name == (
        "Salón Norte Renovado"
    )

    repository.close()
def test_repository_finds_definition_by_whatsapp_phone_number_id(
) -> None:
    repository = SQLiteInstanceDefinitionRepository(
        database_path=":memory:",
    )
    definition = InstanceDefinition(
        id="hairdressing_demo",
        name="Salón Estilo",
        template_id="hairdressing",
        whatsapp_phone_number_id=(
            "test-phone-number-id"
        ),
    )

    repository.save(
        definition
    )

    result = repository.get_by_whatsapp_phone_number_id(
        "test-phone-number-id"
    )

    assert result == definition

    repository.close()
def test_repository_preserves_client_calendar_id(
) -> None:
    repository = SQLiteInstanceDefinitionRepository(
        database_path=":memory:",
    )
    definition = InstanceDefinition(
        id="salon_norte",
        name="Salón Norte",
        template_id="hairdressing",
        calendar_id="salon-norte-calendar-id",
    )

    repository.save(
        definition
    )

    result = repository.get(
        "salon_norte"
    )

    assert result is not None
    assert result.calendar_id == (
        "salon-norte-calendar-id"
    )

    repository.close()