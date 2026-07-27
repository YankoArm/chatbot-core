from __future__ import annotations


class AvailabilityError(ValueError):
    """Base exception for availability operations."""


class BusinessHoursError(AvailabilityError):
    """Base exception for business-hours configuration."""


class InvalidTimeRangeError(BusinessHoursError):
    """Raised when a business-hours interval is invalid."""


class OverlappingTimeRangeError(BusinessHoursError):
    """Raised when two business-hours intervals overlap."""


class BookingRulesError(AvailabilityError):
    """Base exception for booking-rule configuration."""


class InvalidDurationError(BookingRulesError):
    """Raised when an appointment duration is invalid."""


class InvalidBufferError(BookingRulesError):
    """Raised when a booking buffer is invalid."""


class InvalidBookingNoticeError(BookingRulesError):
    """Raised when minimum booking notice is invalid."""


class InvalidBookingWindowError(BookingRulesError):
    """Raised when the maximum booking window is invalid."""


class InvalidSlotIntervalError(BookingRulesError):
    """Raised when the slot interval is invalid."""

class SlotGenerationError(AvailabilityError):
    """Base exception for slot generation."""


class TimezoneMismatchError(SlotGenerationError):
    """Raised when incompatible timezones are used."""

class AvailabilityServiceError(AvailabilityError):
    """Base exception for availability-service operations."""


class InvalidAvailabilityWindowError(
    AvailabilityServiceError
):
    """Raised when an availability window is invalid."""