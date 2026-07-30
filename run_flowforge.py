from __future__ import annotations

import uvicorn
from fastapi import FastAPI

from chatbot.api.whatsapp_app import build_whatsapp_api
from chatbot.application import Bootstrap
from chatbot.booking import (
    BookingService,
    InMemoryBookingRepository,
)
from chatbot.calendar import CalendarService
from chatbot.capabilities.booking import BookingCapability
from chatbot.connectors.whatsapp.bootstrap import (
    WhatsAppGraphClientProtocol,
    build_whatsapp_message_handler,
)
from chatbot.connectors.whatsapp.graph_client import WhatsAppGraphClient
from chatbot.connectors.whatsapp.signature import WhatsAppSignatureVerifier
from chatbot.infrastructure.config import FlowForgeConfig
from chatbot.instances import Instance
from run_google_calendar import build_calendar_service


def create_app(
    *,
    config: FlowForgeConfig,
    calendar_service: CalendarService,
    graph_client: WhatsAppGraphClientProtocol,
) -> FastAPI:
    """
    Build the production FlowForge WhatsApp application.

    Dependencies are received explicitly so the production
    composition can be tested without connecting to Meta or
    Google Calendar.
    """

    booking_repository = InMemoryBookingRepository()

    booking_service = BookingService(
        repository=booking_repository,
        calendar_service=calendar_service,
    )

    bootstrap = Bootstrap(
        capability_factories={
            "booking": lambda: BookingCapability(
                booking_service=booking_service,
            ),
        },
    )

    instance = Instance(
        id="flowforge-whatsapp",
        name="FlowForge WhatsApp",
        default_language="es",
        channels=["whatsapp"],
        capabilities=[
            "greeting",
            "booking",
        ],
    )

    application = bootstrap.build_from_instance(instance)

    graph_message_handler = build_whatsapp_message_handler(
        application=application,
        graph_client=graph_client,
    )

    signature_verifier = WhatsAppSignatureVerifier(
        app_secret=config.whatsapp.app_secret,
    )

    return build_whatsapp_api(
        message_handler=graph_message_handler,
        verify_token=config.whatsapp.verify_token,
        signature_verifier=signature_verifier,
    )


def create_production_app(
    *,
    config: FlowForgeConfig,
) -> FastAPI:
    """
    Build the production FlowForge application
    using the provided configuration.
    """

    calendar_service = build_calendar_service()

    graph_client = WhatsAppGraphClient(
        access_token=config.whatsapp.access_token,
        phone_number_id=config.whatsapp.phone_number_id,
    )

    return create_app(
        config=config,
        calendar_service=calendar_service,
        graph_client=graph_client,
    )


def main() -> None:
    """
    Run the FlowForge WhatsApp HTTP server.
    """

    config = FlowForgeConfig.load()

    app = create_production_app(
        config=config,
    )

    uvicorn.run(
        app,
        host=config.server.host,
        port=config.server.port,
    )


if __name__ == "__main__":
    main()