from __future__ import annotations

from dataclasses import dataclass

from chatbot.responses import Response


@dataclass(slots=True)
class ActivationDecision:
    """
    Result of evaluating an incoming message through the activation layer.

    If `response` is not None, the application should return it immediately.
    Otherwise, the message may continue to the conversation pipeline.
    """

    continue_processing: bool
    response: Response | None = None