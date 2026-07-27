from __future__ import annotations

from collections.abc import Iterable
from datetime import (
    date,
    datetime,
    timedelta,
    timezone,
)

from chatbot.availability.booking_rules import (
    BookingRules,
)
from chatbot.availability.business_hours import (
    BusinessHours,
)
from chatbot.availability.exceptions import (
    InvalidAvailabilityWindowError,
)
from chatbot.availability.models import (
    BusyPeriod,
    TimeSlot,
)
from chatbot.availability.slot_generator import (
    SlotGenerator,
)
from chatbot.timezone import TimezoneService


class AvailabilityService:
    def __init__(
        self,
        *,
        slot_generator: SlotGenerator | None = None,
        timezone_service: TimezoneService | None = None,
    ) -> None:
        self._timezone_service = (
            timezone_service
            or TimezoneService()
        )

        self._slot_generator = (
            slot_generator
            or SlotGenerator()
        )

    def get_available_slots_for_date(
        self,
        value: date,
        *,
        business_hours: BusinessHours,
        rules: BookingRules,
        busy_periods: Iterable[BusyPeriod] = (),
        now: datetime | None = None,
    ) -> tuple[TimeSlot, ...]:
        theoretical_slots = (
            self._slot_generator.generate_for_date(
                value,
                business_hours=business_hours,
                rules=rules,
            )
        )

        return self.filter_available_slots(
            theoretical_slots,
            rules=rules,
            busy_periods=busy_periods,
            now=now,
        )

    def get_available_slots_between(
        self,
        start_date: date,
        end_date: date,
        *,
        business_hours: BusinessHours,
        rules: BookingRules,
        busy_periods: Iterable[BusyPeriod] = (),
        now: datetime | None = None,
    ) -> tuple[TimeSlot, ...]:
        if end_date < start_date:
            raise InvalidAvailabilityWindowError(
                "End date cannot be earlier than "
                "start date."
            )

        theoretical_slots = (
            self._slot_generator.generate_between(
                start_date,
                end_date,
                business_hours=business_hours,
                rules=rules,
            )
        )

        return self.filter_available_slots(
            theoretical_slots,
            rules=rules,
            busy_periods=busy_periods,
            now=now,
        )

    def filter_available_slots(
        self,
        slots: Iterable[TimeSlot],
        *,
        rules: BookingRules,
        busy_periods: Iterable[BusyPeriod] = (),
        now: datetime | None = None,
    ) -> tuple[TimeSlot, ...]:
        normalized_now = self._normalize_now(
            now,
        )

        normalized_busy_periods = tuple(
            busy_periods
        )

        available_slots: list[TimeSlot] = []

        for slot in slots:
            if not self._passes_booking_window(
                slot,
                rules=rules,
                now=normalized_now,
            ):
                continue

            if self._overlaps_busy_period(
                slot,
                busy_periods=normalized_busy_periods,
            ):
                continue

            available_slots.append(slot)

        return tuple(available_slots)

    def is_slot_available(
        self,
        slot: TimeSlot,
        *,
        rules: BookingRules,
        busy_periods: Iterable[BusyPeriod] = (),
        now: datetime | None = None,
    ) -> bool:
        available = self.filter_available_slots(
            (slot,),
            rules=rules,
            busy_periods=busy_periods,
            now=now,
        )

        return bool(available)

    def find_next_available_slot(
        self,
        start_date: date,
        end_date: date,
        *,
        business_hours: BusinessHours,
        rules: BookingRules,
        busy_periods: Iterable[BusyPeriod] = (),
        now: datetime | None = None,
    ) -> TimeSlot | None:
        slots = self.get_available_slots_between(
            start_date,
            end_date,
            business_hours=business_hours,
            rules=rules,
            busy_periods=busy_periods,
            now=now,
        )

        if not slots:
            return None

        return slots[0]

    @staticmethod
    def _overlaps_busy_period(
        slot: TimeSlot,
        *,
        busy_periods: tuple[BusyPeriod, ...],
    ) -> bool:
        return any(
            busy_period.overlaps_slot(slot)
            for busy_period in busy_periods
        )

    @staticmethod
    def _passes_booking_window(
        slot: TimeSlot,
        *,
        rules: BookingRules,
        now: datetime,
    ) -> bool:
        slot_start_utc = slot.start.astimezone(
            timezone.utc,
        )

        now_utc = now.astimezone(
            timezone.utc,
        )

        if (
            not rules.allow_past_bookings
            and slot_start_utc < now_utc
        ):
            return False

        if rules.minimum_notice > timedelta(0):
            earliest_booking = (
                now_utc
                + rules.minimum_notice
            )

            if slot_start_utc < earliest_booking:
                return False

        if rules.maximum_advance is not None:
            latest_booking = (
                now_utc
                + rules.maximum_advance
            )

            if slot_start_utc > latest_booking:
                return False

        return True

    def _normalize_now(
        self,
        value: datetime | None,
    ) -> datetime:
        if value is None:
            return datetime.now(
                timezone.utc,
            )

        if (
            value.tzinfo is None
            or value.utcoffset() is None
        ):
            raise ValueError(
                "'now' must be timezone-aware."
            )

        return value