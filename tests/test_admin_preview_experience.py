from fastapi.testclient import TestClient

from chatbot.api.whatsapp_app import (
    build_whatsapp_api,
)


class NoOpMessageHandler:
    def handle(
        self,
        payload: dict,
    ) -> None:
        return None


def test_preview_offers_suggestions_and_scrolls_to_latest_turn() -> None:
    app = build_whatsapp_api(
        message_handler=NoOpMessageHandler(),
    )
    client = TestClient(app)

    response = client.get(
        "/admin/clients/professional_services_demo/preview"
    )

    assert response.status_code == 200
    assert 'id="preview-form"' in response.text
    assert response.text.count(
        'form="preview-form"'
    ) == 3
    assert response.text.count('formnovalidate') == 3
    assert 'name="message"' in response.text
    assert 'value="Hola"' in response.text
    assert (
        'value="¿Qué servicios ofrecéis?"'
        in response.text
    )
    assert (
        'value="Quiero hablar con una persona"'
        in response.text
    )
    assert 'data-preview-message' not in response.text
    assert "scrollIntoView" in response.text
    assert "preview-conversation" in response.text