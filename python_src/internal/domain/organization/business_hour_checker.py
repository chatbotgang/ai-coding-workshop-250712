"""Business hour checker for auto-reply validation."""

from datetime import datetime, time
from typing import Optional

from pydantic import BaseModel, Field

from internal.domain.organization.business_hour import BusinessHour


class BusinessHourChecker(BaseModel):
    """Business hour checker for validating time-based triggers."""

    organization_id: int = Field(..., description="Organization ID")
    timezone: str = Field(..., description="Organization timezone")
    business_hours: list[BusinessHour] = Field(..., description="Business hours configuration")

    class Config:
        """Pydantic configuration."""

        arbitrary_types_allowed = True

    def is_in_business_hours(self, check_time: datetime) -> bool:
        """Check if the given time is within business hours.

        Args:
            check_time: The datetime to check (should be in organization timezone)

        Returns:
            True if the time is within business hours, False otherwise
        """
        # Convert to weekday format used by BusinessHour (1=Monday, 7=Sunday)
        weekday = check_time.isoweekday()  # 1=Monday, 7=Sunday
        current_time = check_time.time()

        for business_hour in self.business_hours:
            if not business_hour.is_day_active(weekday):
                continue

            # Normalize time precision to match legacy behavior
            start_time = business_hour.start_time.replace(second=time.min.second, microsecond=time.min.microsecond)
            end_time = business_hour.end_time.replace(second=time.max.second, microsecond=time.max.microsecond)

            # Check if current time is within business hours
            if start_time <= current_time < end_time:
                return True

        return False

    def is_in_non_business_hours(self, check_time: datetime) -> bool:
        """Check if the given time is outside business hours."""
        return not self.is_in_business_hours(check_time)
