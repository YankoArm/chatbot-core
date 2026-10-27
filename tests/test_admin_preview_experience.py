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
    assert 'name="suggestion"' in response.text
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

def test_preview_processes_suggestion_without_manual_message() -> None:
    app = build_whatsapp_api(
        message_handler=NoOpMessageHandler(),
    )
    client = TestClient(app)

    response = client.post(
        "/admin/clients/professional_services_demo/preview",
        data={
            "history": "[]",
            "suggestion": "Hola",
        },
    )

    assert response.status_code == 200
    assert "¡Hola!" in response.text


def test_preview_does_not_intercept_booking_words_during_lead_capture(
) -> None:
    app = build_whatsapp_api(
        message_handler=NoOpMessageHandler(),
    )
    client = TestClient(app)

    response = client.post(
        "/admin/clients/"
        "professional_services_demo/preview",
        data={
            "history": (
                '["Quiero hablar con una persona", '
                '"Jonathan", '
                '"654087601"]'
            ),
            "message": "reservar una cita",
        },
    )

    assert response.status_code == 200
    assert (
        "Gracias. He enviado tus datos al equipo"
        in response.text
    )
    assert (
        "Las reservas no se pueden probar aqu?"
        not in response.text
    )



def test_preview_marks_completed_lead_as_simulation(
) -> None:
    app = build_whatsapp_api(
        message_handler=NoOpMessageHandler(),
    )
    client = TestClient(app)

    response = client.post(
        "/admin/clients/"
        "professional_services_demo/preview",
        data={
            "history": (
                '["Quiero hablar con una persona", '
                '"Jonathan", '
                '"654087601"]'
            ),
            "message": "Necesito informacion comercial",
        },
    )

    assert response.status_code == 200
    assert (
        "Solicitud simulada correctamente"
        in response.text
    )
    assert (
        "Solicitudes recibidas"
        in response.text
    )


def test_preview_offers_restart_conversation(
) -> None:
    app = build_whatsapp_api(
        message_handler=NoOpMessageHandler(),
    )
    client = TestClient(app)

    response = client.get(
        "/admin/clients/"
        "professional_services_demo/preview"
    )

    assert response.status_code == 200
    assert (
        "/admin/clients/"
        "professional_services_demo/preview"
        in response.text
    )
    assert "Reiniciar conversaci" in response.text


def test_preview_hides_booking_notice_when_bot_has_no_booking(
) -> None:
    app = build_whatsapp_api(
        message_handler=NoOpMessageHandler(),
    )
    client = TestClient(app)

    response = client.get(
        "/admin/clients/"
        "professional_services_demo/preview"
    )

    assert response.status_code == 200
    assert (
        "Las reservas est"
        not in response.text
    )
