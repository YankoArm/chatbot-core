from __future__ import annotations

import re
import unicodedata

from collections.abc import Callable
from copy import deepcopy
from dataclasses import replace
from decimal import Decimal, InvalidOperation
from html import escape
from typing import Protocol
from urllib.parse import parse_qs

from fastapi import APIRouter, Request, Response
from fastapi.responses import (
    HTMLResponse,
    RedirectResponse,
)

from chatbot.instances import InstanceDefinition


class InstanceDefinitionRepositoryProtocol(
    Protocol
):
    def save(
        self,
        definition: InstanceDefinition,
    ) -> None:
        ...

    def get(
        self,
        client_id: str,
    ) -> InstanceDefinition | None:
        ...


DefinitionLoader = Callable[
    [str],
    InstanceDefinition | None,
]
PageRenderer = Callable[..., str]


_SERVICE_ID_STOPWORDS = {
    "de",
    "del",
    "el",
    "la",
    "los",
    "las",
}


def _build_unique_service_id(
    name: str,
    services: list[dict],
) -> str:
    normalized = unicodedata.normalize(
        "NFKD",
        name,
    )

    normalized = "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    )

    tokens = re.findall(
        r"[a-z0-9]+",
        normalized.casefold(),
    )

    tokens = [
        token
        for token in tokens
        if token not in _SERVICE_ID_STOPWORDS
    ]

    base = "_".join(tokens)

    if not base:
        base = "service"

    if not base[0].isalpha():
        base = f"service_{base}"

    base = base[:64].rstrip("_")

    existing_ids = {
        str(service.get("id", ""))
        for service in services
    }

    candidate = base
    number = 2

    while candidate in existing_ids:
        suffix = f"_{number}"
        candidate = (
            base[:64 - len(suffix)].rstrip("_")
            + suffix
        )
        number += 1

    return candidate



def _validate_service_details(values: dict[str, str]) -> str | None:
    service_type = values["service_type"]
    billing_period = values["billing_period"]

    if service_type not in {"appointment", "project", "recurring"}:
        return "El tipo de servicio no es v?lido."

    if billing_period not in {"once", "week", "month", "quarter", "year"}:
        return "La periodicidad del precio no es v?lida."

    if service_type == "recurring" and billing_period == "once":
        return "Selecciona una periodicidad para el servicio recurrente."

    if service_type != "recurring" and billing_period != "once":
        return "La periodicidad solo se aplica a servicios recurrentes."

    if len(values["duration_text"]) > 200:
        return "El plazo no puede superar los 200 caracteres."

    return None



def _render_service_details_fields(values: dict[str, str]) -> str:
    service_type = values.get("service_type") or "appointment"
    billing_period = values.get("billing_period") or "once"

    def options(items, selected):
        return "".join(
            f'<option value="{escape(value, quote=True)}"'
            f'{" selected" if value == selected else ""}>'
            f'{escape(label)}</option>'
            for value, label in items
        )

    type_options = options(
        (
            ("appointment", "Cita reservable"),
            ("project", "Proyecto o trabajo por encargo"),
            ("recurring", "Servicio recurrente"),
        ),
        service_type,
    )
    period_options = options(
        (
            ("once", "Pago \u00fanico"),
            ("week", "Semanal"),
            ("month", "Mensual"),
            ("quarter", "Trimestral"),
            ("year", "Anual"),
        ),
        billing_period,
    )
    duration_text = escape(
        values.get("duration_text", ""),
        quote=True,
    )

    fields = f"""
        <label>
            <span>Tipo de servicio</span>
            <select name="service_type" required>
                {type_options}
            </select>
        </label>
        <label>
            <span>Plazo o duraci&#243;n descriptiva</span>
            <input
                name="duration_text"
                value="{duration_text}"
                maxlength="200"
                placeholder="Entre 5 y 10 d&#237;as, o a consultar"
            >
        </label>
        <label>
            <span>Periodicidad del precio</span>
            <select name="billing_period" required>
                {period_options}
            </select>
        </label>
        <p>
            Las citas se reservan en el calendario.
            Los proyectos y servicios recurrentes no reservan
            una franja de minutos.
            La periodicidad indica cada cu&#225;nto se cobra;
            el plazo describe la entrega o duraci&#243;n del servicio.
        </p>
    """

    script = """
        <script>
        (() => {
            const form = document.currentScript.closest("form");
            const type = form.elements.namedItem("service_type");
            const minutes = form.elements.namedItem("duration_minutes");
            const period = form.elements.namedItem("billing_period");

            function updateFields() {
                const appointment = type.value === "appointment";
                const recurring = type.value === "recurring";

                minutes.required = appointment;
                minutes.disabled = !appointment;
                minutes.closest("label").hidden = !appointment;

                period.disabled = !recurring;
                period.closest("label").hidden = !recurring;

                if (recurring && period.value === "once") {
                    period.value = "month";
                }
            }

            type.addEventListener("change", updateFields);
            updateFields();
        })();
        </script>
    """
    return fields + script


