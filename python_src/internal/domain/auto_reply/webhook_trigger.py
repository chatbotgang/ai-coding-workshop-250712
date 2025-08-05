"""Webhook Trigger domain models."""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import IntEnum, StrEnum

from pydantic import BaseModel, Field


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


class BusinessHourSchedule(WebhookTriggerSchedule):
    """Business hour trigger schedule."""

    def get_schedule_type(self) -> WebhookTriggerScheduleType:
        """Get the schedule type."""
        return WebhookTriggerScheduleType.BUSINESS_HOUR

    def get_schedule_settings(self) -> dict[str, object] | None:
        """Get the schedule settings."""
        return None


class NonBusinessHourSchedule(WebhookTriggerSchedule):
    """Non-business hour trigger schedule."""

    def get_schedule_type(self) -> WebhookTriggerScheduleType:
        """Get the schedule type."""
        return WebhookTriggerScheduleType.NON_BUSINESS_HOUR

    def get_schedule_settings(self) -> dict[str, object] | None:
        """Get the schedule settings."""
        return None


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


class ChannelType(StrEnum):
    """Channel type enumeration."""

    LINE = "line"
    FACEBOOK = "fb"
    INSTAGRAM = "ig"


class WebhookEvent(BaseModel, ABC):
    """Abstract base class for webhook events."""

    event_id: str = Field(..., description="Unique event identifier")
    channel_type: ChannelType = Field(..., description="Channel where event originated")
    user_id: str = Field(..., description="User identifier from the channel")
    timestamp: datetime = Field(..., description="Event timestamp")


class MessageEvent(WebhookEvent):
    """Message webhook event."""

    content: str = Field(..., description="Message content/text")
    message_id: str = Field(..., description="Unique message identifier")
    ig_story_id: str | None = Field(None, description="Instagram Story ID if this is a reply to a story")


class BusinessHour(BaseModel):
    """Business hour configuration."""

    weekday: int = Field(..., description="Day of week (1=Monday, 7=Sunday)")
    start_time: str = Field(..., description="Start time in HH:MM format")
    end_time: str = Field(..., description="End time in HH:MM format")
