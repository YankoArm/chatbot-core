from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import date, time
from types import MappingProxyType

from chatbot.availability.exceptions import (
    InvalidTimeRangeError,
    OverlappingTimeRangeError,
)
from chatbot.availability.models import (
    TimeRange,
    Weekday,
)


class BusinessHours:
    def __init__(
        self,
        schedule: Mapping[
            Weekday | int,
            Iterable[TimeRange],
        ]
        | None = None,
        *,
        timezone_name: str = "UTC",
    ) -> None:
        normalized_timezone = timezone_name.strip()

        if not normalized_timezone:
            raise ValueError(
                "Timezone name cannot be empty."
            )

        self._timezone_name = normalized_timezone
        self._schedule = MappingProxyType(
            self._normalize_schedule(
                schedule or {},
            )
        )

    @property
    def timezone_name(self) -> str:
        return self._timezone_name

    @property
    def schedule(
        self,
    ) -> Mapping[Weekday, tuple[TimeRange, ...]]:
        return self._schedule

    def hours_for_weekday(
        self,
        weekday: Weekday | int,
    ) -> tuple[TimeRange, ...]:
        normalized_weekday = self._normalize_weekday(
            weekday,
        )

        return self._schedule[normalized_weekday]

    def hours_for_date(
        self,
        value: date,
    ) -> tuple[TimeRange, ...]:
        return self.hours_for_weekday(
            value.weekday(),
        )

    def is_closed(
        self,
        value: date | Weekday | int,
    ) -> bool:
        if isinstance(value, date):
            ranges = self.hours_for_date(value)
        else:
            ranges = self.hours_for_weekday(value)

        return not ranges

    def contains(
        self,
        value: time,
        *,
        weekday: Weekday | int,
    ) -> bool:
        return any(
            time_range.contains(value)
            for time_range in self.hours_for_weekday(
                weekday,
            )
        )

    @classmethod
    def standard_week(
        cls,
        *,
        start: time,
        end: time,
        timezone_name: str = "UTC",
    ) -> BusinessHours:
        daily_range = TimeRange(
            start=start,
            end=end,
        )

        return cls(
            schedule={
                Weekday.MONDAY: (daily_range,),
                Weekday.TUESDAY: (daily_range,),
                Weekday.WEDNESDAY: (daily_range,),
                Weekday.THURSDAY: (daily_range,),
                Weekday.FRIDAY: (daily_range,),
            },
            timezone_name=timezone_name,
        )

    @staticmethod
    def _normalize_weekday(
        weekday: Weekday | int,
    ) -> Weekday:
        try:
            return Weekday(weekday)
        except ValueError as exc:
            raise ValueError(
                f"Invalid weekday: {weekday!r}."
            ) from exc

    @classmethod
    def _normalize_schedule(
        cls,
        schedule: Mapping[
            Weekday | int,
            Iterable[TimeRange],
        ],
    ) -> dict[Weekday, tuple[TimeRange, ...]]:
        normalized: dict[
            Weekday,
            tuple[TimeRange, ...],
        ] = {
            weekday: ()
            for weekday in Weekday
        }

        for raw_weekday, raw_ranges in schedule.items():
            weekday = cls._normalize_weekday(
                raw_weekday,
            )

            ranges = tuple(
                sorted(raw_ranges)
            )

            cls._validate_ranges(
                weekday,
                ranges,
            )

            normalized[weekday] = ranges

        return normalized

    @staticmethod
    def _validate_ranges(
        weekday: Weekday,
        ranges: tuple[TimeRange, ...],
    ) -> None:
        for time_range in ranges:
            if not isinstance(
                time_range,
                TimeRange,
            ):
                raise InvalidTimeRangeError(
                    "Business-hours entries must be "
                    "TimeRange instances."
                )

        for previous, current in zip(
            ranges,
            ranges[1:],
        ):
            if previous.overlaps(current):
                raise OverlappingTimeRangeError(
                    "Overlapping business-hours intervals "
                    f"for {weekday.name}: "
                    f"{previous!r} and {current!r}."
                )