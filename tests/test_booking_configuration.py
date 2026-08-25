from __future__ import annotations

from datetime import time, timedelta

import pytest

from chatbot.availability import Weekday
from chatbot.booking import build_booking_configuration
from chatbot.instances import Instance


def build_instance(
    *,
    booking_settings: dict,
) -> Instance:
    return Instance(
        id="test-client",
        name="Test Client",
        settings={
            "booking": booking_settings,
        },
    )


def valid_booking_settings() -> dict:
    return {
        "enabled": True,
        "timezone": "Europe/Madrid",
        "business_hours": {
            "monday": [
                ["10:00", "14:00"],
                ["16:00", "20:00"],
            ],
            "tuesday": [],
            "wednesday": [],
            "thursday": [],
            "friday": [],
            "saturday": [],
            "sunday": [],
        },
        "rules": {
            "appointment_duration_minutes": 60,
            "slot_interval_minutes": 30,
            "buffer_before_minutes": 10,
            "buffer_after_minutes": 15,
            "minimum_notice_hours": 2,
            "maximum_advance_days": 30,
            "allow_past_bookings": False,
        },
    }


def test_build_booking_configuration() -> None:
    instance = build_instance(
        booking_settings=valid_booking_settings(),
    )

    configuration = build_booking_configuration(
        instance
    )

    assert (
        configuration.business_hours.timezone_name
        == "Europe/Madrid"
    )

    monday_hours = (
        configuration.business_hours.hours_for_weekday(
            Weekday.MONDAY
        )
    )

    assert len(monday_hours) == 2

    assert monday_hours[0].start == time(10, 0)
    assert monday_hours[0].end == time(14, 0)

    assert monday_hours[1].start == time(16, 0)
    assert monday_hours[1].end == time(20, 0)

    rules = configuration.booking_rules

    assert (
        rules.appointment_duration
        == timedelta(minutes=60)
    )
    assert (
        rules.slot_interval
        == timedelta(minutes=30)
    )
    assert (
        rules.buffer_before
        == timedelta(minutes=10)
    )
    assert (
        rules.buffer_after
        == timedelta(minutes=15)
    )
    assert (
        rules.minimum_notice
        == timedelta(hours=2)
    )
    assert (
        rules.maximum_advance
        == timedelta(days=30)
    )
    assert rules.allow_past_bookings is False


def test_booking_configuration_rejects_invalid_timezone() -> None:
    settings = valid_booking_settings()

    settings["timezone"] = "Invalid/Timezone"

    instance = build_instance(
        booking_settings=settings,
    )

    with pytest.raises(
        ValueError,
        match="Booking timezone is invalid",
    ):
        build_booking_configuration(
            instance
        )


def test_booking_configuration_rejects_invalid_time_format() -> None:
    settings = valid_booking_settings()

    settings["business_hours"]["monday"] = [
        ["10", "14:00"],
    ]

    instance = build_instance(
        booking_settings=settings,
    )

    with pytest.raises(
        ValueError,
        match="must use HH:MM format",
    ):
        build_booking_configuration(
            instance
        )


def test_booking_configuration_rejects_invalid_duration() -> None:
    settings = valid_booking_settings()

    settings["rules"][
        "appointment_duration_minutes"
    ] = 0

    instance = build_instance(
        booking_settings=settings,
    )

    with pytest.raises(
        ValueError,
        match=(
            "appointment_duration_minutes.*"
            "must be a positive integer"
        ),
    ):
        build_booking_configuration(
            instance
        )

def test_booking_configuration_has_empty_services_by_default() -> None:
    instance = build_instance(
        booking_settings=valid_booking_settings(),
    )

    configuration = build_booking_configuration(
        instance
    )

    assert configuration.services == ()


def test_booking_configuration_builds_hairdressing_services() -> None:
    from chatbot.business_templates import (
        create_hairdressing_template,
    )
    from chatbot.clients import (
        create_hairdressing_demo_definition,
    )
    from chatbot.instances import InstanceResolver

    instance = InstanceResolver().resolve(
        template=create_hairdressing_template(),
        definition=create_hairdressing_demo_definition(),
    )

    configuration = build_booking_configuration(
        instance
    )

    assert len(configuration.services) == 7

    highlights = next(
        service
        for service in configuration.services
        if service.id == "highlights"
    )

    assert highlights.name_es == "Mechas"
    assert highlights.name_en == "Highlights"
    assert highlights.duration_minutes == 120
    assert highlights.price_type == "from"
    assert highlights.price_cents == 6500
    assert highlights.currency == "EUR"