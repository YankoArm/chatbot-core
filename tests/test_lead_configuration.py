from chatbot.infrastructure.config import (
    FlowForgeConfig,
    ServerConfig,
    WhatsAppConfig,
)


def build_config(
    **overrides,
) -> FlowForgeConfig:
    values = {
        "whatsapp": WhatsAppConfig(
            access_token="token",
            phone_number_id="phone-id",
            verify_token="verify-token",
            app_secret="app-secret",
        ),
        "server": ServerConfig(
            host="127.0.0.1",
            port=8000,
        ),
    }
    values.update(overrides)

    return FlowForgeConfig(**values)


def test_lead_database_path_defaults_to_shared_sqlite():
    config = build_config()

    assert config.lead_database_path == (
        "data/flowforge_leads.sqlite3"
    )


def test_lead_database_path_accepts_custom_value():
    config = build_config(
        lead_database_path=" persistent/leads.sqlite3 ",
    )

    assert config.lead_database_path == (
        "persistent/leads.sqlite3"
    )
