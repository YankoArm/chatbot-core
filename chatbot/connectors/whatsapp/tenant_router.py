from __future__ import annotations

from typing import Protocol

from chatbot.connectors.whatsapp.message_handler import (
    IncomingWhatsAppMessage,
)
from chatbot.instances import (
    InstanceDefinition,
)


class InstanceDefinitionRepositoryProtocol(Protocol):
    def get_by_whatsapp_phone_number_id(
        self,
        phone_number_id: str,
    ) -> InstanceDefinition | None:
        ...


class WhatsAppTenantRouter:
    """
    Resolve incoming WhatsApp messages to active FlowForge clients.
    """

    def __init__(
        self,
        *,
        instance_definition_repository: (
            InstanceDefinitionRepositoryProtocol
        ),
    ) -> None:
        self._instance_definition_repository = (
            instance_definition_repository
        )

    def resolve_client_id(
        self,
        message: IncomingWhatsAppMessage,
    ) -> str | None:
        phone_number_id = message.phone_number_id

        if phone_number_id is None:
            return None

        definition = (
            self._instance_definition_repository
            .get_by_whatsapp_phone_number_id(
                phone_number_id
            )
        )

        if definition is None:
            return None

        if (
            definition.metadata.get(
                "admin_status",
                "active",
            )
            != "active"
        ):
            return None

        return definition.id