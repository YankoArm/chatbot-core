from __future__ import annotations

import pytest

from chatbot.phone import (
    EmptyPhoneNumberError,
    InvalidPhoneNumberError,
    MissingPhoneRegionError,
    PhoneNumberService,
    UnsupportedPhoneRegionError,
)


def test_parse_spanish_national_number_with_default_region():
    service = PhoneNumberService(
        default_region="ES",
    )

    phone = service.parse(
        "666 555 666",
    )

    assert phone.raw == "666 555 666"
    assert phone.region_code == "ES"
    assert phone.country_calling_code == "+34"
    assert phone.national_number == "666555666"
    assert phone.e164 == "+34666555666"
    assert str(phone) == "+34666555666"


def test_parse_spanish_international_number_without_default_region():
    service = PhoneNumberService()

    phone = service.parse(
        "+34 666 555 666",
    )

    assert phone.region_code == "ES"
    assert phone.country_calling_code == "+34"
    assert phone.e164 == "+34666555666"


def test_parse_us_international_number():
    service = PhoneNumberService()

    phone = service.parse(
        "+1 305 555 1234",
    )

    assert phone.region_code == "US"
    assert phone.country_calling_code == "+1"
    assert phone.national_number == "3055551234"
    assert phone.e164 == "+13055551234"


def test_parse_cuban_international_number():
    service = PhoneNumberService()

    phone = service.parse(
        "+53 5 123 4567",
    )

    assert phone.region_code == "CU"
    assert phone.country_calling_code == "+53"
    assert phone.e164 == "+5351234567"


def test_parse_costa_rican_international_number():
    service = PhoneNumberService()

    phone = service.parse(
        "+506 8888 7777",
    )

    assert phone.region_code == "CR"
    assert phone.country_calling_code == "+506"
    assert phone.e164 == "+50688887777"


def test_normalize_returns_e164_value():
    service = PhoneNumberService(
        default_region="ES",
    )

    result = service.normalize(
        "666-555-666",
    )

    assert result == "+34666555666"


def test_explicit_region_overrides_default_region():
    service = PhoneNumberService(
        default_region="ES",
    )

    phone = service.parse(
        "305 555 1234",
        region="US",
    )

    assert phone.region_code == "US"
    assert phone.e164 == "+13055551234"


def test_national_number_requires_region():
    service = PhoneNumberService()

    with pytest.raises(
        MissingPhoneRegionError,
    ):
        service.parse(
            "666555666",
        )


def test_empty_phone_number_is_rejected():
    service = PhoneNumberService(
        default_region="ES",
    )

    with pytest.raises(
        EmptyPhoneNumberError,
    ):
        service.parse(
            "   ",
        )


def test_invalid_spanish_phone_number_is_rejected():
    service = PhoneNumberService(
        default_region="ES",
    )

    with pytest.raises(
        InvalidPhoneNumberError,
    ):
        service.parse(
            "6665556666",
        )


def test_phone_number_with_letters_is_rejected():
    service = PhoneNumberService(
        default_region="ES",
    )

    with pytest.raises(
        InvalidPhoneNumberError,
    ):
        service.parse(
            "666ABC666",
        )


def test_impossible_international_number_is_rejected():
    service = PhoneNumberService()

    with pytest.raises(
        InvalidPhoneNumberError,
    ):
        service.parse(
            "+999123456789",
        )


def test_unsupported_region_is_rejected_when_service_is_created():
    with pytest.raises(
        UnsupportedPhoneRegionError,
    ):
        PhoneNumberService(
            default_region="ZZ",
        )


def test_unsupported_explicit_region_is_rejected():
    service = PhoneNumberService(
        default_region="ES",
    )

    with pytest.raises(
        UnsupportedPhoneRegionError,
    ):
        service.parse(
            "666555666",
            region="ZZ",
        )


@pytest.mark.parametrize(
    (
        "value",
        "region",
        "expected",
    ),
    [
        (
            "666 555 666",
            "ES",
            True,
        ),
        (
            "+34 666 555 666",
            None,
            True,
        ),
        (
            "+1 305 555 1234",
            None,
            True,
        ),
        (
            "+53 5 123 4567",
            None,
            True,
        ),
        (
            "+506 8888 7777",
            None,
            True,
        ),
        (
            "6665556666",
            "ES",
            False,
        ),
        (
            "phone",
            "ES",
            False,
        ),
        (
            "",
            "ES",
            False,
        ),
    ],
)
def test_is_valid(
    value: str,
    region: str | None,
    expected: bool,
):
    service = PhoneNumberService()

    result = service.is_valid(
        value,
        region=region,
    )

    assert result is expected