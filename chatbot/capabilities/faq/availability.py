from __future__ import annotations

from typing import Any

from chatbot.capabilities.faq.catalog import _normalize_text
from chatbot.language import Language


def build_availability_answer(
    *,
    availability: Any,
    message: str,
    language: Language,
) -> str | None:
    if not isinstance(availability, dict) or not availability:
        return None

    normalized = _normalize_text(message)
    if not any(
        phrase in normalized
        for phrase in ("horario", "opening hours", "schedule")
    ):
        return None

    human = availability.get("human_attention", {})
    if not isinstance(human, dict):
        human = {}

    mode = human.get("mode", "on_request")
    hours = human.get("hours_text", "")
    hours = hours.strip() if isinstance(hours, str) else ""
    english = language is Language.EN

    if availability.get("service_24_7") is True:
        service_text = (
            "Our services operate 24 hours a day, every day."
            if english
            else "Nuestros servicios funcionan las 24 horas, todos los d\u00edas."
        )
    else:
        service_text = (
            "Please ask us about service operating hours."
            if english
            else "Consulta con el equipo el horario de funcionamiento del servicio."
        )

    if mode == "24_7":
        human_text = (
            "Human support is available 24 hours a day, every day."
            if english
            else "La atenci\u00f3n humana est\u00e1 disponible las 24 horas, todos los d\u00edas."
        )
    elif mode == "custom" and hours:
        human_text = (
            f"Human support hours: {hours}."
            if english
            else f"Horario de atenci\u00f3n humana: {hours}."
        )
    else:
        human_text = (
            "Human support availability is on request."
            if english
            else "La disponibilidad de atenci\u00f3n humana es a consultar."
        )

    note = (
        "Appointment times follow their own booking schedule."
        if english
        else "Las citas se rigen por su propio horario de reservas."
    )
    return f"{service_text}\n\n{human_text}\n\n{note}"
