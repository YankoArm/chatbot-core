from __future__ import annotations


class TimezoneError(ValueError):
    """Base exception for timezone operations."""


class EmptyTimezoneError(TimezoneError):
    """Raised when a timezone name is empty."""


class InvalidTimezoneError(TimezoneError):
    """Raised when an IANA timezone name is invalid."""


class NaiveDatetimeError(TimezoneError):
    """Raised when an aware datetime is required."""


class AwareDatetimeError(TimezoneError):
    """Raised when a naive datetime is required."""