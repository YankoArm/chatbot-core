from __future__ import annotations

import logging
from typing import Any, Protocol

from fastapi import (
    APIRouter,
    Header,
    HTTPException,
    Query,
    Request,
)
from fastapi.responses import PlainTextResponse


logger = logging.getLogger(__name__)


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
        logger.info(
            "WhatsApp webhook verification received: mode=%s",
            hub_mode,
        )

        if (
            verify_token is not None
            and hub_verify_token != verify_token
        ):
            logger.warning(
                "WhatsApp webhook verification failed: invalid verify token."
            )
            raise HTTPException(status_code=403)

        logger.info("WhatsApp webhook verification succeeded.")
        return hub_challenge

    @router.post("/webhook")
    async def receive_webhook(
        request: Request,
        x_hub_signature_256: str | None = Header(
            default=None,
            alias="X-Hub-Signature-256",
        ),
    ) -> dict[str, str]:
        logger.info("WhatsApp webhook POST received.")

        body = await request.body()

        logger.info(
            "WhatsApp webhook body received: %s bytes.",
            len(body),
        )

        if signature_verifier is not None:
            if x_hub_signature_256 is None:
                logger.warning(
                    "WhatsApp webhook rejected: missing "
                    "X-Hub-Signature-256 header."
                )
                raise HTTPException(status_code=403)

            if not signature_verifier.verify(
                body=body,
                signature=x_hub_signature_256,
            ):
                logger.warning(
                    "WhatsApp webhook rejected: invalid signature."
                )
                raise HTTPException(status_code=403)

            logger.info("WhatsApp webhook signature verified.")

        try:
            payload: dict[str, Any] = await request.json()
        except Exception:
            logger.exception(
                "WhatsApp webhook rejected: invalid JSON payload."
            )
            raise HTTPException(
                status_code=400,
                detail="Invalid JSON payload.",
            )

        logger.info(
            "WhatsApp webhook payload received: object=%s entries=%s",
            payload.get("object"),
            len(payload.get("entry", [])),
        )

        if message_handler is None:
            logger.warning(
                "WhatsApp webhook received without a configured message handler."
            )
            return {"status": "ok"}

        try:
            message_handler.handle(payload)
        except Exception:
            logger.exception(
                "WhatsApp webhook message handler failed."
            )
            raise

        logger.info("WhatsApp webhook processed successfully.")
        return {"status": "ok"}

    return router