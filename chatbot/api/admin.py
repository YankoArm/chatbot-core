from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from html import escape
import re
from urllib.parse import parse_qs
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from typing import Protocol

from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse

from chatbot.api.admin_business import (
    build_admin_business_router,
)
from chatbot.api.admin_faq import (
    build_admin_faq_router,
)
from chatbot.api.admin_schedule import (
    build_admin_schedule_router,
)
from chatbot.api.admin_services import (
    build_admin_services_router,
)
from chatbot.clients.registry import (
    UnknownClientError,
    build_client_definition,
    build_client_instance,
    build_instance_from_definition,
    list_template_ids,
    list_client_ids,
)
from chatbot.instances import (
    Instance,
    InstanceDefinition,
)


class InstanceDefinitionRepositoryProtocol(
    Protocol
):
    def get(
        self,
        client_id: str,
    ) -> InstanceDefinition | None:
        ...

    def list_all(
        self,
    ) -> tuple[InstanceDefinition, ...]:
        ...

_STYLES = """
:root {
    color-scheme: dark;
    font-family:
        Inter,
        ui-sans-serif,
        system-ui,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
    background: #07111f;
    color: #e8eef8;
}

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    min-height: 100vh;
    background:
        radial-gradient(
            circle at top right,
            rgba(46, 196, 182, 0.16),
            transparent 32rem
        ),
        linear-gradient(
            145deg,
            #07111f,
            #0b1728
        );
}

header {
    border-bottom: 1px solid rgba(148, 163, 184, 0.18);
    background: rgba(7, 17, 31, 0.82);
    backdrop-filter: blur(16px);
}

.header-content,
main {
    width: min(1120px, calc(100% - 40px));
    margin: 0 auto;
}

.header-content {
    min-height: 74px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.brand {
    color: #ffffff;
    font-size: 1.15rem;
    font-weight: 750;
    letter-spacing: 0.02em;
    text-decoration: none;
}

.brand span {
    color: #2ec4b6;
}

.environment {
    padding: 7px 11px;
    border: 1px solid rgba(46, 196, 182, 0.32);
    border-radius: 999px;
    color: #82e8dd;
    background: rgba(46, 196, 182, 0.08);
    font-size: 0.78rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

main {
    padding: 58px 0 80px;
}

.eyebrow {
    margin: 0 0 10px;
    color: #2ec4b6;
    font-size: 0.78rem;
    font-weight: 800;
    letter-spacing: 0.12em;
    text-transform: uppercase;
}

h1 {
    margin: 0;
    max-width: 760px;
    color: #ffffff;
    font-size: clamp(2rem, 5vw, 3.4rem);
    line-height: 1.06;
    letter-spacing: -0.04em;
}

.intro {
    max-width: 680px;
    margin: 18px 0 38px;
    color: #9fb0c6;
    font-size: 1.05rem;
    line-height: 1.7;
}

.grid {
    display: grid;
    grid-template-columns:
        repeat(auto-fit, minmax(280px, 1fr));
    gap: 20px;
}

.card,
.panel {
    border: 1px solid rgba(148, 163, 184, 0.16);
    border-radius: 20px;
    background: rgba(15, 30, 50, 0.78);
    box-shadow: 0 22px 70px rgba(0, 0, 0, 0.18);
}

.card {
    display: flex;
    min-height: 265px;
    padding: 25px;
    flex-direction: column;
    transition:
        transform 160ms ease,
        border-color 160ms ease;
}

.card:hover {
    transform: translateY(-3px);
    border-color: rgba(46, 196, 182, 0.48);
}

.card h2 {
    margin: 13px 0 5px;
    color: #ffffff;
    font-size: 1.35rem;
}

.identifier {
    color: #71849c;
    font-family: ui-monospace, monospace;
    font-size: 0.83rem;
}

.tags {
    display: flex;
    margin: 21px 0 25px;
    gap: 8px;
    flex-wrap: wrap;
}

.tag {
    padding: 6px 9px;
    border-radius: 8px;
    color: #b9c8da;
    background: rgba(148, 163, 184, 0.09);
    font-size: 0.76rem;
}

.action {
    margin-top: auto;
    color: #65ddd1;
    font-size: 0.9rem;
    font-weight: 750;
    text-decoration: none;
}

.action:hover {
    color: #a3fff6;
}

.status {
    display: inline-flex;
    width: fit-content;
    align-items: center;
    gap: 7px;
    color: #8df0b0;
    font-size: 0.78rem;
    font-weight: 750;
}

.status::before {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #49d17d;
    content: "";
    box-shadow: 0 0 12px rgba(73, 209, 125, 0.8);
}

.back {
    display: inline-block;
    margin-bottom: 26px;
    color: #85dcd4;
    text-decoration: none;
}

.panel {
    margin-top: 34px;
    padding: 28px;
}

.definition-grid {
    display: grid;
    grid-template-columns:
        repeat(auto-fit, minmax(220px, 1fr));
    gap: 16px;
}

.definition {
    padding: 18px;
    border-radius: 14px;
    background: rgba(5, 14, 26, 0.48);
}

.definition-label {
    display: block;
    margin-bottom: 8px;
    color: #71849c;
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.definition-value {
    color: #e8eef8;
    line-height: 1.55;
}

.admin-form {
    display: grid;
    gap: 22px;
}

.admin-form label {
    display: grid;
    gap: 8px;
    color: #dce7f5;
    font-weight: 700;
}

.admin-form small {
    color: #71849c;
    font-weight: 400;
}

.admin-form input,
.admin-form select {
    width: 100%;
    padding: 13px 14px;
    border: 1px solid rgba(148, 163, 184, 0.24);
    border-radius: 11px;
    outline: none;
    color: #e8eef8;
    background: rgba(5, 14, 26, 0.72);
    font: inherit;
}

.admin-form input:focus,
.admin-form select:focus {
    border-color: #2ec4b6;
    box-shadow: 0 0 0 3px rgba(46, 196, 182, 0.12);
}

.primary-button {
    display: inline-flex;
    width: fit-content;
    margin-bottom: 28px;
    padding: 12px 18px;
    border: 0;
    border-radius: 11px;
    color: #041311;
    background: #2ec4b6;
    font: inherit;
    font-weight: 800;
    text-decoration: none;
    cursor: pointer;
}

.primary-button:hover {
    background: #65ddd1;
}

.admin-form .primary-button {
    margin: 4px 0 0;
}

.danger-button {
    display: inline-flex;
    padding: 12px 18px;
    border: 1px solid rgba(248, 113, 113, 0.48);
    border-radius: 11px;
    color: #fecaca;
    background: rgba(127, 29, 29, 0.28);
    font: inherit;
    font-weight: 800;
    cursor: pointer;
}

.danger-button:hover {
    color: #ffffff;
    background: rgba(185, 28, 28, 0.62);
}
.form-error {
    margin-bottom: 20px;
    padding: 13px 15px;
    border: 1px solid rgba(248, 113, 113, 0.38);
    border-radius: 10px;
    color: #fecaca;
    background: rgba(127, 29, 29, 0.18);
}
.empty {
    color: #71849c;
}
"""


