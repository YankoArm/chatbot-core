from __future__ import annotations


class PhoneNumberError(ValueError):
    """
    Base exception for phone-number processing errors.
    """


class EmptyPhoneNumberError(PhoneNumberError):
    """
    Raised when an empty phone number is provided.
    """


class MissingPhoneRegionError(PhoneNumberError):
    """
    Raised when a national number is provided without a region.
    """


class UnsupportedPhoneRegionError(PhoneNumberError):
    """
    Raised when the supplied region code is not supported.
    """


class InvalidPhoneNumberError(PhoneNumberError):
    """
    Raised when a phone number cannot be parsed or is not valid.
    """