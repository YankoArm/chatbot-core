from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from dataclasses import replace
from datetime import datetime
from html import escape
from typing import Protocol
from urllib.parse import parse_qs
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Request, Response
from fastapi.responses import (
    HTMLResponse,
    RedirectResponse,
)

from chatbot.instances import InstanceDefinition


_WEEKDAYS = (
    ("monday", "Lunes"),
    ("tuesday", "Martes"),
    ("wednesday", "Miércoles"),
    ("thursday", "Jueves"),
    ("friday", "Viernes"),
    ("saturday", "Sábado"),
    ("sunday", "Domingo"),
)


class InstanceDefinitionRepositoryProtocol(
    Protocol
):
    def save(
        self,
        definition: InstanceDefinition,
    ) -> None:
        ...


DefinitionLoader = Callable[
    [str],
    InstanceDefinition | None,
]
PageRenderer = Callable[..., str]


def build_admin_schedule_router(
    *,
    instance_definition_repository: (
        InstanceDefinitionRepositoryProtocol | None
    ),
    definition_loader: DefinitionLoader,
    page_renderer: PageRenderer,
) -> APIRouter:
    router = APIRouter()

    def render_schedule_form(
        *,
        definition: InstanceDefinition,
        values: dict[str, str],
        error: str | None = None,
    ) -> str:
        error_html = ""

        if error is not None:
            error_html = (
                '<div class="form-error">'
                f"{escape(error)}"
                "</div>"
            )

        weekday_fields = "".join(
            _render_weekday_fields(
                weekday_name=weekday_name,
                weekday_label=weekday_label,
                values=values,
            )
            for weekday_name, weekday_label in _WEEKDAYS
        )

        return f"""
        <a
            class="back"
            href="/admin/clients/{escape(definition.id)}"
        >
            ← Volver al bot
        </a>
        <p class="eyebrow">Disponibilidad</p>
        <h1>Horarios y reservas</h1>
        <p class="intro">
            Configura cuándo puede reservar el cliente
            y con cuánta antelación.
        </p>
        {error_html}
        <form
            class="admin-form"
            method="post"
            action="/admin/clients/{escape(definition.id)}/schedule"
        >
            <section class="form-section">
                <h2>Zona horaria</h2>
                <label>
                    Zona horaria
                    <input
                        name="timezone"
                        value="{escape(values["timezone"])}"
                        placeholder="Europe/Madrid"
                        required
                    >
                </label>
            </section>

            <section class="form-section">
                <h2>Horario semanal</h2>
                <p class="form-help">
                    Cada día puede tener una franja continua
                    o un horario partido.
                </p>
                <div class="schedule-grid">
                    {weekday_fields}
                </div>
            </section>

            <section class="form-section">
                <h2>Reglas de reserva</h2>
                <div class="form-grid">
                    {_render_number_field(
                        name="appointment_duration_minutes",
                        label="Duración predeterminada (minutos)",
                        value=values[
                            "appointment_duration_minutes"
                        ],
                        minimum=1,
                    )}
                    {_render_number_field(
                        name="slot_interval_minutes",
                        label="Intervalo entre horas (minutos)",
                        value=values[
                            "slot_interval_minutes"
                        ],
                        minimum=1,
                    )}
                    {_render_number_field(
                        name="minimum_notice_hours",
                        label="Antelación mínima (horas)",
                        value=values[
                            "minimum_notice_hours"
                        ],
                        minimum=0,
                    )}
                    {_render_number_field(
                        name="maximum_advance_days",
                        label="Máximo de días reservables",
                        value=values[
                            "maximum_advance_days"
                        ],
                        minimum=1,
                    )}
                    {_render_number_field(
                        name="buffer_before_minutes",
                        label="Margen anterior (minutos)",
                        value=values[
                            "buffer_before_minutes"
                        ],
                        minimum=0,
                    )}
                    {_render_number_field(
                        name="buffer_after_minutes",
                        label="Margen posterior (minutos)",
                        value=values[
                            "buffer_after_minutes"
                        ],
                        minimum=0,
                    )}
                </div>
            </section>

            <button
                class="primary-button"
                type="submit"
            >
                Guardar horarios
            </button>
        </form>
        """

    @router.get(
        "/admin/clients/{client_id}/schedule",
        response_class=HTMLResponse,
    )
    def admin_schedule(
        client_id: str,
    ) -> Response:
        definition = definition_loader(
            client_id
        )

        if definition is None:
            return HTMLResponse(
                content=page_renderer(
                    title="Cliente no encontrado",
                    content=(
                        "<h1>Cliente no encontrado</h1>"
                        "<p>El bot solicitado no existe.</p>"
                    ),
                ),
                status_code=404,
            )

        values = _definition_form_values(
            definition
        )

        return HTMLResponse(
            content=page_renderer(
                title=(
                    f"Horarios · {definition.name}"
                ),
                content=render_schedule_form(
                    definition=definition,
                    values=values,
                ),
            )
        )

    @router.post(
        "/admin/clients/{client_id}/schedule",
    )
    async def update_admin_schedule(
        client_id: str,
        request: Request,
    ) -> Response:
        definition = definition_loader(
            client_id
        )

        if definition is None:
            return HTMLResponse(
                content=page_renderer(
                    title="Cliente no encontrado",
                    content=(
                        "<h1>Cliente no encontrado</h1>"
                        "<p>El bot solicitado no existe.</p>"
                    ),
                ),
                status_code=404,
            )

        if instance_definition_repository is None:
            return HTMLResponse(
                content=page_renderer(
                    title="Almacenamiento no disponible",
                    content=(
                        "<h1>No se pueden guardar cambios</h1>"
                        "<p>El almacenamiento no está configurado.</p>"
                    ),
                ),
                status_code=503,
            )

        body = (
            await request.body()
        ).decode(
            "utf-8"
        )
        parsed_form = parse_qs(
            body,
            keep_blank_values=True,
        )
        values = {
            key: form_values[0]
            for key, form_values in parsed_form.items()
        }

        try:
            booking_settings = (
                _build_booking_settings(
                    values
                )
            )
        except ValueError as exc:
            return HTMLResponse(
                content=page_renderer(
                    title=(
                        f"Horarios · {definition.name}"
                    ),
                    content=render_schedule_form(
                        definition=definition,
                        values=_complete_form_values(
                            values
                        ),
                        error=str(exc),
                    ),
                ),
                status_code=400,
            )

        updated_settings = deepcopy(
            definition.settings
        )
        updated_settings["booking"] = (
            booking_settings
        )

        updated_definition = replace(
            definition,
            settings=updated_settings,
        )

        instance_definition_repository.save(
            updated_definition
        )

        return RedirectResponse(
            url=(
                f"/admin/clients/{definition.id}"
            ),
            status_code=303,
        )

    return router


