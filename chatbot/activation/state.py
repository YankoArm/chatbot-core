from dataclasses import dataclass
from datetime import datetime


@dataclass
class ActivationState:
    """
    Estado de activación asociado a una conversación o usuario.

    Esta primera versión mantiene el estado desacoplado de cualquier
    sistema de persistencia.
    """

    active: bool = False
    activated_at: datetime | None = None
    expires_at: datetime | None = None
    prompt_sent_at: datetime | None = None