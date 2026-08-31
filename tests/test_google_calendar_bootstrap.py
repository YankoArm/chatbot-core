import run_google_calendar


def test_calendar_service_factory_reuses_google_authentication(
    monkeypatch,
) -> None:
    authenticated_google_service = object()
    created_providers: list[tuple[object, str, str]] = []

    class RecordingGoogleCalendarProvider:
        def __init__(
            self,
            *,
            service: object,
            calendar_id: str,
            timezone: str,
        ) -> None:
            created_providers.append(
                (
                    service,
                    calendar_id,
                    timezone,
                )
            )

    monkeypatch.setattr(
        run_google_calendar,
        "build_google_calendar_service",
        lambda **_kwargs: authenticated_google_service,
    )
    monkeypatch.setattr(
        run_google_calendar,
        "GoogleCalendarProvider",
        RecordingGoogleCalendarProvider,
    )

    factory = (
        run_google_calendar.build_calendar_service_factory()
    )

    first_service = factory(
        "salon-norte-calendar"
    )
    second_service = factory(
        "salon-sur-calendar"
    )

    assert first_service is not second_service
    assert created_providers == [
        (
            authenticated_google_service,
            "salon-norte-calendar",
            "Europe/Madrid",
        ),
        (
            authenticated_google_service,
            "salon-sur-calendar",
            "Europe/Madrid",
        ),
    ]