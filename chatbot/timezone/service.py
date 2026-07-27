from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from chatbot.timezone.exceptions import (
    AwareDatetimeError,
    EmptyTimezoneError,
    InvalidTimezoneError,
    NaiveDatetimeError,
)
from chatbot.timezone.models import TimezoneDateTime


class TimezoneService:
    def __init__(
        self,
        default_timezone: str = "UTC",
    ) -> None:
        self._default_timezone = self._validate_timezone_name(
            default_timezone,
        )

    @property
    def default_timezone(self) -> str:
        return self._default_timezone

    def get_zone(
        self,
        timezone_name: str | None = None,
    ) -> ZoneInfo:
        resolved_name = self._resolve_timezone_name(
            timezone_name,
        )

        try:
            return ZoneInfo(resolved_name)
        except ZoneInfoNotFoundError as exc:
            raise InvalidTimezoneError(
                f"Unknown timezone: {resolved_name!r}."
            ) from exc

    def is_valid(
        self,
        timezone_name: str,
    ) -> bool:
        try:
            self.get_zone(timezone_name)
        except (
            EmptyTimezoneError,
            InvalidTimezoneError,
        ):
            return False

        return True

    def localize(
        self,
        value: datetime,
        *,
        timezone_name: str | None = None,
    ) -> datetime:
        if value.tzinfo is not None:
            raise AwareDatetimeError(
                "localize() requires a naive datetime."
            )

        zone = self.get_zone(timezone_name)

        return value.replace(
            tzinfo=zone,
        )

    def to_utc(
        self,
        value: datetime,
        *,
        timezone_name: str | None = None,
    ) -> datetime:
        if value.tzinfo is None:
            value = self.localize(
                value,
                timezone_name=timezone_name,
            )

        return value.astimezone(
            timezone.utc,
        )

    def from_utc(
        self,
        value: datetime,
        *,
        timezone_name: str | None = None,
    ) -> datetime:
        if value.tzinfo is None:
            raise NaiveDatetimeError(
                "from_utc() requires an aware UTC datetime."
            )

        zone = self.get_zone(timezone_name)

        return value.astimezone(
            zone,
        )

    def convert(
        self,
        value: datetime,
        *,
        target_timezone: str,
    ) -> datetime:
        if value.tzinfo is None:
            raise NaiveDatetimeError(
                "convert() requires an aware datetime."
            )

        target_zone = self.get_zone(
            target_timezone,
        )

        return value.astimezone(
            target_zone,
        )

    def build(
        self,
        value: datetime,
        *,
        timezone_name: str | None = None,
    ) -> TimezoneDateTime:
        resolved_name = self._resolve_timezone_name(
            timezone_name,
        )

        if value.tzinfo is None:
            local_datetime = self.localize(
                value,
                timezone_name=resolved_name,
            )
        else:
            local_datetime = self.convert(
                value,
                target_timezone=resolved_name,
            )

        utc_datetime = local_datetime.astimezone(
            timezone.utc,
        )

        return TimezoneDateTime(
            timezone_name=resolved_name,
            local_datetime=local_datetime,
            utc_datetime=utc_datetime,
        )

    def now(
        self,
        *,
        timezone_name: str | None = None,
    ) -> datetime:
        zone = self.get_zone(
            timezone_name,
        )

        return datetime.now(
            tz=zone,
        )

    def _resolve_timezone_name(
        self,
        timezone_name: str | None,
    ) -> str:
        if timezone_name is None:
            return self._default_timezone

        return self._validate_timezone_name(
            timezone_name,
        )

    @staticmethod
    def _validate_timezone_name(
        timezone_name: str,
    ) -> str:
        normalized = timezone_name.strip()

        if not normalized:
            raise EmptyTimezoneError(
                "Timezone name cannot be empty."
            )

        try:
            ZoneInfo(normalized)
        except ZoneInfoNotFoundError as exc:
            raise InvalidTimezoneError(
                f"Unknown timezone: {normalized!r}."
            ) from exc

        return normalized