def build_admin_services_router(
    *,
    instance_definition_repository: (
        InstanceDefinitionRepositoryProtocol | None
    ),
    definition_loader: DefinitionLoader,
    page_renderer: PageRenderer,
) -> APIRouter:
    router = APIRouter()

    def render_services_page(
        definition: InstanceDefinition,
    ) -> str:
        services = definition.settings.get(
            "services",
            [],
        )

        if services:
            service_cards = "".join(
                render_service_card(
                    definition.id,
                    service,
                )
                for service in services
            )
        else:
            service_cards = (
                '<p class="empty">'
                "Este bot todavía no tiene servicios configurados."
                "</p>"
            )

        return f"""
        <a
            class="back"
            href="/admin/clients/{escape(definition.id)}"
        >
            ← Volver al bot
        </a>
        <p class="eyebrow">Catálogo</p>
        <h1>Servicios y precios</h1>
        <p class="intro">
            Gestiona los servicios que el asistente
            puede ofrecer y reservar.
        </p>
        <a
            class="primary-button"
            href="/admin/clients/{escape(definition.id)}/services/new"
        >
            Añadir servicio
        </a>
        <section class="grid">
            {service_cards}
        </section>
        """

    def render_service_form(
        *,
        definition: InstanceDefinition,
        error: str | None = None,
        values: dict[str, str] | None = None,
    ) -> str:
        form_values = values or {}
        price_type = form_values.get(
            "price_type",
            "fixed",
        )
        currency = form_values.get(
            "currency",
            "EUR",
        )

        error_html = ""

        if error is not None:
            error_html = (
                '<div class="form-error">'
                f"{escape(error)}"
                "</div>"
            )

        fixed_selected = (
            " selected"
            if price_type == "fixed"
            else ""
        )
        from_selected = (
            " selected"
            if price_type == "from"
            else ""
        )

        return f"""
        <a
            class="back"
            href="/admin/clients/{escape(definition.id)}/services"
        >
            ← Volver a servicios
        </a>
        <p class="eyebrow">Nuevo servicio</p>
        <h1>Añadir servicio</h1>
        <p class="intro">
            Define el nombre, duración y precio
            que verá el cliente.
        </p>
        <section class="panel">
            {error_html}
            <form
                class="admin-form"
                method="post"
                action="/admin/clients/{escape(definition.id)}/services"
            >


                <label>
                    <span>Nombre en español</span>
                    <input
                        name="name_es"
                        value="{escape(form_values.get("name_es", ""))}"
                        placeholder="Corte de pelo"
                        required
                    >
                </label>

                <label>
                    <span>Nombre en inglés</span>
                    <input
                        name="name_en"
                        value="{escape(form_values.get("name_en", ""))}"
                        placeholder="Haircut"
                    >
                </label>

                <label>
                    <span>Duración en minutos</span>
                    <input
                        name="duration_minutes"
                        value="{escape(form_values.get("duration_minutes", ""))}"
                        type="number"
                        min="1"
                        max="1440"
                    >
                </label>

                {_render_service_details_fields(form_values)}

                <label>
                    <span>Tipo de precio</span>
                    <select
                        name="price_type"
                        required
                    >
                        <option
                            value="fixed"{fixed_selected}
                        >
                            Precio fijo
                        </option>
                        <option
                            value="from"{from_selected}
                        >
                            Desde
                        </option>
                    </select>
                </label>

                <label>
                    <span>Precio</span>
                    <input
                        name="price_amount"
                        value="{escape(form_values.get("price_amount", ""))}"
                        inputmode="decimal"
                        placeholder="25.00"
                        required
                    >
                </label>

                <label>
                    <span>Moneda</span>
                    <select
                        name="currency"
                        required
                    >
                        <option
                            value="EUR"
                            {"selected" if currency == "EUR" else ""}
                        >
                            EUR
                        </option>
                    </select>
                </label>

                <button
                    class="primary-button"
                    type="submit"
                >
                    Guardar servicio
                </button>
            </form>
        </section>
        """

    @router.get(
        "/admin/clients/{client_id}/services",
        response_class=HTMLResponse,
    )
    def admin_client_services(
        client_id: str,
    ) -> Response:
        definition = definition_loader(
            client_id
        )

        if definition is None:
            return HTMLResponse(
                content=page_renderer(
                    title="Bot no encontrado",
                    content="<h1>Bot no encontrado</h1>",
                ),
                status_code=404,
            )

        return HTMLResponse(
            content=page_renderer(
                title=(
                    f"Servicios de {definition.name}"
                ),
                content=render_services_page(
                    definition
                ),
            )
        )

    @router.get(
        "/admin/clients/{client_id}/services/new",
        response_class=HTMLResponse,
    )
    def admin_new_service(
        client_id: str,
    ) -> Response:
        definition = definition_loader(
            client_id
        )

        if definition is None:
            return HTMLResponse(
                content=page_renderer(
                    title="Bot no encontrado",
                    content="<h1>Bot no encontrado</h1>",
                ),
                status_code=404,
            )

        return HTMLResponse(
            content=page_renderer(
                title="Añadir servicio",
                content=render_service_form(
                    definition=definition,
                ),
            )
        )

    @router.post(
        "/admin/clients/{client_id}/services",
    )
    async def admin_create_service(
        client_id: str,
        request: Request,
    ) -> Response:
        if instance_definition_repository is None:
            return HTMLResponse(
                content=page_renderer(
                    title="Administración no disponible",
                    content="<h1>Administración no disponible</h1>",
                ),
                status_code=503,
            )

        definition = definition_loader(
            client_id
        )

        if definition is None:
            return HTMLResponse(
                content=page_renderer(
                    title="Bot no encontrado",
                    content="<h1>Bot no encontrado</h1>",
                ),
                status_code=404,
            )

        raw_body = (
            await request.body()
        ).decode(
            "utf-8"
        )
        parsed_form = parse_qs(
            raw_body,
            keep_blank_values=True,
        )
        values = {
            field: parsed_form.get(
                field,
                [""],
            )[0].strip()
            for field in (
                "service_id",
                "name_es",
                "name_en",
                "duration_minutes",
                "service_type",
                "duration_text",
                "billing_period",
                "price_type",
                "price_amount",
                "currency",
            )
        }

        values["service_id"] = (
            _build_unique_service_id(
                values["name_es"],
                [],
            )
        )

        values["service_type"] = values["service_type"] or "appointment"
        values["billing_period"] = values["billing_period"] or "once"

        error: str | None = _validate_service_details(values)
        duration_minutes = None
        amount_cents = 0

        if not re.fullmatch(
            r"[a-z][a-z0-9_]{2,63}",
            values["service_id"],
        ):
            error = (
                "El identificador del servicio no es válido."
            )
        elif not values["name_es"]:
            error = (
                "El nombre en español es obligatorio."
            )
        elif values["service_type"] == "appointment":
            try:
                duration_minutes = int(
                    values["duration_minutes"]
                )
            except ValueError:
                error = (
                    "La duración debe ser un número entero."
                )

        if (
            error is None
            and values["service_type"] == "appointment"
            and not 1 <= duration_minutes <= 1440
        ):
            error = (
                "La duración debe estar entre 1 y 1440 minutos."
            )

        if (
            error is None
            and values["price_type"]
            not in {"fixed", "from"}
        ):
            error = (
                "El tipo de precio no es válido."
            )

        if error is None:
            try:
                price_amount = Decimal(
                    values["price_amount"].replace(
                        ",",
                        ".",
                    )
                )

                if (
                    price_amount < 0
                    or price_amount
                    != price_amount.quantize(
                        Decimal("0.01")
                    )
                ):
                    raise InvalidOperation

                amount_cents = int(
                    price_amount * 100
                )
            except (
                InvalidOperation,
                ValueError,
            ):
                error = (
                    "El precio debe ser un importe válido "
                    "con un máximo de dos decimales."
                )

        services = list(
            definition.settings.get(
                "services",
                [],
            )
        )

        values["service_id"] = (
            _build_unique_service_id(
                values["name_es"],
                services,
            )
        )

        if (
            error is None
            and any(
                service.get("id")
                == values["service_id"]
                for service in services
            )
        ):
            error = (
                "Ya existe un servicio con ese identificador."
            )

        if error is not None:
            return HTMLResponse(
                content=page_renderer(
                    title="Añadir servicio",
                    content=render_service_form(
                        definition=definition,
                        error=error,
                        values=values,
                    ),
                ),
                status_code=422,
            )

        names = {
            "es": values["name_es"],
        }

        if values["name_en"]:
            names["en"] = values["name_en"]

        service = {
            "id": values["service_id"],
            "name": names,
            "duration_minutes": duration_minutes,
            **(
                {
                    "service_type": values["service_type"],
                    "duration_text": values["duration_text"],
                }
                if values["service_type"] != "appointment"
                else (
                    {"duration_text": values["duration_text"]}
                    if values["duration_text"]
                    else {}
                )
            ),
            "price": {
                "type": values["price_type"],
                "amount_cents": amount_cents,
                "currency": values["currency"],
                **(
                    {"billing_period": values["billing_period"]}
                    if (
                        values["service_type"] != "appointment"
                        or values["billing_period"] != "once"
                    )
                    else {}
                ),
            },
        }

        services.append(
            service
        )

        settings = deepcopy(
            definition.settings
        )
        settings["services"] = services

        instance_definition_repository.save(
            replace(
                definition,
                settings=settings,
            )
        )

        return RedirectResponse(
            url=(
                f"/admin/clients/{client_id}/services"
            ),
            status_code=303,
        )

    def render_edit_service_form(
        *,
        definition: InstanceDefinition,
        service: dict,
        error: str | None = None,
        values: dict[str, str] | None = None,
    ) -> str:
        price = service.get(
            "price",
            {},
        )
        names = service.get(
            "name",
            {},
        )

        default_values = {
            "name_es": str(
                names.get(
                    "es",
                    "",
                )
            ),
            "name_en": str(
                names.get(
                    "en",
                    "",
                )
            ),
            "duration_minutes": str(
                service.get(
                    "duration_minutes",
                    "",
                )
            ),
            "service_type": str(
                service.get("service_type", "appointment")
            ),
            "duration_text": str(
                service.get("duration_text") or ""
            ),
            "billing_period": str(
                price.get("billing_period", "once")
            ),
            "price_type": str(
                price.get(
                    "type",
                    "fixed",
                )
            ),
            "price_amount": (
                f'{price.get("amount_cents", 0) / 100:.2f}'
            ),
            "currency": str(
                price.get(
                    "currency",
                    "EUR",
                )
            ),
        }

        form_values = (
            default_values
            if values is None
            else values
        )
        error_html = ""

        if error is not None:
            error_html = (
                '<div class="form-error">'
                f"{escape(error)}"
                "</div>"
            )

        fixed_selected = (
            " selected"
            if form_values.get(
                "price_type"
            ) == "fixed"
            else ""
        )
        from_selected = (
            " selected"
            if form_values.get(
                "price_type"
            ) == "from"
            else ""
        )

        service_id = str(
            service.get(
                "id",
                "",
            )
        )

        return f"""
        <a
            class="back"
            href="/admin/clients/{escape(definition.id)}/services"
        >
            ← Volver a servicios
        </a>
        <p class="eyebrow">Catálogo</p>
        <h1>Editar servicio</h1>
        <p class="intro">
            Actualiza el nombre, duración y precio
            del servicio.
        </p>
        <section class="panel">
            {error_html}
            <form
                class="admin-form"
                method="post"
                action="/admin/clients/{escape(definition.id)}/services/{escape(service_id)}"
            >
                <label>
                    <span>Identificador</span>
                    <input
                        value="{escape(service_id)}"
                        disabled
                    >
                </label>

                <label>
                    <span>Nombre en español</span>
                    <input
                        name="name_es"
                        value="{escape(form_values.get("name_es", ""))}"
                        required
                    >
                </label>

                <label>
                    <span>Nombre en inglés</span>
                    <input
                        name="name_en"
                        value="{escape(form_values.get("name_en", ""))}"
                    >
                </label>

                <label>
                    <span>Duración en minutos</span>
                    <input
                        name="duration_minutes"
                        value="{escape(form_values.get("duration_minutes", ""))}"
                        type="number"
                        min="1"
                        max="1440"
                    >
                </label>

                {_render_service_details_fields(form_values)}

                <label>
                    <span>Tipo de precio</span>
                    <select
                        name="price_type"
                        required
                    >
                        <option
                            value="fixed"{fixed_selected}
                        >
                            Precio fijo
                        </option>
                        <option
                            value="from"{from_selected}
                        >
                            Desde
                        </option>
                    </select>
                </label>

                <label>
                    <span>Precio</span>
                    <input
                        name="price_amount"
                        value="{escape(form_values.get("price_amount", ""))}"
                        inputmode="decimal"
                        required
                    >
                </label>

                <label>
                    <span>Moneda</span>
                    <select
                        name="currency"
                        required
                    >
                        <option value="EUR" selected>
                            EUR
                        </option>
                    </select>
                </label>

                <button
                    class="primary-button"
                    type="submit"
                >
                    Guardar cambios
                </button>
            </form>
        </section>
        """

    @router.get(
        "/admin/clients/{client_id}/services/{service_id}/edit",
        response_class=HTMLResponse,
    )
    def admin_edit_service(
        client_id: str,
        service_id: str,
    ) -> Response:
        definition = definition_loader(
            client_id
        )

        if definition is None:
            return HTMLResponse(
                content=page_renderer(
                    title="Bot no encontrado",
                    content="<h1>Bot no encontrado</h1>",
                ),
                status_code=404,
            )

        service = next(
            (
                candidate
                for candidate in definition.settings.get(
                    "services",
                    [],
                )
                if candidate.get("id") == service_id
            ),
            None,
        )

        if service is None:
            return HTMLResponse(
                content=page_renderer(
                    title="Servicio no encontrado",
                    content="<h1>Servicio no encontrado</h1>",
                ),
                status_code=404,
            )

        return HTMLResponse(
            content=page_renderer(
                title="Editar servicio",
                content=render_edit_service_form(
                    definition=definition,
                    service=service,
                ),
            )
        )

    @router.post(
        "/admin/clients/{client_id}/services/{service_id}",
    )
    async def admin_update_service(
        client_id: str,
        service_id: str,
        request: Request,
    ) -> Response:
        if instance_definition_repository is None:
            return HTMLResponse(
                content=page_renderer(
                    title="Administración no disponible",
                    content="<h1>Administración no disponible</h1>",
                ),
                status_code=503,
            )

        definition = definition_loader(
            client_id
        )

        if definition is None:
            return HTMLResponse(
                content=page_renderer(
                    title="Bot no encontrado",
                    content="<h1>Bot no encontrado</h1>",
                ),
                status_code=404,
            )

        services = list(
            definition.settings.get(
                "services",
                [],
            )
        )
        service_index = next(
            (
                index
                for index, candidate in enumerate(
                    services
                )
                if candidate.get("id") == service_id
            ),
            None,
        )

        if service_index is None:
            return HTMLResponse(
                content=page_renderer(
                    title="Servicio no encontrado",
                    content="<h1>Servicio no encontrado</h1>",
                ),
                status_code=404,
            )

        original_service = services[
            service_index
        ]

        raw_body = (
            await request.body()
        ).decode(
            "utf-8"
        )
        parsed_form = parse_qs(
            raw_body,
            keep_blank_values=True,
        )
        values = {
            field: parsed_form.get(
                field,
                [""],
            )[0].strip()
            for field in (
                "name_es",
                "name_en",
                "duration_minutes",
                "service_type",
                "duration_text",
                "billing_period",
                "price_type",
                "price_amount",
                "currency",
            )
        }

        values["service_type"] = values["service_type"] or "appointment"
        values["billing_period"] = values["billing_period"] or "once"

        error: str | None = _validate_service_details(values)
        duration_minutes = None
        amount_cents = 0

        if not values["name_es"]:
            error = (
                "El nombre en español es obligatorio."
            )
        elif values["service_type"] == "appointment":
            try:
                duration_minutes = int(
                    values["duration_minutes"]
                )
            except ValueError:
                error = (
                    "La duración debe ser un número entero."
                )

        if (
            error is None
            and values["service_type"] == "appointment"
            and not 1 <= duration_minutes <= 1440
        ):
            error = (
                "La duración debe estar entre 1 y 1440 minutos."
            )

        if (
            error is None
            and values["price_type"]
            not in {"fixed", "from"}
        ):
            error = (
                "El tipo de precio no es válido."
            )

        if error is None:
            try:
                price_amount = Decimal(
                    values["price_amount"].replace(
                        ",",
                        ".",
                    )
                )

                if (
                    price_amount < 0
                    or price_amount
                    != price_amount.quantize(
                        Decimal("0.01")
                    )
                ):
                    raise InvalidOperation

                amount_cents = int(
                    price_amount * 100
                )
            except (
                InvalidOperation,
                ValueError,
            ):
                error = (
                    "El precio debe ser un importe válido "
                    "con un máximo de dos decimales."
                )

        if error is not None:
            return HTMLResponse(
                content=page_renderer(
                    title="Editar servicio",
                    content=render_edit_service_form(
                        definition=definition,
                        service=original_service,
                        error=error,
                        values=values,
                    ),
                ),
                status_code=422,
            )

        names = {
            "es": values["name_es"],
        }

        if values["name_en"]:
            names["en"] = values["name_en"]

        services[service_index] = {
            "id": service_id,
            "name": names,
            "duration_minutes": duration_minutes,
            **(
                {
                    "service_type": values["service_type"],
                    "duration_text": values["duration_text"],
                }
                if values["service_type"] != "appointment"
                else (
                    {"duration_text": values["duration_text"]}
                    if values["duration_text"]
                    else {}
                )
            ),
            "price": {
                "type": values["price_type"],
                "amount_cents": amount_cents,
                "currency": values["currency"],
                **(
                    {"billing_period": values["billing_period"]}
                    if (
                        values["service_type"] != "appointment"
                        or values["billing_period"] != "once"
                    )
                    else {}
                ),
            },
        }

        settings = deepcopy(
            definition.settings
        )
        settings["services"] = services

        instance_definition_repository.save(
            replace(
                definition,
                settings=settings,
            )
        )

        return RedirectResponse(
            url=(
                f"/admin/clients/{client_id}/services"
            ),
            status_code=303,
        )
    @router.get(
        "/admin/clients/{client_id}/services/{service_id}/delete",
        response_class=HTMLResponse,
    )
    def admin_confirm_delete_service(
        client_id: str,
        service_id: str,
    ) -> Response:
        definition = definition_loader(
            client_id
        )

        if definition is None:
            return HTMLResponse(
                content=page_renderer(
                    title="Bot no encontrado",
                    content="<h1>Bot no encontrado</h1>",
                ),
                status_code=404,
            )

        service = next(
            (
                candidate
                for candidate in definition.settings.get(
                    "services",
                    [],
                )
                if candidate.get("id") == service_id
            ),
            None,
        )

        if service is None:
            return HTMLResponse(
                content=page_renderer(
                    title="Servicio no encontrado",
                    content="<h1>Servicio no encontrado</h1>",
                ),
                status_code=404,
            )

        names = service.get(
            "name",
            {},
        )
        visible_name = (
            names.get("es")
            or names.get("en")
            or service_id
        )

        content = f"""
        <a
            class="back"
            href="/admin/clients/{escape(client_id)}/services"
        >
            ← Volver a servicios
        </a>
        <p class="eyebrow">Confirmación</p>
        <h1>Eliminar servicio</h1>
        <p class="intro">
            Vas a eliminar
            <strong>{escape(str(visible_name))}</strong>.
            Esta acción no se puede deshacer.
        </p>
        <section class="panel">
            <form
                method="post"
                action="/admin/clients/{escape(client_id)}/services/{escape(service_id)}/delete"
            >
                <button
                    class="danger-button"
                    type="submit"
                >
                    Eliminar definitivamente
                </button>
            </form>
        </section>
        """

        return HTMLResponse(
            content=page_renderer(
                title="Eliminar servicio",
                content=content,
            )
        )

    @router.post(
        "/admin/clients/{client_id}/services/{service_id}/delete",
    )
    def admin_delete_service(
        client_id: str,
        service_id: str,
    ) -> Response:
        if instance_definition_repository is None:
            return HTMLResponse(
                content=page_renderer(
                    title="Administración no disponible",
                    content="<h1>Administración no disponible</h1>",
                ),
                status_code=503,
            )

        definition = definition_loader(
            client_id
        )

        if definition is None:
            return HTMLResponse(
                content=page_renderer(
                    title="Bot no encontrado",
                    content="<h1>Bot no encontrado</h1>",
                ),
                status_code=404,
            )

        original_services = list(
            definition.settings.get(
                "services",
                [],
            )
        )
        remaining_services = [
            service
            for service in original_services
            if service.get("id") != service_id
        ]

        if (
            len(remaining_services)
            == len(original_services)
        ):
            return HTMLResponse(
                content=page_renderer(
                    title="Servicio no encontrado",
                    content="<h1>Servicio no encontrado</h1>",
                ),
                status_code=404,
            )

        settings = deepcopy(
            definition.settings
        )
        settings["services"] = (
            remaining_services
        )

        instance_definition_repository.save(
            replace(
                definition,
                settings=settings,
            )
        )

        return RedirectResponse(
            url=(
                f"/admin/clients/{client_id}/services"
            ),
            status_code=303,
        )
    return router


