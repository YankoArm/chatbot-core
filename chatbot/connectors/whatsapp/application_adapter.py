from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from chatbot.connectors.whatsapp.message_handler import (
    IncomingWhatsAppMessage,
)
from chatbot.responses import Response


class FlowForgeApplicationProtocol(Protocol):
    def chat(
        self,
        session_id: str,
        message: str,
    ) -> Response:
        ...


class FlowForgeWhatsAppAdapter:
    """
    Adapt WhatsApp messages to the FlowForge application interface.

    The WhatsApp user identifier is used as the conversation session
    identifier so subsequent messages from the same phone number reuse
    the same conversation context.
    """

    def __init__(
        self,
        application: FlowForgeApplicationProtocol,
        is_active: Callable[[], bool] | None = None,
    ) -> None:
        self._application = application
        self._is_active = is_active or (
            lambda: True
        )

    def handle(
        self,
        message: IncomingWhatsAppMessage,
    ) -> str | None:
        if not self._is_active():
            return None

        response = self._application.chat(
            session_id=message.user_id,
            message=message.text,
        )

        return response.text
class WhatsAppTenantRouterProtocol(Protocol):
    def resolve_client_id(
        self,
        message: IncomingWhatsAppMessage,
    ) -> str | None:
        ...


class TenantApplicationRegistryProtocol(Protocol):
    def get_application(
        self,
        client_id: str,
    ) -> FlowForgeApplicationProtocol | None:
        ...


class TenantFlowForgeWhatsAppAdapter:
    """
    Route each incoming WhatsApp message to its client runtime.
    """

    def __init__(
        self,
        *,
        tenant_router: WhatsAppTenantRouterProtocol,
        application_registry: (
            TenantApplicationRegistryProtocol
        ),
    ) -> None:
        self._tenant_router = tenant_router
        self._application_registry = (
            application_registry
        )

    def handle(
        self,
        message: IncomingWhatsAppMessage,
    ) -> str | None:
        client_id = self._tenant_router.resolve_client_id(
            message
        )

        if client_id is None:
            return None

        application = (
            self._application_registry.get_application(
                client_id
            )
        )

        if application is None:
            return None

        response = application.chat(
            session_id=message.user_id,
            message=message.text,
        )

        return response.text