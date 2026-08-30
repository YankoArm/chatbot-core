from __future__ import annotations

import re

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
                    <span>Identificador</span>
                    <input
                        name="service_id"
                        value="{escape(form_values.get("service_id", ""))}"
                        placeholder="haircut"
                        required
                        pattern="[a-z][a-z0-9_]*"
                    >
                </label>

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
                        required
                    >
                </label>

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
                "price_type",
                "price_amount",
                "currency",
            )
        }

        error: str | None = None
        duration_minutes = 0
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
        else:
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
            "price": {
                "type": values["price_type"],
                "amount_cents": amount_cents,
                "currency": values["currency"],
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
                        required
                    >
                </label>

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
                "price_type",
                "price_amount",
                "currency",
            )
        }

        error: str | None = None
        duration_minutes = 0
        amount_cents = 0

        if not values["name_es"]:
            error = (
                "El nombre en español es obligatorio."
            )
        else:
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
            "price": {
                "type": values["price_type"],
                "amount_cents": amount_cents,
                "currency": values["currency"],
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
    names = service.get(
        "name",
        {},
    )
    visible_name = (
        names.get("es")
        or names.get("en")
        or service.get("id", "Servicio")
    )

    service_id = str(
        service.get(
            "id",
            "",
        )
    )
    duration_minutes = service.get(
        "duration_minutes",
        0,
    )
    price = service.get(
        "price",
        {},
    )
    amount_cents = price.get(
        "amount_cents",
        0,
    )
    price_type = price.get(
        "type",
        "fixed",
    )

    formatted_amount = (
        f"{amount_cents / 100:.2f}"
        .replace(
            ".",
            ",",
        )
    )
    price_prefix = (
        "Desde "
        if price_type == "from"
        else ""
    )

    escaped_client_id = escape(
        client_id,
        quote=True,
    )
    escaped_service_id = escape(
        service_id,
        quote=True,
    )

    return f"""
    <article class="card">
        <span class="status">Servicio activo</span>
        <h2>{escape(str(visible_name))}</h2>
        <span class="identifier">
            {escape(service_id)}
        </span>
        <div class="tags">
            <span class="tag">
                {escape(str(duration_minutes))} minutos
            </span>
            <span class="tag">
                {price_prefix}{formatted_amount} €
            </span>
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