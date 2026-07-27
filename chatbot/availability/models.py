from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from enum import IntEnum


class Weekday(IntEnum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


@dataclass(frozen=True, slots=True, order=True)
class TimeRange:
    start: time
    end: time

    def __post_init__(self) -> None:
        if self.end <= self.start:
            raise ValueError(
                "Time range end must be later than start."
            )

    def contains(
        self,
        value: time,
    ) -> bool:
        return self.start <= value < self.end

    def overlaps(
        self,
        other: TimeRange,
    ) -> bool:
        return (
            self.start < other.end
            and other.start < self.end
        )


@dataclass(frozen=True, slots=True, order=True)
class TimeSlot:
    start: datetime
    end: datetime
    occupied_start: datetime
    occupied_end: datetime

    def __post_init__(self) -> None:
        values = (
            self.start,
            self.end,
            self.occupied_start,
            self.occupied_end,
        )

        if any(
            value.tzinfo is None
            or value.utcoffset() is None
            for value in values
        ):
            raise ValueError(
                "Time-slot datetimes must be timezone-aware."
            )

        if self.end <= self.start:
            raise ValueError(
                "Time-slot end must be later than start."
            )

        if self.occupied_end <= self.occupied_start:
            raise ValueError(
                "Occupied end must be later than "
                "occupied start."
            )

        if self.occupied_start > self.start:
            raise ValueError(
                "Occupied start cannot be later than "
                "appointment start."
            )

        if self.occupied_end < self.end:
            raise ValueError(
                "Occupied end cannot be earlier than "
                "appointment end."
            )

    @property
    def timezone_name(self) -> str:
        return getattr(
            self.start.tzinfo,
            "key",
            str(self.start.tzinfo),
        )

    def overlaps(
        self,
        other: TimeSlot,
    ) -> bool:
        return (
            self.occupied_start < other.occupied_end
            and other.occupied_start < self.occupied_end
        )

@dataclass(frozen=True, slots=True, order=True)
class BusyPeriod:
    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        values = (
            self.start,
            self.end,
        )

        if any(
            value.tzinfo is None
            or value.utcoffset() is None
            for value in values
        ):
            raise ValueError(
                "Busy-period datetimes must be "
                "timezone-aware."
            )

        if self.end <= self.start:
            raise ValueError(
                "Busy-period end must be later than start."
            )

    def overlaps_slot(
        self,
        slot: TimeSlot,
    ) -> bool:
        return (
            self.start < slot.occupied_end
            and slot.occupied_start < self.end
        )