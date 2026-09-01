from __future__ import annotations

import logging
from dataclasses import replace

import uvicorn
from fastapi import FastAPI

from chatbot.api.whatsapp_app import (
    build_whatsapp_api,
)
from chatbot.application import Bootstrap
from chatbot.application.tenant_registry import (
    TenantApplicationRegistry,
)
from chatbot.booking import (
    BookingRepository,
    BookingService,
    InMemoryBookingRepository,
    SQLiteBookingRepository,
    build_booking_configuration,
)
from chatbot.calendar import CalendarService
from chatbot.calendar.tenant_registry import (
    TenantCalendarRegistry,
)
from chatbot.capabilities.booking import (
    BookingCapability,
)
from chatbot.clients.registry import (
    build_client_instance,
    build_client_definition,
    build_instance_from_definition,
)
from chatbot.connectors.whatsapp.bootstrap import (
    WhatsAppGraphClientProtocol,
    build_tenant_whatsapp_message_handler,
    build_whatsapp_message_handler,
)
from chatbot.connectors.whatsapp.graph_client import (
    WhatsAppGraphClient,
    WhatsAppGraphClientProvider,
)
from chatbot.connectors.whatsapp.tenant_router import (
    WhatsAppTenantRouter,
)
from chatbot.connectors.whatsapp.signature import (
    WhatsAppSignatureVerifier,
)
from chatbot.infrastructure.config import (
    FlowForgeConfig,
)
from chatbot.instances import (
    InstanceDefinition,
    SQLiteInstanceDefinitionRepository,
)
from run_google_calendar import (
    build_calendar_service_factory,
    DEFAULT_CALENDAR_ID,
)


logger = logging.getLogger(__name__)


def build_booking_repository(
    config: FlowForgeConfig,
) -> SQLiteBookingRepository:
    """
    Build the persistent booking repository for production.
    """

    database_path = config.booking_database_path

    if database_path is None:
        raise ValueError(
            "Booking database path is not configured."
        )

    return SQLiteBookingRepository(
        database_path=database_path,
    )


def build_admin_repository(
    config: FlowForgeConfig,
) -> SQLiteInstanceDefinitionRepository:
    """
    Build the shared editable client repository.
    """

    database_path = config.admin_database_path

    if database_path is None:
        raise ValueError(
            "Admin database path is not configured."
        )

    return SQLiteInstanceDefinitionRepository(
        database_path=database_path,
    )


def is_runtime_client_active(
    *,
    client_id: str,
    instance_definition_repository: (
        SQLiteInstanceDefinitionRepository | None
    ),
) -> bool:
    """
    Return whether the configured client may answer messages.

    Built-in clients remain active until an editable definition
    explicitly changes their lifecycle status.
    """

    if instance_definition_repository is None:
        return True

    definition = instance_definition_repository.get(
        client_id
    )

    if definition is None:
        return True

    return (
        definition.metadata.get(
            "admin_status",
            "active",
        )
        == "active"
    )

def ensure_runtime_client_definition(
    *,
    config: FlowForgeConfig,
    instance_definition_repository: (
        SQLiteInstanceDefinitionRepository
    ),
):
    """
    Persist the configured legacy client for tenant routing.

    Existing editable definitions always take precedence over
    the built-in defaults.
    """

    existing_definition = (
        instance_definition_repository.get(
            config.client_id
        )
    )

    if existing_definition is not None:
        return existing_definition

    built_in_definition = build_client_definition(
        config.client_id
    )

    definition = replace(
        built_in_definition,
        whatsapp_phone_number_id=(
            config.whatsapp.phone_number_id
        ),
        calendar_id=DEFAULT_CALENDAR_ID,
    )

    instance_definition_repository.save(
        definition
    )

    return definition

