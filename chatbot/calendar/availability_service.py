from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable

from chatbot.availability import BusyPeriod


@dataclass(frozen=True, slots=True)
class AvailableSlot:
    """
    Available calendar interval that can contain one booking.
    """

    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        if self.start.tzinfo is None:
            raise ValueError(
                "Available slot start must be timezone-aware."
            )

        if self.end.tzinfo is None:
            raise ValueError(
                "Available slot end must be timezone-aware."
            )

        if self.end <= self.start:
            raise ValueError(
                "Available slot end must be after start."
            )


class AvailabilityService:
    """
    Calculate bookable calendar slots inside a time window.
    """

    def find_available_slots(
        self,
        *,
        start: datetime,
        end: datetime,
        duration_minutes: int,
        busy_periods: Iterable[BusyPeriod] = (),
        buffer_minutes: int = 0,
    ) -> tuple[AvailableSlot, ...]:
        self._validate_window(
            start=start,
            end=end,
        )

        if duration_minutes <= 0:
            raise ValueError(
                "Duration minutes must be greater than zero."
            )

        if buffer_minutes < 0:
            raise ValueError(
                "Buffer minutes cannot be negative."
            )

        duration = timedelta(
            minutes=duration_minutes,
        )

        buffer = timedelta(
            minutes=buffer_minutes,
        )

        blocked_periods = self._merge_busy_periods(
            busy_periods=busy_periods,
            window_start=start,
            window_end=end,
            buffer=buffer,
        )

        slots: list[AvailableSlot] = []
        cursor = start

        for busy_period in blocked_periods:
            slots.extend(
                self._build_slots(
                    start=cursor,
                    end=busy_period.start,
                    duration=duration,
                )
            )

            if busy_period.end > cursor:
                cursor = busy_period.end

        slots.extend(
            self._build_slots(
                start=cursor,
                end=end,
                duration=duration,
            )
        )

        return tuple(slots)

    @staticmethod
    def _build_slots(
        *,
        start: datetime,
        end: datetime,
        duration: timedelta,
    ) -> list[AvailableSlot]:
        slots: list[AvailableSlot] = []
        cursor = start

        while cursor + duration <= end:
            slot_end = cursor + duration

            slots.append(
                AvailableSlot(
                    start=cursor,
                    end=slot_end,
                )
            )

            cursor = slot_end

        return slots

    @staticmethod
    def _merge_busy_periods(
        *,
        busy_periods: Iterable[BusyPeriod],
        window_start: datetime,
        window_end: datetime,
        buffer: timedelta,
    ) -> tuple[BusyPeriod, ...]:
        clipped_periods: list[BusyPeriod] = []

        for period in busy_periods:
            AvailabilityService._validate_window(
                start=period.start,
                end=period.end,
            )

            blocked_start = max(
                window_start,
                period.start - buffer,
            )

            blocked_end = min(
                window_end,
                period.end + buffer,
            )

            if blocked_end <= window_start:
                continue

            if blocked_start >= window_end:
                continue

            clipped_periods.append(
                BusyPeriod(
                    start=blocked_start,
                    end=blocked_end,
                )
            )

        clipped_periods.sort(
            key=lambda period: period.start
        )

        merged: list[BusyPeriod] = []

        for period in clipped_periods:
            if not merged:
                merged.append(period)
                continue

            previous = merged[-1]

            if period.start <= previous.end:
                merged[-1] = BusyPeriod(
                    start=previous.start,
                    end=max(
                        previous.end,
                        period.end,
                    ),
                )
                continue

            merged.append(period)

        return tuple(merged)

    @staticmethod
    def _validate_window(
        *,
        start: datetime,
        end: datetime,
    ) -> None:
        if start.tzinfo is None:
            raise ValueError(
                "Window start must be timezone-aware."
            )

        if end.tzinfo is None:
            raise ValueError(
                "Window end must be timezone-aware."
            )

        if end <= start:
            raise ValueError(
                "Window end must be after start."
            )