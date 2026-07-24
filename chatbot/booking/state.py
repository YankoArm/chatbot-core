from __future__ import annotations

from dataclasses import dataclass
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


@dataclass(slots=True)
class BookingState:
    """
    Runtime state of an ongoing booking conversation.
    """

    name: str | None = None
    phone: str | None = None
    date: str | None = None
    time: str | None = None

    @property
    def is_complete(self) -> bool:
        return all(
            (
                self.name,
                self.phone,
                self.date,
                self.time,
            )
        )

    @property
    def next_step(self) -> BookingStep:
        if not self.name:
            return BookingStep.NAME

        if not self.phone:
            return BookingStep.PHONE

        if not self.date:
            return BookingStep.DATE

        if not self.time:
            return BookingStep.TIME

        return BookingStep.COMPLETE

    def reset(self) -> None:
        self.name = None
        self.phone = None
        self.date = None
        self.time = None