from __future__ import annotations

from datetime import date, datetime

from chatbot.availability.booking_rules import (
    BookingRules,
)
from chatbot.availability.business_hours import (
    BusinessHours,
)
from chatbot.availability.models import (
    TimeRange,
    TimeSlot,
)
from chatbot.timezone import TimezoneService


class SlotGenerator:
    def __init__(
        self,
        timezone_service: TimezoneService | None = None,
    ) -> None:
        self._timezone_service = timezone_service

    def generate_for_date(
        self,
        value: date,
        *,
        business_hours: BusinessHours,
        rules: BookingRules,
    ) -> tuple[TimeSlot, ...]:
        timezone_service = self._resolve_timezone_service(
            business_hours,
        )

        slots: list[TimeSlot] = []

        for time_range in business_hours.hours_for_date(
            value,
        ):
            slots.extend(
                self._generate_for_range(
                    value,
                    time_range=time_range,
                    rules=rules,
                    timezone_service=timezone_service,
                )
            )

        return tuple(slots)

    def generate_between(
        self,
        start_date: date,
        end_date: date,
        *,
        business_hours: BusinessHours,
        rules: BookingRules,
    ) -> tuple[TimeSlot, ...]:
        if end_date < start_date:
            raise ValueError(
                "End date cannot be earlier than "
                "start date."
            )

        slots: list[TimeSlot] = []
        current_date = start_date

        while current_date <= end_date:
            slots.extend(
                self.generate_for_date(
                    current_date,
                    business_hours=business_hours,
                    rules=rules,
                )
            )

            current_date = date.fromordinal(
                current_date.toordinal() + 1
            )

        return tuple(slots)

    def _generate_for_range(
        self,
        value: date,
        *,
        time_range: TimeRange,
        rules: BookingRules,
        timezone_service: TimezoneService,
    ) -> list[TimeSlot]:
        range_start = timezone_service.localize(
            datetime.combine(
                value,
                time_range.start,
            )
        )

        range_end = timezone_service.localize(
            datetime.combine(
                value,
                time_range.end,
            )
        )

        slots: list[TimeSlot] = []
        appointment_start = range_start

        while (
            appointment_start
            + rules.appointment_duration
            <= range_end
        ):
            appointment_end = (
                appointment_start
                + rules.appointment_duration
            )

            occupied_start = (
                appointment_start
                - rules.buffer_before
            )

            occupied_end = (
                appointment_end
                + rules.buffer_after
            )

            if (
                occupied_start >= range_start
                and occupied_end <= range_end
            ):
                slots.append(
                    TimeSlot(
                        start=appointment_start,
                        end=appointment_end,
                        occupied_start=occupied_start,
                        occupied_end=occupied_end,
                    )
                )

            appointment_start += rules.slot_interval

        return slots

    def _resolve_timezone_service(
        self,
        business_hours: BusinessHours,
    ) -> TimezoneService:
        if self._timezone_service is None:
            return TimezoneService(
                default_timezone=(
                    business_hours.timezone_name
                )
            )

        if (
            self._timezone_service.default_timezone
            != business_hours.timezone_name
        ):
            return TimezoneService(
                default_timezone=(
                    business_hours.timezone_name
                )
            )

        return self._timezone_service