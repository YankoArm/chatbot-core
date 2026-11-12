from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from chatbot.connectors.whatsapp.message_handler import (
    IncomingWhatsAppMessage,
    WhatsAppButtonReply,
)
from chatbot.capabilities.greeting import GreetingCapability
from chatbot.language import Language
from chatbot.responses import Response


_MENU_BUTTONS = {
    Language.ES: {
        "services": ("ff_menu_prices_es", "Ver precios"),
        "booking": ("ff_menu_booking_es", "Reservar cita"),
        "human_transfer": ("ff_menu_human_es", "Hablar con alguien"),
    },
    Language.EN: {
        "services": ("ff_menu_prices_en", "View prices"),
        "booking": ("ff_menu_booking_en", "Book appointment"),
        "human_transfer": ("ff_menu_human_en", "Talk to someone"),
    },
}


def _format_tenant_reply(
    application: FlowForgeApplicationProtocol,
    session_id: str,
    response: Response,
) -> str | WhatsAppButtonReply:
    metadata = getattr(response, "metadata", None)
    if not isinstance(metadata, dict):
        return response.text

    activated = metadata.get("activation_succeeded") is True
    if not activated and metadata.get("capability") != "greeting":
        return response.text

    store = getattr(application, "conversation_store", None)
    if store is None:
        return response.text

    context = store.get(session_id)
    knowledge = getattr(context, "knowledge_service", None)
    if knowledge is None:
        return response.text

    try:
        greetings = knowledge.get_section("greetings", {})
    except FileNotFoundError:
        return response.text

    if not isinstance(greetings, dict):
        return response.text

    menu = greetings.get("menu")
    if not isinstance(menu, dict) or menu.get("enabled") is not True:
        return response.text

    items = menu.get("items")
    if not isinstance(items, dict):
        return response.text

    language = (
        Language.EN if metadata.get("language") == "en" else Language.ES
    )
    buttons = tuple(
        button
        for key, button in _MENU_BUTTONS[language].items()
        if items.get(key) is True
    )

    suffix = GreetingCapability._append_guided_menu(
        response_text="",
        greetings=greetings,
        language=language,
    )

    if not buttons:
        return response.text + suffix if activated else response.text

    body = response.text if activated else response.text.removesuffix(suffix)
    if items.get("faq") is True:
        body += (
            "\n\nYou can also type your question."
            if language is Language.EN
            else "\n\nTambi\u00e9n puedes escribir tu pregunta."
        )

    fallback = response.text + suffix if activated else response.text
    if len(body) > 1024:
        return fallback

    return WhatsAppButtonReply(
        text=body,
        buttons=buttons,
        fallback_text=fallback,
    )


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
    ) -> str | WhatsAppButtonReply | None:
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

        return _format_tenant_reply(
            application=application,
            session_id=message.user_id,
            response=response,
        )
