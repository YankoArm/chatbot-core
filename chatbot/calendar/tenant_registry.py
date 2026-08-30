from __future__ import annotations

from collections.abc import Callable
from threading import RLock


CalendarServiceFactory = Callable[
    [str],
    object,
]


class TenantCalendarRegistry:
    """
    Build and retain one calendar service per calendar identifier.
    """

    def __init__(
        self,
        *,
        calendar_service_factory: (
            CalendarServiceFactory
        ),
    ) -> None:
        self._calendar_service_factory = (
            calendar_service_factory
        )
        self._calendar_services: dict[
            str,
            object,
        ] = {}
        self._lock = RLock()

    def get_calendar_service(
        self,
        calendar_id: str,
    ) -> object:
        normalized_calendar_id = calendar_id.strip()

        if not normalized_calendar_id:
            raise ValueError(
                "Calendar id cannot be empty."
            )

        with self._lock:
            cached_service = (
                self._calendar_services.get(
                    normalized_calendar_id
                )
            )

            if cached_service is not None:
                return cached_service

            calendar_service = (
                self._calendar_service_factory(
                    normalized_calendar_id
                )
            )
            self._calendar_services[
                normalized_calendar_id
            ] = calendar_service

            return calendar_service