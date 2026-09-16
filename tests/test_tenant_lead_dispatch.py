from chatbot.clients.registry import (
    build_client_definition,
)
from chatbot.leads import SQLiteLeadRepository
from run_flowforge import build_tenant_application


def test_tenant_application_persists_captured_leads() -> None:
    repository = SQLiteLeadRepository(
        database_path=":memory:",
    )

    application = build_tenant_application(
        definition=build_client_definition(
            "professional_services_demo"
        ),
        calendar_service=None,
        booking_repository=None,
        lead_repository=repository,
    )

    session_id = "tenant-lead-session"

    application.chat(
        session_id=session_id,
        message="Quiero hablar con una persona",
    )
    application.chat(
        session_id=session_id,
        message="Yanko",
    )
    application.chat(
        session_id=session_id,
        message="600123123",
    )
    application.chat(
        session_id=session_id,
        message="Necesito un presupuesto.",
    )

    leads = repository.list_by_client(
        client_id="professional_services_demo",
    )

    assert len(leads) == 1
    assert leads[0].name == "Yanko"
    assert leads[0].phone == "+34600123123"
    assert leads[0].reason == "Necesito un presupuesto."
    assert leads[0].session_id == session_id

    repository.close()