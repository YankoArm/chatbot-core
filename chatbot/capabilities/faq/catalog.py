from __future__ import annotations

import re
import unicodedata
from typing import Any

from chatbot.booking.services import (
    build_bookable_services,
)
from chatbot.language import Language


_CATALOG_KEYWORDS = {
    Language.ES: {
        "precio",
        "precios",
        "cuanto cuesta",
        "cuanto vale",
        "tarifa",
        "tarifas",
        "servicio",
        "servicios",
        "sesion",
        "sesiones",
    },
    Language.EN: {
        "price",
        "prices",
        "how much",
        "cost",
        "rates",
        "service",
        "services",
        "session",
        "sessions",
    },
}


def build_service_catalog_answer(
    *,
    services: Any,
    message: str,
    language: Language,
) -> str | None:
    """
    Build a conversational answer from the configured
    service catalog.

    The catalog is the source of truth for service names
    and prices. Invalid or absent catalogs are ignored so
    the normal FAQ mechanism can act as fallback.
    """

    normalized_message = _normalize_text(
        message
    )

    keywords = _CATALOG_KEYWORDS.get(
        language,
        set(),
    )

    if not any(
        keyword in normalized_message
        for keyword in keywords
    ):
        return None

    try:
        catalog = build_bookable_services(
            services
        )
    except (TypeError, ValueError):
        return None

    if not catalog:
        return None

    lines: list[str] = []

    for service in catalog:
        name = (
            service.name_en
            if language is Language.EN
            else service.name_es
        )

        price = _format_price(
            price_cents=service.price_cents,
            price_type=service.price_type,
            currency=service.currency,
            language=language,
        )

        lines.append(
            f"- {name} - {price}"
        )

    if language is Language.EN:
        return (
            "We currently offer:\n\n"
            + "\n".join(lines)
            + "\n\nWould you like to book one of these services?"
        )

    return (
        "Actualmente ofrecemos:\n\n"
        + "\n".join(lines)
        + "\n\n\u00bfQuieres reservar alguno de estos servicios?"
    )


def _format_price(
    *,
    price_cents: int,
    price_type: str,
    currency: str,
    language: Language,
) -> str:
    amount = price_cents / 100

    if language is Language.EN:
        amount_text = f"{amount:.2f}"

        if currency == "EUR":
            value = f"\u20ac{amount_text}"
        else:
            value = f"{amount_text} {currency}"

        if price_type == "from":
            return f"from {value}"

        return value

    amount_text = f"{amount:.2f}".replace(
        ".",
        ",",
    )

    if currency == "EUR":
        value = f"{amount_text} \u20ac"
    else:
        value = f"{amount_text} {currency}"

    if price_type == "from":
        return f"desde {value}"

    return value


def _normalize_text(
    text: str,
) -> str:
    normalized = unicodedata.normalize(
        "NFKD",
        text,
    )

    normalized = "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    )

    normalized = normalized.casefold()

    normalized = re.sub(
        r"[^a-z0-9\s]",
        " ",
        normalized,
    )

    return re.sub(
        r"\s+",
        " ",
        normalized,
    ).strip()
