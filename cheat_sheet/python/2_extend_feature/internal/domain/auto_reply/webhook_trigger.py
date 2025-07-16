"""Webhook Trigger domain models."""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import IntEnum, StrEnum

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

    def is_ig_story_trigger(self) -> bool:
        """Check if this trigger is specific to IG Stories.

        Returns:
            True if trigger has IG story configuration in extra field
        """
        if not self.extra:
            return False
        return "ig_story_ids" in self.extra

    def get_ig_story_ids(self) -> list[str]:
        """Get the IG story IDs configured for this trigger.

        Returns:
            List of IG story IDs, empty list if not IG story trigger
        """
        if not self.extra or "ig_story_ids" not in self.extra:
            return []

        story_ids = self.extra.get("ig_story_ids", [])
        if isinstance(story_ids, list):
            return [str(story_id) for story_id in story_ids]
        return []

    def get_ig_story_keywords(self) -> list[str]:
        """Get keywords for IG Story keyword triggers.

        Returns:
            List of keywords for IG story triggers, empty list if not keyword trigger
        """
        if not self.extra or "keywords" not in self.extra:
            return []

        keywords = self.extra.get("keywords", [])
        if isinstance(keywords, list):
            return [str(keyword) for keyword in keywords]
        return []

    def matches_ig_story(self, ig_story_id: str) -> bool:
        """Check if this trigger matches the given IG story ID.

        Args:
            ig_story_id: The IG story ID to match against

        Returns:
            True if this trigger is configured for the given story ID
        """
        return ig_story_id in self.get_ig_story_ids()

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
