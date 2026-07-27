from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from chatbot.calendar import CalendarService
from chatbot.calendar import CalendarProvider


def build_provider(
    events: list[dict[str, Any]],
) -> Mock:
    provider = Mock(
        spec=CalendarProvider,
    )

    provider.list_bookings.return_value = tuple(
        events
    )

    return provider

def test_get_busy_periods_converts_calendar_events() -> None:
    provider = build_provider(
        [
            {
                "start": {
                    "dateTime": (
                        "2026-07-31T10:00:00+02:00"
                    ),
                },
                "end": {
                    "dateTime": (
                        "2026-07-31T11:00:00+02:00"
                    ),
                },
            },
        ]
    )

    service = CalendarService(provider)

    start = datetime(
        2026,
        7,
        31,
        0,
        0,
        tzinfo=timezone.utc,
    )

    end = datetime(
        2026,
        8,
        1,
        0,
        0,
        tzinfo=timezone.utc,
    )

    periods = service.get_busy_periods(
        start,
        end,
    )

    assert len(periods) == 1
    assert periods[0].start.hour == 10
    assert periods[0].end.hour == 11


def test_get_busy_periods_requests_expected_window() -> None:
    provider = build_provider([])

    service = CalendarService(provider)

    start = datetime(
        2026,
        7,
        31,
        8,
        0,
        tzinfo=timezone.utc,
    )

    end = datetime(
        2026,
        7,
        31,
        18,
        0,
        tzinfo=timezone.utc,
    )

    service.get_busy_periods(
        start,
        end,
    )

    provider.list_bookings.assert_called_once_with(
        start=start,
        end=end,
    )

def test_get_busy_periods_ignores_cancelled_events() -> None:
    provider = build_provider(
        [
            {
                "status": "cancelled",
                "start": {
                    "dateTime": (
                        "2026-07-31T10:00:00+02:00"
                    ),
                },
                "end": {
                    "dateTime": (
                        "2026-07-31T11:00:00+02:00"
                    ),
                },
            },
        ]
    )

    service = CalendarService(provider)

    periods = service.get_busy_periods(
        datetime(
            2026,
            7,
            31,
            tzinfo=timezone.utc,
        ),
        datetime(
            2026,
            8,
            1,
            tzinfo=timezone.utc,
        ),
    )

    assert periods == ()


def test_calendar_window_requires_aware_datetimes() -> None:
    provider = build_provider([])

    service = CalendarService(provider)

    with pytest.raises(ValueError):
        service.get_busy_periods(
            datetime(2026, 7, 31),
            datetime(
                2026,
                8,
                1,
                tzinfo=timezone.utc,
            ),
        )

    provider.list_bookings.assert_not_called()


def test_calendar_window_requires_end_after_start() -> None:
    provider = build_provider([])

    service = CalendarService(provider)

    start = datetime(
        2026,
        7,
        31,
        10,
        0,
        tzinfo=timezone.utc,
    )

    with pytest.raises(ValueError):
        service.get_busy_periods(
            start,
            start,
        )

    provider.list_bookings.assert_not_called()