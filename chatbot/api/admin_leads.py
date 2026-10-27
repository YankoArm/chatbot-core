from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from html import escape

from fastapi import APIRouter
from fastapi.responses import (
    HTMLResponse,
    RedirectResponse,
)

from chatbot.leads import (
    Lead,
    LeadRepository,
)


PageRenderer = Callable[..., str]


def build_admin_leads_router(
    *,
    lead_repository: LeadRepository | None,
    page_renderer: PageRenderer,
) -> APIRouter:
    router = APIRouter()

    @router.get(
        "/admin/clients/{client_id}/leads",
        response_class=HTMLResponse,
    )
    def admin_leads(
        client_id: str,
    ) -> HTMLResponse:
        leads = (
            lead_repository.list_by_client(
                client_id=client_id,
            )
            if lead_repository is not None
            else ()
        )

        return HTMLResponse(
            content=page_renderer(
                title="Solicitudes recibidas",
                content=_render_leads_page(
                    client_id=client_id,
                    leads=leads,
                ),
            )
        )

    @router.post(
        "/admin/clients/{client_id}/leads/"
        "{action_id}/contacted"
    )
    def mark_lead_contacted(
        client_id: str,
        action_id: str,
    ) -> RedirectResponse:
        if lead_repository is not None:
            mark_contacted = getattr(
                lead_repository,
                "mark_contacted",
                None,
            )

            if callable(mark_contacted):
                mark_contacted(
                    client_id=client_id,
                    action_id=action_id,
                )

        return RedirectResponse(
            url=(
                f"/admin/clients/"
                f"{client_id}/leads"
            ),
            status_code=303,
        )

    return router


def _render_leads_page(
    *,
    client_id: str,
    leads: tuple[Lead, ...],
) -> str:
    if not leads:
        body = """
        <section class="panel">
            <p class="empty">
                Todav\u00eda no se ha recibido ninguna solicitud
                de contacto para este bot.
            </p>
        </section>
        """
    else:
        pending_count = sum(
            lead.status != "contacted"
            for lead in leads
        )

        body = f"""
        <section class="panel">
            <div class="lead-summary">
                <strong>{len(leads)}</strong>
                solicitudes recibidas
                &middot;
                <strong>{pending_count}</strong>
                pendientes
            </div>

            <div class="definition-grid">
                {
                    "".join(
                        _render_lead(
                            client_id=client_id,
                            lead=lead,
                        )
                        for lead in leads
                    )
                }
            </div>
        </section>
        """

    return f"""
    <a
        class="back"
        href="/admin/clients/{escape(client_id)}"
    >
        \u2190 Volver al bot
    </a>

    <p class="eyebrow">Atenci\u00f3n comercial</p>
    <h1>Solicitudes recibidas</h1>
    <p class="intro">
        Contactos capturados por el asistente
        cuando una persona solicita atenci\u00f3n humana.
    </p>

    {body}
    """


def _render_lead(
    *,
    client_id: str,
    lead: Lead,
) -> str:
    contacted = (
        lead.status == "contacted"
    )

    status_label = (
        "Contactado"
        if contacted
        else "Pendiente"
    )

    contacted_html = ""

    if contacted and lead.contacted_at:
        contacted_html = f"""
        <span class="definition-label">
            Contactado
        </span>
        <span class="definition-value">
            {escape(_format_timestamp(lead.contacted_at))}
        </span>
        """

    action_html = ""

    if not contacted:
        action_html = f"""
        <form
            method="post"
            action="/admin/clients/{escape(client_id)}/leads/{escape(lead.action_id)}/contacted"
        >
            <button
                class="secondary-button"
                type="submit"
            >
                Marcar como contactado
            </button>
        </form>
        """

    return f"""
    <article class="definition lead-card">
        <div class="lead-card-header">
            <strong class="lead-name">
                {escape(lead.name)}
            </strong>
            <span class="lead-status lead-status-{escape(lead.status)}">
                {status_label}
            </span>
        </div>

        <span class="definition-label">
            Tel\u00e9fono
        </span>
        <span class="definition-value">
            <a
                class="action"
                href="tel:{escape(lead.phone)}"
            >
                {escape(lead.phone)}
            </a>
        </span>

        <span class="definition-label">
            Necesidad
        </span>
        <span class="definition-value">
            {escape(lead.reason)}
        </span>

        <span class="definition-label">
            Recibida
        </span>
        <span class="definition-value">
            {escape(_format_timestamp(lead.created_at))}
        </span>

        {contacted_html}

        <span class="definition-label">
            Conversaci\u00f3n
        </span>
        <span class="identifier">
            {escape(lead.session_id)}
        </span>

        <div class="lead-actions">
            {action_html}
        </div>
    </article>
    """


def _format_timestamp(
    value: str,
) -> str:
    try:
        normalized = value.replace(
            "Z",
            "+00:00",
        )

        parsed = datetime.fromisoformat(
            normalized
        )

        if parsed.tzinfo is None:
            parsed = parsed.replace(
                tzinfo=timezone.utc
            )

        parsed = parsed.astimezone(
            timezone.utc
        )

        return parsed.strftime(
            "%d/%m/%Y %H:%M UTC"
        )
    except ValueError:
        return value
