from __future__ import annotations

from collections.abc import Callable
from html import escape

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

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
                Todavía no se ha recibido ninguna solicitud
                de contacto para este bot.
            </p>
        </section>
        """
    else:
        body = f"""
        <section class="panel">
            <div class="definition-grid">
                {
                    "".join(
                        _render_lead(lead)
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
        ← Volver al bot
    </a>
    <p class="eyebrow">Contactos comerciales</p>
    <h1>Solicitudes recibidas</h1>
    <p class="intro">
        Contactos que han pedido hablar con una persona.
    </p>
    {body}
    """


def _render_lead(
    lead: Lead,
) -> str:
    return f"""
    <article class="definition">
        <span class="definition-label">Contacto</span>
        <span class="definition-value">
            {escape(lead.name)}
        </span>
        <span class="definition-label">Teléfono</span>
        <span class="definition-value">
            {escape(lead.phone)}
        </span>
        <span class="definition-label">Necesidad</span>
        <span class="definition-value">
            {escape(lead.reason)}
        </span>
        <span class="definition-label">Conversación</span>
        <span class="identifier">
            {escape(lead.session_id)}
        </span>
    </article>
    """