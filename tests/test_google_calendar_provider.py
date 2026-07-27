from __future__ import annotations

from datetime import datetime
from typing import Any

import pytest

from chatbot.calendar import GoogleCalendarProvider


class FakeGoogleRequest:
    def __init__(
        self,
        response: Any = None,
    ) -> None:
        self._response = response

    def execute(
        self,
    ) -> Any:
        return self._response


class FakeGoogleEventsResource:
    def __init__(
        self,
    ) -> None:
        self.list_responses: list[
            dict[str, Any]
        ] = []

        self.insert_response: dict[
            str,
            Any,
        ] = {
            "id": "google-event-123",
        }

        self.list_calls: list[
            dict[str, Any]
        ] = []

        self.insert_calls: list[
            dict[str, Any]
        ] = []

        self.delete_calls: list[
            dict[str, Any]
        ] = []

    def list(
        self,
        **kwargs: Any,
    ) -> FakeGoogleRequest:
        self.list_calls.append(
            kwargs
        )

        if self.list_responses:
            response = self.list_responses.pop(
                0
            )
        else:
            response = {
                "items": [],
            }

        return FakeGoogleRequest(
            response
        )

    def insert(
        self,
        **kwargs: Any,
    ) -> FakeGoogleRequest:
        self.insert_calls.append(
            kwargs
        )

        return FakeGoogleRequest(
            self.insert_response
        )

    def delete(
        self,
        **kwargs: Any,
    ) -> FakeGoogleRequest:
        self.delete_calls.append(
            kwargs
        )

        return FakeGoogleRequest(
            None
        )


class FakeGoogleCalendarService:
    def __init__(
        self,
    ) -> None:
        self.events_resource = (
            FakeGoogleEventsResource()
        )

    def events(
        self,
    ) -> FakeGoogleEventsResource:
        return self.events_resource


@pytest.fixture
def google_service() -> FakeGoogleCalendarService:
    return FakeGoogleCalendarService()


@pytest.fixture
def provider(
    google_service: FakeGoogleCalendarService,
) -> GoogleCalendarProvider:
    return GoogleCalendarProvider(
        service=google_service,
        calendar_id="primary",
        timezone="Europe/Madrid",
    )


def test_google_provider_requires_service() -> None:
    with pytest.raises(
        ValueError,
        match="service cannot be None",
    ):
        GoogleCalendarProvider(
            service=None,
        )


def test_google_provider_rejects_empty_calendar_id() -> None:
    service = FakeGoogleCalendarService()

    with pytest.raises(
        ValueError,
        match="id cannot be empty",
    ):
        GoogleCalendarProvider(
            service=service,
            calendar_id=" ",
        )


def test_google_provider_rejects_empty_timezone() -> None:
    service = FakeGoogleCalendarService()

    with pytest.raises(
        ValueError,
        match="timezone cannot be empty",
    ):
        GoogleCalendarProvider(
            service=service,
            timezone=" ",
        )


def test_google_provider_rejects_invalid_send_updates() -> None:
    service = FakeGoogleCalendarService()

    with pytest.raises(
        ValueError,
        match="send_updates",
    ):
        GoogleCalendarProvider(
            service=service,
            send_updates="invalid",
        )


def test_google_provider_reports_available_range(
    provider: GoogleCalendarProvider,
) -> None:
    available = provider.is_available(
        start=datetime(
            2026,
            7,
            28,
            16,
            0,
        ),
        end=datetime(
            2026,
            7,
            28,
            17,
            0,
        ),
    )

    assert available is True


def test_google_provider_reports_unavailable_range(
    provider: GoogleCalendarProvider,
    google_service: FakeGoogleCalendarService,
) -> None:
    google_service.events_resource.list_responses = [
        {
            "items": [
                {
                    "id": "event-1",
                    "summary": "Existing booking",
                    "start": {
                        "dateTime": (
                            "2026-07-28T16:00:00"
                        ),
                    },
                    "end": {
                        "dateTime": (
                            "2026-07-28T17:00:00"
                        ),
                    },
                }
            ]
        }
    ]

    available = provider.is_available(
        start=datetime(
            2026,
            7,
            28,
            16,
            0,
        ),
        end=datetime(
            2026,
            7,
            28,
            17,
            0,
        ),
    )

    assert available is False


