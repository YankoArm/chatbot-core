from __future__ import annotations

from dataclasses import dataclass


@dataclass(
    frozen=True,
    slots=True,
)
class PhoneNumber:
    """
    Validated and normalized international phone number.

    The canonical value stored by FlowForge is the E.164
    representation.
    """

    raw: str
    region_code: str | None
    country_calling_code: str
    national_number: str
    e164: str
    international_format: str
    national_format: str

    def __str__(self) -> str:
        """
        Return the canonical E.164 representation.
        """

        return self.e164