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
        value = self._extract_value(
            payload
        )
        message = self._extract_message(
            value
        )
        phone_number_id = (
            self._extract_phone_number_id(
                value
            )
        )

        return self._extract_text_message(
            message,
            phone_number_id=phone_number_id,
        )

    def _extract_value(
        self,
        payload: dict[str, object],
    ) -> dict[str, object]:
        try:
            entry = payload["entry"]
            change = entry[0]["changes"][0]
            value = change["value"]

        except (
            KeyError,
            IndexError,
            TypeError,
        ) as exc:
            raise WhatsAppPayloadError(
                "WhatsApp payload does not contain a message"
            ) from exc

        if not isinstance(value, dict):
            raise WhatsAppPayloadError(
                "WhatsApp payload does not contain a message"
            )

        return value

    def _extract_message(
        self,
        value: dict[str, object],
    ) -> dict[str, object]:
        try:
            message = value["messages"][0]

        except (
            KeyError,
            IndexError,
            TypeError,
        ) as exc:
            raise WhatsAppPayloadError(
                "WhatsApp payload does not contain a message"
            ) from exc

        if not isinstance(message, dict):
            raise WhatsAppPayloadError(
                "WhatsApp payload does not contain a message"
            )

        return message

    def _extract_phone_number_id(
        self,
        value: dict[str, object],
    ) -> str | None:
        metadata = value.get(
            "metadata"
        )

        if metadata is None:
            return None

        if not isinstance(metadata, dict):
            raise WhatsAppPayloadError(
                "WhatsApp payload metadata is invalid"
            )

        phone_number_id = metadata.get(
            "phone_number_id"
        )

        if phone_number_id is None:
            return None

        if not isinstance(phone_number_id, str):
            raise WhatsAppPayloadError(
                "WhatsApp phone number id is invalid"
            )

        return phone_number_id

    def _extract_text_message(
        self,
        message: dict[str, object],
        *,
        phone_number_id: str | None,
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
            phone_number_id=phone_number_id,
        )