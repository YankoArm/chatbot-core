from __future__ import annotations

from html import escape
from typing import Any


def availability_form_values(settings: dict[str, Any]) -> dict[str, str]:
    availability = settings.get("availability", {})
    if not isinstance(availability, dict):
        availability = {}

    human = availability.get("human_attention", {})
    if not isinstance(human, dict):
        human = {}

    return {
        "service_24_7": (
            "on" if availability.get("service_24_7") is True else ""
        ),
        "human_attention_mode": str(human.get("mode", "on_request")),
        "human_attention_hours": str(human.get("hours_text") or ""),
    }


def build_availability_settings(values: dict[str, str]) -> dict[str, Any]:
    mode = values.get("human_attention_mode", "on_request").strip()
    hours = values.get("human_attention_hours", "").strip()
    service_value = values.get("service_24_7", "")

    if service_value not in {"", "on"}:
        raise ValueError("La disponibilidad 24/7 no es v\u00e1lida.")

    if mode not in {"on_request", "24_7", "custom"}:
        raise ValueError("El modo de atenci\u00f3n humana no es v\u00e1lido.")

    if mode == "custom" and not hours:
        raise ValueError("Indica el horario de atenci\u00f3n humana.")

    if len(hours) > 300:
        raise ValueError("El horario no puede superar los 300 caracteres.")

    return {
        "service_24_7": service_value == "on",
        "human_attention": {
            "mode": mode,
            "hours_text": hours if mode == "custom" else "",
        },
    }


def render_availability_fields(values: dict[str, str]) -> str:
    checked = " checked" if values.get("service_24_7") == "on" else ""
    mode = values.get("human_attention_mode", "on_request")
    options = "".join(
        f'<option value="{value}"'
        f'{" selected" if mode == value else ""}>'
        f'{escape(label)}</option>'
        for value, label in (
            ("on_request", "Disponibilidad a consultar"),
            ("24_7", "Atenci\u00f3n humana 24 horas, todos los d\u00edas"),
            ("custom", "Horario de atenci\u00f3n indicado"),
        )
    )
    hours = escape(values.get("human_attention_hours", ""), quote=True)

    return f"""
    <section class="panel">
        <h2>Disponibilidad del negocio</h2>
        <input type="hidden" name="availability_configured" value="1">
        <label>
            <input type="checkbox" name="service_24_7" value="on"{checked}>
            Servicio disponible 24 horas, todos los d&#237;as
        </label>
        <p>
            Por ejemplo, servidores o servicios online disponibles 24/7.
            Esta opci&#243;n no cambia las horas reservables ni
            implica una respuesta humana inmediata.
        </p>
        <label>
            <span>Disponibilidad de atenci&#243;n humana</span>
            <select name="human_attention_mode">{options}</select>
        </label>
        <label>
            <span>Horario humano, si seleccionas horario indicado</span>
            <input
                name="human_attention_hours"
                value="{hours}"
                maxlength="300"
                placeholder="Lunes a viernes de 09:00 a 18:00"
            >
        </label>
    </section>
    """
