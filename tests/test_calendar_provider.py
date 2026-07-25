from datetime import datetime

import pytest

from chatbot.calendar import CalendarProvider


def test_calendar_provider_cannot_be_instantiated():
    with pytest.raises(TypeError):
        CalendarProvider()


def test_calendar_provider_defines_expected_contract():
    expected_methods = {
        "is_available",
        "create_booking",
        "cancel_booking",
        "list_bookings",
    }

    assert expected_methods.issubset(
        CalendarProvider.__abstractmethods__
    )


def test_calendar_provider_method_signatures_exist():
    assert callable(
        getattr(
            CalendarProvider,
            "is_available",
        )
    )

    assert callable(
        getattr(
            CalendarProvider,
            "create_booking",
        )
    )

    assert callable(
        getattr(
            CalendarProvider,
            "cancel_booking",
        )
    )

    assert callable(
        getattr(
            CalendarProvider,
            "list_bookings",
        )
    )