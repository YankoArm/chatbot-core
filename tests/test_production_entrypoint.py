from __future__ import annotations

from fastapi.testclient import TestClient

from chatbot.booking import (
    InMemoryBookingRepository,
    SQLiteBookingRepository,
)

from chatbot.instances import (
    SQLiteInstanceDefinitionRepository,
)

from chatbot.infrastructure.config import (
    FlowForgeConfig,
    ServerConfig,
    WhatsAppConfig,
)
from run_flowforge import (
    build_admin_repository,
    build_booking_repository,
    create_app,
    create_production_app,
)


class FakeCalendarService:
    def is_available(
        self,
        *,
        date: str,
        time: str,
        duration_minutes: int,
    ) -> bool:
        return True

    def create_booking(
        self,
        *,
        date: str,
        time: str,
        title: str,
        description: str | None = None,
        attendee: str | None = None,
        metadata: dict | None = None,
    ) -> str:
        return "booking-test-id"

    def cancel_booking(
        self,
        booking_id: str,
    ) -> None:
        return None


class FakeWhatsAppGraphClient:
    def send_text_message(
        self,
        *,
        to: str,
        text: str,
    ) -> object:
        return object()


def test_create_app_builds_production_whatsapp_api() -> None:
    config = FlowForgeConfig(
        whatsapp=WhatsAppConfig(
            access_token="test-access-token",
            phone_number_id="test-phone-number-id",
            verify_token="test-verify-token",
            app_secret="test-app-secret",
        ),
        server=ServerConfig(
            host="127.0.0.1",
            port=8000,
        ),
    )

    app = create_app(
        config=config,
        calendar_service=FakeCalendarService(),
        graph_client=FakeWhatsAppGraphClient(),
    )

    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "flowforge-whatsapp",
    }

def test_create_app_verifies_whatsapp_webhook() -> None:
    config = FlowForgeConfig(
        whatsapp=WhatsAppConfig(
            access_token="test-access-token",
            phone_number_id="test-phone-number-id",
            verify_token="my-secret-token",
            app_secret="test-app-secret",
        ),
        server=ServerConfig(
            host="127.0.0.1",
            port=8000,
        ),
    )

    app = create_app(
        config=config,
        calendar_service=FakeCalendarService(),
        graph_client=FakeWhatsAppGraphClient(),
    )

    client = TestClient(app)

    response = client.get(
        "/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "my-secret-token",
            "hub.challenge": "123456",
        },
    )

    assert response.status_code == 200
    assert response.text == "123456"

def test_create_app_uses_configured_client_instance() -> None:
    config = FlowForgeConfig(
        whatsapp=WhatsAppConfig(
            access_token="test-access-token",
            phone_number_id="test-phone-number-id",
            verify_token="test-verify-token",
            app_secret="test-app-secret",
        ),
        server=ServerConfig(
            host="127.0.0.1",
            port=8000,
        ),
        client_id="hairdressing_demo",
    )

    app = create_app(
        config=config,
        calendar_service=FakeCalendarService(),
        graph_client=FakeWhatsAppGraphClient(),
    )

    assert app.state.flowforge_instance.id == (
        "hairdressing_demo"
    )
    assert app.state.flowforge_instance.name == (
        "Salón Estilo"
    )
    assert app.state.flowforge_instance.template_id == (
        "hairdressing"
    )
    assert app.state.flowforge_instance.capabilities == [
        "greeting",
        "faq",
        "booking",
        "help",
        "human_transfer",
    ]

def test_build_booking_repository_uses_configured_sqlite_path(
    tmp_path,
) -> None:
    database_path = (
        tmp_path
        / "production-bookings.sqlite3"
    )

    config = FlowForgeConfig(
        whatsapp=WhatsAppConfig(
            access_token="test-access-token",
            phone_number_id="test-phone-number-id",
            verify_token="test-verify-token",
            app_secret="test-app-secret",
        ),
        server=ServerConfig(
            host="127.0.0.1",
            port=8000,
        ),
        client_id="hairdressing_demo",
        booking_database_path=str(
            database_path
        ),
    )

    repository = build_booking_repository(
        config
    )

    assert isinstance(
        repository,
        SQLiteBookingRepository,
    )
    assert database_path.exists()

    repository.close()


def test_create_app_uses_provided_booking_repository() -> None:
    config = FlowForgeConfig(
        whatsapp=WhatsAppConfig(
            access_token="test-access-token",
            phone_number_id="test-phone-number-id",
            verify_token="test-verify-token",
            app_secret="test-app-secret",
        ),
        server=ServerConfig(
            host="127.0.0.1",
            port=8000,
        ),
    )
    repository = InMemoryBookingRepository()

    app = create_app(
        config=config,
        calendar_service=FakeCalendarService(),
        graph_client=FakeWhatsAppGraphClient(),
        booking_repository=repository,
    )

    assert app.state.booking_repository is repository

class ClosableBookingRepository(
    InMemoryBookingRepository
):
    def __init__(
        self,
    ) -> None:
        super().__init__()
        self.closed = False

    def close(
        self,
    ) -> None:
        self.closed = True


