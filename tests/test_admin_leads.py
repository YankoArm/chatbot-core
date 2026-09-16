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


def test_admin_lists_only_the_selected_client_leads() -> None:
    repository = SQLiteLeadRepository(
        database_path=":memory:",
    )
    repository.save(
        Lead(
            action_id="lead-nexo-1",
            client_id="professional_services_demo",
            session_id="session-nexo-1",
            name="Yanko",
            phone="+34600123123",
            reason="Necesito automatizar la atención al cliente.",
        )
    )
    repository.save(
        Lead(
            action_id="lead-otro-1",
            client_id="hairdressing_demo",
            session_id="session-salon-1",
            name="Otra persona",
            phone="+34600999999",
            reason="Quiero reservar una cita.",
        )
    )

    app = build_whatsapp_api(
        message_handler=NoOpMessageHandler(),
        lead_repository=repository,
    )
    client = TestClient(app)

    detail_response = client.get(
        "/admin/clients/professional_services_demo"
    )
    leads_response = client.get(
        "/admin/clients/professional_services_demo/leads"
    )

    assert detail_response.status_code == 200
    assert (
        'href="/admin/clients/'
        'professional_services_demo/leads"'
        in detail_response.text
    )

    assert leads_response.status_code == 200
    assert "Solicitudes recibidas" in leads_response.text
    assert "Yanko" in leads_response.text
    assert "+34600123123" in leads_response.text
    assert (
        "Necesito automatizar la atención al cliente."
        in leads_response.text
    )
    assert "session-nexo-1" in leads_response.text

    assert "Otra persona" not in leads_response.text
    assert "+34600999999" not in leads_response.text

    repository.close()