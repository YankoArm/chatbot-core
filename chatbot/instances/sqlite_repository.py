from __future__ import annotations

import json
import sqlite3

from dataclasses import asdict
from pathlib import Path
from threading import RLock
from typing import Any

from chatbot.activation import ActivationConfig
from chatbot.instances.definition import (
    InstanceDefinition,
)


class SQLiteInstanceDefinitionRepository:
    """
    Persist editable client definitions in SQLite.

    Definitions are stored as structured JSON while identity fields
    remain separately indexed for efficient administration queries.
    """

    def __init__(
        self,
        database_path: str | Path,
    ) -> None:
        self._database_path = str(
            database_path
        )
        self._lock = RLock()

        if self._database_path != ":memory:":
            Path(
                self._database_path
            ).parent.mkdir(
                parents=True,
                exist_ok=True,
            )

        self._connection = sqlite3.connect(
            self._database_path,
            check_same_thread=False,
        )
        self._connection.row_factory = (
            sqlite3.Row
        )

        self._create_schema()

    def save(
        self,
        definition: InstanceDefinition,
    ) -> None:
        """
        Insert a definition or replace its editable values.
        """

        serialized_definition = (
            self._serialize_definition(
                definition
            )
        )

        with self._lock:
            with self._connection:
                self._connection.execute(
                    """
                    INSERT INTO instance_definitions (
                        id,
                        name,
                        template_id,
                        definition_json
                    )
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        name = excluded.name,
                        template_id = excluded.template_id,
                        definition_json = excluded.definition_json,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (
                        definition.id,
                        definition.name,
                        definition.template_id,
                        serialized_definition,
                    ),
                )

    def get(
        self,
        client_id: str,
    ) -> InstanceDefinition | None:
        """
        Return a stored client definition by identifier.
        """

        with self._lock:
            row = self._connection.execute(
                """
                SELECT definition_json
                FROM instance_definitions
                WHERE id = ?
                """,
                (
                    client_id,
                ),
            ).fetchone()

        if row is None:
            return None

        return self._deserialize_definition(
            row["definition_json"]
        )

    def list_all(
        self,
    ) -> tuple[InstanceDefinition, ...]:
        """
        Return all definitions ordered by display name.
        """

        with self._lock:
            rows = self._connection.execute(
                """
                SELECT definition_json
                FROM instance_definitions
                ORDER BY name COLLATE NOCASE ASC, id ASC
                """
            ).fetchall()

        return tuple(
            self._deserialize_definition(
                row["definition_json"]
            )
            for row in rows
        )

    def close(
        self,
    ) -> None:
        """
        Close the SQLite connection.
        """

        with self._lock:
            self._connection.close()

    def _create_schema(
        self,
    ) -> None:
        """
        Create the editable instance definition table.
        """

        with self._lock:
            with self._connection:
                self._connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS instance_definitions (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        template_id TEXT NOT NULL,
                        definition_json TEXT NOT NULL,
                        created_at TEXT NOT NULL
                            DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT NOT NULL
                            DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )

                self._connection.execute(
                    """
                    CREATE INDEX IF NOT EXISTS
                        idx_instance_definitions_name
                    ON instance_definitions (name)
                    """
                )

                self._connection.execute(
                    """
                    CREATE INDEX IF NOT EXISTS
                        idx_instance_definitions_template
                    ON instance_definitions (template_id)
                    """
                )

    @staticmethod
    def _serialize_definition(
        definition: InstanceDefinition,
    ) -> str:
        """
        Convert a definition to stable UTF-8 JSON.
        """

        return json.dumps(
            asdict(
                definition
            ),
            ensure_ascii=False,
            separators=(
                ",",
                ":",
            ),
            sort_keys=True,
        )

    @staticmethod
    def _deserialize_definition(
        serialized_definition: str,
    ) -> InstanceDefinition:
        """
        Rebuild a definition and its activation configuration.
        """

        raw_data = json.loads(
            serialized_definition
        )

        if not isinstance(raw_data, dict):
            raise ValueError(
                "Stored instance definition must be a JSON object."
            )

        data: dict[str, Any] = dict(
            raw_data
        )

        activation_data = data.get(
            "activation"
        )

        if activation_data is None:
            activation = None
        elif isinstance(
            activation_data,
            dict,
        ):
            activation = ActivationConfig(
                **activation_data
            )
        else:
            raise ValueError(
                "Stored activation configuration is invalid."
            )

        data["activation"] = activation

        return InstanceDefinition(
            **data
        )