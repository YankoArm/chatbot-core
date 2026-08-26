from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class BookingStep(str, Enum):
    """
    Steps required to complete a booking request.
    """

    SERVICE = "service"
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

    Service selection is optional so generic appointment businesses
    can preserve the original name-first booking flow.
    """

    requires_service_selection: bool = False

    service_id: str | None = None
    service_name: str | None = None
    service_duration_minutes: int | None = None
    service_price_cents: int | None = None
    service_price_type: str | None = None
    service_currency: str | None = None

    name: str | None = None
    phone: str | None = None
    date: str | None = None
    time: str | None = None

    available_times: tuple[str, ...] = ()
    available_times_page: int = 0
    available_dates: tuple[str, ...] = ()

    confirmed: bool = False
    notes: str | None = None
    booking_id: str | None = None

    @property
    def has_required_data(self) -> bool:
        """
        Return whether all mandatory booking information has been collected.
        """

        if (
            self.requires_service_selection
            and not self.service_id
        ):
            return False

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

        if (
            self.requires_service_selection
            and not self.service_id
        ):
            return BookingStep.SERVICE

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

        self.service_id = None
        self.service_name = None
        self.service_duration_minutes = None
        self.service_price_cents = None
        self.service_price_type = None
        self.service_currency = None

        self.name = None
        self.phone = None
        self.date = None
        self.time = None

        self.available_times = ()
        self.available_times_page = 0
        self.available_dates = ()

        self.confirmed = False
        self.notes = None
        self.booking_id = None