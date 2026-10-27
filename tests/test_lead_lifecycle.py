from __future__ import annotations

import sqlite3

from fastapi.testclient import TestClient

from chatbot.api.whatsapp_app import (
    build_whatsapp_api,
)
from chatbot.leads import (
    Lead,
    SQLiteLeadRepository,
)


class NoOpMessageHandler:
    def handle(
        self,
        payload: dict,
    ) -> None:
        return None


def test_repository_migrates_existing_lead_database(
    tmp_path,
) -> None:
    database_path = (
        tmp_path / "legacy-leads.sqlite3"
    )

    connection = sqlite3.connect(
        database_path
    )

    connection.execute(
        """
        CREATE TABLE leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action_id TEXT NOT NULL UNIQUE,
            client_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            reason TEXT NOT NULL
        )
        """
    )

    connection.execute(
        """
        INSERT INTO leads (
            action_id,
            client_id,
            session_id,
            name,
            phone,
            reason
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            "legacy-lead",
            "professional_services_demo",
            "legacy-session",
            "Jonathan",
            "+34654087601",
            "reservar una cita",
        ),
    )

    connection.commit()
    connection.close()

    repository = SQLiteLeadRepository(
        database_path=database_path,
    )

    leads = repository.list_by_client(
        client_id="professional_services_demo"
    )

    assert len(leads) == 1
    assert leads[0].status == "pending"
    assert leads[0].created_at

    repository.close()


def test_repository_lists_newest_lead_first(
) -> None:
    repository = SQLiteLeadRepository(
        database_path=":memory:",
    )

    repository.save(
        Lead(
            action_id="old",
            client_id="client",
            session_id="session-old",
            name="Old",
            phone="+34600000001",
            reason="Old lead",
            created_at=(
                "2026-10-27T10:00:00+00:00"
            ),
        )
    )

    repository.save(
        Lead(
            action_id="new",
            client_id="client",
            session_id="session-new",
            name="New",
            phone="+34600000002",
            reason="New lead",
            created_at=(
                "2026-10-27T20:00:00+00:00"
            ),
        )
    )

    leads = repository.list_by_client(
        client_id="client"
    )

    assert [
        lead.action_id
        for lead in leads
    ] == [
        "new",
        "old",
    ]

    repository.close()


def test_admin_can_mark_lead_as_contacted(
) -> None:
    repository = SQLiteLeadRepository(
        database_path=":memory:",
    )

    repository.save(
        Lead(
            action_id="lead-1",
            client_id="professional_services_demo",
            session_id="session-1",
            name="Jonathan",
            phone="+34654087601",
            reason="reservar una cita",
        )
    )

    app = build_whatsapp_api(
        message_handler=NoOpMessageHandler(),
        lead_repository=repository,
    )

    client = TestClient(app)

    page = client.get(
        "/admin/clients/"
        "professional_services_demo/leads"
    )

    assert page.status_code == 200
    assert "Jonathan" in page.text
    assert "Pendiente" in page.text
    assert "Marcar como contactado" in page.text

    response = client.post(
        "/admin/clients/"
        "professional_services_demo/"
        "leads/lead-1/contacted",
        follow_redirects=False,
    )

    assert response.status_code == 303

    leads = repository.list_by_client(
        client_id="professional_services_demo"
    )

    assert len(leads) == 1
    assert leads[0].status == "contacted"
    assert leads[0].contacted_at is not None

    repository.close()
