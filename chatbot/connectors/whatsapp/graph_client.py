from __future__ import annotations

from typing import Protocol
from dataclasses import dataclass

class HttpClientProtocol(Protocol):
    def post(
        self,
        *,
        url: str,
        headers: dict[str, str],
        json: dict[str, object],
    ) -> dict[str, object]:
        ...

@dataclass(frozen=True)
class WhatsAppMessageResponse:
    message_id: str

class WhatsAppGraphResponseError(Exception):
    pass

class WhatsAppGraphClient:
    def __init__(
        self,
        *,
        access_token: str,
        phone_number_id: str,
        http_client: HttpClientProtocol | None = None,
    ) -> None:
        self._access_token = access_token
        self._phone_number_id = phone_number_id
        self._http_client = http_client

    def send_text_message(
        self,
        *,
        to: str,
        text: str,
    ) -> WhatsAppMessageResponse:
        response = self._http_client.post(
            url=(
                "https://graph.facebook.com/v23.0/"
                f"{self._phone_number_id}/messages"
            ),
            headers={
                "Authorization": f"Bearer {self._access_token}",
                "Content-Type": "application/json",
            },
            json={
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {
                    "body": text,
                },
            },
        )

        try:
            message_id = response["messages"][0]["id"]
        except (KeyError, IndexError, TypeError) as exc:
            raise WhatsAppGraphResponseError(
                "WhatsApp Graph response missing messages"
            ) from exc

        return WhatsAppMessageResponse(
            message_id=message_id,
        )