def _definition_form_values(
    definition: InstanceDefinition,
) -> dict[str, str]:
    booking = definition.settings.get(
        "booking",
        {},
    )
    business_hours = booking.get(
        "business_hours",
        {},
    )
    rules = booking.get(
        "rules",
        {},
    )

    values = _complete_form_values({
        "timezone": str(
            booking.get(
                "timezone",
                "Europe/Madrid",
            )
        ),
        "appointment_duration_minutes": str(
            rules.get(
                "appointment_duration_minutes",
                30,
            )
        ),
        "slot_interval_minutes": str(
            rules.get(
                "slot_interval_minutes",
                30,
            )
        ),
        "buffer_before_minutes": str(
            rules.get(
                "buffer_before_minutes",
                0,
            )
        ),
        "buffer_after_minutes": str(
            rules.get(
                "buffer_after_minutes",
                0,
            )
        ),
        "minimum_notice_hours": str(
            rules.get(
                "minimum_notice_hours",
                2,
            )
        ),
        "maximum_advance_days": str(
            rules.get(
                "maximum_advance_days",
                30,
            )
        ),
    })

    for weekday_name, _ in _WEEKDAYS:
        ranges = business_hours.get(
            weekday_name,
            [],
        )

        if not ranges:
            continue

        values[
            f"{weekday_name}_enabled"
        ] = "on"

        for range_index, time_range in enumerate(
            ranges[:2],
            start=1,
        ):
            if (
                not isinstance(time_range, list)
                or len(time_range) != 2
            ):
                continue

            values[
                f"{weekday_name}_start_{range_index}"
            ] = str(
                time_range[0]
            )
            values[
                f"{weekday_name}_end_{range_index}"
            ] = str(
                time_range[1]
            )

    return values


def _complete_form_values(
    values: dict[str, str],
) -> dict[str, str]:
    completed = dict(
        values
    )

    defaults = {
        "timezone": "Europe/Madrid",
        "appointment_duration_minutes": "30",
        "slot_interval_minutes": "30",
        "buffer_before_minutes": "0",
        "buffer_after_minutes": "0",
        "minimum_notice_hours": "2",
        "maximum_advance_days": "30",
    }

    for field_name, default_value in defaults.items():
        completed.setdefault(
            field_name,
            default_value,
        )

    for weekday_name, _ in _WEEKDAYS:
        completed.setdefault(
            f"{weekday_name}_enabled",
            "",
        )

        for range_index in (1, 2):
            completed.setdefault(
                f"{weekday_name}_start_{range_index}",
                "",
            )
            completed.setdefault(
                f"{weekday_name}_end_{range_index}",
                "",
            )

    return completed


