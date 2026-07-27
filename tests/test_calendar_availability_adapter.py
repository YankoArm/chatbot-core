from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from chatbot.calendar import (
    CalendarAvailabilityAdapter,
    CalendarEventAdapterError,
)


MADRID = ZoneInfo("Europe/Madrid")


def test_converts_timed_event_to_busy_period() -> None:
    adapter = CalendarAvailabilityAdapter()

    event = {
        "status": "confirmed",
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
    }

    period = adapter.event_to_busy_period(event)

    assert period is not None
    assert period.start == datetime(
        2026,
        7,
        31,
        10,
        0,
        tzinfo=MADRID,
    )
    assert period.end == datetime(
        2026,
        7,
        31,
        11,
        0,
        tzinfo=MADRID,
    )


def test_converts_utc_event() -> None:
    adapter = CalendarAvailabilityAdapter()

    event = {
        "start": {
            "dateTime": "2026-07-31T08:00:00Z",
        },
        "end": {
            "dateTime": "2026-07-31T09:00:00Z",
        },
    }

    period = adapter.event_to_busy_period(event)

    assert period is not None
    assert period.start.utcoffset().total_seconds() == 0
    assert period.end.utcoffset().total_seconds() == 0


def test_localizes_naive_calendar_datetime() -> None:
    adapter = CalendarAvailabilityAdapter()

    event = {
        "start": {
            "dateTime": "2026-07-31T10:00:00",
            "timeZone": "Europe/Madrid",
        },
        "end": {
            "dateTime": "2026-07-31T11:00:00",
            "timeZone": "Europe/Madrid",
        },
    }

    period = adapter.event_to_busy_period(event)

    assert period is not None
    assert period.start.tzinfo is not None
    assert period.start.hour == 10
    assert period.end.hour == 11


def test_converts_all_day_event() -> None:
    adapter = CalendarAvailabilityAdapter()

    event = {
        "start": {
            "date": "2026-07-31",
        },
        "end": {
            "date": "2026-08-01",
        },
    }

    period = adapter.event_to_busy_period(event)

    assert period is not None
    assert period.start == datetime(
        2026,
        7,
        31,
        0,
        0,
        tzinfo=MADRID,
    )
    assert period.end == datetime(
        2026,
        8,
        1,
        0,
        0,
        tzinfo=MADRID,
    )


def test_ignores_cancelled_event() -> None:
    adapter = CalendarAvailabilityAdapter()

    event = {
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
    }

    assert (
        adapter.event_to_busy_period(event)
        is None
    )


def test_ignores_transparent_event() -> None:
    adapter = CalendarAvailabilityAdapter()

    event = {
        "transparency": "transparent",
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
    }

    assert (
        adapter.event_to_busy_period(event)
        is None
    )


def test_converts_and_sorts_multiple_events() -> None:
    adapter = CalendarAvailabilityAdapter()

    events = (
        {
            "start": {
                "dateTime": (
                    "2026-07-31T11:00:00+02:00"
                ),
            },
            "end": {
                "dateTime": (
                    "2026-07-31T12:00:00+02:00"
                ),
            },
        },
        {
            "start": {
                "dateTime": (
                    "2026-07-31T09:00:00+02:00"
                ),
            },
            "end": {
                "dateTime": (
                    "2026-07-31T10:00:00+02:00"
                ),
            },
        },
    )

    periods = adapter.events_to_busy_periods(
        events
    )

    assert len(periods) == 2
    assert periods[0].start.hour == 9
    assert periods[1].start.hour == 11


def test_invalid_start_is_rejected() -> None:
    adapter = CalendarAvailabilityAdapter()

    event = {
        "start": None,
        "end": {
            "dateTime": (
                "2026-07-31T11:00:00+02:00"
            ),
        },
    }

    with pytest.raises(
        CalendarEventAdapterError
    ):
        adapter.event_to_busy_period(event)


def test_missing_start_type_is_rejected() -> None:
    adapter = CalendarAvailabilityAdapter()

    event = {
        "start": {},
        "end": {},
    }

    with pytest.raises(
        CalendarEventAdapterError
    ):
        adapter.event_to_busy_period(event)


def test_invalid_datetime_is_rejected() -> None:
    adapter = CalendarAvailabilityAdapter()

    event = {
        "start": {
            "dateTime": "not-a-datetime",
        },
        "end": {
            "dateTime": (
                "2026-07-31T11:00:00+02:00"
            ),
        },
    }

    with pytest.raises(
        CalendarEventAdapterError
    ):
        adapter.event_to_busy_period(event)


def test_invalid_all_day_date_is_rejected() -> None:
    adapter = CalendarAvailabilityAdapter()

    event = {
        "start": {
            "date": "31/07/2026",
        },
        "end": {
            "date": "2026-08-01",
        },
    }

    with pytest.raises(
        CalendarEventAdapterError
    ):
        adapter.event_to_busy_period(event)