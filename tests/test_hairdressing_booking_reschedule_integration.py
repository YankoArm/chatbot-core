from __future__ import annotations

import re
from datetime import datetime, timedelta

from chatbot.application import Bootstrap
from chatbot.booking import (
    Booking,
    BookingService,
    InMemoryBookingRepository,
    build_booking_configuration,
)
from chatbot.calendar import (
    CalendarService,
    InMemoryCalendarProvider,
)
from chatbot.capabilities.booking import BookingCapability
from chatbot.clients.registry import build_client_instance


_DATE_PATTERN = re.compile(
    r"\b\d{2}/\d{2}/\d{4}\b"
)

_TIME_PATTERN = re.compile(
    r"\b\d{2}:\d{2}\b"
)


def test_hairdressing_application_reschedules_existing_booking(
) -> None:
    instance = build_client_instance(
        "hairdressing_demo"
    )
    booking_configuration = (
        build_booking_configuration(
            instance
        )
    )

    calendar_provider = (
        InMemoryCalendarProvider()
    )
    calendar_service = CalendarService(
        provider=calendar_provider,
        default_duration_minutes=60,
    )
    booking_repository = (
        InMemoryBookingRepository()
    )
    booking_service = BookingService(
        repository=booking_repository,
        calendar_service=calendar_service,
    )


    original_start = (
        datetime.now()
        + timedelta(days=45)
    ).replace(
        hour=16,
        minute=30,
        second=0,
        microsecond=0,
    )
    original_end = original_start + timedelta(
        minutes=120
    )

    calendar_booking_id = (
        calendar_provider.create_booking(
            start=original_start,
            end=original_end,
            title="Mechas — Yanko",
        )
    )

    original_booking = Booking(
        name="Yanko",
        phone="+34600123123",
        date=original_start.strftime(
            "%d/%m/%Y"
        ),
        time=original_start.strftime(
            "%H:%M"
        ),
        service_id="highlights",
        service_name="Mechas",
        duration_minutes=120,
        price_cents=6500,
        price_type="from",
        currency="EUR",
        calendar_booking_id=calendar_booking_id,
    )
    booking_repository.save(
        original_booking
    )

    bootstrap = Bootstrap(
        capability_factories={
            "booking": lambda: BookingCapability(
                booking_service=booking_service,
                business_hours=(
                    booking_configuration.business_hours
                ),
                booking_rules=(
                    booking_configuration.booking_rules
                ),
                services=(
                    booking_configuration.services
                ),
            ),
        },
    )
    application = bootstrap.build_from_instance(
        instance
    )

    session_id = (
        "hairdressing-reschedule-integration"
    )

    application.chat(
        session_id=session_id,
        message="Peluquería",
    )

    phone_response = application.chat(
        session_id=session_id,
        message="Quiero cambiar mi cita",
    )
    assert "teléfono" in phone_response.text.lower()

    dates_response = application.chat(
        session_id=session_id,
        message="600123123",
    )

    available_dates = _DATE_PATTERN.findall(
        dates_response.text
    )
    assert available_dates, dates_response.text

    selected_date = available_dates[0]

    times_response = application.chat(
        session_id=session_id,
        message=selected_date,
    )

    available_times = _TIME_PATTERN.findall(
        times_response.text
    )
    assert available_times

    selected_time = available_times[0]

    confirmation_response = application.chat(
        session_id=session_id,
        message=selected_time,
    )

    assert selected_date in confirmation_response.text
    assert selected_time in confirmation_response.text

    completed_response = application.chat(
        session_id=session_id,
        message="sí",
    )

    assert completed_response.metadata[
        "booking_rescheduled"
    ] is True
    assert "cambiado correctamente" in (
        completed_response.text.lower()
    )

    stored_bookings = (
        booking_repository.find_by_phone(
            "+34600123123"
        )
    )

    assert len(stored_bookings) == 1

    updated_booking = stored_bookings[0]

    assert updated_booking.date == selected_date
    assert updated_booking.time == selected_time
    assert updated_booking.calendar_booking_id == (
        calendar_booking_id
    )

    calendar_events = (
        calendar_provider.list_bookings(
            start=datetime.now()
            - timedelta(days=1),
            end=datetime.now()
            + timedelta(days=365),
        )
    )

    matching_events = [
        event
        for event in calendar_events
        if event["id"] == calendar_booking_id
    ]

    assert len(matching_events) == 1

    updated_event = matching_events[0]

    assert updated_event["start"].strftime(
        "%d/%m/%Y"
    ) == selected_date
    assert updated_event["start"].strftime(
        "%H:%M"
    ) == selected_time
    assert (
        updated_event["end"]
        - updated_event["start"]
    ) == timedelta(
        minutes=120
    )
