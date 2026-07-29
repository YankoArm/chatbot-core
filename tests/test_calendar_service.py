from datetime import date, datetime, time
from typing import Any
from zoneinfo import ZoneInfo

import pytest

from chatbot.availability import (
    BookingRules,
    BusinessHours,
)
from chatbot.calendar import (
    CalendarService,
    InMemoryCalendarProvider,
)
from chatbot.calendar.provider import CalendarProvider


class FakeCalendarProvider(CalendarProvider):
    def is_available(
        self,
        *,
        start: datetime,
        end: datetime,
    ) -> bool:
        return True

    def create_booking(
        self,
        *,
        start: datetime,
        end: datetime,
        title: str,
        description: str | None = None,
        attendee: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        return "booking-123"

    def cancel_booking(
        self,
        booking_id: str,
    ) -> None:
        pass

    def list_bookings(
        self,
        *,
        start: datetime,
        end: datetime,
    ) -> list[dict[str, Any]]:
        return []


def make_service(
    duration_minutes: int = 60,
) -> CalendarService:
    return CalendarService(
        provider=InMemoryCalendarProvider(),
        default_duration_minutes=duration_minutes,
    )


def test_calendar_service_builds_time_range():
    service = make_service()

    start, end = service.build_time_range(
        date="25/07/2026",
        time="16:30",
    )

    assert start == datetime(
        2026,
        7,
        25,
        16,
        30,
    )

    assert end == datetime(
        2026,
        7,
        25,
        17,
        30,
    )


def test_calendar_service_uses_default_duration():
    service = make_service(
        duration_minutes=30,
    )

    start, end = service.build_time_range(
        date="25/07/2026",
        time="16:30",
    )

    assert end == datetime(
        2026,
        7,
        25,
        17,
        0,
    )

    assert end > start


def test_calendar_service_allows_duration_override():
    service = make_service()

    start, end = service.build_time_range(
        date="25/07/2026",
        time="16:30",
        duration_minutes=90,
    )

    assert end == datetime(
        2026,
        7,
        25,
        18,
        0,
    )

    assert end > start


def test_calendar_service_reports_available_slot():
    service = make_service()

    assert service.is_available(
        date="25/07/2026",
        time="16:30",
    ) is True


def test_calendar_service_creates_booking():
    provider = InMemoryCalendarProvider()

    service = CalendarService(
        provider=provider,
    )

    booking_id = service.create_booking(
        date="25/07/2026",
        time="16:30",
        title="Tarot session",
        description="Client: Yanko",
        metadata={
            "client_phone": "600123123",
        },
    )

    bookings = provider.list_bookings(
        start=datetime(
            2026,
            7,
            25,
            16,
            0,
        ),
        end=datetime(
            2026,
            7,
            25,
            18,
            0,
        ),
    )

    assert len(bookings) == 1
    assert bookings[0]["id"] == booking_id
    assert bookings[0]["title"] == (
        "Tarot session"
    )

    assert bookings[0]["metadata"] == {
        "client_phone": "600123123",
    }


def test_calendar_service_rejects_unavailable_slot():
    provider = InMemoryCalendarProvider()

    provider.create_booking(
        start=datetime(
            2026,
            7,
            25,
            16,
            0,
        ),
        end=datetime(
            2026,
            7,
            25,
            17,
            0,
        ),
        title="Existing booking",
    )

    service = CalendarService(
        provider=provider,
    )

    with pytest.raises(
        ValueError,
        match="not available",
    ):
        service.create_booking(
            date="25/07/2026",
            time="16:30",
            title="Conflicting booking",
        )


def test_calendar_service_cancels_booking():
    provider = InMemoryCalendarProvider()

    service = CalendarService(
        provider=provider,
    )

    booking_id = service.create_booking(
        date="25/07/2026",
        time="16:30",
        title="Tarot session",
    )

    service.cancel_booking(
        booking_id,
    )

    assert service.is_available(
        date="25/07/2026",
        time="16:30",
    ) is True


def test_calendar_service_rejects_invalid_datetime():
    service = make_service()

    with pytest.raises(
        ValueError,
        match="DD/MM/YYYY and HH:MM",
    ):
        service.build_time_range(
            date="2026-07-25",
            time="16:30",
        )


@pytest.mark.parametrize(
    "duration_minutes",
    [
        0,
        -1,
        -30,
    ],
)
def test_calendar_service_rejects_invalid_default_duration(
    duration_minutes,
):
    provider = InMemoryCalendarProvider()

    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        CalendarService(
            provider=provider,
            default_duration_minutes=duration_minutes,
        )


@pytest.mark.parametrize(
    "duration_minutes",
    [
        0,
        -1,
        -30,
    ],
)
def test_calendar_service_rejects_invalid_override_duration(
    duration_minutes,
):
    service = make_service()

    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        service.build_time_range(
            date="25/07/2026",
            time="16:30",
            duration_minutes=duration_minutes,
        )


def test_calendar_service_returns_dates_with_available_slots() -> None:
    provider = FakeCalendarProvider()

    service = CalendarService(
        provider=provider,
    )

    business_hours = BusinessHours.standard_week(
        start=time(9, 0),
        end=time(18, 0),
        timezone_name="Europe/Madrid",
    )

    rules = BookingRules.hourly()

    now = datetime(
        2026,
        7,
        28,
        8,
        0,
        tzinfo=ZoneInfo("Europe/Madrid"),
    )

    available_dates = service.get_available_dates(
        start_date=date(2026, 7, 28),
        days=3,
        business_hours=business_hours,
        rules=rules,
        now=now,
    )

    assert available_dates == (
        date(2026, 7, 28),
        date(2026, 7, 29),
        date(2026, 7, 30),
    )

def test_calendar_service_skips_dates_without_available_slots() -> None:
    provider = FakeCalendarProvider()

    service = CalendarService(
        provider=provider,
    )

    business_hours = BusinessHours.standard_week(
        start=time(9, 0),
        end=time(18, 0),
        timezone_name="Europe/Madrid",
    )

    rules = BookingRules.hourly()

    now = datetime(
        2026,
        7,
        28,
        8,
        0,
        tzinfo=ZoneInfo("Europe/Madrid"),
    )

    provider.list_bookings = lambda **kwargs: [
        {
            "start": {
                "dateTime": (
                    "2026-07-28T09:00:00+02:00"
                ),
            },
            "end": {
                "dateTime": (
                    "2026-07-28T18:00:00+02:00"
                ),
            },
        }
    ]

    available_dates = service.get_available_dates(
        start_date=date(2026, 7, 28),
        days=3,
        business_hours=business_hours,
        rules=rules,
        now=now,
    )

    assert available_dates == (
        date(2026, 7, 29),
        date(2026, 7, 30),
    )