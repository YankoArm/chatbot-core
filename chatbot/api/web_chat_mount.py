from __future__ import annotations

from typing import Any, Callable

from fastapi import FastAPI

from chatbot.api.web_chat import build_web_chat_router
from chatbot.api.web_chat_widget import build_web_chat_widget_router
from chatbot.api.web_widget_resolver import (
    resolve_web_widget_definition,
)
from chatbot.instances.definition import InstanceDefinition


def mount_web_chat(
    app: FastAPI,
    *,
    repository: Any,
    application_factory: Callable[[InstanceDefinition], Any],
    enabled: bool = False,
) -> None:
    """
    Register the web channel only when explicitly enabled.

    Public deployment remains disabled until the security
    and persistent-session requirements are completed.
    """
    if not enabled:
        return

    if repository is None:
        raise ValueError(
            "Web chat requires an instance definition repository."
        )

    app.include_router(
        build_web_chat_router(
            resolve_widget=lambda widget_id: (
                resolve_web_widget_definition(
                    repository,
                    widget_id,
                )
            ),
            build_application=application_factory,
        )
    )

    app.include_router(
        build_web_chat_widget_router(
            resolve_widget=lambda widget_id: (
                resolve_web_widget_definition(
                    repository,
                    widget_id,
                )
            ),
        )
    )
