from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class TimezoneDateTime:
    timezone_name: str
    local_datetime: datetime
    utc_datetime: datetime

    def __post_init__(self) -> None:
        if self.local_datetime.tzinfo is None:
            raise ValueError(
                "local_datetime must be timezone-aware."
            )

        if self.utc_datetime.tzinfo is None:
            raise ValueError(
                "utc_datetime must be timezone-aware."
            )