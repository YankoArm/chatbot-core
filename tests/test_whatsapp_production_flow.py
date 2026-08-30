from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any

from fastapi.testclient import TestClient

from chatbot.infrastructure.config import (
    FlowForgeConfig,
    ServerConfig,
    WhatsAppConfig,
)
from run_flowforge import create_app


_APP_SECRET = "test-app-secret"
_PHONE_NUMBER = "34600123123"


class RecordingWhatsAppGraphClient:
    def __init__(
        self,
    ) -> None:
        self.sent_messages: list[
            dict[str, str]
        ] = []

    def send_text_message(
        self,
        *,
        to: str,
        text: str,
    ) -> object:
        self.sent_messages.append(
            {
                "to": to,
                "text": text,
            }
        )

        return object()


def build_config() -> FlowForgeConfig:
    return FlowForgeConfig(
        whatsapp=WhatsAppConfig(
            access_token="test-access-token",
            phone_number_id="test-phone-number-id",
            verify_token="test-verify-token",
            app_secret=_APP_SECRET,
        ),
        server=ServerConfig(
            host="127.0.0.1",
            port=8000,
        ),
        client_id="hairdressing_demo",
    )


def build_payload(
    *,
    message_id: str,
    text: str,
    phone_number: str = _PHONE_NUMBER,
) -> dict[str, Any]:
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "business-account-id",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "messaging_product": (
                                "whatsapp"
                            ),
                            "metadata": {
                                "display_phone_number": (
                                    "34123456789"
                                ),
                                "phone_number_id": (
                                    "test-phone-number-id"
                                ),
                            },
                            "contacts": [
                                {
                                    "profile": {
                                        "name": "Yanko",
                                    },
                                    "wa_id": phone_number,
                                },
                            ],
                            "messages": [
                                {
                                    "from": phone_number,
                                    "id": message_id,
                                    "timestamp": (
                                        "1787821200"
                                    ),
                                    "type": "text",
                                    "text": {
                                        "body": text,
                                    },
                                },
                            ],
                        },
                    },
                ],
            },
        ],
    }


def post_signed_webhook(
    client: TestClient,
    payload: dict[str, Any],
) -> object:
    body = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(
            ",",
            ":",
        ),
    ).encode(
        "utf-8"
    )

    digest = hmac.new(
        _APP_SECRET.encode(
            "utf-8"
        ),
        body,
        hashlib.sha256,
    ).hexdigest()

    return client.post(
        "/webhook",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": (
                f"sha256={digest}"
            ),
        },
    )


def test_whatsapp_production_flow_preserves_conversation_session(
) -> None:
    graph_client = (
        RecordingWhatsAppGraphClient()
    )

    app = create_app(
        config=build_config(),
        calendar_service=None,
        graph_client=graph_client,
    )

    client = TestClient(
        app
    )

    activation_response = post_signed_webhook(
        client,
        build_payload(
            message_id="wamid.activation-1",
            text="Peluquería",
        ),
    )

    assert activation_response.status_code == 200
    assert activation_response.json() == {
        "status": "ok",
    }

    faq_response = post_signed_webhook(
        client,
        build_payload(
            message_id="wamid.faq-1",
            text="¿Qué horario tenéis?",
        ),
    )

    assert faq_response.status_code == 200
    assert faq_response.json() == {
        "status": "ok",
    }

    assert len(
        graph_client.sent_messages
    ) == 2

    first_message = (
        graph_client.sent_messages[0]
    )
    second_message = (
        graph_client.sent_messages[1]
    )

    assert first_message["to"] == (
        _PHONE_NUMBER
    )
    assert (
        "Demostración de peluquería "
        "activada correctamente"
    ) in first_message["text"]

    assert second_message["to"] == (
        _PHONE_NUMBER
    )
    assert (
        "Abrimos de lunes a viernes"
    ) in second_message["text"]
    assert (
        "domingos permanecemos cerrados"
    ) in second_message["text"]

def test_whatsapp_production_flow_ignores_duplicate_message_id(
) -> None:
    graph_client = (
        RecordingWhatsAppGraphClient()
    )

    app = create_app(
        config=build_config(),
        calendar_service=None,
        graph_client=graph_client,
    )

    client = TestClient(
        app
    )

    payload = build_payload(
        message_id="wamid.duplicate-1",
        text="Peluquería",
    )

    first_response = post_signed_webhook(
        client,
        payload,
    )
    duplicate_response = post_signed_webhook(
        client,
        payload,
    )

    assert first_response.status_code == 200
    assert duplicate_response.status_code == 200

    assert first_response.json() == {
        "status": "ok",
    }
    assert duplicate_response.json() == {
        "status": "ok",
    }

    assert len(
        graph_client.sent_messages
    ) == 1
    assert (
        graph_client.sent_messages[0]["to"]
        == _PHONE_NUMBER
    )
def test_production_flow_ignores_unknown_receiver_phone_number(
) -> None:
    from chatbot.instances import (
        SQLiteInstanceDefinitionRepository,
    )

    graph_client = RecordingWhatsAppGraphClient()
    repository = SQLiteInstanceDefinitionRepository(
        database_path=":memory:",
    )

    app = create_app(
        config=build_config(),
        calendar_service=None,
        graph_client=graph_client,
        instance_definition_repository=repository,
    )

    payload = build_payload(
        message_id="wamid.unknown-number-1",
        text="Peluquería",
    )
    payload["entry"][0]["changes"][0]["value"][
        "metadata"
    ]["phone_number_id"] = "unknown-phone-number-id"

    response = post_signed_webhook(
        TestClient(app),
        payload,
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
    }
    assert graph_client.sent_messages == []

    repository.close()
def test_production_flow_routes_registered_receiver_phone_number(
) -> None:
    from chatbot.instances import (
        SQLiteInstanceDefinitionRepository,
    )

    graph_client = RecordingWhatsAppGraphClient()
    repository = SQLiteInstanceDefinitionRepository(
        database_path=":memory:",
    )

    app = create_app(
        config=build_config(),
        calendar_service=None,
        graph_client=graph_client,
        instance_definition_repository=repository,
    )

    response = post_signed_webhook(
        TestClient(app),
        build_payload(
            message_id="wamid.registered-number-1",
            text="Peluquería",
        ),
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
    }
    assert len(graph_client.sent_messages) == 1
    assert graph_client.sent_messages[0]["to"] == (
        _PHONE_NUMBER
    )

    repository.close()