from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class HttpClientProtocol(Protocol):
    def post(
        self,
        *,
        url: str,
        headers: dict[str, str],
        json: dict[str, object],
    ) -> dict[str, Any]:
        ...


class StandardHttpClient:
    def post(
        self,
        *,
        url: str,
        headers: dict[str, str],
        json: dict[str, object],
    ) -> dict[str, Any]:
        request = Request(
            url=url,
            data=self._encode_payload(json),
            headers=headers,
            method="POST",
        )

        try:
            with urlopen(
                request,
                timeout=30,
            ) as response:
                body = response.read()
        except HTTPError as exc:
            error_body = exc.read().decode(
                "utf-8",
                errors="replace",
            )

            raise WhatsAppGraphResponseError(
                "WhatsApp Graph API returned "
                f"HTTP {exc.code}: {error_body}"
            ) from exc
        except URLError as exc:
            raise WhatsAppGraphResponseError(
                "Could not connect to WhatsApp Graph API"
            ) from exc

        try:
            payload = json_module.loads(
                body.decode("utf-8")
            )
        except (
            UnicodeDecodeError,
            json_module.JSONDecodeError,
        ) as exc:
            raise WhatsAppGraphResponseError(
                "WhatsApp Graph API returned invalid JSON"
            ) from exc

        if not isinstance(payload, dict):
            raise WhatsAppGraphResponseError(
                "WhatsApp Graph API returned "
                "an unexpected response"
            )

        return payload

    @staticmethod
    def _encode_payload(
        payload: dict[str, object],
    ) -> bytes:
        return json_module.dumps(
            payload
        ).encode("utf-8")


json_module = json


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
        self._http_client = (
            http_client or StandardHttpClient()
        )

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
                "Authorization": (
                    f"Bearer {self._access_token}"
                ),
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
            messages = response["messages"]
            first_message = messages[0]
            message_id = first_message["id"]
        except (KeyError, IndexError, TypeError) as exc:
            raise WhatsAppGraphResponseError(
                "WhatsApp Graph response missing messages"
            ) from exc

        if not isinstance(message_id, str):
            raise WhatsAppGraphResponseError(
                "WhatsApp Graph response contains "
                "an invalid message id"
            )

        return WhatsAppMessageResponse(
            message_id=message_id,
        )
from collections.abc import Callable
from threading import RLock


GraphClientFactory = Callable[
    [str],
    object,
]


class WhatsAppGraphClientProvider:
    """
    Build and retain one Graph client per WhatsApp phone number.

    The access token remains server-side and is shared only through
    the factory used to create per-number clients.
    """

    def __init__(
        self,
        *,
        access_token: str,
        graph_client_factory: (
            GraphClientFactory | None
        ) = None,
    ) -> None:
        self._access_token = access_token
        self._graph_client_factory = (
            graph_client_factory
            or self._build_graph_client
        )
        self._graph_clients: dict[
            str,
            object,
        ] = {}
        self._lock = RLock()

    def get_client(
        self,
        phone_number_id: str,
    ) -> object:
        normalized_phone_number_id = (
            phone_number_id.strip()
        )

        if not normalized_phone_number_id:
            raise ValueError(
                "WhatsApp phone number id cannot be empty."
            )

        with self._lock:
            cached_client = self._graph_clients.get(
                normalized_phone_number_id
            )

            if cached_client is not None:
                return cached_client

            graph_client = self._graph_client_factory(
                normalized_phone_number_id
            )
            self._graph_clients[
                normalized_phone_number_id
            ] = graph_client

            return graph_client

    def _build_graph_client(
        self,
        phone_number_id: str,
    ) -> WhatsAppGraphClient:
        return WhatsAppGraphClient(
            access_token=self._access_token,
            phone_number_id=phone_number_id,
        )