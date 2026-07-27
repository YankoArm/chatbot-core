from __future__ import annotations

from datetime import datetime
from typing import Any

from chatbot.calendar.provider import CalendarProvider
from zoneinfo import ZoneInfo

class GoogleCalendarProvider(CalendarProvider):
    """
    Google Calendar implementation of CalendarProvider.

    The provider receives an authenticated Google Calendar API service.
    Authentication and credential management remain outside this class.
    """

    def __init__(
        self,
        service: Any,
        calendar_id: str = "primary",
        timezone: str = "Europe/Madrid",
        send_updates: str = "none",
    ) -> None:
        if service is None:
            raise ValueError(
                "Google Calendar service cannot be None."
            )

        normalized_calendar_id = calendar_id.strip()

        if not normalized_calendar_id:
            raise ValueError(
                "Google Calendar id cannot be empty."
            )

        normalized_timezone = timezone.strip()

        if not normalized_timezone:
            raise ValueError(
                "Google Calendar timezone cannot be empty."
            )

        try:
            timezone_info = ZoneInfo(
                normalized_timezone
            )
        except Exception as exc:
            raise ValueError(
                "Google Calendar timezone is invalid."
            ) from exc

        allowed_send_updates = {
            "all",
            "externalOnly",
            "none",
        }

        if send_updates not in allowed_send_updates:
            raise ValueError(
                "send_updates must be one of: "
                "'all', 'externalOnly' or 'none'."
            )

        self._service = service
        self._calendar_id = normalized_calendar_id
        self._timezone = normalized_timezone
        self._timezone_info = timezone_info
        self._send_updates = send_updates

    def is_available(
        self,
        *,
        start: datetime,
        end: datetime,
    ) -> bool:
        """
        Return whether no Google Calendar event overlaps the interval.
        """

        self._validate_time_range(
            start=start,
            end=end,
        )

        return not self.list_bookings(
            start=start,
            end=end,
        )

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
        """
        Create a Google Calendar event and return its event id.
        """

        self._validate_time_range(
            start=start,
            end=end,
        )

        normalized_title = title.strip()

        if not normalized_title:
            raise ValueError(
                "Booking title cannot be empty."
            )

        event_body: dict[str, Any] = {
            "summary": normalized_title,
            "start": self._build_event_datetime(
                start
            ),
            "end": self._build_event_datetime(
                end
            ),
        }

        if description is not None:
            event_body["description"] = description

        normalized_attendee = self._normalize_optional_text(
            attendee
        )

        if normalized_attendee is not None:
            event_body["attendees"] = [
                {
                    "email": normalized_attendee,
                }
            ]

        normalized_metadata = self._normalize_metadata(
            metadata
        )

        if normalized_metadata:
            event_body["extendedProperties"] = {
                "private": normalized_metadata,
            }

        created_event = (
            self._service
            .events()
            .insert(
                calendarId=self._calendar_id,
                body=event_body,
                sendUpdates=self._send_updates,
            )
            .execute()
        )

        event_id = created_event.get("id")

        if not isinstance(event_id, str):
            raise RuntimeError(
                "Google Calendar did not return an event id."
            )

        normalized_event_id = event_id.strip()

        if not normalized_event_id:
            raise RuntimeError(
                "Google Calendar returned an empty event id."
            )

        return normalized_event_id

    def cancel_booking(
        self,
        booking_id: str,
    ) -> None:
        """
        Delete a Google Calendar event.
        """

        normalized_booking_id = booking_id.strip()

        if not normalized_booking_id:
            raise ValueError(
                "Booking id cannot be empty."
            )

        (
            self._service
            .events()
            .delete(
                calendarId=self._calendar_id,
                eventId=normalized_booking_id,
                sendUpdates=self._send_updates,
            )
            .execute()
        )

    def list_bookings(
        self,
        *,
        start: datetime,
        end: datetime,
    ) -> list[dict[str, Any]]:
        """
        Return Google Calendar events overlapping the requested interval.
        """

        self._validate_time_range(
            start=start,
            end=end,
        )

        bookings: list[dict[str, Any]] = []
        page_token: str | None = None

        while True:
            request_arguments: dict[str, Any] = {
                "calendarId": self._calendar_id,
                "timeMin": self._to_google_datetime(start),
                "timeMax": self._to_google_datetime(end),
                "singleEvents": True,
                "orderBy": "startTime",
                "showDeleted": False,
            }

            if page_token is not None:
                request_arguments["pageToken"] = page_token

            response = (
                self._service
                .events()
                .list(
                    **request_arguments
                )
                .execute()
            )

            for event in response.get("items", []):
                booking = self._map_event(
                    event
                )

                if booking is not None:
                    bookings.append(
                        booking
                    )

            page_token = response.get(
                "nextPageToken"
            )

            if not page_token:
                break

        return bookings

    def _build_event_datetime(
        self,
        value: datetime,
    ) -> dict[str, str]:
        event_datetime = {
            "dateTime": self._to_google_datetime(
                value
            ),
        }

        if value.tzinfo is None:
            event_datetime["timeZone"] = (
                self._timezone
            )

        return event_datetime

    def _map_event(
        self,
        event: dict[str, Any],
    ) -> dict[str, Any] | None:
        """
        Convert a Google Calendar event into FlowForge booking format.

        All-day events are ignored because FlowForge bookings require
        explicit start and end times.
        """

        start_data = event.get("start", {})
        end_data = event.get("end", {})

        start_value = start_data.get(
            "dateTime"
        )

        end_value = end_data.get(
            "dateTime"
        )

        if not start_value or not end_value:
            return None

        event_id = event.get("id")

        if not event_id:
            return None

        private_metadata = (
            event
            .get("extendedProperties", {})
            .get("private", {})
        )

        attendees = event.get(
            "attendees",
            [],
        )

        attendee = None

        if attendees:
            attendee = attendees[0].get(
                "email"
            )

        return {
            "id": event_id,
            "start": self._parse_google_datetime(
                start_value
            ),
            "end": self._parse_google_datetime(
                end_value
            ),
            "title": event.get(
                "summary",
                "",
            ),
            "description": event.get(
                "description"
            ),
            "attendee": attendee,
            "metadata": dict(
                private_metadata
            ),
        }

    @staticmethod
    def _validate_time_range(
        *,
        start: datetime,
        end: datetime,
    ) -> None:
        if not isinstance(start, datetime):
            raise TypeError(
                "Booking start must be a datetime."
            )

        if not isinstance(end, datetime):
            raise TypeError(
                "Booking end must be a datetime."
            )

        if end <= start:
            raise ValueError(
                "Booking end must be later than start."
            )

    @staticmethod
    def _normalize_optional_text(
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized_value = value.strip()

        if not normalized_value:
            return None

        return normalized_value

    @staticmethod
    def _normalize_metadata(
        metadata: dict[str, Any] | None,
    ) -> dict[str, str]:
        if metadata is None:
            return {}

        return {
            str(key): str(value)
            for key, value in metadata.items()
            if value is not None
        }

    def _to_google_datetime(
        self,
        value: datetime,
    ) -> str:
        """
        Convert a datetime into an RFC 3339 value accepted by Google.

        Naive datetime values are interpreted using the provider timezone.
        Aware datetime values preserve their original timezone information.
        """

        normalized_value = value

        if normalized_value.tzinfo is None:
            normalized_value = normalized_value.replace(
                tzinfo=self._timezone_info
            )

        return normalized_value.isoformat()

    @staticmethod
    def _parse_google_datetime(
        value: str,
    ) -> datetime:
        normalized_value = value.replace(
            "Z",
            "+00:00",
        )

        return datetime.fromisoformat(
            normalized_value
        )