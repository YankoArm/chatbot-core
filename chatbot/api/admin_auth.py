from __future__ import annotations

from hmac import compare_digest
from urllib.parse import parse_qs

from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse


_ADMIN_SESSION_KEY = "flowforge_admin_authenticated"


def build_admin_auth_router(
    *,
    admin_password: str,
    page_renderer,
) -> APIRouter:
    router = APIRouter()

    @router.get("/admin/login")
    def admin_login_page() -> HTMLResponse:
        return HTMLResponse(
            content=page_renderer(
                title="Acceso administrador",
                content=_render_login_page(),
            )
        )

    @router.post("/admin/login")
    async def admin_login(
        request: Request,
    ) -> Response:
        raw_body = (
            await request.body()
        ).decode("utf-8")
        form_data = parse_qs(
            raw_body,
            keep_blank_values=True,
        )
        password = form_data.get(
            "password",
            [""],
        )[0]

        if not compare_digest(
            password,
            admin_password,
        ):
            return HTMLResponse(
                content=page_renderer(
                    title="Acceso administrador",
                    content=_render_login_page(
                        error="Contraseña incorrecta.",
                    ),
                ),
                status_code=401,
            )

        request.session[_ADMIN_SESSION_KEY] = True

        return RedirectResponse(
            url="/admin",
            status_code=303,
        )

    @router.post("/admin/logout")
    def admin_logout(
        request: Request,
    ) -> RedirectResponse:
        request.session.clear()

        return RedirectResponse(
            url="/admin/login",
            status_code=303,
        )

    return router


def is_admin_authenticated(
    request: Request,
) -> bool:
    return request.session.get(
        _ADMIN_SESSION_KEY,
        False,
    ) is True


def _render_login_page(
    *,
    error: str | None = None,
) -> str:
    error_html = ""

    if error is not None:
        error_html = (
            '<div class="form-error">'
            f"{error}"
            "</div>"
        )

    return f"""
    <p class="eyebrow">Administración</p>
    <h1>Acceso a FlowForge</h1>
    <section class="panel">
        <p class="intro">
            Introduce la contraseña de administrador.
        </p>
        {error_html}
        <form
            method="post"
            action="/admin/login"
        >
            <label>
                Contraseña
                <input
                    name="password"
                    type="password"
                    autocomplete="current-password"
                    required
                >
            </label>
            <button
                class="primary-button"
                type="submit"
            >
                Entrar
            </button>
        </form>
    </section>
    """