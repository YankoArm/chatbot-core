from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from chatbot.availability.exceptions import (
    InvalidBookingNoticeError,
    InvalidBookingWindowError,
    InvalidBufferError,
    InvalidDurationError,
    InvalidSlotIntervalError,
)


@dataclass(frozen=True, slots=True)
class BookingRules:
    appointment_duration: timedelta
    slot_interval: timedelta = timedelta(minutes=30)
    buffer_before: timedelta = timedelta(0)
    buffer_after: timedelta = timedelta(0)
    minimum_notice: timedelta = timedelta(0)
    maximum_advance: timedelta | None = None
    allow_past_bookings: bool = False

    def __post_init__(self) -> None:
        self._validate_duration()
        self._validate_slot_interval()
        self._validate_buffers()
        self._validate_minimum_notice()
        self._validate_maximum_advance()
        self._validate_booking_window()

    @property
    def occupied_duration(self) -> timedelta:
        return (
            self.buffer_before
            + self.appointment_duration
            + self.buffer_after
        )

    def _validate_duration(self) -> None:
        if self.appointment_duration <= timedelta(0):
            raise InvalidDurationError(
                "Appointment duration must be greater "
                "than zero."
            )

    def _validate_slot_interval(self) -> None:
        if self.slot_interval <= timedelta(0):
            raise InvalidSlotIntervalError(
                "Slot interval must be greater than zero."
            )

    def _validate_buffers(self) -> None:
        if self.buffer_before < timedelta(0):
            raise InvalidBufferError(
                "Buffer before cannot be negative."
            )

        if self.buffer_after < timedelta(0):
            raise InvalidBufferError(
                "Buffer after cannot be negative."
            )

    def _validate_minimum_notice(self) -> None:
        if self.minimum_notice < timedelta(0):
            raise InvalidBookingNoticeError(
                "Minimum booking notice cannot be negative."
            )

    def _validate_maximum_advance(self) -> None:
        if (
            self.maximum_advance is not None
            and self.maximum_advance <= timedelta(0)
        ):
            raise InvalidBookingWindowError(
                "Maximum booking advance must be greater "
                "than zero."
            )

    def _validate_booking_window(self) -> None:
        if (
            self.maximum_advance is not None
            and self.minimum_notice
            > self.maximum_advance
        ):
            raise InvalidBookingWindowError(
                "Minimum booking notice cannot exceed "
                "maximum booking advance."
            )

    @classmethod
    def hourly(
        cls,
        *,
        slot_interval_minutes: int = 30,
        buffer_before_minutes: int = 0,
        buffer_after_minutes: int = 0,
        minimum_notice_hours: int = 0,
        maximum_advance_days: int | None = None,
    ) -> BookingRules:
        maximum_advance = (
            timedelta(days=maximum_advance_days)
            if maximum_advance_days is not None
            else None
        )

        return cls(
            appointment_duration=timedelta(hours=1),
            slot_interval=timedelta(
                minutes=slot_interval_minutes,
            ),
            buffer_before=timedelta(
                minutes=buffer_before_minutes,
            ),
            buffer_after=timedelta(
                minutes=buffer_after_minutes,
            ),
            minimum_notice=timedelta(
                hours=minimum_notice_hours,
            ),
            maximum_advance=maximum_advance,
        )