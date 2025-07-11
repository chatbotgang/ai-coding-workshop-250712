"""Business Hour domain models."""

from datetime import time
from enum import IntEnum

from pydantic import BaseModel


class WeekDay(IntEnum):
    """Week day enumeration (Monday = 0, Sunday = 6)."""

    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


class BusinessHour(BaseModel):
    """Business hour configuration for an organization."""

    id: int
    organization_id: int
    day_of_week: WeekDay
    start_time: time
    end_time: time
    is_active: bool = True

    def is_day_active(self, weekday: int) -> bool:
        """Check if business hours are active for the given weekday.

        Args:
            weekday: Weekday number (Monday = 0, Sunday = 6)

        Returns:
            True if business hours are active for this day, False otherwise
        """
        return self.is_active and self.day_of_week == weekday

    def is_time_within_hours(self, check_time: time) -> bool:
        """Check if the given time is within business hours.

        Args:
            check_time: Time to check

        Returns:
            True if time is within business hours, False otherwise
        """
        return self.start_time <= check_time <= self.end_time

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
