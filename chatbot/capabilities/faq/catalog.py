from __future__ import annotations

import re
import unicodedata
from typing import Any

from chatbot.booking.services import build_bookable_services
from chatbot.language import Language


_CATALOG_KEYWORDS = {
    Language.ES: {
        "precio", "precios", "cuanto cuesta", "cuanto vale",
        "tarifa", "tarifas", "servicio", "servicios",
        "sesion", "sesiones",
    },
    Language.EN: {
        "price", "prices", "how much", "cost", "rates",
        "service", "services", "session", "sessions",
    },
}

_PERIOD_LABELS = {
    Language.ES: {
        "once": "",
        "week": " / semana",
        "month": " / mes",
        "quarter": " / trimestre",
        "year": " / a\u00f1o",
    },
    Language.EN: {
        "once": "",
        "week": " / week",
        "month": " / month",
        "quarter": " / quarter",
        "year": " / year",
    },
}


def build_service_catalog_answer(
    *,
    services: Any,
    message: str,
    language: Language,
) -> str | None:
    """
    Show the complete catalog, including non-bookable services.

    Validate common service data with the shared validator.
    Preserve the existing presentation for appointment catalogs.
    """
    normalized_message = _normalize_text(message)
    keywords = _CATALOG_KEYWORDS.get(language, set())

    if not any(keyword in normalized_message for keyword in keywords):
        return None

    try:
        # Validate all entries and obtain the appointment subset.
        appointments = build_bookable_services(services)

        if not services:
            return None

        periods = _PERIOD_LABELS[language]
        lines: list[str] = []

        for raw_service in services:
            service_type = raw_service.get(
                "service_type", "appointment"
            )
            names = raw_service["name"]
            name = (
                names["en"].strip()
                if language is Language.EN
                else names["es"].strip()
            )
            raw_price = raw_service["price"]
            period = raw_price.get("billing_period", "once")

            if not isinstance(period, str) or period not in periods:
                return None

            if service_type == "recurring":
                if period == "once":
                    return None
            elif period != "once":
                return None

            duration_text = raw_service.get("duration_text", "")
            if duration_text is None:
                duration_text = ""
            if not isinstance(duration_text, str):
                return None
            duration_text = duration_text.strip()
            if len(duration_text) > 200:
                return None

            price = _format_price(
                price_cents=raw_price["amount_cents"],
                price_type=raw_price["type"].strip(),
                currency=raw_price["currency"].strip().upper(),
                language=language,
            )
            line = f"- {name} - {price}{periods[period]}"

            if duration_text:
                line += f" - {duration_text}"
            elif service_type != "appointment":
                line += (
                    " - Delivery/duration on request"
                    if language is Language.EN
                    else " - Plazo a consultar"
                )

            lines.append(line)

    except (TypeError, ValueError, KeyError):
        return None

    if language is Language.EN:
        if len(appointments) == len(services):
            closing = "Would you like to book one of these services?"
        elif appointments:
            closing = (
                "Would you like more information or to book an appointment?"
            )
        else:
            closing = "Would you like more information about these services?"

        return (
            "We currently offer:\n\n"
            + "\n".join(lines)
            + "\n\n"
            + closing
        )

    if len(appointments) == len(services):
        closing = "\u00bfQuieres reservar alguno de estos servicios?"
    elif appointments:
        closing = (
            "\u00bfQuieres m\u00e1s informaci\u00f3n "
            "o reservar una cita?"
        )
    else:
        closing = (
            "\u00bfQuieres solicitar m\u00e1s informaci\u00f3n "
            "sobre estos servicios?"
        )

    return (
        "Actualmente ofrecemos:\n\n"
        + "\n".join(lines)
        + "\n\n"
        + closing
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

    amount_text = f"{amount:.2f}".replace(".", ",")

    if currency == "EUR":
        value = f"{amount_text} \u20ac"
    else:
        value = f"{amount_text} {currency}"

    if price_type == "from":
        return f"desde {value}"

    return value


def _normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    normalized = "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    )
    normalized = normalized.casefold()
    normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()