def test_google_provider_creates_booking(
    provider: GoogleCalendarProvider,
    google_service: FakeGoogleCalendarService,
) -> None:
    booking_id = provider.create_booking(
        start=datetime(
            2026,
            7,
            28,
            16,
            30,
        ),
        end=datetime(
            2026,
            7,
            28,
            17,
            30,
        ),
        title="Booking - Yanko",
        description="Client: Yanko",
        attendee="yanko@example.com",
        metadata={
            "client_name": "Yanko",
            "duration": 60,
        },
    )

    assert booking_id == "google-event-123"

    call = (
        google_service
        .events_resource
        .insert_calls[0]
    )

    assert call["calendarId"] == "primary"
    assert call["sendUpdates"] == "none"

    body = call["body"]

    assert body["summary"] == "Booking - Yanko"
    assert body["description"] == "Client: Yanko"

    assert body["start"] == {
        "dateTime": "2026-07-28T16:30:00+02:00",
        "timeZone": "Europe/Madrid",
    }

    assert body["end"] == {
        "dateTime": "2026-07-28T17:30:00+02:00",
        "timeZone": "Europe/Madrid",
    }

    assert body["attendees"] == [
        {
            "email": "yanko@example.com",
        }
    ]

    assert body["extendedProperties"]["private"] == {
        "client_name": "Yanko",
        "duration": "60",
    }


def test_google_provider_omits_optional_event_fields(
    provider: GoogleCalendarProvider,
    google_service: FakeGoogleCalendarService,
) -> None:
    provider.create_booking(
        start=datetime(
            2026,
            7,
            28,
            16,
            30,
        ),
        end=datetime(
            2026,
            7,
            28,
            17,
            30,
        ),
        title="Booking",
    )

    body = (
        google_service
        .events_resource
        .insert_calls[0]["body"]
    )

    assert "description" not in body
    assert "attendees" not in body
    assert "extendedProperties" not in body


def test_google_provider_rejects_empty_title(
    provider: GoogleCalendarProvider,
) -> None:
    with pytest.raises(
        ValueError,
        match="title cannot be empty",
    ):
        provider.create_booking(
            start=datetime(
                2026,
                7,
                28,
                16,
                0,
            ),
            end=datetime(
                2026,
                7,
                28,
                17,
                0,
            ),
            title=" ",
        )


def test_google_provider_requires_event_id(
    provider: GoogleCalendarProvider,
    google_service: FakeGoogleCalendarService,
) -> None:
    google_service.events_resource.insert_response = {}

    with pytest.raises(
        RuntimeError,
        match="did not return an event id",
    ):
        provider.create_booking(
            start=datetime(
                2026,
                7,
                28,
                16,
                0,
            ),
            end=datetime(
                2026,
                7,
                28,
                17,
                0,
            ),
            title="Booking",
        )


def test_google_provider_cancels_booking(
    provider: GoogleCalendarProvider,
    google_service: FakeGoogleCalendarService,
) -> None:
    provider.cancel_booking(
        "google-event-123"
    )

    assert (
        google_service
        .events_resource
        .delete_calls
    ) == [
        {
            "calendarId": "primary",
            "eventId": "google-event-123",
            "sendUpdates": "none",
        }
    ]


def test_google_provider_rejects_empty_booking_id(
    provider: GoogleCalendarProvider,
) -> None:
    with pytest.raises(
        ValueError,
        match="id cannot be empty",
    ):
        provider.cancel_booking(
            " "
        )


