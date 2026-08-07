from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import date, datetime, time, timedelta
from typing import Any

from chatbot.availability import BusyPeriod
from chatbot.timezone import TimezoneService


class CalendarEventAdapterError(ValueError):
    """Raised when a calendar event cannot be converted."""


class CalendarAvailabilityAdapter:
    def __init__(
        self,
        *,
        default_timezone: str = "Europe/Madrid",
        timezone_service: TimezoneService | None = None,
    ) -> None:
        if not default_timezone.strip():
            raise ValueError(
                "Default timezone cannot be empty."
            )

        self._default_timezone = default_timezone
        self._timezone_service = (
            timezone_service
            or TimezoneService()
        )

    def events_to_busy_periods(
        self,
        events: Iterable[Mapping[str, Any]],
    ) -> tuple[BusyPeriod, ...]:
        periods: list[BusyPeriod] = []

        for event in events:
            period = self.event_to_busy_period(event)

            if period is not None:
                periods.append(period)

        periods.sort(
            key=lambda period: period.start
        )

        return tuple(periods)

    def event_to_busy_period(
        self,
        event: Mapping[str, Any],
    ) -> BusyPeriod | None:
        if self._should_ignore_event(event):
            return None

        start_data = event.get("start")
        end_data = event.get("end")

        if isinstance(start_data, datetime):
            if not isinstance(end_data, datetime):
                raise CalendarEventAdapterError(
                    "Calendar event does not contain "
                    "a valid end datetime."
                )

            return BusyPeriod(
                start=start_data,
                end=end_data,
            )

        if not isinstance(start_data, Mapping):
            raise CalendarEventAdapterError(
                "Calendar event does not contain "
                "a valid start value."
            )

        if not isinstance(end_data, Mapping):
            raise CalendarEventAdapterError(
                "Calendar event does not contain "
                "a valid end value."
            )

        if "dateTime" in start_data:
            return self._convert_timed_event(
                start_data=start_data,
                end_data=end_data,
            )

        if "date" in start_data:
            return self._convert_all_day_event(
                start_data=start_data,
                end_data=end_data,
            )

        raise CalendarEventAdapterError(
            "Calendar event start must contain "
            "'dateTime' or 'date'."
        )

    @staticmethod
    def _should_ignore_event(
        event: Mapping[str, Any],
    ) -> bool:
        if event.get("status") == "cancelled":
            return True

        transparency = event.get(
            "transparency",
            "opaque",
        )

        if transparency == "transparent":
            return True

        return False

    def _convert_timed_event(
        self,
        *,
        start_data: Mapping[str, Any],
        end_data: Mapping[str, Any],
    ) -> BusyPeriod:
        start_value = start_data.get("dateTime")
        end_value = end_data.get("dateTime")

        if not isinstance(start_value, str):
            raise CalendarEventAdapterError(
                "Timed event start must contain "
                "a string 'dateTime'."
            )

        if not isinstance(end_value, str):
            raise CalendarEventAdapterError(
                "Timed event end must contain "
                "a string 'dateTime'."
            )

        timezone_name = self._resolve_timezone_name(
            start_data,
            end_data,
        )

        start = self._parse_datetime(
            start_value,
            timezone_name=timezone_name,
        )

        end = self._parse_datetime(
            end_value,
            timezone_name=timezone_name,
        )

        return BusyPeriod(
            start=start,
            end=end,
        )

    def _convert_all_day_event(
        self,
        *,
        start_data: Mapping[str, Any],
        end_data: Mapping[str, Any],
    ) -> BusyPeriod:
        start_value = start_data.get("date")
        end_value = end_data.get("date")

        if not isinstance(start_value, str):
            raise CalendarEventAdapterError(
                "All-day event start must contain "
                "a string 'date'."
            )

        if not isinstance(end_value, str):
            raise CalendarEventAdapterError(
                "All-day event end must contain "
                "a string 'date'."
            )

        timezone_name = self._resolve_timezone_name(
            start_data,
            end_data,
        )

        start_date = self._parse_date(
            start_value,
        )

        end_date = self._parse_date(
            end_value,
        )

        start = self._timezone_service.localize(
            datetime.combine(
                start_date,
                time.min,
            ),
            timezone_name=timezone_name,
        )

        end = self._timezone_service.localize(
            datetime.combine(
                end_date,
                time.min,
            ),
            timezone_name=timezone_name,
        )

        return BusyPeriod(
            start=start,
            end=end,
        )

    def _parse_datetime(
        self,
        value: str,
        *,
        timezone_name: str,
    ) -> datetime:
        normalized = value.replace(
            "Z",
            "+00:00",
        )

        try:
            parsed = datetime.fromisoformat(
                normalized
            )
        except ValueError as exc:
            raise CalendarEventAdapterError(
                f"Invalid calendar datetime: {value}"
            ) from exc

        if (
            parsed.tzinfo is None
            or parsed.utcoffset() is None
        ):
            return self._timezone_service.localize(
                parsed,
                timezone_name=timezone_name,
            )

        return parsed

    @staticmethod
    def _parse_date(
        value: str,
    ) -> date:
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise CalendarEventAdapterError(
                f"Invalid calendar date: {value}"
            ) from exc

    def _resolve_timezone_name(
        self,
        start_data: Mapping[str, Any],
        end_data: Mapping[str, Any],
    ) -> str:
        for data in (
            start_data,
            end_data,
        ):
            timezone_name = data.get("timeZone")

            if (
                isinstance(timezone_name, str)
                and timezone_name.strip()
            ):
                return timezone_name

        return self._default_timezone