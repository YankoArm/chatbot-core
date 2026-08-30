from __future__ import annotations

import re

from collections.abc import Callable
from copy import deepcopy
from dataclasses import replace
from html import escape
from typing import Any, Protocol
from urllib.parse import parse_qs

from fastapi import APIRouter, Request, Response
from fastapi.responses import (
    HTMLResponse,
    RedirectResponse,
)

from chatbot.instances import InstanceDefinition
from chatbot.knowledge import JsonKnowledgeProvider


_FAQ_ID_PATTERN = re.compile(
    r"^[a-z][a-z0-9_]*$"
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


def build_admin_faq_router(
    *,
    instance_definition_repository: (
        InstanceDefinitionRepositoryProtocol | None
    ),
    definition_loader: DefinitionLoader,
    page_renderer: PageRenderer,
) -> APIRouter:
    router = APIRouter()

    def render_faq_page(
        definition: InstanceDefinition,
    ) -> str:
        faq_entries = _get_effective_faq_entries(
            definition
        )

        if faq_entries:
            cards = "".join(
                _render_faq_card(
                    client_id=definition.id,
                    faq_id=faq_id,
                    entry=entry,
                )
                for faq_id, entry in faq_entries.items()
            )
        else:
            cards = (
                '<p class="empty">'
                "Este bot todavía no tiene "
                "preguntas frecuentes configuradas."
                "</p>"
            )

        return f"""
        <a
            class="back"
            href="/admin/clients/{escape(definition.id)}"
        >
            ← Volver al bot
        </a>
        <p class="eyebrow">Conocimiento</p>
        <h1>Preguntas frecuentes</h1>
        <p class="intro">
            Configura las preguntas que el asistente
            podrá reconocer y responder.
        </p>
        <a
            class="primary-button"
            href="/admin/clients/{escape(definition.id)}/faq/new"
        >
            Añadir pregunta
        </a>
        <section class="grid">
            {cards}
        </section>
        """

    def render_faq_form(
        *,
        definition: InstanceDefinition,
        error: str | None = None,
        values: dict[str, str] | None = None,
    ) -> str:
        form_values = _complete_form_values(
            values or {}
        )
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
            href="/admin/clients/{escape(definition.id)}/faq"
        >
            ← Volver a preguntas frecuentes
        </a>
        <p class="eyebrow">Conocimiento</p>
        <h1>Añadir pregunta frecuente</h1>
        <p class="intro">
            Añade varias expresiones que los clientes
            podrían utilizar para realizar la pregunta.
        </p>
        {error_html}
        <form
            class="admin-form"
            method="post"
            action="/admin/clients/{escape(definition.id)}/faq"
        >
            <label>
                Identificador interno
                <input
                    name="faq_id"
                    value="{escape(form_values["faq_id"])}"
                    placeholder="payment_methods"
                    pattern="[a-z][a-z0-9_]*"
                    required
                >
            </label>

            <label>
                Pregunta
                <input
                    name="question"
                    value="{escape(form_values["question"])}"
                    placeholder="¿Cómo puedo pagar?"
                    required
                >
            </label>

            <label>
                Palabras o frases clave
                <textarea
                    name="keywords"
                    rows="6"
                    placeholder="formas de pago&#10;pagar con tarjeta&#10;aceptáis Bizum"
                    required
                >{escape(form_values["keywords"])}</textarea>
            </label>

            <label>
                Respuesta en español
                <textarea
                    name="answer_es"
                    rows="6"
                    required
                >{escape(form_values["answer_es"])}</textarea>
            </label>

            <label>
                Respuesta en inglés
                <textarea
                    name="answer_en"
                    rows="6"
                >{escape(form_values["answer_en"])}</textarea>
            </label>

            <button
                class="primary-button"
                type="submit"
            >
                Guardar pregunta
            </button>
        </form>
        """

    @router.get(
        "/admin/clients/{client_id}/faq",
        response_class=HTMLResponse,
    )
    def admin_faq(
        client_id: str,
    ) -> Response:
        definition = definition_loader(
            client_id
        )

        if definition is None:
            return _not_found_response(
                page_renderer
            )

        return HTMLResponse(
            content=page_renderer(
                title=(
                    f"FAQ · {definition.name}"
                ),
                content=render_faq_page(
                    definition
                ),
            )
        )

    @router.get(
        "/admin/clients/{client_id}/faq/new",
        response_class=HTMLResponse,
    )
    def new_admin_faq(
        client_id: str,
    ) -> Response:
        definition = definition_loader(
            client_id
        )

        if definition is None:
            return _not_found_response(
                page_renderer
            )

        return HTMLResponse(
            content=page_renderer(
                title=(
                    f"Nueva pregunta · {definition.name}"
                ),
                content=render_faq_form(
                    definition=definition,
                ),
            )
        )

    @router.post(
        "/admin/clients/{client_id}/faq",
    )
    async def create_admin_faq(
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

        values = await _parse_form(
            request
        )

        try:
            faq_id, faq_entry = _build_faq_entry(
                values
            )
            existing_entries = (
                _get_effective_faq_entries(
                    definition
                )
            )

            if faq_id in existing_entries:
                raise ValueError(
                    "Ya existe una pregunta "
                    "con ese identificador."
                )
        except ValueError as exc:
            return HTMLResponse(
                content=page_renderer(
                    title=(
                        f"Nueva pregunta · {definition.name}"
                    ),
                    content=render_faq_form(
                        definition=definition,
                        error=str(exc),
                        values=values,
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

        faq_entries = knowledge.setdefault(
            "faq",
            {},
        )

        if not isinstance(
            faq_entries,
            dict,
        ):
            return _invalid_knowledge_response(
                page_renderer
            )

        faq_entries[faq_id] = faq_entry

        updated_definition = replace(
            definition,
            settings=updated_settings,
        )

        instance_definition_repository.save(
            updated_definition
        )

        return RedirectResponse(
            url=(
                f"/admin/clients/{definition.id}/faq"
            ),
            status_code=303,
        )

    @router.get(
        "/admin/clients/{client_id}/faq/{faq_id}/edit",
        response_class=HTMLResponse,
    )
    def edit_admin_faq(
        client_id: str,
        faq_id: str,
    ) -> Response:
        definition = definition_loader(
            client_id
        )

        if definition is None:
            return _not_found_response(
                page_renderer
            )

        faq_entries = _get_effective_faq_entries(
            definition
        )
        entry = faq_entries.get(
            faq_id
        )

        if entry is None:
            return _faq_not_found_response(
                page_renderer
            )

        return HTMLResponse(
            content=page_renderer(
                title=(
                    f"Editar pregunta · {definition.name}"
                ),
                content=_render_existing_faq_form(
                    definition=definition,
                    faq_id=faq_id,
                    entry=entry,
                ),
            )
        )

    @router.post(
        "/admin/clients/{client_id}/faq/{faq_id}",
    )
    async def update_admin_faq(
        client_id: str,
        faq_id: str,
        request: Request,
    ) -> Response:
        definition = definition_loader(
            client_id
        )

        if definition is None:
            return _not_found_response(
                page_renderer
            )

        faq_entries = _get_effective_faq_entries(
            definition
        )
        existing_entry = faq_entries.get(
            faq_id
        )

        if existing_entry is None:
            return _faq_not_found_response(
                page_renderer
            )

        if instance_definition_repository is None:
            return _storage_unavailable_response(
                page_renderer
            )

        values = await _parse_form(
            request
        )
        values_with_id = dict(
            values
        )
        values_with_id["faq_id"] = faq_id

        try:
            _, updated_entry = _build_faq_entry(
                values_with_id
            )
        except ValueError as exc:
            return HTMLResponse(
                content=page_renderer(
                    title=(
                        f"Editar pregunta · {definition.name}"
                    ),
                    content=_render_existing_faq_form(
                        definition=definition,
                        faq_id=faq_id,
                        entry=existing_entry,
                        error=str(exc),
                        values=values,
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

        stored_faq = knowledge.setdefault(
            "faq",
            {},
        )

        if not isinstance(
            stored_faq,
            dict,
        ):
            return _invalid_knowledge_response(
                page_renderer
            )

        stored_faq[faq_id] = updated_entry

        updated_definition = replace(
            definition,
            settings=updated_settings,
        )

        instance_definition_repository.save(
            updated_definition
        )

        return RedirectResponse(
            url=(
                f"/admin/clients/{definition.id}/faq"
            ),
            status_code=303,
        )

    @router.get(
        "/admin/clients/{client_id}/faq/{faq_id}/delete",
        response_class=HTMLResponse,
    )
    def confirm_delete_admin_faq(
        client_id: str,
        faq_id: str,
    ) -> Response:
        definition = definition_loader(
            client_id
        )

        if definition is None:
            return _not_found_response(
                page_renderer
            )

        faq_entries = _get_effective_faq_entries(
            definition
        )
        entry = faq_entries.get(
            faq_id
        )

        if entry is None:
            return _faq_not_found_response(
                page_renderer
            )

        return HTMLResponse(
            content=page_renderer(
                title=(
                    f"Eliminar pregunta · {definition.name}"
                ),
                content=_render_delete_confirmation(
                    definition=definition,
                    faq_id=faq_id,
                    entry=entry,
                ),
            )
        )

    @router.post(
        "/admin/clients/{client_id}/faq/{faq_id}/delete",
    )
    def delete_admin_faq(
        client_id: str,
        faq_id: str,
    ) -> Response:
        definition = definition_loader(
            client_id
        )

        if definition is None:
            return _not_found_response(
                page_renderer
            )

        faq_entries = _get_effective_faq_entries(
            definition
        )

        if faq_id not in faq_entries:
            return _faq_not_found_response(
                page_renderer
            )

        if instance_definition_repository is None:
            return _storage_unavailable_response(
                page_renderer
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

        stored_faq = knowledge.setdefault(
            "faq",
            {},
        )

        if not isinstance(
            stored_faq,
            dict,
        ):
            return _invalid_knowledge_response(
                page_renderer
            )

        base_faq_entries = _get_base_faq_entries(
            definition
        )

        if faq_id in base_faq_entries:
            stored_faq[faq_id] = None
        else:
            stored_faq.pop(
                faq_id,
                None,
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
                f"/admin/clients/{definition.id}/faq"
            ),
            status_code=303,
        )

    return router


def _render_existing_faq_form(
    *,
    definition: InstanceDefinition,
    faq_id: str,
    entry: dict[str, Any],
    error: str | None = None,
    values: dict[str, str] | None = None,
) -> str:
    form_values = (
        _complete_form_values(
            values
        )
        if values is not None
        else _faq_entry_form_values(
            entry
        )
    )
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
        href="/admin/clients/{escape(definition.id)}/faq"
    >
        ← Volver a preguntas frecuentes
    </a>
    <p class="eyebrow">Conocimiento</p>
    <h1>Editar pregunta frecuente</h1>
    <p class="intro">
        Actualiza las expresiones reconocidas
        y las respuestas del asistente.
    </p>
    {error_html}
    <form
        class="admin-form"
        method="post"
        action="/admin/clients/{escape(definition.id)}/faq/{escape(faq_id)}"
    >
        <label>
            Identificador interno
            <input
                value="{escape(faq_id)}"
                disabled
            >
        </label>

        <label>
            Pregunta
            <input
                name="question"
                value="{escape(form_values["question"])}"
                required
            >
        </label>

        <label>
            Palabras o frases clave
            <textarea
                name="keywords"
                rows="6"
                required
            >{escape(form_values["keywords"])}</textarea>
        </label>

        <label>
            Respuesta en español
            <textarea
                name="answer_es"
                rows="6"
                required
            >{escape(form_values["answer_es"])}</textarea>
        </label>

        <label>
            Respuesta en inglés
            <textarea
                name="answer_en"
                rows="6"
            >{escape(form_values["answer_en"])}</textarea>
        </label>

        <button
            class="primary-button"
            type="submit"
        >
            Guardar cambios
        </button>
    </form>
    """


def _render_delete_confirmation(
    *,
    definition: InstanceDefinition,
    faq_id: str,
    entry: dict[str, Any],
) -> str:
    question = str(
        entry.get(
            "question",
            faq_id,
        )
    )

    return f"""
    <a
        class="back"
        href="/admin/clients/{escape(definition.id)}/faq"
    >
        ← Volver a preguntas frecuentes
    </a>
    <p class="eyebrow">Confirmación</p>
    <h1>Eliminar pregunta frecuente</h1>
    <p class="intro">
        Vas a eliminar
        <strong>{escape(question)}</strong>.
        El asistente dejará de reconocer
        esta pregunta.
    </p>
    <form
        method="post"
        action="/admin/clients/{escape(definition.id)}/faq/{escape(faq_id)}/delete"
    >
        <button
            class="danger-button"
            type="submit"
        >
            Eliminar definitivamente
        </button>
    </form>
    """


def _faq_entry_form_values(
    entry: dict[str, Any],
) -> dict[str, str]:
    keywords = entry.get(
        "keywords",
        [],
    )
    answers = entry.get(
        "answers",
        {},
    )

    if not isinstance(
        keywords,
        list,
    ):
        keywords = []

    if not isinstance(
        answers,
        dict,
    ):
        answers = {}

    return _complete_form_values({
        "question": str(
            entry.get(
                "question",
                "",
            )
        ),
        "keywords": "\n".join(
            str(keyword)
            for keyword in keywords
        ),
        "answer_es": str(
            answers.get(
                "es",
                "",
            )
        ),
        "answer_en": str(
            answers.get(
                "en",
                "",
            )
        ),
    })


def _faq_not_found_response(
    page_renderer: PageRenderer,
) -> HTMLResponse:
    return HTMLResponse(
        content=page_renderer(
            title="Pregunta no encontrada",
            content=(
                "<h1>Pregunta no encontrada</h1>"
                "<p>La pregunta frecuente solicitada "
                "no existe.</p>"
            ),
        ),
        status_code=404,
    )


def _get_base_faq_entries(
    definition: InstanceDefinition,
) -> dict[str, dict[str, Any]]:
    knowledge_path = definition.knowledge_path

    if not knowledge_path:
        return {}

    provider = JsonKnowledgeProvider()

    try:
        knowledge = provider.load(
            knowledge_path
        )
    except (
        FileNotFoundError,
        NotADirectoryError,
    ):
        return {}

    faq_entries = knowledge.get(
        "faq",
        {},
    )

    if not isinstance(
        faq_entries,
        dict,
    ):
        return {}

    return {
        str(faq_id): deepcopy(entry)
        for faq_id, entry in faq_entries.items()
        if isinstance(
            entry,
            dict,
        )
    }


def _get_inline_faq_overrides(
    definition: InstanceDefinition,
) -> dict[str, Any]:
    knowledge = definition.settings.get(
        "knowledge",
        {},
    )

    if not isinstance(
        knowledge,
        dict,
    ):
        return {}

    faq_entries = knowledge.get(
        "faq",
        {},
    )

    if not isinstance(
        faq_entries,
        dict,
    ):
        return {}

    return {
        str(faq_id): entry
        for faq_id, entry in faq_entries.items()
    }


def _get_effective_faq_entries(
    definition: InstanceDefinition,
) -> dict[str, dict[str, Any]]:
    effective_entries = _get_base_faq_entries(
        definition
    )
    overrides = _get_inline_faq_overrides(
        definition
    )

    for faq_id, override_entry in overrides.items():
        if override_entry is None:
            effective_entries.pop(
                faq_id,
                None,
            )
            continue

        if not isinstance(
            override_entry,
            dict,
        ):
            continue

        base_entry = effective_entries.get(
            faq_id,
            {},
        )

        effective_entries[faq_id] = (
            _deep_merge_dictionary(
                base_entry,
                override_entry,
            )
        )

    return effective_entries


def _deep_merge_dictionary(
    base: dict[str, Any],
    overrides: dict[str, Any],
) -> dict[str, Any]:
    merged = deepcopy(
        base
    )

    for key, override_value in overrides.items():
        base_value = merged.get(
            key
        )

        if (
            isinstance(base_value, dict)
            and isinstance(
                override_value,
                dict,
            )
        ):
            merged[key] = _deep_merge_dictionary(
                base_value,
                override_value,
            )
            continue

        merged[key] = deepcopy(
            override_value
        )

    return merged

def _build_faq_entry(
    values: dict[str, str],
) -> tuple[str, dict[str, Any]]:
    faq_id = values.get(
        "faq_id",
        "",
    ).strip()
    question = values.get(
        "question",
        "",
    ).strip()
    answer_es = values.get(
        "answer_es",
        "",
    ).strip()
    answer_en = values.get(
        "answer_en",
        "",
    ).strip()

    if not _FAQ_ID_PATTERN.fullmatch(
        faq_id
    ):
        raise ValueError(
            "El identificador debe comenzar por una letra "
            "y usar solo minúsculas, números y guiones bajos."
        )

    if not question:
        raise ValueError(
            "La pregunta es obligatoria."
        )

    keywords = _parse_keywords(
        values.get(
            "keywords",
            "",
        )
    )

    if not keywords:
        raise ValueError(
            "Añade al menos una palabra "
            "o frase clave."
        )

    if not answer_es:
        raise ValueError(
            "La respuesta en español es obligatoria."
        )

    answers = {
        "es": answer_es,
    }

    if answer_en:
        answers["en"] = answer_en

    return faq_id, {
        "question": question,
        "keywords": keywords,
        "answers": answers,
    }


def _parse_keywords(
    raw_keywords: str,
) -> list[str]:
    keywords: list[str] = []

    for line in raw_keywords.splitlines():
        keyword = line.strip()

        if (
            keyword
            and keyword not in keywords
        ):
            keywords.append(
                keyword
            )

    return keywords


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


def _complete_form_values(
    values: dict[str, str],
) -> dict[str, str]:
    completed = dict(
        values
    )

    for field_name in (
        "faq_id",
        "question",
        "keywords",
        "answer_es",
        "answer_en",
    ):
        completed.setdefault(
            field_name,
            "",
        )

    return completed


def _render_faq_card(
    *,
    client_id: str,
    faq_id: str,
    entry: dict[str, Any],
) -> str:
    question = str(
        entry.get(
            "question",
            faq_id,
        )
    )
    keywords = entry.get(
        "keywords",
        [],
    )
    answers = entry.get(
        "answers",
        {},
    )

    if not isinstance(
        keywords,
        list,
    ):
        keywords = []

    if not isinstance(
        answers,
        dict,
    ):
        answers = {}

    keyword_tags = "".join(
        (
            '<span class="tag">'
            f"{escape(str(keyword))}"
            "</span>"
        )
        for keyword in keywords
    )

    answer_es = str(
        answers.get(
            "es",
            "Sin respuesta en español.",
        )
    )
    escaped_client_id = escape(
        client_id,
        quote=True,
    )
    escaped_faq_id = escape(
        faq_id,
        quote=True,
    )

    return f"""
    <article class="card">
        <span class="status">FAQ activa</span>
        <h2>{escape(question)}</h2>
        <span class="identifier">
            {escape(faq_id)}
        </span>
        <p>{escape(answer_es)}</p>
        <div class="tags">
            {keyword_tags}
        </div>
        <div class="actions">
            <a
                class="button secondary"
                href="/admin/clients/{escaped_client_id}/faq/{escaped_faq_id}/edit"
            >
                Editar
            </a>
            <a
                class="danger-button"
                href="/admin/clients/{escaped_client_id}/faq/{escaped_faq_id}/delete"
            >
                Eliminar
            </a>
        </div>
    </article>
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