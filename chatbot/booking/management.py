from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from chatbot.booking.models import Booking


class BookingManagementAction(str, Enum):
    """
    Operations that can be performed on an existing booking.
    """

    CANCEL = "cancel"
    RESCHEDULE = "reschedule"


class BookingManagementStep(str, Enum):
    """
    Steps required to manage an existing booking.
    """

    PHONE = "phone"
    SELECTION = "selection"
    DATE = "date"
    TIME = "time"
    CONFIRMATION = "confirmation"
    COMPLETE = "complete"


@dataclass(slots=True)
class BookingManagementState:
    """
    Runtime state for cancelling or rescheduling an existing booking.
    """

    action: BookingManagementAction

    phone: str | None = None
    matching_bookings: tuple[Booking, ...] = ()
    selected_booking: Booking | None = None

    new_date: str | None = None
    new_time: str | None = None
    available_dates: tuple[str, ...] = ()
    available_times: tuple[str, ...] = ()

    completed: bool = False

    @property
    def next_step(self) -> BookingManagementStep:
        """
        Return the next required management step.
        """

        if self.completed:
            return BookingManagementStep.COMPLETE

        if not self.phone:
            return BookingManagementStep.PHONE

        if self.selected_booking is None:
            return BookingManagementStep.SELECTION

        if (
            self.action
            is BookingManagementAction.RESCHEDULE
        ):
            if not self.new_date:
                return BookingManagementStep.DATE

            if not self.new_time:
                return BookingManagementStep.TIME

        return BookingManagementStep.CONFIRMATION

    @property
    def is_complete(self) -> bool:
        """
        Return whether the requested operation has completed.
        """

        return self.completed

    def complete(self) -> None:
        """
        Mark management of the selected booking as complete.
        """

        if self.selected_booking is None:
            raise ValueError(
                "Cannot complete booking management "
                "without a selected booking."
            )

        if (
            self.action
            is BookingManagementAction.RESCHEDULE
            and (
                not self.new_date
                or not self.new_time
            )
        ):
            raise ValueError(
                "Cannot complete rescheduling without "
                "a new date and time."
            )

        self.completed = True

    def reset(self) -> None:
        """
        Clear collected data while preserving the requested action.
        """

        self.phone = None
        self.matching_bookings = ()
        self.selected_booking = None

        self.new_date = None
        self.new_time = None
        self.available_dates = ()
        self.available_times = ()

        self.completed = False