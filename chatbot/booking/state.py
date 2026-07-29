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
    CONFIRMATION = "confirmation"
    COMPLETE = "complete"


@dataclass(slots=True)
class BookingState:
    """
    Runtime state of an ongoing booking conversation.

    The state contains both the information collected from the user,
    the available times offered during the conversation,
    and the identifiers generated when the booking is confirmed.
    """

    name: str | None = None
    phone: str | None = None
    date: str | None = None
    time: str | None = None

    available_times: tuple[str, ...] = ()
    available_dates: tuple[str, ...] = ()

    confirmed: bool = False
    notes: str | None = None
    booking_id: str | None = None

    @property
    def has_required_data(self) -> bool:
        """
        Return whether all mandatory booking information has been collected.
        """

        return all(
            (
                self.name,
                self.phone,
                self.date,
                self.time,
            )
        )

    @property
    def is_complete(self) -> bool:
        """
        Return whether the booking data is complete and confirmed.
        """

        return self.has_required_data and self.confirmed

    @property
    def next_step(self) -> BookingStep:
        """
        Return the next step required by the booking flow.
        """

        if not self.name:
            return BookingStep.NAME

        if not self.phone:
            return BookingStep.PHONE

        if not self.date:
            return BookingStep.DATE

        if not self.time:
            return BookingStep.TIME

        if not self.confirmed:
            return BookingStep.CONFIRMATION

        return BookingStep.COMPLETE

    def confirm(
        self,
        booking_id: str | None = None,
    ) -> None:
        """
        Mark the booking as confirmed.

        The optional booking identifier can contain an external reference,
        such as a Google Calendar event ID.
        """

        if not self.has_required_data:
            raise ValueError(
                "Cannot confirm a booking with incomplete required data."
            )

        self.confirmed = True
        self.booking_id = booking_id

    def reset(self) -> None:
        """
        Restore the booking state to its initial values.
        """

        self.name = None
        self.phone = None
        self.date = None
        self.time = None
        self.available_times = ()
        self.confirmed = False
        self.notes = None
        self.booking_id = None