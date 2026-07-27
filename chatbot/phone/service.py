from __future__ import annotations

import phonenumbers
from phonenumbers import PhoneNumberFormat
from phonenumbers.phonenumberutil import (
    NumberParseException,
)

from chatbot.phone.exceptions import (
    EmptyPhoneNumberError,
    InvalidPhoneNumberError,
    MissingPhoneRegionError,
    UnsupportedPhoneRegionError,
)
from chatbot.phone.models import PhoneNumber


class PhoneNumberService:
    """
    Parse, validate and normalize international phone numbers.

    National phone numbers require either a default region configured
    in the service or an explicit region passed to ``parse``.

    International numbers beginning with ``+`` do not require a
    default region.
    """

    def __init__(
        self,
        default_region: str | None = None,
    ) -> None:
        self._default_region = self._normalize_region(
            default_region
        )

    @property
    def default_region(self) -> str | None:
        """
        Return the configured default region.
        """

        return self._default_region

    def parse(
        self,
        value: str,
        *,
        region: str | None = None,
    ) -> PhoneNumber:
        """
        Parse and validate a phone number.

        Args:
            value:
                Raw phone number entered by the user.
            region:
                Optional ISO 3166-1 alpha-2 region code, such as
                ``ES``, ``US``, ``CU`` or ``CR``.

        Returns:
            A validated and normalized ``PhoneNumber``.

        Raises:
            EmptyPhoneNumberError:
                When the supplied value is empty.
            MissingPhoneRegionError:
                When a national number is supplied without a region.
            UnsupportedPhoneRegionError:
                When the region code is unsupported.
            InvalidPhoneNumberError:
                When the number cannot be parsed or validated.
        """

        raw_value = value.strip()

        if not raw_value:
            raise EmptyPhoneNumberError(
                "Phone number cannot be empty."
            )

        if any(
            character.isalpha()
            for character in raw_value
        ):
            raise InvalidPhoneNumberError(
                "Phone number cannot contain letters."
            )

        selected_region = self._resolve_region(
            raw_value,
            region,
        )

        try:
            parsed_number = phonenumbers.parse(
                raw_value,
                selected_region,
            )
        except NumberParseException as error:
            raise InvalidPhoneNumberError(
                "Phone number could not be parsed."
            ) from error

        if not phonenumbers.is_possible_number(
            parsed_number
        ):
            raise InvalidPhoneNumberError(
                "Phone number has an invalid length or structure."
            )

        if not phonenumbers.is_valid_number(
            parsed_number
        ):
            raise InvalidPhoneNumberError(
                "Phone number is not valid for its region."
            )

        detected_region = (
            phonenumbers.region_code_for_number(
                parsed_number
            )
        )

        return PhoneNumber(
            raw=raw_value,
            region_code=detected_region,
            country_calling_code=(
                f"+{parsed_number.country_code}"
            ),
            national_number=str(
                parsed_number.national_number
            ),
            e164=phonenumbers.format_number(
                parsed_number,
                PhoneNumberFormat.E164,
            ),
            international_format=(
                phonenumbers.format_number(
                    parsed_number,
                    PhoneNumberFormat.INTERNATIONAL,
                )
            ),
            national_format=phonenumbers.format_number(
                parsed_number,
                PhoneNumberFormat.NATIONAL,
            ),
        )

    def normalize(
        self,
        value: str,
        *,
        region: str | None = None,
    ) -> str:
        """
        Return a validated phone number in E.164 format.
        """

        return self.parse(
            value,
            region=region,
        ).e164

    def is_valid(
        self,
        value: str,
        *,
        region: str | None = None,
    ) -> bool:
        """
        Return whether a phone number can be parsed and validated.
        """

        try:
            self.parse(
                value,
                region=region,
            )
        except (
            EmptyPhoneNumberError,
            MissingPhoneRegionError,
            UnsupportedPhoneRegionError,
            InvalidPhoneNumberError,
        ):
            return False

        return True

    def _resolve_region(
        self,
        value: str,
        region: str | None,
    ) -> str | None:
        """
        Resolve the region required to parse the supplied number.
        """

        if value.startswith("+"):
            return None

        selected_region = self._normalize_region(
            region
        )

        if selected_region is None:
            selected_region = self._default_region

        if selected_region is None:
            raise MissingPhoneRegionError(
                "A region is required for a national phone number."
            )

        return selected_region

    @staticmethod
    def _normalize_region(
        region: str | None,
    ) -> str | None:
        """
        Normalize and validate an ISO region code.
        """

        if region is None:
            return None

        normalized_region = region.strip().upper()

        if not normalized_region:
            return None

        if normalized_region not in (
            phonenumbers.SUPPORTED_REGIONS
        ):
            raise UnsupportedPhoneRegionError(
                f"Unsupported phone region: "
                f"{normalized_region}."
            )

        return normalized_region