def test_google_provider_lists_bookings(
    provider: GoogleCalendarProvider,
    google_service: FakeGoogleCalendarService,
) -> None:
    google_service.events_resource.list_responses = [
        {
            "items": [
                {
                    "id": "event-1",
                    "summary": "Booking - Yanko",
                    "description": "Client: Yanko",
                    "start": {
                        "dateTime": (
                            "2026-07-28T16:30:00"
                        ),
                    },
                    "end": {
                        "dateTime": (
                            "2026-07-28T17:30:00"
                        ),
                    },
                    "attendees": [
                        {
                            "email": (
                                "yanko@example.com"
                            ),
                        }
                    ],
                    "extendedProperties": {
                        "private": {
                            "client_name": "Yanko",
                        }
                    },
                }
            ]
        }
    ]

    bookings = provider.list_bookings(
        start=datetime(
            2026,
            7,
            28,
            0,
            0,
        ),
        end=datetime(
            2026,
            7,
            29,
            0,
            0,
        ),
    )

    assert bookings == [
        {
            "id": "event-1",
            "start": datetime(
                2026,
                7,
                28,
                16,
                30,
            ),
            "end": datetime(
                2026,
                7,
                28,
                17,
                30,
            ),
            "title": "Booking - Yanko",
            "description": "Client: Yanko",
            "attendee": "yanko@example.com",
            "metadata": {
                "client_name": "Yanko",
            },
        }
    ]

    call = (
        google_service
        .events_resource
        .list_calls[0]
    )

    assert call["calendarId"] == "primary"
    assert call["timeMin"] == (
        "2026-07-28T00:00:00+02:00"
    )

    assert call["timeMax"] == (
        "2026-07-29T00:00:00+02:00"
    )
    assert call["singleEvents"] is True
    assert call["orderBy"] == "startTime"
    assert call["showDeleted"] is False


def test_google_provider_lists_all_pages(
    provider: GoogleCalendarProvider,
    google_service: FakeGoogleCalendarService,
) -> None:
    google_service.events_resource.list_responses = [
        {
            "items": [
                {
                    "id": "event-1",
                    "summary": "First",
                    "start": {
                        "dateTime": (
                            "2026-07-28T10:00:00"
                        ),
                    },
                    "end": {
                        "dateTime": (
                            "2026-07-28T11:00:00"
                        ),
                    },
                }
            ],
            "nextPageToken": "page-2",
        },
        {
            "items": [
                {
                    "id": "event-2",
                    "summary": "Second",
                    "start": {
                        "dateTime": (
                            "2026-07-28T12:00:00"
                        ),
                    },
                    "end": {
                        "dateTime": (
                            "2026-07-28T13:00:00"
                        ),
                    },
                }
            ]
        },
    ]

    bookings = provider.list_bookings(
        start=datetime(
            2026,
            7,
            28,
            0,
            0,
        ),
        end=datetime(
            2026,
            7,
            29,
            0,
            0,
        ),
    )

    assert [
        booking["id"]
        for booking in bookings
    ] == [
        "event-1",
        "event-2",
    ]

    assert len(
        google_service
        .events_resource
        .list_calls
    ) == 2

    second_call = (
        google_service
        .events_resource
        .list_calls[1]
    )

    assert second_call["pageToken"] == "page-2"


def test_google_provider_ignores_all_day_events(
    provider: GoogleCalendarProvider,
    google_service: FakeGoogleCalendarService,
) -> None:
    google_service.events_resource.list_responses = [
        {
            "items": [
                {
                    "id": "all-day-event",
                    "summary": "Holiday",
                    "start": {
                        "date": "2026-07-28",
                    },
                    "end": {
                        "date": "2026-07-29",
                    },
                }
            ]
        }
    ]

    bookings = provider.list_bookings(
        start=datetime(
            2026,
            7,
            28,
            0,
            0,
        ),
        end=datetime(
            2026,
            7,
            29,
            0,
            0,
        ),
    )

    assert bookings == []


@pytest.mark.parametrize(
    (
        "start",
        "end",
        "expected_exception",
    ),
    [
        (
            "2026-07-28",
            datetime(
                2026,
                7,
                28,
                17,
                0,
            ),
            TypeError,
        ),
        (
            datetime(
                2026,
                7,
                28,
                16,
                0,
            ),
            "2026-07-28",
            TypeError,
        ),
        (
            datetime(
                2026,
                7,
                28,
                17,
                0,
            ),
            datetime(
                2026,
                7,
                28,
                16,
                0,
            ),
            ValueError,
        ),
    ],
)
def test_google_provider_rejects_invalid_time_ranges(
    provider: GoogleCalendarProvider,
    start: Any,
    end: Any,
    expected_exception: type[Exception],
) -> None:
    with pytest.raises(
        expected_exception
    ):
        provider.is_available(
            start=start,
            end=end,
        )