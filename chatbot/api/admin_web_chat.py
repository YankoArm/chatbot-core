from __future__ import annotations

import os
import re
import secrets
from dataclasses import replace
from html import escape
from typing import Any, Callable
from urllib.parse import parse_qs, urlsplit

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from chatbot.clients.registry import build_instance_from_definition


WIDGET_ID_PATTERN = re.compile(r"[A-Za-z0-9_-]{12,96}\Z")


def normalize_origins(raw: str) -> list[str]:
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    if len(lines) > 10:
        raise ValueError("Se permiten como maximo 10 dominios.")

    origins: list[str] = []
    for line in lines:
        if len(line) > 250:
            raise ValueError("Un dominio es demasiado largo.")

        try:
            parsed = urlsplit(line)
            host = parsed.hostname
            port = parsed.port
        except ValueError as error:
            raise ValueError("Dominio no valido.") from error

        if (
            parsed.scheme not in {"https", "http"}
            or not host
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path not in {"", "/"}
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("Introduce solo el origen, sin rutas ni parametros.")

        if parsed.scheme == "http" and host not in {
            "localhost", "127.0.0.1", "::1"
        }:
            raise ValueError("Los dominios publicos deben usar HTTPS.")

        if not re.fullmatch(r"[A-Za-z0-9.-]+", host) and host != "::1":
            raise ValueError("Nombre de dominio no valido.")

        # Accessing parsed.port above rejects malformed ports.
        _ = port
        origin = f"{parsed.scheme}://{parsed.netloc.lower()}"
        if origin not in origins:
            origins.append(origin)

    return origins


def create_unique_widget_id(repository: Any) -> str:
    used = {
        (definition.settings.get("web_chat") or {}).get("widget_id")
        for definition in repository.list_all()
        if isinstance(definition.settings.get("web_chat"), dict)
    }
    for _ in range(20):
        widget_id = "wf_" + secrets.token_urlsafe(24)
        if widget_id not in used:
            return widget_id
    raise RuntimeError("No se pudo generar un widget unico.")


def build_admin_web_chat_router(
    *,
    instance_definition_repository: Any,
    page_renderer: Callable[..., str],
) -> APIRouter:
    router = APIRouter()

    def get_definition(client_id: str) -> Any:
        if instance_definition_repository is None:
            return None
        return instance_definition_repository.get(client_id)

    def render(
        definition: Any,
        *,
        error: str | None = None,
        origin_text: str | None = None,
        enabled_value: bool | None = None,
    ) -> HTMLResponse:
        settings = definition.settings.get("web_chat") or {}
        if not isinstance(settings, dict):
            settings = {}

        stored_origins = settings.get("allowed_origins") or []
        if not isinstance(stored_origins, list):
            stored_origins = []

        visible_origins = (
            "\n".join(str(value) for value in stored_origins)
            if origin_text is None else origin_text
        )
        enabled = (
            settings.get("enabled") is True
            if enabled_value is None else enabled_value
        )
        widget_id = settings.get("widget_id") or ""
        can_use_web = "web" in build_instance_from_definition(definition).channels
        status = definition.metadata.get("admin_status", "draft")
        base_url = os.getenv(
            "FLOWFORGE_PUBLIC_BASE_URL", "https://chatbot.easyappcode.com"
        ).strip().rstrip("/")

        code = (
            f'<script src="{base_url}/webchat/embed.js" '
            f'data-flowforge-widget="{widget_id}" defer></script>'
            if widget_id else "Guarda la configuracion para generar el codigo."
        )
        warning = (
            "Selecciona Solo Chat Web o Ambos en Editar configuracion "
            "antes de activar este widget."
            if not can_use_web else
            "El widget web solo funcionara cuando se habilite el canal "
            "en el servidor y se completen las protecciones pendientes."
        )
        error_html = (
            f'<div class="form-error">{escape(error)}</div>' if error else ""
        )
        checked = " checked" if enabled else ""
        client_id = escape(definition.id, quote=True)
        content = f"""
        <a class="back" href="/admin/clients/{client_id}">
            &larr; Volver al bot
        </a>
        <p class="eyebrow">Canal web</p>
        <h1>Chat Web de {escape(definition.name)}</h1>
        <p class="intro">Configura el widget instalable en la web del negocio.</p>
        <section class="panel">
            {error_html}
            <p>{escape(warning)}</p>
            <p>Estado del asistente: {escape(str(status))}</p>
            <form class="admin-form" method="post"
                  action="/admin/clients/{client_id}/web-chat">
                <label>
                    <span>Activar configuracion del widget</span>
                    <input type="checkbox" name="enabled" value="on"{checked}>
                </label>
                <label>
                    <span>Dominios autorizados (uno por linea)</span>
                    <textarea name="allowed_origins" rows="5"
                        placeholder="https://www.ejemplo.com">{escape(visible_origins)}</textarea>
                    <small>HTTPS obligatorio. Para pruebas locales se permite localhost.</small>
                </label>
                <button class="primary-button" type="submit">
                    Guardar Chat Web
                </button>
            </form>
        </section>
        <section class="panel">
            <h2>Codigo de instalacion</h2>
            <p>Identificador: <code>{escape(str(widget_id)) if widget_id else 'Pendiente'}</code></p>
            <textarea readonly rows="3" aria-label="Codigo de instalacion">{escape(code)}</textarea>
            <p><small>Codigo preparado para el dominio publico configurado.
            No publicar hasta validar seguridad y despliegue.</small></p>
        </section>
        """
        return HTMLResponse(
            page_renderer(title=f"Chat Web - {definition.name}", content=content),
            status_code=422 if error else 200,
            headers={"Cache-Control": "no-store"},
        )

    @router.get("/admin/clients/{client_id}/web-chat")
    def show_web_chat(client_id: str) -> HTMLResponse:
        if instance_definition_repository is None:
            return HTMLResponse("Administracion no disponible", status_code=503)
        definition = get_definition(client_id)
        if definition is None:
            return HTMLResponse("Bot no encontrado", status_code=404)
        return render(definition)

    @router.post("/admin/clients/{client_id}/web-chat")
    async def save_web_chat(client_id: str, request: Request):
        if instance_definition_repository is None:
            return HTMLResponse("Administracion no disponible", status_code=503)
        definition = get_definition(client_id)
        if definition is None:
            return HTMLResponse("Bot no encontrado", status_code=404)

        body = (await request.body()).decode("utf-8")
        data = parse_qs(body, keep_blank_values=True)
        enabled = data.get("enabled", [""])[0] == "on"
        origins_text = data.get("allowed_origins", [""])[0]

        try:
            origins = normalize_origins(origins_text)
        except ValueError as error:
            return render(
                definition, error=str(error),
                origin_text=origins_text, enabled_value=enabled,
            )

        if enabled and "web" not in build_instance_from_definition(definition).channels:
            return render(
                definition,
                error="Este bot no tiene seleccionado el canal Web.",
                origin_text=origins_text, enabled_value=enabled,
            )
        if enabled and not origins:
            return render(
                definition,
                error="Indica al menos un dominio autorizado.",
                origin_text=origins_text, enabled_value=enabled,
            )

        settings = dict(definition.settings)
        web = dict(settings.get("web_chat") or {})
        widget_id = web.get("widget_id")
        if widget_id and not WIDGET_ID_PATTERN.fullmatch(str(widget_id)):
            return render(definition, error="Identificador de widget no valido.")
        if not widget_id:
            widget_id = create_unique_widget_id(instance_definition_repository)

        for other in instance_definition_repository.list_all():
            if other.id == definition.id:
                continue
            other_web = other.settings.get("web_chat") or {}
            if isinstance(other_web, dict) and other_web.get("widget_id") == widget_id:
                return HTMLResponse("Widget duplicado", status_code=409)

        web.update({
            "widget_id": widget_id,
            "enabled": enabled,
            "allowed_origins": origins,
        })
        settings["web_chat"] = web
        instance_definition_repository.save(replace(definition, settings=settings))
        return RedirectResponse(
            url=f"/admin/clients/{client_id}/web-chat",
            status_code=303,
        )

    return router
