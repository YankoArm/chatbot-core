from typing import Protocol

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import (
    SessionMiddleware,
)

from chatbot.api.admin_auth import (
    build_admin_auth_router,
    is_admin_authenticated,
)
from chatbot.api.admin import (
    InstanceDefinitionRepositoryProtocol,
    build_admin_router,
)
from chatbot.api.admin_preview import (
    build_admin_preview_router,
)
from chatbot.api.admin_status import (
    build_admin_status_router,
)
from chatbot.api.whatsapp import (
    WhatsAppSignatureVerifierProtocol,
    create_whatsapp_router,
)


class WhatsAppMessageHandlerProtocol(Protocol):
    def handle(
        self,
        payload: dict,
    ) -> object:
        ...


def _render_admin_page(
    *,
    title: str,
    content: str,
) -> str:
    from chatbot.api.admin import _render_page

    return _render_page(
        title=title,
        content=content,
    )


def build_whatsapp_api(
    *,
    message_handler: WhatsAppMessageHandlerProtocol,
    verify_token: str | None = None,
    signature_verifier: (
        WhatsAppSignatureVerifierProtocol | None
    ) = None,
    instance_definition_repository: (
        InstanceDefinitionRepositoryProtocol | None
    ) = None,
    admin_password: str | None = None,
    admin_session_secret: str | None = None,
    admin_session_secure: bool = False,
) -> FastAPI:
    app = FastAPI(
        title="FlowForge WhatsApp API",
        version="1.0.0",
    )

    if (
        (admin_password is None)
        != (admin_session_secret is None)
    ):
        raise ValueError(
            "Admin password and session secret "
            "must be configured together."
        )

    if admin_password is not None:

        @app.middleware("http")
        async def require_admin_login(
            request: Request,
            call_next,
        ):
            if (
                request.url.path.startswith("/admin")
                and request.url.path
                not in {
                    "/admin/login",
                }
                and not is_admin_authenticated(request)
            ):
                return RedirectResponse(
                    url="/admin/login",
                    status_code=303,
                )

            return await call_next(request)

        app.add_middleware(
            SessionMiddleware,
            secret_key=admin_session_secret,
            max_age=43_200,
            same_site="lax",
            https_only=admin_session_secure,
        )
        app.include_router(
            build_admin_auth_router(
                admin_password=admin_password,
                page_renderer=_render_admin_page,
            )
        )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "service": "flowforge-whatsapp",
        }

    @app.get("/ready")
    def ready() -> dict[str, str]:
        return {
            "status": "ready",
            "service": "flowforge-whatsapp",
        }

    app.include_router(
        build_admin_router(
            instance_definition_repository
        )
    )

    app.include_router(
        build_admin_preview_router(
            instance_definition_repository=(
                instance_definition_repository
            ),
            page_renderer=_render_admin_page,
        )
    )

    app.include_router(
        build_admin_status_router(
            instance_definition_repository=(
                instance_definition_repository
            ),
            page_renderer=_render_admin_page,
        )
    )

    app.include_router(
        create_whatsapp_router(
            message_handler=message_handler,
            verify_token=verify_token,
            signature_verifier=signature_verifier,
        )
    )

    return app