def build_tenant_application(
    *,
    definition: InstanceDefinition,
    calendar_service: CalendarService | None,
    booking_repository: BookingRepository | None,
) -> object:
    """
    Build the isolated runtime application for one stored client.
    """

    instance = build_instance_from_definition(
        definition
    )
    capability_factories: dict[str, object] = {}

    if calendar_service is not None:
        if booking_repository is None:
            raise ValueError(
                "Booking repository is required with Calendar."
            )

        booking_configuration = (
            build_booking_configuration(
                instance
            )
        )

        booking_service = BookingService(
            repository=booking_repository,
            calendar_service=calendar_service,
            client_id=definition.id,
        )

        capability_factories["booking"] = (
            lambda: BookingCapability(
                booking_service=booking_service,
                business_hours=(
                    booking_configuration.business_hours
                ),
                booking_rules=(
                    booking_configuration.booking_rules
                ),
                services=(
                    booking_configuration.services
                ),
            )
        )
    else:
        instance = replace(
            instance,
            capabilities=[
                capability_name
                for capability_name in instance.capabilities
                if capability_name != "booking"
            ],
        )

    return Bootstrap(
        capability_factories=capability_factories,
    ).build_from_instance(
        instance
    )

def create_app(
    *,
    config: FlowForgeConfig,
    calendar_service: CalendarService | None,
    calendar_service_factory: object | None = None,
    graph_client: WhatsAppGraphClientProtocol,
    graph_client_provider: object | None = None,
    booking_repository: BookingRepository | None = None,
    instance_definition_repository: (
        SQLiteInstanceDefinitionRepository | None
    ) = None,
) -> FastAPI:
    """
    Build the FlowForge WhatsApp and administration application.

    Dependencies can be supplied explicitly so composition can be
    tested without connecting to Meta, Google Calendar or SQLite.

    Booking is removed from the runtime when Calendar is unavailable,
    while the remaining client capabilities continue working.
    """

    if instance_definition_repository is not None:
        ensure_runtime_client_definition(
            config=config,
            instance_definition_repository=(
                instance_definition_repository
            ),
        )
    instance = build_client_instance(
        config.client_id,
    )

    capability_factories: dict[str, object] = {}
    active_booking_repository: (
        BookingRepository | None
    ) = None

    if (
        calendar_service is None
        and calendar_service_factory is not None
    ):
        active_booking_repository = (
            booking_repository
            if booking_repository is not None
            else InMemoryBookingRepository()
        )

    if calendar_service is not None:
        booking_configuration = (
            build_booking_configuration(
                instance
            )
        )

        active_booking_repository = (
            booking_repository
            if booking_repository is not None
            else InMemoryBookingRepository()
        )

        booking_service = BookingService(
            repository=active_booking_repository,
            calendar_service=calendar_service,
        )

        capability_factories["booking"] = (
            lambda: BookingCapability(
                booking_service=booking_service,
                business_hours=(
                    booking_configuration.business_hours
                ),
                booking_rules=(
                    booking_configuration.booking_rules
                ),
                services=(
                    booking_configuration.services
                ),
            )
        )
    else:
        instance = replace(
            instance,
            capabilities=[
                capability_name
                for capability_name in instance.capabilities
                if capability_name != "booking"
            ],
        )

    bootstrap = Bootstrap(
        capability_factories=capability_factories,
    )

    application = bootstrap.build_from_instance(
        instance,
    )

    if instance_definition_repository is None:
        graph_message_handler = (
            build_whatsapp_message_handler(
                application=application,
                graph_client=graph_client,
                is_active=lambda: is_runtime_client_active(
                    client_id=config.client_id,
                    instance_definition_repository=None,
                ),
            )
        )
    else:
        tenant_calendar_registry = (
            TenantCalendarRegistry(
                calendar_service_factory=(
                    calendar_service_factory
                ),
            )
            if calendar_service_factory is not None
            else None
        )

        tenant_router = WhatsAppTenantRouter(
            instance_definition_repository=(
                instance_definition_repository
            ),
        )

        application_registry = (
            TenantApplicationRegistry(
                instance_definition_repository=(
                    instance_definition_repository
                ),
                application_factory=lambda definition: (
                    build_tenant_application(
                        definition=definition,
                        calendar_service=(
                            tenant_calendar_registry
                            .get_calendar_service(
                                definition.calendar_id
                            )
                            if (
                                tenant_calendar_registry
                                is not None
                                and definition.calendar_id
                                is not None
                            )
                            else calendar_service
                        ),
                        booking_repository=(
                            active_booking_repository
                        ),
                    )
                ),
            )
        )

        if graph_client_provider is None:
            graph_client_provider = (
                WhatsAppGraphClientProvider(
                    access_token=config.whatsapp.access_token,
                    graph_client_factory=lambda _phone_number_id: (
                        graph_client
                    ),
                )
            )

        graph_message_handler = (
            build_tenant_whatsapp_message_handler(
                tenant_router=tenant_router,
                application_registry=application_registry,
                graph_client_provider=graph_client_provider,
            )
        )

    signature_verifier = (
        WhatsAppSignatureVerifier(
            app_secret=(
                config.whatsapp.app_secret
            ),
        )
    )

    app = build_whatsapp_api(
        message_handler=graph_message_handler,
        verify_token=(
            config.whatsapp.verify_token
        ),
        signature_verifier=signature_verifier,
        instance_definition_repository=(
            instance_definition_repository
        ),
        admin_password=config.admin_password,
        admin_session_secret=config.admin_session_secret,
        admin_session_secure=True,
    )

    app.state.flowforge_instance = instance
    app.state.booking_repository = (
        active_booking_repository
    )
    app.state.instance_definition_repository = (
        instance_definition_repository
    )

    close_booking_repository = getattr(
        active_booking_repository,
        "close",
        None,
    )

    if callable(
        close_booking_repository
    ):
        app.router.add_event_handler(
            "shutdown",
            close_booking_repository,
        )

    close_instance_repository = getattr(
        instance_definition_repository,
        "close",
        None,
    )

    if callable(
        close_instance_repository
    ):
        app.router.add_event_handler(
            "shutdown",
            close_instance_repository,
        )

    return app


