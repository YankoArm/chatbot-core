from __future__ import annotations

import re
from typing import Protocol

from chatbot.instances.definition import InstanceDefinition


class WidgetDefinitionRepository(Protocol):
    def list_all(self) -> tuple[InstanceDefinition, ...]:
        ...


def resolve_web_widget_definition(
    repository: WidgetDefinitionRepository,
    widget_id: str,
) -> InstanceDefinition | None:
    """
    Resolve a public widget identifier to exactly one client.

    Duplicate identifiers are rejected rather than choosing
    an arbitrary tenant. Activation and lifecycle checks
    remain the responsibility of the web-chat API.
    """
    if not isinstance(widget_id, str):
        return None

    if re.fullmatch(r"[A-Za-z0-9_-]{12,96}", widget_id) is None:
        return None

    matched = None

    for definition in repository.list_all():
        settings = definition.settings

        if not isinstance(settings, dict):
            continue

        web_settings = settings.get("web_chat")

        if not isinstance(web_settings, dict):
            continue

        if web_settings.get("widget_id") != widget_id:
            continue

        if matched is not None:
            return None

        matched = definition

    return matched
