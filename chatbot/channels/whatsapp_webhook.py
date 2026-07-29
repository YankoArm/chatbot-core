from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class WhatsAppWebhookMessage:
    phone_number: str
    message_id: str
    text: str
    metadata: dict[str, Any]


class WhatsAppWebhookParser:
    def parse(
        self,
        payload: dict[str, Any],
    ) -> WhatsAppWebhookMessage | None:
        value = (
            payload["entry"][0]
            ["changes"][0]
            ["value"]
        )

        messages = value.get("messages")

        if not messages:
            return None

        message = messages[0]

        if message.get("type") != "text":
            return None

        provider_metadata: dict[str, Any] = {}

        contacts = value.get("contacts", [])

        if contacts:
            profile = contacts[0].get("profile", {})
            profile_name = profile.get("name")

            if profile_name is not None:
                provider_metadata["profile_name"] = profile_name

        webhook_metadata = value.get("metadata", {})
        phone_number_id = webhook_metadata.get("phone_number_id")

        if phone_number_id is not None:
            provider_metadata["phone_number_id"] = phone_number_id

        return WhatsAppWebhookMessage(
            phone_number=message["from"],
            message_id=message["id"],
            text=message["text"]["body"],
            metadata=provider_metadata,
        )