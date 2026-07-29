from __future__ import annotations

from typing import Any, Protocol

from fastapi import (
    APIRouter,
    Header,
    HTTPException,
    Query,
    Request,
)
from fastapi.responses import PlainTextResponse

class WhatsAppMessageHandlerProtocol(Protocol):
    def handle(
        self,
        payload: dict[str, Any],
    ) -> object:
        ...

class WhatsAppSignatureVerifierProtocol(Protocol):
    def verify(
        self,
        *,
        body: bytes,
        signature: str,
    ) -> bool:
        ...


def create_whatsapp_router(
    *,
    message_handler: WhatsAppMessageHandlerProtocol | None = None,
    verify_token: str | None = None,
    signature_verifier: WhatsAppSignatureVerifierProtocol | None = None,
) -> APIRouter:
    router = APIRouter()

    @router.get(
        "/webhook",
        response_class=PlainTextResponse,
    )
    def verify_webhook(
        hub_mode: str = Query(alias="hub.mode"),
        hub_verify_token: str = Query(alias="hub.verify_token"),
        hub_challenge: str = Query(alias="hub.challenge"),
    ) -> str:
        if (
            verify_token is not None
            and hub_verify_token != verify_token
        ):
            raise HTTPException(status_code=403)

        return hub_challenge

    @router.post("/webhook")
    async def receive_webhook(
        request: Request,
        x_hub_signature_256: str | None = Header(
            default=None,
            alias="X-Hub-Signature-256",
        ),
    ) -> dict[str, str]:
        body = await request.body()

        if signature_verifier is not None:
            if (
                x_hub_signature_256 is None
                or not signature_verifier.verify(
                    body=body,
                    signature=x_hub_signature_256,
                )
            ):
                raise HTTPException(status_code=403)

        payload: dict[str, Any] = await request.json()

        if message_handler is not None:
            message_handler.handle(payload)

        return {"status": "ok"}

    return router