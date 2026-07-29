from __future__ import annotations

import os
from dataclasses import dataclass


class MissingConfigurationError(ValueError):
    pass


@dataclass(frozen=True)
class WhatsAppConfig:
    access_token: str
    phone_number_id: str
    verify_token: str
    app_secret: str

@dataclass(frozen=True)
class ServerConfig:
    host: str
    port: int

@dataclass(frozen=True)
class FlowForgeConfig:
    whatsapp: WhatsAppConfig
    server: ServerConfig

    @classmethod
    def load(cls) -> "FlowForgeConfig":
        return cls(
            whatsapp=WhatsAppConfig(
                access_token=_required_environment_variable(
                    "WHATSAPP_ACCESS_TOKEN"
                ),
                phone_number_id=_required_environment_variable(
                    "WHATSAPP_PHONE_NUMBER_ID"
                ),
                verify_token=_required_environment_variable(
                    "WHATSAPP_VERIFY_TOKEN"
                ),
                app_secret=_required_environment_variable(
                    "WHATSAPP_APP_SECRET"
                ),
            ),
            server=ServerConfig(
                host=os.getenv(
                    "FLOWFORGE_HOST",
                    "0.0.0.0",
                ),
                port=_environment_integer(
                    "FLOWFORGE_PORT",
                    _environment_integer(
                        "PORT",
                        8000,
                    ),
                ),
            ),
        )

def _required_environment_variable(
    name: str,
) -> str:
    value = os.getenv(name)

    if value is None or not value.strip():
        raise MissingConfigurationError(
            f"Missing required environment variable: {name}"
        )

    return value

def _environment_integer(
        name: str,
        default: int,
    ) -> int:
        raw_value = os.getenv(name)

        if raw_value is None or not raw_value.strip():
            return default

        try:
            value = int(raw_value)
        except ValueError as exc:
            raise MissingConfigurationError(
                f"{name} must be a valid integer"
            ) from exc

        if not 1 <= value <= 65535:
            raise MissingConfigurationError(
                f"{name} must be between 1 and 65535"
            )

        return value