def create_production_app(
    *,
    config: FlowForgeConfig,
) -> FastAPI:
    """
    Build the production FlowForge application.

    The administration repository remains available even when Google
    Calendar credentials are unavailable. In that situation booking
    is disabled, but bots can still be viewed and configured.
    """

    try:
        calendar_service_factory = (
            build_calendar_service_factory()
        )
        calendar_service: CalendarService | None = None
    except FileNotFoundError as error:
        logger.warning(
            "Google Calendar credentials are unavailable. "
            "FlowForge will start without booking support: %s",
            error,
        )
        calendar_service = None
        calendar_service_factory = None

    graph_client = WhatsAppGraphClient(
        access_token=(
            config.whatsapp.access_token
        ),
        phone_number_id=(
            config.whatsapp.phone_number_id
        ),
    )

    graph_client_provider = (
        WhatsAppGraphClientProvider(
            access_token=config.whatsapp.access_token,
        )
    )

    booking_repository = (
        build_booking_repository(
            config
        )
        if calendar_service_factory is not None
        else None
    )

    instance_definition_repository = (
        build_admin_repository(
            config
        )
    )

    return create_app(
        config=config,
        calendar_service=calendar_service,
        calendar_service_factory=calendar_service_factory,
        graph_client=graph_client,
        graph_client_provider=graph_client_provider,
        booking_repository=booking_repository,
        instance_definition_repository=(
            instance_definition_repository
        ),
    )


def main(
) -> None:
    """
    Run the FlowForge HTTP server.
    """

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s %(levelname)s "
            "%(name)s: %(message)s"
        ),
    )

    config = FlowForgeConfig.load()

    app = create_production_app(
        config=config,
    )

    logger.info(
        "Starting FlowForge client: %s",
        config.client_id,
    )
    logger.info(
        "Booking database: %s",
        config.booking_database_path,
    )
    logger.info(
        "Admin database: %s",
        config.admin_database_path,
    )

    uvicorn.run(
        app,
        host=config.server.host,
        port=config.server.port,
    )


if __name__ == "__main__":
    main()