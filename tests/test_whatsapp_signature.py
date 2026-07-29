from chatbot.connectors.whatsapp.signature import (
    WhatsAppSignatureVerifier,
)


def test_signature_verifier_accepts_valid_signature() -> None:
    verifier = WhatsAppSignatureVerifier(
        app_secret="secret",
    )

    body = b'{"message":"hola"}'
    signature = (
        "sha256="
    "bed02614ab68b29c8524e86ce4f70c92"
    "e7abca6796e9e988aad45309a2593fc6"
    )

    assert verifier.verify(
        body=body,
        signature=signature,
    )

def test_signature_verifier_rejects_signature_without_sha256_prefix() -> None:
    verifier = WhatsAppSignatureVerifier(
        app_secret="secret",
    )

    body = b'{"message":"hola"}'
    signature = (
        "bed02614ab68b29c8524e86ce4f70c92"
        "e7abca6796e9e988aad45309a2593fc6"
    )

    assert not verifier.verify(
        body=body,
        signature=signature,
    )

def test_signature_verifier_rejects_invalid_signature() -> None:
    verifier = WhatsAppSignatureVerifier(
        app_secret="secret",
    )

    body = b'{"message":"hola"}'
    signature = "sha256=invalid-signature"

    assert not verifier.verify(
        body=body,
        signature=signature,
    )