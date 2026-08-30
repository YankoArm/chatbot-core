from __future__ import annotations

import json

from collections.abc import Callable
from dataclasses import replace
from html import escape
from typing import Protocol

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, Response

from chatbot.application.bootstrap import Bootstrap
from chatbot.clients.registry import (
    UnknownClientError,
    build_client_definition,
    build_instance_from_definition,
)
from chatbot.instances import (
    Instance,
    InstanceDefinition,
)

from urllib.parse import parse_qs


_MAX_PREVIEW_MESSAGES = 12


class InstanceDefinitionRepositoryProtocol(
    Protocol
):
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


def build_admin_preview_router(
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

    def build_preview_instance(
        definition: InstanceDefinition,
    ) -> Instance:
        instance = build_instance_from_definition(
            definition
        )

        settings = dict(
            instance.settings
        )
        knowledge = settings.get(
            "knowledge"
        )

        if not isinstance(
            knowledge,
            dict,
        ):
            knowledge = {}

        knowledge = dict(
            knowledge
        )
        knowledge["_preview"] = {}
        settings["knowledge"] = knowledge

        return replace(
            instance,
            capabilities=[
                capability_name
                for capability_name in instance.capabilities
                if capability_name != "booking"
            ],
            settings=settings,
        )
    def run_preview(
        definition: InstanceDefinition,
        messages: list[str],
    ) -> list[str]:
        instance = build_preview_instance(
            definition
        )

        application = Bootstrap().build_from_instance(
            instance
        )

        responses: list[str] = []

        for message in messages:
            if _is_booking_preview_request(
                message
            ):
                responses.append(
                    "Las reservas no se pueden probar aquí "
                    "porque esta vista no se conecta a Calendar."
                )
                continue

            response = application.chat(
                session_id=(
                    f"admin-preview:{definition.id}"
                ),
                message=message,
            )
            responses.append(
                response.text
            )

        return responses
    @router.get(
        "/admin/clients/{client_id}/preview",
        response_class=HTMLResponse,
    )
    def admin_preview(
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
                title=f"Probar {definition.name}",
                content=_render_preview_page(
                    definition=definition,
                    messages=[],
                    responses=[],
                ),
            )
        )

    @router.post(
        "/admin/clients/{client_id}/preview",
        response_class=HTMLResponse,
    )
    async def admin_preview_message(
        client_id: str,
        request: Request,
    ) -> Response:
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

        try:
            history = _parse_history(
                form_data.get(
                    "history",
                    ["[]"],
                )[0]
            )
            message = form_data.get(
                "message",
                [""],
            )[0].strip()

            if not message:
                raise ValueError(
                    "Escribe un mensaje para probar el asistente."
                )

            if len(history) >= _MAX_PREVIEW_MESSAGES:
                raise ValueError(
                    "La vista previa admite un máximo de "
                    f"{_MAX_PREVIEW_MESSAGES} mensajes. "
                    "Inicia una nueva conversación."
                )

            messages = [
                *history,
                message,
            ]
            responses = run_preview(
                definition,
                messages,
            )
        except (
            ValueError,
            json.JSONDecodeError,
        ) as error:
            return HTMLResponse(
                content=page_renderer(
                    title=f"Probar {definition.name}",
                    content=_render_preview_page(
                        definition=definition,
                        messages=[],
                        responses=[],
                        error=str(error),
                    ),
                ),
                status_code=422,
            )

        return HTMLResponse(
            content=page_renderer(
                title=f"Probar {definition.name}",
                content=_render_preview_page(
                    definition=definition,
                    messages=messages,
                    responses=responses,
                ),
            )
        )

    return router

def _is_booking_preview_request(
    message: str,
) -> bool:
    normalized_message = message.casefold()

    booking_terms = (
        "reservar",
        "reserva",
        "cita",
        "booking",
        "appointment",
    )

    return any(
        term in normalized_message
        for term in booking_terms
    )

def _parse_history(
    raw_history: str,
) -> list[str]:
    parsed_history = json.loads(
        raw_history
    )

    if not isinstance(
        parsed_history,
        list,
    ):
        raise ValueError(
            "El historial de vista previa no es válido."
        )

    if len(parsed_history) > _MAX_PREVIEW_MESSAGES:
        raise ValueError(
            "El historial de vista previa es demasiado largo."
        )

    messages: list[str] = []

    for item in parsed_history:
        if not isinstance(
            item,
            str,
        ):
            raise ValueError(
                "El historial de vista previa no es válido."
            )

        message = item.strip()

        if not message:
            raise ValueError(
                "El historial de vista previa no es válido."
            )

        messages.append(
            message
        )

    return messages


def _render_preview_page(
    *,
    definition: InstanceDefinition,
    messages: list[str],
    responses: list[str],
    error: str | None = None,
) -> str:
    error_html = ""

    if error is not None:
        error_html = (
            '<div class="form-error">'
            f"{escape(error)}"
            "</div>"
        )

    history = json.dumps(
        messages,
        ensure_ascii=False,
    )

    return f"""
    <a
        class="back"
        href="/admin/clients/{escape(definition.id)}"
    >
        ← Volver al bot
    </a>
    <p class="eyebrow">Entorno de pruebas</p>
    <h1>Prueba el asistente</h1>
    <p class="intro">
        Comprueba cómo responde {escape(definition.name)}
        con su configuración actual.
    </p>
    <section class="panel">
        <p class="intro">
            Las reservas están desactivadas en esta vista:
            no se crea ninguna cita ni se conecta con Calendar.
        </p>
        {error_html}
        <div class="preview-conversation">
            {_render_turns(messages, responses)}
        </div>
        <form
            class="admin-form"
            method="post"
            action="/admin/clients/{escape(definition.id)}/preview"
        >
            <input
                type="hidden"
                name="history"
                value="{escape(history)}"
            >
            <label>
                <span>Mensaje de prueba</span>
                <input
                    name="message"
                    placeholder="Escribe como si fueras un cliente"
                    autocomplete="off"
                    required
                >
            </label>
            <button
                class="primary-button"
                type="submit"
            >
                Enviar mensaje
            </button>
        </form>
    </section>
    """


def _render_turns(
    messages: list[str],
    responses: list[str],
) -> str:
    if not messages:
        return (
            '<p class="empty">'
            "Escribe un mensaje para iniciar la prueba."
            "</p>"
        )

    turns: list[str] = []

    for message, response in zip(
        messages,
        responses,
    ):
        turns.append(
            f"""
            <div class="definition">
                <span class="definition-label">
                    Cliente
                </span>
                <span class="definition-value">
                    {escape(message)}
                </span>
            </div>
            <div class="definition">
                <span class="definition-label">
                    Asistente
                </span>
                <span class="definition-value">
                    {escape(response)}
                </span>
            </div>
            """
        )

    return "".join(
        turns
    )


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