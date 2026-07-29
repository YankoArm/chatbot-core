from chatbot.connectors.whatsapp.graph_client import (
    WhatsAppGraphClient,
    WhatsAppGraphResponseError,
    WhatsAppMessageResponse,
)
import pytest

class RecordingHttpClient:
    def __init__(self) -> None:
        self.url: str | None = None
        self.headers: dict[str, str] | None = None
        self.json: dict[str, object] | None = None

    def post(
        self,
        *,
        url: str,
        headers: dict[str, str],
        json: dict[str, object],
    ) -> dict[str, object]:
        self.url = url
        self.headers = headers
        self.json = json

        return {
            "messages": [
                {
                    "id": "wamid.recorded-message-id",
                },
            ],
        }


def test_graph_client_can_be_created() -> None:
    client = WhatsAppGraphClient(
        access_token="test-token",
        phone_number_id="123456",
    )

    assert client is not None


def test_graph_client_exposes_send_text_message() -> None:
    client = WhatsAppGraphClient(
        access_token="test-token",
        phone_number_id="123456",
        http_client=RecordingHttpClient(),
    )

    result = client.send_text_message(
        to="34600000000",
        text="Hola",
    )

    assert result == WhatsAppMessageResponse(
        message_id="wamid.recorded-message-id",
    )


def test_graph_client_posts_to_messages_endpoint() -> None:
    http_client = RecordingHttpClient()

    client = WhatsAppGraphClient(
        access_token="test-token",
        phone_number_id="123456",
        http_client=http_client,
    )

    client.send_text_message(
        to="34600000000",
        text="Hola",
    )

    assert http_client.url == (
        "https://graph.facebook.com/v23.0/"
        "123456/messages"
    )


def test_graph_client_sends_authorization_header() -> None:
    http_client = RecordingHttpClient()

    client = WhatsAppGraphClient(
        access_token="my-token",
        phone_number_id="123456",
        http_client=http_client,
    )

    client.send_text_message(
        to="34600000000",
        text="Hola",
    )

    assert http_client.headers is not None
    assert http_client.headers["Authorization"] == "Bearer my-token"


def test_graph_client_sends_json_content_type() -> None:
    http_client = RecordingHttpClient()

    client = WhatsAppGraphClient(
        access_token="my-token",
        phone_number_id="123456",
        http_client=http_client,
    )

    client.send_text_message(
        to="34600000000",
        text="Hola",
    )

    assert http_client.headers is not None
    assert (
        http_client.headers["Content-Type"]
        == "application/json"
    )


def test_graph_client_sends_text_message_payload() -> None:
    http_client = RecordingHttpClient()

    client = WhatsAppGraphClient(
        access_token="test-token",
        phone_number_id="123456",
        http_client=http_client,
    )

    client.send_text_message(
        to="34600000000",
        text="Hola",
    )

    assert http_client.json == {
        "messaging_product": "whatsapp",
        "to": "34600000000",
        "type": "text",
        "text": {
            "body": "Hola",
        },
    }


def test_graph_client_returns_http_response() -> None:
    expected_response = {
        "messages": [
            {
                "id": "wamid.test-message-id",
            },
        ],
    }

    class ReturningHttpClient:
        def post(
            self,
            *,
            url: str,
            headers: dict[str, str],
            json: dict[str, object],
        ) -> dict[str, object]:
            return expected_response

    client = WhatsAppGraphClient(
        access_token="test-token",
        phone_number_id="123456",
        http_client=ReturningHttpClient(),
    )

    result = client.send_text_message(
        to="34600000000",
        text="Hola",
    )

    assert result == WhatsAppMessageResponse(
        message_id="wamid.test-message-id",
    )


def test_graph_client_returns_message_id() -> None:
    class ReturningHttpClient:
        def post(
            self,
            *,
            url: str,
            headers: dict[str, str],
            json: dict[str, object],
        ) -> dict[str, object]:
            return {
                "messages": [
                    {
                        "id": (
                            "wamid.HBgLMzQ2MDAwMDAwMDAVAgARGB..."
                        ),
                    },
                ],
            }

    client = WhatsAppGraphClient(
        access_token="test-token",
        phone_number_id="123456",
        http_client=ReturningHttpClient(),
    )

    response = client.send_text_message(
        to="34600000000",
        text="Hola",
    )

    assert response.message_id == (
        "wamid.HBgLMzQ2MDAwMDAwMDAVAgARGB..."
    )


def test_whatsapp_message_response_stores_message_id() -> None:
    response = WhatsAppMessageResponse(
        message_id="wamid.test-message-id",
    )

    assert response.message_id == "wamid.test-message-id"


def test_graph_client_returns_whatsapp_message_response() -> None:
    class ReturningHttpClient:
        def post(
            self,
            *,
            url: str,
            headers: dict[str, str],
            json: dict[str, object],
        ) -> dict[str, object]:
            return {
                "messages": [
                    {
                        "id": "wamid.test-message-id",
                    },
                ],
            }

    client = WhatsAppGraphClient(
        access_token="test-token",
        phone_number_id="123456",
        http_client=ReturningHttpClient(),
    )

    response = client.send_text_message(
        to="34600000000",
        text="Hola",
    )

    assert response == WhatsAppMessageResponse(
        message_id="wamid.test-message-id",
    )

def test_graph_client_raises_response_error_when_messages_are_missing() -> None:
    class ReturningHttpClient:
        def post(
            self,
            *,
            url: str,
            headers: dict[str, str],
            json: dict[str, object],
        ) -> dict[str, object]:
            return {}

    client = WhatsAppGraphClient(
        access_token="test-token",
        phone_number_id="123456",
        http_client=ReturningHttpClient(),
    )

    with pytest.raises(
        WhatsAppGraphResponseError,
        match="missing messages",
    ):
        client.send_text_message(
            to="34600000000",
            text="Hola",
        )

def test_graph_client_raises_response_error_when_messages_are_empty() -> None:
    class ReturningHttpClient:
        def post(
            self,
            *,
            url: str,
            headers: dict[str, str],
            json: dict[str, object],
        ) -> dict[str, object]:
            return {
                "messages": [],
            }

    client = WhatsAppGraphClient(
        access_token="test-token",
        phone_number_id="123456",
        http_client=ReturningHttpClient(),
    )

    with pytest.raises(
        WhatsAppGraphResponseError,
        match="missing messages",
    ):
        client.send_text_message(
            to="34600000000",
            text="Hola",
        )

def test_graph_client_raises_response_error_when_message_id_is_missing() -> None:
    class ReturningHttpClient:
        def post(
            self,
            *,
            url: str,
            headers: dict[str, str],
            json: dict[str, object],
        ) -> dict[str, object]:
            return {
                "messages": [
                    {},
                ],
            }

    client = WhatsAppGraphClient(
        access_token="test-token",
        phone_number_id="123456",
        http_client=ReturningHttpClient(),
    )

    with pytest.raises(
        WhatsAppGraphResponseError,
        match="missing messages",
    ):
        client.send_text_message(
            to="34600000000",
            text="Hola",
        )