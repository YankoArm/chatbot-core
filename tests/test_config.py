import os

import pytest

from chatbot.infrastructure.config import (
    FlowForgeConfig,
    MissingConfigurationError,
)

def test_load_config_from_environment() -> None:
    os.environ["WHATSAPP_ACCESS_TOKEN"] = "token"
    os.environ["WHATSAPP_PHONE_NUMBER_ID"] = "phone"
    os.environ["WHATSAPP_VERIFY_TOKEN"] = "verify"
    os.environ["WHATSAPP_APP_SECRET"] = "secret"

    config = FlowForgeConfig.load()

    assert config.whatsapp.access_token == "token"
    assert config.whatsapp.phone_number_id == "phone"
    assert config.whatsapp.verify_token == "verify"
    assert config.whatsapp.app_secret == "secret"

def test_load_server_config_with_defaults() -> None:
    os.environ["WHATSAPP_ACCESS_TOKEN"] = "token"
    os.environ["WHATSAPP_PHONE_NUMBER_ID"] = "phone"
    os.environ["WHATSAPP_VERIFY_TOKEN"] = "verify"
    os.environ["WHATSAPP_APP_SECRET"] = "secret"

    config = FlowForgeConfig.load()

    assert config.server.host == "0.0.0.0"
    assert config.server.port == 8000

def test_load_server_config_from_environment() -> None:
    os.environ["WHATSAPP_ACCESS_TOKEN"] = "token"
    os.environ["WHATSAPP_PHONE_NUMBER_ID"] = "phone"
    os.environ["WHATSAPP_VERIFY_TOKEN"] = "verify"
    os.environ["WHATSAPP_APP_SECRET"] = "secret"

    os.environ["FLOWFORGE_HOST"] = "127.0.0.1"
    os.environ["FLOWFORGE_PORT"] = "9000"

    config = FlowForgeConfig.load()

    assert config.server.host == "127.0.0.1"
    assert config.server.port == 9000

def test_reject_invalid_server_port() -> None:
    os.environ["WHATSAPP_ACCESS_TOKEN"] = "token"
    os.environ["WHATSAPP_PHONE_NUMBER_ID"] = "phone"
    os.environ["WHATSAPP_VERIFY_TOKEN"] = "verify"
    os.environ["WHATSAPP_APP_SECRET"] = "secret"

    os.environ["FLOWFORGE_PORT"] = "not-a-number"

    with pytest.raises(
        MissingConfigurationError,
        match="FLOWFORGE_PORT must be a valid integer",
    ):
        FlowForgeConfig.load()

def test_reject_missing_whatsapp_access_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(
        "WHATSAPP_ACCESS_TOKEN",
        raising=False,
    )
    monkeypatch.setenv(
        "WHATSAPP_PHONE_NUMBER_ID",
        "phone",
    )
    monkeypatch.setenv(
        "WHATSAPP_VERIFY_TOKEN",
        "verify",
    )
    monkeypatch.setenv(
        "WHATSAPP_APP_SECRET",
        "secret",
    )

    with pytest.raises(
        MissingConfigurationError,
        match=(
            "Missing required environment variable: "
            "WHATSAPP_ACCESS_TOKEN"
        ),
    ):
        FlowForgeConfig.load()

@pytest.mark.parametrize(
    "port_value",
    [
        "0",
        "-1",
        "65536",
    ],
)
def test_reject_server_port_out_of_range(
    monkeypatch: pytest.MonkeyPatch,
    port_value: str,
) -> None:
    monkeypatch.setenv(
        "WHATSAPP_ACCESS_TOKEN",
        "token",
    )
    monkeypatch.setenv(
        "WHATSAPP_PHONE_NUMBER_ID",
        "phone",
    )
    monkeypatch.setenv(
        "WHATSAPP_VERIFY_TOKEN",
        "verify",
    )
    monkeypatch.setenv(
        "WHATSAPP_APP_SECRET",
        "secret",
    )
    monkeypatch.setenv(
        "FLOWFORGE_PORT",
        port_value,
    )

    with pytest.raises(
        MissingConfigurationError,
        match="FLOWFORGE_PORT must be between 1 and 65535",
    ):
        FlowForgeConfig.load()

def test_load_default_client_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "WHATSAPP_ACCESS_TOKEN",
        "token",
    )
    monkeypatch.setenv(
        "WHATSAPP_PHONE_NUMBER_ID",
        "phone",
    )
    monkeypatch.setenv(
        "WHATSAPP_VERIFY_TOKEN",
        "verify",
    )
    monkeypatch.setenv(
        "WHATSAPP_APP_SECRET",
        "secret",
    )
    monkeypatch.setenv(
        "FLOWFORGE_PORT",
        "8000",
    )
    monkeypatch.delenv(
        "FLOWFORGE_CLIENT_ID",
        raising=False,
    )

    config = FlowForgeConfig.load()

    assert config.client_id == "tarot_alvin"


def test_load_client_id_from_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "WHATSAPP_ACCESS_TOKEN",
        "token",
    )
    monkeypatch.setenv(
        "WHATSAPP_PHONE_NUMBER_ID",
        "phone",
    )
    monkeypatch.setenv(
        "WHATSAPP_VERIFY_TOKEN",
        "verify",
    )
    monkeypatch.setenv(
        "WHATSAPP_APP_SECRET",
        "secret",
    )
    monkeypatch.setenv(
        "FLOWFORGE_PORT",
        "8000",
    )
    monkeypatch.setenv(
        "FLOWFORGE_CLIENT_ID",
        "hairdressing_demo",
    )

    config = FlowForgeConfig.load()

    assert config.client_id == "hairdressing_demo"