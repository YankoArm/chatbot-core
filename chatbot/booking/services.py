from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class BookableService:
    """
    Validated service that can be selected during a booking.
    """

    id: str
    name_es: str
    name_en: str
    duration_minutes: int
    price_type: str
    price_cents: int
    currency: str


def build_bookable_services(
    value: Any,
) -> tuple[BookableService, ...]:
    """
    Build and validate bookable services from instance settings.
    """

    if value is None:
        return ()

    if not isinstance(value, list):
        raise ValueError(
            "Instance services must be a list."
        )

    services: list[BookableService] = []
    registered_ids: set[str] = set()

    for index, raw_service in enumerate(value):
        if not isinstance(raw_service, dict):
            raise ValueError(
                "Each instance service must be a dictionary."
            )

        service_id = _require_string(
            raw_service,
            "id",
            prefix=f"services[{index}]",
        )

        if service_id in registered_ids:
            raise ValueError(
                "Duplicate instance service id: "
                f"{service_id!r}."
            )

        raw_name = raw_service.get("name")

        if not isinstance(raw_name, dict):
            raise ValueError(
                f"services[{index}].name must be a dictionary."
            )

        name_es = _require_string(
            raw_name,
            "es",
            prefix=f"services[{index}].name",
        )

        name_en = _require_string(
            raw_name,
            "en",
            prefix=f"services[{index}].name",
        )

        duration_minutes = _require_positive_integer(
            raw_service,
            "duration_minutes",
            prefix=f"services[{index}]",
        )

        raw_price = raw_service.get("price")

        if not isinstance(raw_price, dict):
            raise ValueError(
                f"services[{index}].price must be a dictionary."
            )

        price_type = _require_string(
            raw_price,
            "type",
            prefix=f"services[{index}].price",
        )

        if price_type not in {
            "fixed",
            "from",
        }:
            raise ValueError(
                f"services[{index}].price.type must be "
                "'fixed' or 'from'."
            )

        price_cents = _require_positive_integer(
            raw_price,
            "amount_cents",
            prefix=f"services[{index}].price",
        )

        currency = _require_string(
            raw_price,
            "currency",
            prefix=f"services[{index}].price",
        ).upper()

        if len(currency) != 3:
            raise ValueError(
                f"services[{index}].price.currency "
                "must contain three letters."
            )

        services.append(
            BookableService(
                id=service_id,
                name_es=name_es,
                name_en=name_en,
                duration_minutes=duration_minutes,
                price_type=price_type,
                price_cents=price_cents,
                currency=currency,
            )
        )

        registered_ids.add(service_id)

    return tuple(services)


def _require_string(
    settings: dict[str, Any],
    key: str,
    *,
    prefix: str,
) -> str:
    value = settings.get(key)

    if not isinstance(value, str):
        raise ValueError(
            f"{prefix}.{key} must be a string."
        )

    normalized_value = value.strip()

    if not normalized_value:
        raise ValueError(
            f"{prefix}.{key} cannot be empty."
        )

    return normalized_value


def _require_positive_integer(
    settings: dict[str, Any],
    key: str,
    *,
    prefix: str,
) -> int:
    value = settings.get(key)

    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value <= 0
    ):
        raise ValueError(
            f"{prefix}.{key} must be a positive integer."
        )

    return value