from __future__ import annotations

from datetime import datetime, timezone

import pytest

from chatbot.timezone import (
    AwareDatetimeError,
    EmptyTimezoneError,
    InvalidTimezoneError,
    NaiveDatetimeError,
    TimezoneDateTime,
    TimezoneService,
)


def test_service_uses_utc_by_default() -> None:
    service = TimezoneService()

    assert service.default_timezone == "UTC"


def test_service_accepts_valid_default_timezone() -> None:
    service = TimezoneService(
        default_timezone="Europe/Madrid",
    )

    assert service.default_timezone == "Europe/Madrid"


def test_service_rejects_empty_default_timezone() -> None:
    with pytest.raises(
        EmptyTimezoneError,
    ):
        TimezoneService(
            default_timezone="   ",
        )


def test_service_rejects_invalid_default_timezone() -> None:
    with pytest.raises(
        InvalidTimezoneError,
    ):
        TimezoneService(
            default_timezone="Europe/Invalid",
        )


def test_get_zone_uses_default_timezone() -> None:
    service = TimezoneService(
        default_timezone="Europe/Madrid",
    )

    zone = service.get_zone()

    assert zone.key == "Europe/Madrid"


def test_get_zone_accepts_explicit_timezone() -> None:
    service = TimezoneService(
        default_timezone="UTC",
    )

    zone = service.get_zone(
        "America/New_York",
    )

    assert zone.key == "America/New_York"


@pytest.mark.parametrize(
    (
        "timezone_name",
        "expected",
    ),
    [
        (
            "UTC",
            True,
        ),
        (
            "Europe/Madrid",
            True,
        ),
        (
            "America/New_York",
            True,
        ),
        (
            "Asia/Tokyo",
            True,
        ),
        (
            "Europe/Invalid",
            False,
        ),
        (
            "",
            False,
        ),
        (
            "   ",
            False,
        ),
    ],
)
def test_is_valid(
    timezone_name: str,
    expected: bool,
) -> None:
    service = TimezoneService()

    result = service.is_valid(
        timezone_name,
    )

    assert result is expected


def test_localize_adds_default_timezone() -> None:
    service = TimezoneService(
        default_timezone="Europe/Madrid",
    )

    naive = datetime(
        2026,
        7,
        28,
        17,
        0,
    )

    localized = service.localize(
        naive,
    )

    assert localized.tzinfo is not None
    assert localized.tzinfo.key == "Europe/Madrid"
    assert localized.hour == 17


def test_localize_accepts_explicit_timezone() -> None:
    service = TimezoneService(
        default_timezone="UTC",
    )

    naive = datetime(
        2026,
        7,
        28,
        17,
        0,
    )

    localized = service.localize(
        naive,
        timezone_name="Asia/Tokyo",
    )

    assert localized.tzinfo is not None
    assert localized.tzinfo.key == "Asia/Tokyo"
    assert localized.hour == 17


def test_localize_rejects_aware_datetime() -> None:
    service = TimezoneService()

    aware = datetime(
        2026,
        7,
        28,
        17,
        0,
        tzinfo=timezone.utc,
    )

    with pytest.raises(
        AwareDatetimeError,
    ):
        service.localize(
            aware,
        )


def test_to_utc_localizes_naive_datetime() -> None:
    service = TimezoneService(
        default_timezone="Europe/Madrid",
    )

    naive = datetime(
        2026,
        7,
        28,
        17,
        0,
    )

    result = service.to_utc(
        naive,
    )

    assert result == datetime(
        2026,
        7,
        28,
        15,
        0,
        tzinfo=timezone.utc,
    )


def test_to_utc_converts_aware_datetime() -> None:
    service = TimezoneService(
        default_timezone="Europe/Madrid",
    )

    aware = service.localize(
        datetime(
            2026,
            7,
            28,
            17,
            0,
        )
    )

    result = service.to_utc(
        aware,
    )

    assert result == datetime(
        2026,
        7,
        28,
        15,
        0,
        tzinfo=timezone.utc,
    )


