from __future__ import annotations

from collections.abc import Callable
from threading import RLock
from typing import Protocol

from chatbot.instances import (
    InstanceDefinition,
)


class InstanceDefinitionRepositoryProtocol(Protocol):
    def get(
        self,
        client_id: str,
    ) -> InstanceDefinition | None:
        ...


ApplicationFactory = Callable[
    [InstanceDefinition],
    object,
]


class TenantApplicationRegistry:
    """
    Build and retain one runtime application per FlowForge client.
    """

    def __init__(
        self,
        *,
        instance_definition_repository: (
            InstanceDefinitionRepositoryProtocol
        ),
        application_factory: ApplicationFactory,
    ) -> None:
        self._instance_definition_repository = (
            instance_definition_repository
        )
        self._application_factory = application_factory
        self._applications: dict[
            str,
            object,
        ] = {}
        self._lock = RLock()

    def get_application(
        self,
        client_id: str,
    ) -> object | None:
        with self._lock:
            cached_application = self._applications.get(
                client_id
            )

            if cached_application is not None:
                return cached_application

            definition = (
                self._instance_definition_repository.get(
                    client_id
                )
            )

            if definition is None:
                return None

            application = self._application_factory(
                definition
            )
            self._applications[client_id] = application

            return application