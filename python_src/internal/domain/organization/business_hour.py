"""Business Hour domain models."""

from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime, time
from enum import IntEnum, StrEnum
from typing import Sequence

from pydantic import BaseModel, Field
import pytz
# from internal.domain.organization import BusinessHour # This causes circular import

# from internal.domain.auto_reply.auto_reply import AutoReply # This causes circular import


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
    weekday: int  # Monday=1, Sunday=7
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
        return self.is_active and self.weekday == weekday

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