def test_from_utc_converts_to_default_timezone() -> None:
    service = TimezoneService(
        default_timezone="Europe/Madrid",
    )

    utc_value = datetime(
        2026,
        7,
        28,
        15,
        0,
        tzinfo=timezone.utc,
    )

    result = service.from_utc(
        utc_value,
    )

    assert result.tzinfo is not None
    assert result.tzinfo.key == "Europe/Madrid"
    assert result.hour == 17


def test_from_utc_accepts_explicit_timezone() -> None:
    service = TimezoneService(
        default_timezone="UTC",
    )

    utc_value = datetime(
        2026,
        7,
        28,
        15,
        0,
        tzinfo=timezone.utc,
    )

    result = service.from_utc(
        utc_value,
        timezone_name="Asia/Tokyo",
    )

    assert result.tzinfo is not None
    assert result.tzinfo.key == "Asia/Tokyo"
    assert result.hour == 0
    assert result.day == 29


def test_from_utc_rejects_naive_datetime() -> None:
    service = TimezoneService()

    naive = datetime(
        2026,
        7,
        28,
        15,
        0,
    )

    with pytest.raises(
        NaiveDatetimeError,
    ):
        service.from_utc(
            naive,
        )


def test_convert_changes_timezone_preserving_instant() -> None:
    service = TimezoneService(
        default_timezone="Europe/Madrid",
    )

    madrid_value = service.localize(
        datetime(
            2026,
            7,
            28,
            17,
            0,
        )
    )

    result = service.convert(
        madrid_value,
        target_timezone="America/New_York",
    )

    assert result.tzinfo is not None
    assert result.tzinfo.key == "America/New_York"
    assert result.hour == 11

    assert result.astimezone(
        timezone.utc,
    ) == datetime(
        2026,
        7,
        28,
        15,
        0,
        tzinfo=timezone.utc,
    )


def test_convert_rejects_naive_datetime() -> None:
    service = TimezoneService()

    naive = datetime(
        2026,
        7,
        28,
        17,
        0,
    )

    with pytest.raises(
        NaiveDatetimeError,
    ):
        service.convert(
            naive,
            target_timezone="Europe/Madrid",
        )


def test_build_from_naive_datetime() -> None:
    service = TimezoneService(
        default_timezone="Europe/Madrid",
    )

    result = service.build(
        datetime(
            2026,
            7,
            28,
            17,
            0,
        )
    )

    assert isinstance(
        result,
        TimezoneDateTime,
    )

    assert result.timezone_name == "Europe/Madrid"
    assert result.local_datetime.tzinfo is not None
    assert result.local_datetime.tzinfo.key == "Europe/Madrid"

    assert result.utc_datetime == datetime(
        2026,
        7,
        28,
        15,
        0,
        tzinfo=timezone.utc,
    )


def test_build_converts_aware_datetime_to_requested_timezone() -> None:
    service = TimezoneService(
        default_timezone="UTC",
    )

    utc_value = datetime(
        2026,
        7,
        28,
        15,
        0,
        tzinfo=timezone.utc,
    )

    result = service.build(
        utc_value,
        timezone_name="Europe/Madrid",
    )

    assert result.timezone_name == "Europe/Madrid"
    assert result.local_datetime.hour == 17
    assert result.utc_datetime == utc_value


def test_now_returns_aware_datetime() -> None:
    service = TimezoneService(
        default_timezone="Europe/Madrid",
    )

    result = service.now()

    assert result.tzinfo is not None
    assert result.tzinfo.key == "Europe/Madrid"


def test_timezone_datetime_rejects_naive_local_datetime() -> None:
    with pytest.raises(
        ValueError,
    ):
        TimezoneDateTime(
            timezone_name="Europe/Madrid",
            local_datetime=datetime(
                2026,
                7,
                28,
                17,
                0,
            ),
            utc_datetime=datetime(
                2026,
                7,
                28,
                15,
                0,
                tzinfo=timezone.utc,
            ),
        )


def test_timezone_datetime_rejects_naive_utc_datetime() -> None:
    with pytest.raises(
        ValueError,
    ):
        TimezoneDateTime(
            timezone_name="Europe/Madrid",
            local_datetime=datetime(
                2026,
                7,
                28,
                17,
                0,
                tzinfo=timezone.utc,
            ),
            utc_datetime=datetime(
                2026,
                7,
                28,
                15,
                0,
            ),
        )