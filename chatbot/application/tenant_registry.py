from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
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

    Cached applications are reused while their persisted client definition
    remains unchanged. When the definition changes, only that tenant runtime
    is rebuilt on its next access.
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
        self._definitions: dict[
            str,
            InstanceDefinition,
        ] = {}
        self._lock = RLock()

    def get_application(
        self,
        client_id: str,
    ) -> object | None:
        with self._lock:
            definition = (
                self._instance_definition_repository.get(
                    client_id
                )
            )

            if definition is None:
                self._applications.pop(
                    client_id,
                    None,
                )
                self._definitions.pop(
                    client_id,
                    None,
                )
                return None

            cached_definition = self._definitions.get(
                client_id
            )

            if (
                client_id in self._applications
                and cached_definition == definition
            ):
                return self._applications[
                    client_id
                ]

            application = self._application_factory(
                definition
            )

            self._applications[
                client_id
            ] = application
            self._definitions[
                client_id
            ] = deepcopy(
                definition
            )

            return application