def test_create_app_closes_booking_repository_on_shutdown(
) -> None:
    config = FlowForgeConfig(
        whatsapp=WhatsAppConfig(
            access_token="test-access-token",
            phone_number_id="test-phone-number-id",
            verify_token="test-verify-token",
            app_secret="test-app-secret",
        ),
        server=ServerConfig(
            host="127.0.0.1",
            port=8000,
        ),
        client_id="hairdressing_demo",
    )
    repository = ClosableBookingRepository()

    app = create_app(
        config=config,
        calendar_service=FakeCalendarService(),
        graph_client=FakeWhatsAppGraphClient(),
        booking_repository=repository,
    )

    assert repository.closed is False

    with TestClient(
        app
    ):
        pass

    assert repository.closed is True

def test_build_admin_repository_uses_configured_sqlite_path(
    tmp_path,
) -> None:
    database_path = (
        tmp_path
        / "flowforge-admin.sqlite3"
    )

    config = FlowForgeConfig(
        whatsapp=WhatsAppConfig(
            access_token="test-access-token",
            phone_number_id="test-phone-number-id",
            verify_token="test-verify-token",
            app_secret="test-app-secret",
        ),
        server=ServerConfig(
            host="127.0.0.1",
            port=8000,
        ),
        admin_database_path=str(
            database_path
        ),
    )

    repository = build_admin_repository(
        config
    )

    assert isinstance(
        repository,
        SQLiteInstanceDefinitionRepository,
    )
    assert database_path.exists()

    repository.close()


def test_create_app_uses_provided_admin_repository(
) -> None:
    admin_repository = (
        SQLiteInstanceDefinitionRepository(
            database_path=":memory:",
        )
    )

    config = FlowForgeConfig(
        whatsapp=WhatsAppConfig(
            access_token="test-access-token",
            phone_number_id="test-phone-number-id",
            verify_token="test-verify-token",
            app_secret="test-app-secret",
        ),
        server=ServerConfig(
            host="127.0.0.1",
            port=8000,
        ),
    )

    app = create_app(
        config=config,
        calendar_service=FakeCalendarService(),
        graph_client=FakeWhatsAppGraphClient(),
        instance_definition_repository=(
            admin_repository
        ),
    )

    assert (
        app.state.instance_definition_repository
        is admin_repository
    )

    admin_repository.close()
def test_runtime_client_availability_uses_stored_lifecycle_status(
) -> None:
    from chatbot.instances import InstanceDefinition
    from run_flowforge import (
        is_runtime_client_active,
    )

    repository = (
        SQLiteInstanceDefinitionRepository(
            database_path=":memory:",
        )
    )
    repository.save(
        InstanceDefinition(
            id="hairdressing_demo",
            name="Salón Estilo",
            template_id="hairdressing",
            metadata={
                "admin_status": "paused",
            },
        )
    )

    assert is_runtime_client_active(
        client_id="hairdressing_demo",
        instance_definition_repository=repository,
    ) is False

    repository.close()
def test_runtime_seed_registers_configured_client_for_tenant_routing(
) -> None:
    from run_flowforge import (
        ensure_runtime_client_definition,
    )

    repository = SQLiteInstanceDefinitionRepository(
        database_path=":memory:",
    )
    config = FlowForgeConfig(
        whatsapp=WhatsAppConfig(
            access_token="test-access-token",
            phone_number_id="test-phone-number-id",
            verify_token="test-verify-token",
            app_secret="test-app-secret",
        ),
        server=ServerConfig(
            host="127.0.0.1",
            port=8000,
        ),
        client_id="hairdressing_demo",
    )

    definition = ensure_runtime_client_definition(
        config=config,
        instance_definition_repository=repository,
    )

    assert definition.id == "hairdressing_demo"
    assert definition.whatsapp_phone_number_id == (
        "test-phone-number-id"
    )
    assert definition.calendar_id == "primary"

    stored_definition = repository.get(
        "hairdressing_demo"
    )
    assert stored_definition == definition

    repository.close()
def test_create_app_seeds_configured_client_when_repository_is_provided(
) -> None:
    repository = SQLiteInstanceDefinitionRepository(
        database_path=":memory:",
    )
    config = FlowForgeConfig(
        whatsapp=WhatsAppConfig(
            access_token="test-access-token",
            phone_number_id="test-phone-number-id",
            verify_token="test-verify-token",
            app_secret="test-app-secret",
        ),
        server=ServerConfig(
            host="127.0.0.1",
            port=8000,
        ),
        client_id="hairdressing_demo",
    )

    create_app(
        config=config,
        calendar_service=None,
        graph_client=FakeWhatsAppGraphClient(),
        instance_definition_repository=repository,
    )

    definition = repository.get(
        "hairdressing_demo"
    )

    assert definition is not None
    assert definition.whatsapp_phone_number_id == (
        "test-phone-number-id"
    )

    repository.close()

def test_create_production_app_accepts_admin_configuration(
    monkeypatch,
) -> None:
    def missing_calendar_credentials():
        raise FileNotFoundError("test: no Google credentials")

    monkeypatch.setattr(
        "run_flowforge.build_calendar_service_factory",
        missing_calendar_credentials,
    )

    config = FlowForgeConfig(
        whatsapp=WhatsAppConfig(
            access_token="test-access-token",
            phone_number_id="test-phone-number-id",
            verify_token="test-verify-token",
            app_secret="test-app-secret",
        ),
        server=ServerConfig(
            host="127.0.0.1",
            port=8000,
        ),
        admin_password="test-admin-password",
        admin_session_secret="test-admin-session-secret",
    )

    app = create_production_app(config=config)

    assert app is not None
