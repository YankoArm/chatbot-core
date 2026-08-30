from __future__ import annotations

import sqlite3
from pathlib import Path
from threading import RLock

from chatbot.booking.models import (
    Booking,
    BookingStatus,
)
from chatbot.booking.repository import BookingRepository


class SQLiteBookingRepository(
    BookingRepository
):
    """
    Persist bookings in a local SQLite database.
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
        booking: Booking,
    ) -> None:
        with self._lock:
            with self._connection:
                self._connection.execute(
                    """
                    INSERT INTO bookings (
                        client_id,
                        name,
                        phone,
                        booking_date,
                        booking_time,
                        service_id,
                        service_name,
                        duration_minutes,
                        price_cents,
                        price_type,
                        currency,
                        calendar_booking_id,
                        status
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    self._booking_values(
                        booking
                    ),
                )

    def update(
        self,
        booking: Booking,
    ) -> None:
        with self._lock:
            with self._connection:
                if booking.calendar_booking_id is not None:
                    cursor = self._connection.execute(
                        """
                        UPDATE bookings
                        SET
                            name = ?,
                            phone = ?,
                            booking_date = ?,
                            booking_time = ?,
                            service_id = ?,
                            service_name = ?,
                            duration_minutes = ?,
                            price_cents = ?,
                            price_type = ?,
                            currency = ?,
                            status = ?
                        WHERE client_id = ?
                          AND calendar_booking_id = ?
                        """,
                        (
                            booking.name,
                            booking.phone,
                            booking.date,
                            booking.time,
                            booking.service_id,
                            booking.service_name,
                            booking.duration_minutes,
                            booking.price_cents,
                            booking.price_type,
                            booking.currency,
                            booking.status.value,
                            booking.client_id,
                            booking.calendar_booking_id,
                        ),
                    )
                else:
                    cursor = self._connection.execute(
                        """
                        UPDATE bookings
                        SET
                            name = ?,
                            service_id = ?,
                            service_name = ?,
                            duration_minutes = ?,
                            price_cents = ?,
                            price_type = ?,
                            currency = ?,
                            status = ?
                        WHERE client_id = ?
                          AND phone = ?
                          AND booking_date = ?
                          AND booking_time = ?
                          AND calendar_booking_id IS NULL
                        """,
                        (
                            booking.name,
                            booking.service_id,
                            booking.service_name,
                            booking.duration_minutes,
                            booking.price_cents,
                            booking.price_type,
                            booking.currency,
                            booking.status.value,
                            booking.client_id,
                            booking.phone,
                            booking.date,
                            booking.time,
                        ),
                    )

                if cursor.rowcount == 0:
                    raise ValueError(
                        "Cannot update a booking that is not stored."
                    )

    def find_by_phone(
        self,
        phone: str,
    ) -> tuple[Booking, ...]:
        normalized_phone = phone.strip()

        with self._lock:
            rows = self._connection.execute(
                """
                SELECT
                    client_id,
                    name,
                    phone,
                    booking_date,
                    booking_time,
                    service_id,
                    service_name,
                    duration_minutes,
                    price_cents,
                    price_type,
                    currency,
                    calendar_booking_id,
                    status
                FROM bookings
                WHERE phone = ?
                ORDER BY id ASC
                """,
                (
                    normalized_phone,
                ),
            ).fetchall()

        return tuple(
            self._row_to_booking(row)
            for row in rows
        )

    def find_by_client_and_phone(
        self,
        *,
        client_id: str,
        phone: str,
    ) -> tuple[Booking, ...]:
        normalized_phone = phone.strip()

        with self._lock:
            rows = self._connection.execute(
                """
                SELECT
                    client_id,
                    name,
                    phone,
                    booking_date,
                    booking_time,
                    service_id,
                    service_name,
                    duration_minutes,
                    price_cents,
                    price_type,
                    currency,
                    calendar_booking_id,
                    status
                FROM bookings
                WHERE client_id = ?
                  AND phone = ?
                ORDER BY id ASC
                """,
                (
                    client_id,
                    normalized_phone,
                ),
            ).fetchall()

        return tuple(
            self._row_to_booking(row)
            for row in rows
        )

    def list_all(
        self,
    ) -> tuple[Booking, ...]:
        with self._lock:
            rows = self._connection.execute(
                """
                SELECT
                    client_id,
                    name,
                    phone,
                    booking_date,
                    booking_time,
                    service_id,
                    service_name,
                    duration_minutes,
                    price_cents,
                    price_type,
                    currency,
                    calendar_booking_id,
                    status
                FROM bookings
                ORDER BY id ASC
                """
            ).fetchall()

        return tuple(
            self._row_to_booking(row)
            for row in rows
        )

    def close(self) -> None:
        with self._lock:
            self._connection.close()

    def _create_schema(self) -> None:
        with self._lock:
            with self._connection:
                self._connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS bookings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        client_id TEXT NOT NULL DEFAULT 'legacy',
                        name TEXT NOT NULL,
                        phone TEXT NOT NULL,
                        booking_date TEXT NOT NULL,
                        booking_time TEXT NOT NULL,
                        service_id TEXT,
                        service_name TEXT,
                        duration_minutes INTEGER,
                        price_cents INTEGER,
                        price_type TEXT,
                        currency TEXT,
                        calendar_booking_id TEXT,
                        status TEXT NOT NULL
                    )
                    """
                )

                columns = {
                    row["name"]
                    for row in self._connection.execute(
                        """
                        PRAGMA table_info(bookings)
                        """
                    ).fetchall()
                }

                if "client_id" not in columns:
                    self._connection.execute(
                        """
                        ALTER TABLE bookings
                        ADD COLUMN client_id TEXT NOT NULL
                            DEFAULT 'legacy'
                        """
                    )

                self._connection.execute(
                    """
                    CREATE INDEX IF NOT EXISTS
                        idx_bookings_phone
                    ON bookings (phone)
                    """
                )

                self._connection.execute(
                    """
                    CREATE INDEX IF NOT EXISTS
                        idx_bookings_client_phone
                    ON bookings (client_id, phone)
                    """
                )

                self._connection.execute(
                    """
                    DROP INDEX IF EXISTS
                        idx_bookings_calendar_id
                    """
                )

                self._connection.execute(
                    """
                    CREATE UNIQUE INDEX IF NOT EXISTS
                        idx_bookings_client_calendar_id
                    ON bookings (
                        client_id,
                        calendar_booking_id
                    )
                    WHERE calendar_booking_id IS NOT NULL
                    """
                )

    @staticmethod
    def _booking_values(
        booking: Booking,
    ) -> tuple[object, ...]:
        return (
            booking.client_id,
            booking.name,
            booking.phone,
            booking.date,
            booking.time,
            booking.service_id,
            booking.service_name,
            booking.duration_minutes,
            booking.price_cents,
            booking.price_type,
            booking.currency,
            booking.calendar_booking_id,
            booking.status.value,
        )

    @staticmethod
    def _row_to_booking(
        row: sqlite3.Row,
    ) -> Booking:
        return Booking(
            client_id=row["client_id"],
            name=row["name"],
            phone=row["phone"],
            date=row["booking_date"],
            time=row["booking_time"],
            service_id=row["service_id"],
            service_name=row["service_name"],
            duration_minutes=row[
                "duration_minutes"
            ],
            price_cents=row["price_cents"],
            price_type=row["price_type"],
            currency=row["currency"],
            calendar_booking_id=row[
                "calendar_booking_id"
            ],
            status=BookingStatus(
                row["status"]
            ),
        )