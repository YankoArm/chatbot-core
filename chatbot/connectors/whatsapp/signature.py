from __future__ import annotations

import hashlib
import hmac


class WhatsAppSignatureVerifier:
    def __init__(self, *, app_secret: str) -> None:
        self._app_secret = app_secret.encode("utf-8")

    def verify(
        self,
        *,
        body: bytes,
        signature: str,
    ) -> bool:
        if not signature.startswith("sha256="):
            return False

        expected_signature = hmac.new(
            self._app_secret,
            body,
            hashlib.sha256,
        ).hexdigest()

        provided_signature = signature.removeprefix(
            "sha256="
        )

        return hmac.compare_digest(
            expected_signature,
            provided_signature,
        )