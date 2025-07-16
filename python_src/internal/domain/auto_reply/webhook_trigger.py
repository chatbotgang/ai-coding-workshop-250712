"""Webhook Trigger domain models."""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import IntEnum, StrEnum
from zoneinfo import ZoneInfo

from pydantic import BaseModel


class WebhookTriggerEventType(IntEnum):
    """Webhook trigger event type enumeration."""

    MESSAGE = 1
    POSTBACK = 2
    FOLLOW = 3
    BEACON = 4
    TIME = 100
    MESSAGE_EDITOR = 101
    POSTBACK_EDITOR = 102


class WebhookTriggerScheduleType(StrEnum):
    """Webhook trigger schedule type enumeration."""

    DAILY = "daily"
    BUSINESS_HOUR = "business_hour"
    NON_BUSINESS_HOUR = "non_business_hour"
    MONTHLY = "monthly"
    DATE_RANGE = "date_range"


class WebhookTriggerSchedule(BaseModel, ABC):
    """Abstract base class for webhook trigger schedule."""

    @abstractmethod
    def get_schedule_type(self) -> WebhookTriggerScheduleType:
        """Get the schedule type."""
        pass

    @abstractmethod
    def get_schedule_settings(self) -> dict[str, object] | None:
        """Get the schedule settings."""
        pass

    @abstractmethod
    def is_active(self, event_time: datetime, organization_timezone: str = "Asia/Taipei") -> bool:
        """Check if the schedule is active at the given time.

        Args:
            event_time: The event time to check (should be timezone-aware)
            organization_timezone: Organization's timezone (e.g., "Asia/Taipei")

        Returns:
            True if the schedule is active, False otherwise
        """
        pass


class DailySchedule(WebhookTriggerSchedule):
    """Daily trigger schedule."""

    start_time: str
    end_time: str

    def get_schedule_type(self) -> WebhookTriggerScheduleType:
        """Get the schedule type."""
        return WebhookTriggerScheduleType.DAILY

    def get_schedule_settings(self) -> dict[str, object]:
        """Get the schedule settings."""
        return {"start_time": self.start_time, "end_time": self.end_time}

    def is_active(self, event_time: datetime, organization_timezone: str = "Asia/Taipei") -> bool:
        """Check if the daily schedule is active at the given time.

        Args:
            event_time: The event time to check (timezone-aware)
            organization_timezone: Organization's timezone for time conversion

        Returns:
            True if the daily schedule is active, False otherwise
        """
        from datetime import time

        # Convert event time to organization timezone
        if event_time.tzinfo is None:
            # If naive datetime, assume UTC
            event_time = event_time.replace(tzinfo=ZoneInfo("UTC"))

        # Convert to organization timezone
        org_time = event_time.astimezone(ZoneInfo(organization_timezone))

        # Parse time strings to time objects
        start_time = time.fromisoformat(self.start_time)
        end_time = time.fromisoformat(self.end_time)
        event_time_only = org_time.time()

        # Handle midnight crossing: start_time > end_time
        if start_time > end_time:
            # Range crosses midnight (e.g., 22:00 to 06:00)
            return event_time_only >= start_time or event_time_only < end_time
        else:
            # Normal range (e.g., 09:00 to 17:00)
            return start_time <= event_time_only < end_time


class MonthlySchedule(WebhookTriggerSchedule):
    """Monthly trigger schedule."""

    day: int
    start_time: str
    end_time: str

    def get_schedule_type(self) -> WebhookTriggerScheduleType:
        """Get the schedule type."""
        return WebhookTriggerScheduleType.MONTHLY

    def get_schedule_settings(self) -> dict[str, object]:
        """Get the schedule settings."""
        return {"day": self.day, "start_time": self.start_time, "end_time": self.end_time}

    def is_active(self, event_time: datetime, organization_timezone: str = "Asia/Taipei") -> bool:
        """Check if the monthly schedule is active at the given time.

        Args:
            event_time: The event time to check (timezone-aware)
            organization_timezone: Organization's timezone for time conversion

        Returns:
            True if the monthly schedule is active, False otherwise
        """
        from datetime import time

        # Convert event time to organization timezone
        if event_time.tzinfo is None:
            # If naive datetime, assume UTC
            event_time = event_time.replace(tzinfo=ZoneInfo("UTC"))

        # Convert to organization timezone
        org_time = event_time.astimezone(ZoneInfo(organization_timezone))

        # Check if the day matches
        if org_time.day != self.day:
            return False

        # Parse time strings to time objects
        start_time = time.fromisoformat(self.start_time)
        end_time = time.fromisoformat(self.end_time)
        event_time_only = org_time.time()

        # Check if time is within range (inclusive start, exclusive end)
        return start_time <= event_time_only < end_time