def _build_booking_settings(
    values: dict[str, str],
) -> dict:
    timezone_name = values.get(
        "timezone",
        "",
    ).strip()

    if not timezone_name:
        raise ValueError(
            "La zona horaria es obligatoria."
        )

    try:
        ZoneInfo(
            timezone_name
        )
    except ZoneInfoNotFoundError as exc:
        raise ValueError(
            "La zona horaria indicada no es válida."
        ) from exc

    business_hours = {
        weekday_name: _build_weekday_ranges(
            weekday_name=weekday_name,
            values=values,
        )
        for weekday_name, _ in _WEEKDAYS
    }

    if not any(
        business_hours.values()
    ):
        raise ValueError(
            "Debes abrir al menos un día de la semana."
        )

    rules = {
        "appointment_duration_minutes": (
            _parse_integer(
                values,
                "appointment_duration_minutes",
                label="La duración predeterminada",
                minimum=1,
            )
        ),
        "slot_interval_minutes": (
            _parse_integer(
                values,
                "slot_interval_minutes",
                label="El intervalo entre horas",
                minimum=1,
            )
        ),
        "buffer_before_minutes": (
            _parse_integer(
                values,
                "buffer_before_minutes",
                label="El margen anterior",
                minimum=0,
            )
        ),
        "buffer_after_minutes": (
            _parse_integer(
                values,
                "buffer_after_minutes",
                label="El margen posterior",
                minimum=0,
            )
        ),
        "minimum_notice_hours": (
            _parse_integer(
                values,
                "minimum_notice_hours",
                label="La antelación mínima",
                minimum=0,
            )
        ),
        "maximum_advance_days": (
            _parse_integer(
                values,
                "maximum_advance_days",
                label="El máximo de días",
                minimum=1,
            )
        ),
        "allow_past_bookings": False,
    }

    return {
        "timezone": timezone_name,
        "business_hours": business_hours,
        "rules": rules,
    }


def _build_weekday_ranges(
    *,
    weekday_name: str,
    values: dict[str, str],
) -> list[list[str]]:
    enabled = (
        values.get(
            f"{weekday_name}_enabled"
        )
        == "on"
    )

    if not enabled:
        return []

    ranges: list[list[str]] = []

    for range_index in (1, 2):
        start_value = values.get(
            f"{weekday_name}_start_{range_index}",
            "",
        ).strip()
        end_value = values.get(
            f"{weekday_name}_end_{range_index}",
            "",
        ).strip()

        if (
            range_index == 1
            and (
                not start_value
                or not end_value
            )
        ):
            raise ValueError(
                "Cada día abierto necesita "
                "una hora de inicio y de cierre."
            )

        if not start_value and not end_value:
            continue

        if not start_value or not end_value:
            raise ValueError(
                "Cada franja debe tener "
                "hora de inicio y de cierre."
            )

        start_time = _parse_time(
            start_value
        )
        end_time = _parse_time(
            end_value
        )

        if start_time >= end_time:
            raise ValueError(
                "La hora de cierre debe ser "
                "posterior a la de apertura."
            )

        ranges.append([
            start_value,
            end_value,
        ])

    if (
        len(ranges) == 2
        and _parse_time(
            ranges[0][1]
        ) > _parse_time(
            ranges[1][0]
        )
    ):
        raise ValueError(
            "Las franjas de un mismo día "
            "no pueden solaparse."
        )

    return ranges


def _parse_time(
    value: str,
):
    try:
        return datetime.strptime(
            value,
            "%H:%M",
        ).time()
    except ValueError as exc:
        raise ValueError(
            "Las horas deben usar el formato HH:MM."
        ) from exc


def _parse_integer(
    values: dict[str, str],
    field_name: str,
    *,
    label: str,
    minimum: int,
) -> int:
    raw_value = values.get(
        field_name,
        "",
    ).strip()

    try:
        value = int(
            raw_value
        )
    except ValueError as exc:
        raise ValueError(
            f"{label} debe ser un número entero."
        ) from exc

    if value < minimum:
        raise ValueError(
            f"{label} debe ser igual o mayor que {minimum}."
        )

    return value


def _render_weekday_fields(
    *,
    weekday_name: str,
    weekday_label: str,
    values: dict[str, str],
) -> str:
    checked = (
        " checked"
        if values.get(
            f"{weekday_name}_enabled"
        ) == "on"
        else ""
    )

    return f"""
    <article class="schedule-day">
        <label class="schedule-toggle">
            <input
                type="checkbox"
                name="{weekday_name}_enabled"
                value="on"
                {checked}
            >
            <strong>{weekday_label}</strong>
        </label>
        <div class="form-grid">
            {_render_time_field(
                name=f"{weekday_name}_start_1",
                label="Apertura",
                value=values[
                    f"{weekday_name}_start_1"
                ],
            )}
            {_render_time_field(
                name=f"{weekday_name}_end_1",
                label="Cierre",
                value=values[
                    f"{weekday_name}_end_1"
                ],
            )}
            {_render_time_field(
                name=f"{weekday_name}_start_2",
                label="Segunda apertura",
                value=values[
                    f"{weekday_name}_start_2"
                ],
            )}
            {_render_time_field(
                name=f"{weekday_name}_end_2",
                label="Segundo cierre",
                value=values[
                    f"{weekday_name}_end_2"
                ],
            )}
        </div>
    </article>
    """


def _render_time_field(
    *,
    name: str,
    label: str,
    value: str,
) -> str:
    return f"""
    <label>
        {label}
        <input
            type="time"
            name="{name}"
            value="{escape(value)}"
        >
    </label>
    """


def _render_number_field(
    *,
    name: str,
    label: str,
    value: str,
    minimum: int,
) -> str:
    return f"""
    <label>
        {label}
        <input
            type="number"
            name="{name}"
            value="{escape(value)}"
            min="{minimum}"
            required
        >
    </label>
    """