def build_admin_router(
    instance_definition_repository: (
        InstanceDefinitionRepositoryProtocol | None
    ) = None,
) -> APIRouter:
    router = APIRouter()

    def load_instances(
    ) -> tuple[Instance, ...]:
        instances_by_id = {
            client_id: build_client_instance(
                client_id
            )
            for client_id in list_client_ids()
        }

        if instance_definition_repository is not None:
            for definition in (
                instance_definition_repository.list_all()
            ):
                instances_by_id[definition.id] = (
                    build_instance_from_definition(
                        definition
                    )
                )

        return tuple(
            sorted(
                instances_by_id.values(),
                key=lambda instance: (
                    instance.name.casefold(),
                    instance.id,
                ),
            )
        )

    def load_instance(
        client_id: str,
    ) -> Instance:
        if instance_definition_repository is not None:
            stored_definition = (
                instance_definition_repository.get(
                    client_id
                )
            )

            if stored_definition is not None:
                return build_instance_from_definition(
                    stored_definition
                )

        return build_client_instance(
            client_id
        )

    def load_editable_definition(
        client_id: str,
    ) -> InstanceDefinition | None:
        if instance_definition_repository is not None:
            stored_definition = (
                instance_definition_repository.get(
                    client_id
                )
            )

            if stored_definition is not None:
                return stored_definition

        try:
            return build_client_definition(
                client_id
            )
        except UnknownClientError:
            return None
    def render_creation_form(
        *,
        error: str | None = None,
        client_id: str = "",
        name: str = "",
        template_id: str = "",
    ) -> str:

        error_html = ""

        if error is not None:
            error_html = (
                '<div class="form-error">'
                f"{escape(error)}"
                "</div>"
            )

        template_options = "".join(
            (
                '<option value="'
                f'{escape(available_template_id)}"'
                f'{" selected" if available_template_id == template_id else ""}'
                ">"
                f"{escape(available_template_id)}"
                "</option>"
            )
            for available_template_id in (
                list_template_ids()
            )
        )

        return f"""
        <a class="back" href="/admin">← Volver a los bots</a>
        <p class="eyebrow">Nuevo asistente</p>
        <h1>Crear nuevo bot</h1>
        <p class="intro">
            Crea la identidad básica del asistente.
            Después podrás configurar sus servicios,
            horarios y mensajes.
        </p>
        <section class="panel">
            {error_html}
            <form
                class="admin-form"
                method="post"
                action="/admin/clients"
            >
                <label>
                    <span>Identificador</span>
                    <input
                        name="client_id"
                        value="{escape(client_id)}"
                        placeholder="salon_centro"
                        required
                        pattern="[a-z][a-z0-9_]*"
                    >
                    <small>
                        Minúsculas, números y guiones bajos.
                    </small>
                </label>

                <label>
                    <span>Nombre comercial</span>
                    <input
                        name="name"
                        value="{escape(name)}"
                        placeholder="Salón Centro"
                        required
                    >
                </label>

                <label>
                    <span>Plantilla</span>
                    <select
                        name="template_id"
                        required
                    >
                        <option value="">
                            Selecciona una plantilla
                        </option>
                        {template_options}
                    </select>
                </label>

                <button
                    class="primary-button"
                    type="submit"
                >
                    Crear bot
                </button>
            </form>
        </section>
        """

    def render_edit_form(
        *,
        definition: InstanceDefinition,
        supported_languages: list[str],
        error: str | None = None,
        name: str | None = None,
        default_language: str | None = None,
        timezone: str | None = None,
        whatsapp_phone_number_id: str | None = None,
        calendar_id: str | None = None,
    ) -> str:
        visible_name = (
            definition.name
            if name is None
            else name
        )
        visible_language = (
            definition.default_language
            or supported_languages[0]
            if default_language is None
            else default_language
        )

        booking_settings = definition.settings.get(
            "booking",
            {},
        )
        stored_timezone = booking_settings.get(
            "timezone",
            "Europe/Madrid",
        )
        visible_timezone = (
            stored_timezone
            if timezone is None
            else timezone
        )

        visible_phone_number_id = (
            definition.whatsapp_phone_number_id
            if whatsapp_phone_number_id is None
            else whatsapp_phone_number_id
        )
        visible_calendar_id = (
            definition.calendar_id
            if calendar_id is None
            else calendar_id
        )

        error_html = ""

        if error is not None:
            error_html = (
                '<div class="form-error">'
                f"{escape(error)}"
                "</div>"
            )

        language_options = "".join(
            (
                f'<option value="{escape(language)}"'
                f'{" selected" if language == visible_language else ""}'
                ">"
                f"{escape(language.upper())}"
                "</option>"
            )
            for language in supported_languages
        )

        return f"""
        <a
            class="back"
            href="/admin/clients/{escape(definition.id)}"
        >
            ← Volver al bot
        </a>
        <p class="eyebrow">Configuración básica</p>
        <h1>Editar bot</h1>
        <p class="intro">
            Actualiza la identidad, el idioma principal
            y la zona horaria del asistente.
        </p>
        <section class="panel">
            {error_html}
            <form
                class="admin-form"
                method="post"
                action="/admin/clients/{escape(definition.id)}"
            >
                <label>
                    <span>Identificador</span>
                    <input
                        value="{escape(definition.id)}"
                        disabled
                    >
                    <small>
                        El identificador no puede modificarse.
                    </small>
                </label>

                <label>
                    <span>Nombre comercial</span>
                    <input
                        name="name"
                        value="{escape(visible_name)}"
                        required
                    >
                </label>

                <label>
                    <span>Idioma principal</span>
                    <select
                        name="default_language"
                        required
                    >
                        {language_options}
                    </select>
                </label>

                <label>
                    <span>Zona horaria</span>
                    <input
                        name="timezone"
                        value="{escape(visible_timezone)}"
                        required
                        placeholder="Europe/Madrid"
                    >
                </label>

                <label>
                    <span>WhatsApp phone number ID</span>
                    <input
                        name="whatsapp_phone_number_id"
                        value="{escape(visible_phone_number_id or "")}"
                        placeholder="Identificador del número en Meta"
                    >
                </label>

                <label>
                    <span>Google Calendar ID</span>
                    <input
                        name="calendar_id"
                        value="{escape(visible_calendar_id or "")}"
                        placeholder="primary o identificador del calendario"
                    >
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
        "/admin",
        response_class=HTMLResponse,
    )
    def admin_home(
    ) -> HTMLResponse:
        cards = "".join(
            _render_client_card(
                instance
            )
            for instance in load_instances()
        )

        content = f"""
        <p class="eyebrow">Workspace</p>
        <h1>Gestiona tus asistentes desde un único lugar.</h1>
        <p class="intro">
            Consulta los bots registrados, sus plantillas,
            canales y capacidades activas.
        </p>
        <a
            class="primary-button"
            href="/admin/clients/new"
        >
            Crear bot
        </a>
        <section class="grid">
            {cards}
        </section>
        """

        return HTMLResponse(
            content=_render_page(
                title="Bots",
                content=content,
            )
        )

    @router.get(
        "/admin/clients/new",
        response_class=HTMLResponse,
    )
    def admin_new_client(
    ) -> HTMLResponse:
        return HTMLResponse(
            content=_render_page(
                title="Crear bot",
                content=render_creation_form(),
            )
        )

    @router.post(
        "/admin/clients",
    )
    async def admin_create_client(
        request: Request,
    ) -> Response:
        if instance_definition_repository is None:
            return HTMLResponse(
                content=_render_page(
                    title="Administración no disponible",
                    content=render_creation_form(
                        error=(
                            "El almacenamiento administrativo "
                            "no está disponible."
                        ),
                    ),
                ),
                status_code=503,
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

        client_id = (
            form_data.get(
                "client_id",
                [""],
            )[0].strip()
        )
        name = (
            form_data.get(
                "name",
                [""],
            )[0].strip()
        )
        template_id = (
            form_data.get(
                "template_id",
                [""],
            )[0].strip()
        )

        error: str | None = None
        status_code = 422

        if not re.fullmatch(
            r"[a-z][a-z0-9_]{2,63}",
            client_id,
        ):
            error = (
                "El identificador debe tener entre 3 y 64 "
                "caracteres y usar minúsculas, números "
                "o guiones bajos."
            )
        elif not name:
            error = (
                "El nombre comercial es obligatorio."
            )
        elif template_id not in list_template_ids():
            error = (
                "La plantilla seleccionada no es válida."
            )
        elif (
            client_id in list_client_ids()
            or instance_definition_repository.get(
                client_id
            ) is not None
        ):
            error = (
                "Ya existe un bot con ese identificador."
            )
            status_code = 409

        if error is not None:
            return HTMLResponse(
                content=_render_page(
                    title="Crear bot",
                    content=render_creation_form(
                        error=error,
                        client_id=client_id,
                        name=name,
                        template_id=template_id,
                    ),
                ),
                status_code=status_code,
            )

        definition = InstanceDefinition(
            id=client_id,
            name=name,
            template_id=template_id,
            settings={
                "branding": {
                    "display_name": name,
                },
            },
            metadata={
                "admin_status": "draft",
            },
        )

        instance_definition_repository.save(
            definition
        )

        return RedirectResponse(
            url=(
                f"/admin/clients/{client_id}"
            ),
            status_code=303,
        )

    @router.get(
        "/admin/clients/{client_id}/edit",
        response_class=HTMLResponse,
    )
    def admin_edit_client(
        client_id: str,
    ) -> Response:
        if instance_definition_repository is None:
            return HTMLResponse(
                content=_render_page(
                    title="Edición no disponible",
                    content="<h1>Edición no disponible</h1>",
                ),
                status_code=503,
            )

        definition = load_editable_definition(
            client_id
        )

        if definition is None:
            return HTMLResponse(
                content=_render_page(
                    title="Bot no encontrado",
                    content="<h1>Bot no encontrado</h1>",
                ),
                status_code=404,
            )

        resolved_instance = (
            build_instance_from_definition(
                definition
            )
        )

        return HTMLResponse(
            content=_render_page(
                title=f"Editar {definition.name}",
                content=render_edit_form(
                    definition=definition,
                    supported_languages=(
                        resolved_instance.supported_languages
                    ),
                ),
            )
        )

    @router.post(
        "/admin/clients/{client_id}",
    )
    async def admin_update_client(
        client_id: str,
        request: Request,
    ) -> Response:
        if instance_definition_repository is None:
            return HTMLResponse(
                content=_render_page(
                    title="Edición no disponible",
                    content="<h1>Edición no disponible</h1>",
                ),
                status_code=503,
            )

        definition = load_editable_definition(
            client_id
        )

        if definition is None:
            return HTMLResponse(
                content=_render_page(
                    title="Bot no encontrado",
                    content="<h1>Bot no encontrado</h1>",
                ),
                status_code=404,
            )

        resolved_instance = (
            build_instance_from_definition(
                definition
            )
        )
        supported_languages = (
            resolved_instance.supported_languages
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

        name = (
            form_data.get(
                "name",
                [""],
            )[0].strip()
        )
        default_language = (
            form_data.get(
                "default_language",
                [""],
            )[0].strip()
        )
        timezone = (
            form_data.get(
                "timezone",
                [""],
            )[0].strip()
        )

        whatsapp_phone_number_id = (
            form_data.get(
                "whatsapp_phone_number_id",
                [""],
            )[0].strip()
            or None
        )
        calendar_id = (
            form_data.get(
                "calendar_id",
                [""],
            )[0].strip()
            or None
        )
        error: str | None = None

        if not name:
            error = (
                "El nombre comercial es obligatorio."
            )
        elif (
            default_language
            not in supported_languages
        ):
            error = (
                "El idioma principal no es válido "
                "para esta plantilla."
            )
        else:
            try:
                ZoneInfo(
                    timezone
                )
            except (
                ZoneInfoNotFoundError,
                ValueError,
            ):
                error = (
                    "La zona horaria no es válida."
                )

        if error is None:
            for existing_definition in (
                instance_definition_repository.list_all()
            ):
                if existing_definition.id == definition.id:
                    continue

                if (
                    whatsapp_phone_number_id is not None
                    and existing_definition
                    .whatsapp_phone_number_id
                    == whatsapp_phone_number_id
                ):
                    error = (
                        "El WhatsApp phone number ID ya está "
                        "asociado a otro bot."
                    )
                    break

                if (
                    calendar_id is not None
                    and existing_definition.calendar_id
                    == calendar_id
                ):
                    error = (
                        "El Google Calendar ID ya está asociado "
                        "a otro bot."
                    )
                    break
        if error is not None:
            return HTMLResponse(
                content=_render_page(
                    title=f"Editar {definition.name}",
                    content=render_edit_form(
                        definition=definition,
                        supported_languages=(
                            supported_languages
                        ),
                        error=error,
                        name=name,
                        default_language=(
                            default_language
                        ),
                        timezone=timezone,
                        whatsapp_phone_number_id=(
                            whatsapp_phone_number_id
                        ),
                        calendar_id=calendar_id,
                    ),
                ),
                status_code=422,
            )

        settings = deepcopy(
            definition.settings
        )

        branding_settings = settings.setdefault(
            "branding",
            {},
        )
        branding_settings[
            "display_name"
        ] = name

        booking_settings = settings.setdefault(
            "booking",
            {},
        )
        booking_settings[
            "timezone"
        ] = timezone

        updated_definition = replace(
            definition,
            name=name,
            default_language=default_language,
            whatsapp_phone_number_id=(
                whatsapp_phone_number_id
            ),
            calendar_id=calendar_id,
            settings=settings,
        )

        instance_definition_repository.save(
            updated_definition
        )

        return RedirectResponse(
            url=(
                f"/admin/clients/{client_id}"
            ),
            status_code=303,
        )
    @router.get(
        "/admin/clients/{client_id}",
        response_class=HTMLResponse,
    )
    def admin_client_detail(
        client_id: str,
    ) -> HTMLResponse:
        try:
            instance = load_instance(
                client_id
            )
        except UnknownClientError:
            return HTMLResponse(
                content=_render_page(
                    title="Cliente no encontrado",
                    content=(
                        '<a class="back" href="/admin">'
                        "← Volver a los bots"
                        "</a>"
                        "<h1>Cliente no encontrado</h1>"
                        '<p class="intro">'
                        "El bot solicitado no está registrado."
                        "</p>"
                    ),
                ),
                status_code=404,
            )

        content = _render_client_detail(
            instance
        )

        return HTMLResponse(
            content=_render_page(
                title=instance.name,
                content=content,
            )
        )

    router.include_router(
        build_admin_services_router(
            instance_definition_repository=(
                instance_definition_repository
            ),
            definition_loader=(
                load_editable_definition
            ),
            page_renderer=_render_page,
        )
    )

    router.include_router(
        build_admin_schedule_router(
            instance_definition_repository=(
                instance_definition_repository
            ),
            definition_loader=(
                load_editable_definition
            ),
            page_renderer=_render_page,
        )
    )

    router.include_router(
        build_admin_faq_router(
            instance_definition_repository=(
                instance_definition_repository
            ),
            definition_loader=(
                load_editable_definition
            ),
            page_renderer=_render_page,
        )
    )

    router.include_router(
        build_admin_business_router(
            instance_definition_repository=(
                instance_definition_repository
            ),
            definition_loader=(
                load_editable_definition
            ),
            page_renderer=_render_page,
        )
    )

    return router

def _render_client_card(
    instance: Instance,
) -> str:
    tags = _render_tags(
        (
            instance.template_id,
            *instance.channels,
        )
    )

    return f"""
    <article class="card">
        <span class="status">Configurado</span>
        <h2>{escape(instance.name)}</h2>
        <span class="identifier">{escape(instance.id)}</span>
        <div class="tags">{tags}</div>
        <a
            class="action"
            href="/admin/clients/{escape(instance.id)}"
        >
            Ver configuración →
        </a>
    </article>
    """


def _render_client_detail(
    instance: Instance,
) -> str:
    template_id = (
        instance.template_id
        or "Sin plantilla"
    )
    languages = ", ".join(
        instance.supported_languages
    )
    channels = ", ".join(
        instance.channels
    )
    capabilities = ", ".join(
        instance.capabilities
    )

    return f"""
    <a class="back" href="/admin">← Volver a los bots</a>
    <p class="eyebrow">Configuración del bot</p>
    <h1>{escape(instance.name)}</h1>
    <p class="intro">
        Identificador:
        <span class="identifier">{escape(instance.id)}</span>
    </p>
    <a
        class="primary-button"
        href="/admin/clients/{escape(instance.id)}/preview"
    >
        Probar asistente
    </a>
    <a
        class="primary-button"
        href="/admin/clients/{escape(instance.id)}/status"
    >
        Estado del bot
    </a>
    <a
        class="primary-button"
        href="/admin/clients/{escape(instance.id)}/edit"
    >
        Editar configuración
    </a>
    <a
        class="primary-button"
        href="/admin/clients/{escape(instance.id)}/services"
    >
        Servicios y precios
    </a>
    <a
        class="primary-button"
        href="/admin/clients/{escape(instance.id)}/schedule"
    >
        Horarios y reservas
    </a>
    <a
        class="primary-button"
        href="/admin/clients/{escape(instance.id)}/business"
    >
        Información del negocio
    </a>
    <a
        class="primary-button"
        href="/admin/clients/{escape(instance.id)}/faq"
    >
        Preguntas frecuentes
    </a>
    <section class="panel">
        <div class="definition-grid">
            {_render_definition("Plantilla", template_id)}
            {_render_definition("Idioma principal", instance.default_language)}
            {_render_definition("Idiomas", languages)}
            {_render_definition("Canales", channels)}
            {_render_definition("Capacidades", capabilities)}
            {_render_definition(
                "Base de conocimiento",
                instance.knowledge_path or "No configurada",
            )}
        </div>
    </section>
    """

def _render_definition(
    label: str,
    value: str,
) -> str:
    visible_value = (
        value
        if value
        else "No configurado"
    )

    return f"""
    <div class="definition">
        <span class="definition-label">{escape(label)}</span>
        <span class="definition-value">{escape(visible_value)}</span>
    </div>
    """


def _render_tags(
    values: tuple[str | None, ...],
) -> str:
    return "".join(
        f'<span class="tag">{escape(value)}</span>'
        for value in values
        if value
    )


def _render_page(
    *,
    title: str,
    content: str,
) -> str:
    return f"""<!doctype html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <meta
        name="viewport"
        content="width=device-width, initial-scale=1"
    >
    <title>{escape(title)} · FlowForge Admin</title>
    <style>{_STYLES}</style>
</head>
<body>
    <header>
        <div class="header-content">
            <a class="brand" href="/admin">
                FlowForge <span>Admin</span>
            </a>
            <span class="environment">Control panel</span>
        </div>
    </header>
    <main>
        {content}
    </main>
</body>
</html>
"""