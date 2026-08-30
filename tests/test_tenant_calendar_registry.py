from chatbot.calendar.tenant_registry import (
    TenantCalendarRegistry,
)


def test_tenant_calendar_registry_builds_and_caches_calendar_services(
) -> None:
    built_calendar_ids: list[str] = []
    salon_calendar = object()

    def build_calendar_service(
        calendar_id: str,
    ) -> object:
        built_calendar_ids.append(
            calendar_id
        )
        return salon_calendar

    registry = TenantCalendarRegistry(
        calendar_service_factory=build_calendar_service,
    )

    first_service = registry.get_calendar_service(
        "salon-norte-calendar-id"
    )
    second_service = registry.get_calendar_service(
        "salon-norte-calendar-id"
    )

    assert first_service is salon_calendar
    assert second_service is salon_calendar
    assert built_calendar_ids == [
        "salon-norte-calendar-id",
    ]