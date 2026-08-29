from typing import Protocol

from fastapi import FastAPI

from chatbot.api.admin import (
    InstanceDefinitionRepositoryProtocol,
    build_admin_router,
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
) -> FastAPI:
    app = FastAPI(
        title="FlowForge WhatsApp API",
        version="1.0.0",
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
        create_whatsapp_router(
            message_handler=message_handler,
            verify_token=verify_token,
            signature_verifier=signature_verifier,
        )
    )

    return app