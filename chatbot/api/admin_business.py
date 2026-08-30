from __future__ import annotations

import re

from collections.abc import Callable
from copy import deepcopy
from dataclasses import replace
from html import escape
from typing import Any, Protocol
from urllib.parse import (
    parse_qs,
    urlparse,
)

from fastapi import APIRouter, Request, Response
from fastapi.responses import (
    HTMLResponse,
    RedirectResponse,
)

from chatbot.instances import InstanceDefinition


_EMAIL_PATTERN = re.compile(
    r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
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


def build_admin_business_router(
    *,
    instance_definition_repository: (
        InstanceDefinitionRepositoryProtocol | None
    ),
    definition_loader: DefinitionLoader,
    page_renderer: PageRenderer,
) -> APIRouter:
    router = APIRouter()

    def render_business_form(
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

        return f"""
        <a
            class="back"
            href="/admin/clients/{escape(definition.id)}"
        >
            ← Volver al bot
        </a>
        <p class="eyebrow">Identidad y contacto</p>
        <h1>Información del negocio</h1>
        <p class="intro">
            Configura los datos del establecimiento
            y los mensajes principales del asistente.
        </p>
        {error_html}
        <form
            class="admin-form"
            method="post"
            action="/admin/clients/{escape(definition.id)}/business"
        >
            <section class="form-section">
                <h2>Datos comerciales</h2>
                <div class="form-grid">
                    {_render_input(
                        name="company_name",
                        label="Nombre comercial",
                        value=values["company_name"],
                        required=True,
                    )}
                    {_render_input(
                        name="phone",
                        label="Teléfono",
                        value=values["phone"],
                        input_type="tel",
                    )}
                    {_render_input(
                        name="email",
                        label="Correo electrónico",
                        value=values["email"],
                        input_type="email",
                    )}
                    {_render_input(
                        name="website",
                        label="Sitio web",
                        value=values["website"],
                        input_type="url",
                        placeholder="https://ejemplo.es",
                    )}
                    {_render_input(
                        name="address",
                        label="Dirección",
                        value=values["address"],
                    )}
                </div>

                <label>
                    Descripción
                    <textarea
                        name="description"
                        rows="5"
                    >{escape(values["description"])}</textarea>
                </label>
            </section>

            <section class="form-section">
                <h2>Mensaje de bienvenida</h2>
                <p class="form-help">
                    Se utilizará cuando una persona salude al bot.
                </p>
                <label>
                    Español
                    <textarea
                        name="greeting_es"
                        rows="4"
                        required
                    >{escape(values["greeting_es"])}</textarea>
                </label>
                <label>
                    Inglés
                    <textarea
                        name="greeting_en"
                        rows="4"
                    >{escape(values["greeting_en"])}</textarea>
                </label>
            </section>

            <section class="form-section">
                <h2>Transferencia a una persona</h2>
                <p class="form-help">
                    El bot mostrará este mensaje después
                    de registrar la solicitud de atención humana.
                </p>
                <label>
                    Español
                    <textarea
                        name="human_transfer_es"
                        rows="4"
                        required
                    >{escape(values["human_transfer_es"])}</textarea>
                </label>
                <label>
                    Inglés
                    <textarea
                        name="human_transfer_en"
                        rows="4"
                    >{escape(values["human_transfer_en"])}</textarea>
                </label>
            </section>

            <button
                class="primary-button"
                type="submit"
            >
                Guardar información
            </button>
        </form>
        """

    @router.get(
        "/admin/clients/{client_id}/business",
        response_class=HTMLResponse,
    )
    def admin_business(
        client_id: str,
    ) -> Response:
        definition = definition_loader(
            client_id
        )

        if definition is None:
            return _not_found_response(
                page_renderer
            )

        values = _definition_form_values(
            definition
        )

        return HTMLResponse(
            content=page_renderer(
                title=(
                    f"Información · {definition.name}"
                ),
                content=render_business_form(
                    definition=definition,
                    values=values,
                ),
            )
        )

    @router.post(
        "/admin/clients/{client_id}/business",
    )
    async def update_admin_business(
        client_id: str,
        request: Request,
    ) -> Response:
        definition = definition_loader(
            client_id
        )

        if definition is None:
            return _not_found_response(
                page_renderer
            )

        if instance_definition_repository is None:
            return _storage_unavailable_response(
                page_renderer
            )

        values = _complete_form_values(
            await _parse_form(
                request
            )
        )

        try:
            company, greetings, human_transfer = (
                _build_business_knowledge(
                    values
                )
            )
        except ValueError as exc:
            return HTMLResponse(
                content=page_renderer(
                    title=(
                        f"Información · {definition.name}"
                    ),
                    content=render_business_form(
                        definition=definition,
                        values=values,
                        error=str(exc),
                    ),
                ),
                status_code=400,
            )

        updated_settings = deepcopy(
            definition.settings
        )
        knowledge = updated_settings.setdefault(
            "knowledge",
            {},
        )

        if not isinstance(
            knowledge,
            dict,
        ):
            return _invalid_knowledge_response(
                page_renderer
            )

        knowledge["company"] = company
        knowledge["greetings"] = greetings
        knowledge["human_transfer"] = (
            human_transfer
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
    knowledge = definition.settings.get(
        "knowledge",
        {},
    )

    if not isinstance(
        knowledge,
        dict,
    ):
        knowledge = {}

    company = knowledge.get(
        "company",
        {},
    )
    greetings = knowledge.get(
        "greetings",
        {},
    )
    human_transfer = knowledge.get(
        "human_transfer",
        {},
    )

    if not isinstance(
        company,
        dict,
    ):
        company = {}

    welcome = (
        greetings.get(
            "welcome",
            {},
        )
        if isinstance(
            greetings,
            dict,
        )
        else {}
    )
    transfer_response = (
        human_transfer.get(
            "response",
            {},
        )
        if isinstance(
            human_transfer,
            dict,
        )
        else {}
    )

    if not isinstance(
        welcome,
        dict,
    ):
        welcome = {}

    if not isinstance(
        transfer_response,
        dict,
    ):
        transfer_response = {}

    return _complete_form_values({
        "company_name": str(
            company.get(
                "name",
                definition.name,
            )
        ),
        "description": str(
            company.get(
                "description",
                "",
            )
        ),
        "phone": str(
            company.get(
                "phone",
                "",
            )
        ),
        "email": str(
            company.get(
                "email",
                "",
            )
        ),
        "address": str(
            company.get(
                "address",
                "",
            )
        ),
        "website": str(
            company.get(
                "website",
                "",
            )
        ),
        "greeting_es": str(
            welcome.get(
                "es",
                "¡Hola! 👋 ¿En qué puedo ayudarte?",
            )
        ),
        "greeting_en": str(
            welcome.get(
                "en",
                "Hello! 👋 How can I help you?",
            )
        ),
        "human_transfer_es": str(
            transfer_response.get(
                "es",
                (
                    "He registrado tu solicitud. "
                    "Una persona continuará contigo."
                ),
            )
        ),
        "human_transfer_en": str(
            transfer_response.get(
                "en",
                (
                    "I have registered your request. "
                    "A person will continue with you."
                ),
            )
        ),
    })


def _build_business_knowledge(
    values: dict[str, str],
) -> tuple[
    dict[str, str],
    dict[str, dict[str, str]],
    dict[str, dict[str, str]],
]:
    company_name = values[
        "company_name"
    ].strip()
    email = values[
        "email"
    ].strip()
    website = values[
        "website"
    ].strip()
    greeting_es = values[
        "greeting_es"
    ].strip()
    greeting_en = values[
        "greeting_en"
    ].strip()
    human_transfer_es = values[
        "human_transfer_es"
    ].strip()
    human_transfer_en = values[
        "human_transfer_en"
    ].strip()

    if not company_name:
        raise ValueError(
            "El nombre comercial es obligatorio."
        )

    if (
        email
        and not _EMAIL_PATTERN.fullmatch(
            email
        )
    ):
        raise ValueError(
            "El correo electrónico no es válido."
        )

    if website:
        parsed_website = urlparse(
            website
        )

        if (
            parsed_website.scheme
            not in {
                "http",
                "https",
            }
            or not parsed_website.netloc
        ):
            raise ValueError(
                "El sitio web debe ser una URL "
                "completa con http o https."
            )

    if not greeting_es:
        raise ValueError(
            "El saludo en español es obligatorio."
        )

    if not human_transfer_es:
        raise ValueError(
            "El mensaje de transferencia "
            "en español es obligatorio."
        )

    welcome = {
        "es": greeting_es,
    }

    if greeting_en:
        welcome["en"] = greeting_en

    transfer_response = {
        "es": human_transfer_es,
    }

    if human_transfer_en:
        transfer_response["en"] = (
            human_transfer_en
        )

    company = {
        "name": company_name,
        "description": values[
            "description"
        ].strip(),
        "phone": values[
            "phone"
        ].strip(),
        "email": email,
        "address": values[
            "address"
        ].strip(),
        "website": website,
    }

    return (
        company,
        {
            "welcome": welcome,
        },
        {
            "response": transfer_response,
        },
    )


def _complete_form_values(
    values: dict[str, str],
) -> dict[str, str]:
    completed = dict(
        values
    )

    for field_name in (
        "company_name",
        "description",
        "phone",
        "email",
        "address",
        "website",
        "greeting_es",
        "greeting_en",
        "human_transfer_es",
        "human_transfer_en",
    ):
        completed.setdefault(
            field_name,
            "",
        )

    return completed


async def _parse_form(
    request: Request,
) -> dict[str, str]:
    body = (
        await request.body()
    ).decode(
        "utf-8"
    )
    parsed_form = parse_qs(
        body,
        keep_blank_values=True,
    )

    return {
        key: values[0]
        for key, values in parsed_form.items()
    }


def _render_input(
    *,
    name: str,
    label: str,
    value: str,
    input_type: str = "text",
    placeholder: str = "",
    required: bool = False,
) -> str:
    required_attribute = (
        " required"
        if required
        else ""
    )

    return f"""
    <label>
        {label}
        <input
            type="{input_type}"
            name="{name}"
            value="{escape(value)}"
            placeholder="{escape(placeholder)}"
            {required_attribute}
        >
    </label>
    """


def _not_found_response(
    page_renderer: PageRenderer,
) -> HTMLResponse:
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


def _storage_unavailable_response(
    page_renderer: PageRenderer,
) -> HTMLResponse:
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


def _invalid_knowledge_response(
    page_renderer: PageRenderer,
) -> HTMLResponse:
    return HTMLResponse(
        content=page_renderer(
            title="Configuración inválida",
            content=(
                "<h1>Configuración inválida</h1>"
                "<p>La base de conocimiento "
                "no tiene un formato válido.</p>"
            ),
        ),
        status_code=400,
    )