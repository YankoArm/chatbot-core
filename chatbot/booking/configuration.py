from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from chatbot.availability import (
    BookingRules,
    BusinessHours,
    TimeRange,
    Weekday,
)
from chatbot.instances import Instance


_WEEKDAYS_BY_NAME = {
    "monday": Weekday.MONDAY,
    "tuesday": Weekday.TUESDAY,
    "wednesday": Weekday.WEDNESDAY,
    "thursday": Weekday.THURSDAY,
    "friday": Weekday.FRIDAY,
    "saturday": Weekday.SATURDAY,
    "sunday": Weekday.SUNDAY,
}


@dataclass(frozen=True, slots=True)
class BookingConfiguration:
    """
    Runtime booking configuration resolved from an Instance.
    """

    business_hours: BusinessHours
    booking_rules: BookingRules


def build_booking_configuration(
    instance: Instance,
) -> BookingConfiguration:
    """
    Build booking runtime objects from instance settings.
    """

    booking_settings = instance.settings.get(
        "booking",
    )

    if not isinstance(booking_settings, dict):
        raise ValueError(
            "Instance booking settings must be a dictionary."
        )

    if not booking_settings.get("enabled", False):
        raise ValueError(
            "Booking is not enabled for this instance."
        )

    timezone_name = _require_string(
        booking_settings,
        "timezone",
    )

    _validate_timezone(
        timezone_name
    )

    business_hours_settings = booking_settings.get(
        "business_hours",
    )

    if not isinstance(
        business_hours_settings,
        dict,
    ):
        raise ValueError(
            "Booking business_hours must be a dictionary."
        )

    rules_settings = booking_settings.get(
        "rules",
    )

    if not isinstance(
        rules_settings,
        dict,
    ):
        raise ValueError(
            "Booking rules must be a dictionary."
        )

    business_hours = _build_business_hours(
        business_hours_settings,
        timezone_name=timezone_name,
    )

    booking_rules = _build_booking_rules(
        rules_settings
    )

    return BookingConfiguration(
        business_hours=business_hours,
        booking_rules=booking_rules,
    )


def _build_business_hours(
    settings: dict[str, Any],
    *,
    timezone_name: str,
) -> BusinessHours:
    schedule: dict[
        Weekday,
        tuple[TimeRange, ...],
    ] = {}

    for weekday_name, weekday in _WEEKDAYS_BY_NAME.items():
        raw_ranges = settings.get(
            weekday_name,
            [],
        )

        if not isinstance(raw_ranges, list):
            raise ValueError(
                "Business-hours weekday entries must be lists: "
                f"{weekday_name!r}."
            )

        schedule[weekday] = tuple(
            _build_time_range(
                raw_range,
                weekday_name=weekday_name,
            )
            for raw_range in raw_ranges
        )

    return BusinessHours(
        schedule=schedule,
        timezone_name=timezone_name,
    )


def _build_time_range(
    value: Any,
    *,
    weekday_name: str,
) -> TimeRange:
    if (
        not isinstance(value, list)
        or len(value) != 2
    ):
        raise ValueError(
            "Each business-hours range must contain "
            f"exactly two times for {weekday_name!r}."
        )

    start_value, end_value = value

    return TimeRange(
        start=_parse_time(
            start_value,
            field_name=(
                f"{weekday_name}.start"
            ),
        ),
        end=_parse_time(
            end_value,
            field_name=(
                f"{weekday_name}.end"
            ),
        ),
    )


def _build_booking_rules(
    settings: dict[str, Any],
) -> BookingRules:
    appointment_duration_minutes = (
        _require_positive_integer(
            settings,
            "appointment_duration_minutes",
        )
    )

    slot_interval_minutes = (
        _require_positive_integer(
            settings,
            "slot_interval_minutes",
        )
    )

    minimum_notice_hours = (
        _require_non_negative_integer(
            settings,
            "minimum_notice_hours",
        )
    )

    maximum_advance_days = (
        _require_positive_integer(
            settings,
            "maximum_advance_days",
        )
    )

    buffer_before_minutes = (
        _optional_non_negative_integer(
            settings,
            "buffer_before_minutes",
            default=0,
        )
    )

    buffer_after_minutes = (
        _optional_non_negative_integer(
            settings,
            "buffer_after_minutes",
            default=0,
        )
    )

    allow_past_bookings = settings.get(
        "allow_past_bookings",
        False,
    )

    if not isinstance(
        allow_past_bookings,
        bool,
    ):
        raise ValueError(
            "Booking rule 'allow_past_bookings' "
            "must be a boolean."
        )

    return BookingRules(
        appointment_duration=timedelta(
            minutes=appointment_duration_minutes,
        ),
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
        maximum_advance=timedelta(
            days=maximum_advance_days,
        ),
        allow_past_bookings=allow_past_bookings,
    )


def _parse_time(
    value: Any,
    *,
    field_name: str,
) -> time:
    if not isinstance(value, str):
        raise ValueError(
            f"Booking time {field_name!r} must be a string."
        )

    try:
        return datetime.strptime(
            value.strip(),
            "%H:%M",
        ).time()
    except ValueError as exc:
        raise ValueError(
            f"Booking time {field_name!r} "
            "must use HH:MM format."
        ) from exc


def _require_string(
    settings: dict[str, Any],
    key: str,
) -> str:
    value = settings.get(key)

    if not isinstance(value, str):
        raise ValueError(
            f"Booking setting {key!r} must be a string."
        )

    normalized_value = value.strip()

    if not normalized_value:
        raise ValueError(
            f"Booking setting {key!r} cannot be empty."
        )

    return normalized_value


def _require_positive_integer(
    settings: dict[str, Any],
    key: str,
) -> int:
    value = settings.get(key)

    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value <= 0
    ):
        raise ValueError(
            f"Booking setting {key!r} "
            "must be a positive integer."
        )

    return value


def _require_non_negative_integer(
    settings: dict[str, Any],
    key: str,
) -> int:
    value = settings.get(key)

    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value < 0
    ):
        raise ValueError(
            f"Booking setting {key!r} "
            "must be a non-negative integer."
        )

    return value


def _optional_non_negative_integer(
    settings: dict[str, Any],
    key: str,
    *,
    default: int,
) -> int:
    if key not in settings:
        return default

    return _require_non_negative_integer(
        settings,
        key,
    )


def _validate_timezone(
    timezone_name: str,
) -> None:
    try:
        ZoneInfo(
            timezone_name
        )
    except Exception as exc:
        raise ValueError(
            "Booking timezone is invalid: "
            f"{timezone_name!r}."
        ) from exc