from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from dataclasses import replace
from html import escape
from typing import Protocol
from urllib.parse import parse_qs

from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse

from chatbot.clients.registry import (
    UnknownClientError,
    build_client_definition,
)
from chatbot.instances import InstanceDefinition


_STATUSES = (
    "draft",
    "active",
    "paused",
)

_STATUS_LABELS = {
    "draft": "Borrador",
    "active": "Activo",
    "paused": "Pausado",
}


class InstanceDefinitionRepositoryProtocol(
    Protocol
):
    def get(
        self,
        client_id: str,
    ) -> InstanceDefinition | None:
        ...

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


def build_admin_status_router(
    *,
    instance_definition_repository: (
        InstanceDefinitionRepositoryProtocol | None
    ),
    page_renderer: PageRenderer,
) -> APIRouter:
    router = APIRouter()

    def load_definition(
        client_id: str,
    ) -> InstanceDefinition | None:
        if instance_definition_repository is not None:
            definition = (
                instance_definition_repository.get(
                    client_id
                )
            )

            if definition is not None:
                return definition

        try:
            return build_client_definition(
                client_id
            )
        except UnknownClientError:
            return None

    @router.get(
        "/admin/clients/{client_id}/status",
        response_class=HTMLResponse,
    )
    def admin_bot_status(
        client_id: str,
    ) -> HTMLResponse:
        definition = load_definition(
            client_id
        )

        if definition is None:
            return _not_found_response(
                page_renderer
            )

        return HTMLResponse(
            content=page_renderer(
                title=f"Estado de {definition.name}",
                content=_render_status_page(
                    definition=definition,
                ),
            )
        )

    @router.post(
        "/admin/clients/{client_id}/status",
    )
    async def admin_update_bot_status(
        client_id: str,
        request: Request,
    ) -> Response:
        if instance_definition_repository is None:
            return HTMLResponse(
                content=page_renderer(
                    title="Edición no disponible",
                    content=(
                        "<h1>Edición no disponible</h1>"
                    ),
                ),
                status_code=503,
            )

        definition = load_definition(
            client_id
        )

        if definition is None:
            return _not_found_response(
                page_renderer
            )

        raw_body = (
            await request.body()
        ).decode(
            "utf-8"
        )
        form_data = parse_qs(
            raw_body,
            keep_blank_values=True,
        )
        status = form_data.get(
            "status",
            [""],
        )[0].strip()

        if status not in _STATUSES:
            return HTMLResponse(
                content=page_renderer(
                    title=f"Estado de {definition.name}",
                    content=_render_status_page(
                        definition=definition,
                        error="El estado seleccionado no es válido.",
                    ),
                ),
                status_code=422,
            )

        metadata = deepcopy(
            definition.metadata
        )
        metadata["admin_status"] = status

        instance_definition_repository.save(
            replace(
                definition,
                metadata=metadata,
            )
        )

        return RedirectResponse(
            url=f"/admin/clients/{client_id}",
            status_code=303,
        )

    return router


def _render_status_page(
    *,
    definition: InstanceDefinition,
    error: str | None = None,
) -> str:
    status = _get_status(
        definition
    )
    error_html = ""

    if error is not None:
        error_html = (
            '<div class="form-error">'
            f"{escape(error)}"
            "</div>"
        )

    buttons = "".join(
        _render_status_button(
            client_id=definition.id,
            status=available_status,
            selected=(available_status == status),
        )
        for available_status in _STATUSES
    )

    return f"""
    <a
        class="back"
        href="/admin/clients/{escape(definition.id)}"
    >
        ← Volver al bot
    </a>
    <p class="eyebrow">Ciclo de vida</p>
    <h1>Estado del bot</h1>
    <p class="intro">
        Estado actual:
        <span class="identifier">
            {_STATUS_LABELS[status]}
        </span>
    </p>
    <section class="panel">
        <p class="intro">
            Borrador permite preparar la configuración.
            Activo indica que el bot está listo para publicarse.
            Pausado conserva la configuración sin atender
            conversaciones nuevas.
        </p>
        {error_html}
        <div class="definition-grid">
            {buttons}
        </div>
    </section>
    """


def _render_status_button(
    *,
    client_id: str,
    status: str,
    selected: bool,
) -> str:
    label = _STATUS_LABELS[status]
    disabled = " disabled" if selected else ""

    return f"""
    <form
        method="post"
        action="/admin/clients/{escape(client_id)}/status"
    >
        <input
            type="hidden"
            name="status"
            value="{escape(status)}"
        >
        <button
            class="primary-button"
            type="submit"
            {disabled}
        >
            {escape(label)}
        </button>
    </form>
    """


def _get_status(
    definition: InstanceDefinition,
) -> str:
    status = definition.metadata.get(
        "admin_status",
        "active",
    )

    if status not in _STATUSES:
        return "draft"

    return status


def _not_found_response(
    page_renderer: PageRenderer,
) -> HTMLResponse:
    return HTMLResponse(
        content=page_renderer(
            title="Bot no encontrado",
            content="<h1>Bot no encontrado</h1>",
        ),
        status_code=404,
    )