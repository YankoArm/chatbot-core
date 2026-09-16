from __future__ import annotations

import sqlite3
from pathlib import Path
from threading import RLock

from chatbot.leads.models import Lead
from chatbot.leads.repository import LeadRepository


class SQLiteLeadRepository(LeadRepository):
    """
    Persist captured leads in a local SQLite database.
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
        self._connection.row_factory = sqlite3.Row

        self._create_schema()

    def save(
        self,
        lead: Lead,
    ) -> bool:
        with self._lock:
            with self._connection:
                cursor = self._connection.execute(
                    """
                    INSERT OR IGNORE INTO leads (
                        action_id,
                        client_id,
                        session_id,
                        name,
                        phone,
                        reason
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        lead.action_id,
                        lead.client_id,
                        lead.session_id,
                        lead.name,
                        lead.phone,
                        lead.reason,
                    ),
                )

        return cursor.rowcount == 1

    def list_by_client(
        self,
        *,
        client_id: str,
    ) -> tuple[Lead, ...]:
        with self._lock:
            rows = self._connection.execute(
                """
                SELECT
                    action_id,
                    client_id,
                    session_id,
                    name,
                    phone,
                    reason
                FROM leads
                WHERE client_id = ?
                ORDER BY id ASC
                """,
                (
                    client_id,
                ),
            ).fetchall()

        return tuple(
            self._row_to_lead(row)
            for row in rows
        )

    def close(self) -> None:
        with self._lock:
            self._connection.close()

    def _create_schema(
        self,
    ) -> None:
        with self._lock:
            with self._connection:
                self._connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS leads (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        action_id TEXT NOT NULL UNIQUE,
                        client_id TEXT NOT NULL,
                        session_id TEXT NOT NULL,
                        name TEXT NOT NULL,
                        phone TEXT NOT NULL,
                        reason TEXT NOT NULL
                    )
                    """
                )

                self._connection.execute(
                    """
                    CREATE INDEX IF NOT EXISTS
                        idx_leads_client
                    ON leads (client_id)
                    """
                )

    @staticmethod
    def _row_to_lead(
        row: sqlite3.Row,
    ) -> Lead:
        return Lead(
            action_id=row["action_id"],
            client_id=row["client_id"],
            session_id=row["session_id"],
            name=row["name"],
            phone=row["phone"],
            reason=row["reason"],
        )
