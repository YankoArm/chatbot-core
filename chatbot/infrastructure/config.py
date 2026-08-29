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
    client_id: str = "tarot_alvin"
    booking_database_path: str | None = None
    admin_database_path: str | None = None

    def __post_init__(
        self,
    ) -> None:
        """
        Resolve persistent database paths when omitted.
        """

        booking_database_path = (
            self.booking_database_path
        )

        if (
            booking_database_path is None
            or not booking_database_path.strip()
        ):
            booking_database_path = (
                f"data/{self.client_id}_bookings.sqlite3"
            )
        else:
            booking_database_path = (
                booking_database_path.strip()
            )

        admin_database_path = (
            self.admin_database_path
        )

        if (
            admin_database_path is None
            or not admin_database_path.strip()
        ):
            admin_database_path = (
                "data/flowforge_admin.sqlite3"
            )
        else:
            admin_database_path = (
                admin_database_path.strip()
            )

        object.__setattr__(
            self,
            "booking_database_path",
            booking_database_path,
        )
        object.__setattr__(
            self,
            "admin_database_path",
            admin_database_path,
        )

    @classmethod
    def load(
        cls,
    ) -> "FlowForgeConfig":
        client_id = _environment_text(
            "FLOWFORGE_CLIENT_ID",
            "tarot_alvin",
        )

        booking_database_path = os.getenv(
            "FLOWFORGE_BOOKING_DATABASE_PATH"
        )
        admin_database_path = os.getenv(
            "FLOWFORGE_ADMIN_DATABASE_PATH"
        )

        return cls(
            whatsapp=WhatsAppConfig(
                access_token=(
                    _required_environment_variable(
                        "WHATSAPP_ACCESS_TOKEN"
                    )
                ),
                phone_number_id=(
                    _required_environment_variable(
                        "WHATSAPP_PHONE_NUMBER_ID"
                    )
                ),
                verify_token=(
                    _required_environment_variable(
                        "WHATSAPP_VERIFY_TOKEN"
                    )
                ),
                app_secret=(
                    _required_environment_variable(
                        "WHATSAPP_APP_SECRET"
                    )
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
            client_id=client_id,
            booking_database_path=(
                booking_database_path
            ),
            admin_database_path=(
                admin_database_path
            ),
        )


def _required_environment_variable(
    name: str,
) -> str:
    value = os.getenv(
        name
    )

    if value is None or not value.strip():
        raise MissingConfigurationError(
            f"Missing required environment variable: {name}"
        )

    return value


def _environment_integer(
    name: str,
    default: int,
) -> int:
    raw_value = os.getenv(
        name
    )

    if (
        raw_value is None
        or not raw_value.strip()
    ):
        return default

    try:
        value = int(
            raw_value
        )
    except ValueError as exc:
        raise MissingConfigurationError(
            f"{name} must be a valid integer"
        ) from exc

    if not 1 <= value <= 65535:
        raise MissingConfigurationError(
            f"{name} must be between 1 and 65535"
        )

    return value


def _environment_text(
    name: str,
    default: str,
) -> str:
    raw_value = os.getenv(
        name
    )

    if (
        raw_value is None
        or not raw_value.strip()
    ):
        return default

    return raw_value.strip()