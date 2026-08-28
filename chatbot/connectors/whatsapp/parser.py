from __future__ import annotations

from chatbot.connectors.whatsapp.message_handler import (
    IncomingWhatsAppMessage,
)


class WhatsAppPayloadError(Exception):
    pass


class WhatsAppPayloadParser:
    def parse(
        self,
        payload: dict[str, object],
    ) -> IncomingWhatsAppMessage:
        message = self._extract_message(
            payload
        )

        return self._extract_text_message(
            message
        )

    def _extract_message(
        self,
        payload: dict[str, object],
    ) -> dict[str, object]:
        try:
            entry = payload["entry"]
            change = entry[0]["changes"][0]
            value = change["value"]
            message = value["messages"][0]

        except (
            KeyError,
            IndexError,
            TypeError,
        ) as exc:
            raise WhatsAppPayloadError(
                "WhatsApp payload does not contain a message"
            ) from exc

        return message

    def _extract_text_message(
        self,
        message: dict[str, object],
    ) -> IncomingWhatsAppMessage:
        try:
            user_id = message["from"]
            text = message["text"]["body"]

        except (
            KeyError,
            TypeError,
        ) as exc:
            raise WhatsAppPayloadError(
                "WhatsApp message is not a text message"
            ) from exc

        message_id = message.get(
            "id"
        )

        if not isinstance(user_id, str):
            raise WhatsAppPayloadError(
                "WhatsApp message sender is invalid"
            )

        if not isinstance(text, str):
            raise WhatsAppPayloadError(
                "WhatsApp message text is invalid"
            )

        if (
            message_id is not None
            and not isinstance(message_id, str)
        ):
            raise WhatsAppPayloadError(
                "WhatsApp message id is invalid"
            )

        return IncomingWhatsAppMessage(
            user_id=user_id,
            text=text,
            message_id=message_id,
        )