from pathlib import Path

from chatbot.leads import (
    Lead,
    SQLiteLeadRepository,
)


def make_lead(
    *,
    client_id: str = "professional_services_demo",
    action_id: str = "lead-action-001",
) -> Lead:
    return Lead(
        action_id=action_id,
        client_id=client_id,
        session_id="whatsapp:+34600123123",
        name="Yanko",
        phone="+34600123123",
        reason=(
            "Necesito un presupuesto para automatizar "
            "la atención al cliente."
        ),
    )


def build_repository(
    database_path: Path,
) -> SQLiteLeadRepository:
    return SQLiteLeadRepository(
        database_path=database_path,
    )


def test_sqlite_lead_repository_persists_after_reopening(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "leads.sqlite3"
    lead = make_lead()

    repository = build_repository(database_path)

    assert repository.save(lead) is True

    repository.close()

    reopened_repository = build_repository(
        database_path
    )

    assert reopened_repository.list_by_client(
        client_id="professional_services_demo",
    ) == (lead,)

    reopened_repository.close()


def test_sqlite_lead_repository_keeps_clients_isolated(
    tmp_path: Path,
) -> None:
    repository = build_repository(
        tmp_path / "leads.sqlite3"
    )

    professional_lead = make_lead()
    tarot_lead = make_lead(
        client_id="tarot_alvin",
        action_id="lead-action-002",
    )

    repository.save(professional_lead)
    repository.save(tarot_lead)

    assert repository.list_by_client(
        client_id="professional_services_demo",
    ) == (professional_lead,)
    assert repository.list_by_client(
        client_id="tarot_alvin",
    ) == (tarot_lead,)

    repository.close()


def test_sqlite_lead_repository_ignores_repeated_action(
    tmp_path: Path,
) -> None:
    repository = build_repository(
        tmp_path / "leads.sqlite3"
    )
    lead = make_lead()

    assert repository.save(lead) is True
    assert repository.save(lead) is False
    assert repository.list_by_client(
        client_id="professional_services_demo",
    ) == (lead,)

    repository.close()