def render_service_card(
    client_id: str,
    service: dict,
) -> str:
    names = service.get("name", {})
    visible_name = (
        names.get("es")
        or names.get("en")
        or service.get("id", "Servicio")
    )
    service_id = str(service.get("id", ""))
    service_type = service.get("service_type", "appointment")
    duration_text = str(service.get("duration_text") or "").strip()

    type_label = {
        "appointment": "Cita reservable",
        "project": "Proyecto",
        "recurring": "Servicio recurrente",
    }.get(service_type, "Servicio")

    if service_type == "appointment":
        duration_label = f'{service.get("duration_minutes", 0)} minutos'
    else:
        duration_label = duration_text or "Plazo a consultar"

    price = service.get("price", {})
    amount_cents = price.get("amount_cents", 0)
    formatted_amount = f"{amount_cents / 100:.2f}".replace(".", ",")
    price_prefix = "Desde " if price.get("type") == "from" else ""
    period_suffix = {
        "once": "",
        "week": " / semana",
        "month": " / mes",
        "quarter": " / trimestre",
        "year": " / a\u00f1o",
    }.get(price.get("billing_period", "once"), "")

    currency = str(price.get("currency", "EUR"))
    currency_label = "\u20ac" if currency == "EUR" else currency
    price_label = (
        f"{price_prefix}{formatted_amount} "
        f"{currency_label}{period_suffix}"
    )

    escaped_client_id = escape(client_id, quote=True)
    escaped_service_id = escape(service_id, quote=True)

    return f"""
    <article class="card">
        <span class="status">Servicio activo</span>
        <h2>{escape(str(visible_name))}</h2>
        <span class="identifier">{escape(service_id)}</span>
        <div class="tags">
            <span class="tag">{escape(type_label)}</span>
            <span class="tag">{escape(duration_label)}</span>
            <span class="tag">{escape(price_label)}</span>
        </div>
        <div class="actions">
            <a
                class="button secondary"
                href="/admin/clients/{escaped_client_id}/services/{escaped_service_id}/edit"
            >
                Editar
            </a>
            <a
                class="danger-button"
                href="/admin/clients/{escaped_client_id}/services/{escaped_service_id}/delete"
            >
                Eliminar
            </a>
        </div>
    </article>
    """
