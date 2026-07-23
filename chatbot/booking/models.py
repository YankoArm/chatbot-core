from __future__ import annotations

from enum import Enum


class BookingStep(str, Enum):
    """
    Steps required to complete a booking request.
    """

    NAME = "name"
    PHONE = "phone"
    DATE = "date"
    TIME = "time"
    COMPLETE = "complete"