class DateRangeSchedule(WebhookTriggerSchedule):
    """Date range trigger schedule."""

    start_date: str
    end_date: str

    def get_schedule_type(self) -> WebhookTriggerScheduleType:
        """Get the schedule type."""
        return WebhookTriggerScheduleType.DATE_RANGE

    def get_schedule_settings(self) -> dict[str, object]:
        """Get the schedule settings."""
        return {"start_date": self.start_date, "end_date": self.end_date}

    def is_active(self, event_time: datetime, organization_timezone: str = "Asia/Taipei") -> bool:
        """Check if the date range schedule is active at the given time.

        Args:
            event_time: The event time to check (timezone-aware)
            organization_timezone: Organization's timezone for date conversion

        Returns:
            True if the date range schedule is active, False otherwise
        """
        from datetime import date

        # Convert event time to organization timezone
        if event_time.tzinfo is None:
            # If naive datetime, assume UTC
            event_time = event_time.replace(tzinfo=ZoneInfo("UTC"))

        # Convert to organization timezone for date comparison
        org_time = event_time.astimezone(ZoneInfo(organization_timezone))

        # Parse date strings to date objects
        start_date = date.fromisoformat(self.start_date)
        end_date = date.fromisoformat(self.end_date)
        event_date = org_time.date()

        # Check if date is within range (inclusive start and end)
        return start_date <= event_date <= end_date


class BusinessHourSchedule(WebhookTriggerSchedule):
    """Business hour trigger schedule.

    This schedule requires BusinessHour configuration from the organization.
    """

    business_hours: list[dict] | None = None  # BusinessHour configuration

    def get_schedule_type(self) -> WebhookTriggerScheduleType:
        """Get the schedule type."""
        return WebhookTriggerScheduleType.BUSINESS_HOUR

    def get_schedule_settings(self) -> dict[str, object] | None:
        """Get the schedule settings."""
        return {"business_hours": self.business_hours} if self.business_hours else None

    def is_active(self, event_time: datetime, organization_timezone: str = "Asia/Taipei") -> bool:
        """Check if the business hour schedule is active at the given time.

        Args:
            event_time: The event time to check (timezone-aware)
            organization_timezone: Organization's timezone for business hours

        Returns:
            True if within business hours, False otherwise
        """
        if not self.business_hours:
            # No business hours configured, assume always inactive
            return False

        # Convert event time to organization timezone
        if event_time.tzinfo is None:
            # If naive datetime, assume UTC
            event_time = event_time.replace(tzinfo=ZoneInfo("UTC"))

        # Convert to organization timezone
        org_time = event_time.astimezone(ZoneInfo(organization_timezone))

        # Check if current time is within any business hour
        current_weekday = org_time.weekday()  # Monday = 0, Sunday = 6
        current_time = org_time.time()

        for bh in self.business_hours:
            # Match weekday and check if time is within range
            if bh.get("day_of_week") == current_weekday and bh.get("is_active", True):

                start_time = bh.get("start_time")
                end_time = bh.get("end_time")

                if start_time and end_time:
                    # Convert string times to time objects if needed
                    if isinstance(start_time, str):
                        start_time = datetime.fromisoformat(f"2000-01-01T{start_time}").time()
                    if isinstance(end_time, str):
                        end_time = datetime.fromisoformat(f"2000-01-01T{end_time}").time()

                    # Check if current time is within business hours
                    if start_time <= current_time <= end_time:
                        return True

        return False


class NonBusinessHourSchedule(WebhookTriggerSchedule):
    """Non-business hour trigger schedule.

    This schedule is the inverse of BusinessHourSchedule.
    """

    business_hours: list[dict] | None = None  # BusinessHour configuration

    def get_schedule_type(self) -> WebhookTriggerScheduleType:
        """Get the schedule type."""
        return WebhookTriggerScheduleType.NON_BUSINESS_HOUR

    def get_schedule_settings(self) -> dict[str, object] | None:
        """Get the schedule settings."""
        return {"business_hours": self.business_hours} if self.business_hours else None

    def is_active(self, event_time: datetime, organization_timezone: str = "Asia/Taipei") -> bool:
        """Check if the non-business hour schedule is active at the given time.

        This is the inverse of BusinessHourSchedule - active when NOT in business hours.

        Args:
            event_time: The event time to check (timezone-aware)
            organization_timezone: Organization's timezone for business hours

        Returns:
            True if outside business hours, False otherwise
        """
        # Create a temporary BusinessHourSchedule to check business hours
        business_schedule = BusinessHourSchedule(business_hours=self.business_hours)

        # Return the inverse of business hour check
        return not business_schedule.is_active(event_time, organization_timezone)


class WebhookTriggerScheduleSettings(BaseModel):
    """Webhook trigger schedule settings."""

    schedules: list[
        DailySchedule | MonthlySchedule | DateRangeSchedule | BusinessHourSchedule | NonBusinessHourSchedule
    ]

    class Config:
        """Pydantic configuration."""

        use_enum_values = True


class WebhookTriggerSetting(BaseModel):
    """Webhook trigger setting domain model.

    Represents the channel-level configuration for webhook triggers (Auto-Reply).
    """

    id: int
    auto_reply_id: int
    bot_id: int
    enable: bool
    name: str  # Will be deprecated
    event_type: WebhookTriggerEventType
    trigger_code: str | None = None  # Will be deprecated
    trigger_schedule_type: WebhookTriggerScheduleType | None = None  # Will be deprecated
    trigger_schedule_settings: dict[str, object] | None = None  # Will be deprecated
    created_at: datetime
    updated_at: datetime
    archived: bool = False
    extra: dict[str, object] | None = None

    def is_active(self) -> bool:
        """Check if the webhook trigger setting is active."""
        return self.enable and not self.archived

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
