"""Auto-reply trigger validation domain models and logic."""

from datetime import datetime, time
from typing import Optional

import pytz
from pydantic import BaseModel, Field

from internal.domain.auto_reply.auto_reply import AutoReply, AutoReplyEventType, AutoReplyStatus
from internal.domain.auto_reply.webhook_trigger import (
    MessageEvent,
    WebhookTriggerEventType,
    WebhookTriggerScheduleSettings,
    WebhookTriggerScheduleType,
    WebhookTriggerSetting,
)
from internal.domain.organization.business_hour_checker import BusinessHourChecker


class AutoReplyTriggerSetting(BaseModel):
    """Merged domain model combining AutoReply and WebhookTriggerSetting.

    This model provides unified access to both auto-reply configuration
    and webhook trigger settings for validation logic.
    """

    # AutoReply fields
    auto_reply_id: int = Field(..., description="Auto reply ID")
    auto_reply_name: str = Field(..., description="Auto reply name")
    auto_reply_status: AutoReplyStatus = Field(..., description="Auto reply status")
    auto_reply_event_type: AutoReplyEventType = Field(..., description="Auto reply event type")
    auto_reply_priority: int = Field(..., description="Auto reply priority for sorting")
    keywords: list[str] | None = Field(None, description="Keywords for keyword triggers")
    ig_story_ids: list[str] | None = Field(None, description="Instagram Story IDs for IG Story-specific triggers")

    # WebhookTriggerSetting fields
    webhook_trigger_id: int = Field(..., description="Webhook trigger setting ID")
    bot_id: int = Field(..., description="Bot ID")
    enable: bool = Field(..., description="Whether trigger is enabled")
    webhook_event_type: WebhookTriggerEventType = Field(..., description="Webhook event type")
    trigger_schedule_type: WebhookTriggerScheduleType | None = Field(None, description="Schedule type")
    trigger_schedule_settings: WebhookTriggerScheduleSettings | None = Field(None, description="Schedule settings")
    created_at: datetime = Field(..., description="Created timestamp")
    updated_at: datetime = Field(..., description="Updated timestamp")
    archived: bool = Field(False, description="Whether trigger is archived")

    class Config:
        """Pydantic configuration."""

        use_enum_values = True

    def is_active(self) -> bool:
        """Check if the trigger setting is active."""
        return self.enable and not self.archived and self.auto_reply_status == AutoReplyStatus.ACTIVE

    def is_keyword_trigger(self) -> bool:
        """Check if this is a keyword trigger."""
        return (
            self.auto_reply_event_type == AutoReplyEventType.KEYWORD
            and self.keywords is not None
            and len(self.keywords) > 0
        )

    def is_general_time_trigger(self) -> bool:
        """Check if this is a general time-based trigger."""
        return self.auto_reply_event_type == AutoReplyEventType.TIME and self.trigger_schedule_type is not None

    def is_ig_story_trigger(self) -> bool:
        """Check if this is an IG Story-specific trigger."""
        return self.ig_story_ids is not None and len(self.ig_story_ids) > 0

    def is_ig_story_keyword_trigger(self) -> bool:
        """Check if this is an IG Story keyword trigger."""
        return self.is_ig_story_trigger() and self.is_keyword_trigger()

    def is_ig_story_general_trigger(self) -> bool:
        """Check if this is an IG Story general (time-based) trigger."""
        return self.is_ig_story_trigger() and self.is_general_time_trigger()

    def is_general_keyword_trigger(self) -> bool:
        """Check if this is a general keyword trigger (not IG Story-specific)."""
        return self.is_keyword_trigger() and not self.is_ig_story_trigger()

    def is_general_time_only_trigger(self) -> bool:
        """Check if this is a general time-based trigger (not IG Story-specific)."""
        return self.is_general_time_trigger() and not self.is_ig_story_trigger()

    def normalize_keyword(self, keyword: str) -> str:
        """Normalize keyword for matching: case insensitive + trim spaces."""
        return keyword.strip().lower()

    def matches_keyword(self, message_content: str) -> bool:
        """Check if message content matches any configured keyword.

        Matching rules:
        - Case insensitive
        - Trim spaces
        - Exact match (not substring)
        """
        if not self.is_keyword_trigger():
            return False

        normalized_content = self.normalize_keyword(message_content)

        for keyword in self.keywords:
            normalized_keyword = self.normalize_keyword(keyword)
            if normalized_content == normalized_keyword:
                return True

        return False

    def matches_ig_story_id(self, ig_story_id: str | None) -> bool:
        """Check if the provided IG Story ID matches any configured story IDs."""
        if not self.is_ig_story_trigger() or ig_story_id is None:
            return False
        
        return ig_story_id in self.ig_story_ids

    @classmethod
    def from_auto_reply_and_webhook_trigger(
        cls, auto_reply: AutoReply, webhook_trigger: WebhookTriggerSetting
    ) -> "AutoReplyTriggerSetting":
        """Create AutoReplyTriggerSetting from AutoReply and WebhookTriggerSetting."""
        return cls(
            auto_reply_id=auto_reply.id,
            auto_reply_name=auto_reply.name,
            auto_reply_status=auto_reply.status,
            auto_reply_event_type=auto_reply.event_type,
            auto_reply_priority=auto_reply.priority,
            keywords=auto_reply.keywords,
            ig_story_ids=getattr(auto_reply, 'ig_story_ids', None),
            webhook_trigger_id=webhook_trigger.id,
            bot_id=webhook_trigger.bot_id,
            enable=webhook_trigger.enable,
            webhook_event_type=webhook_trigger.event_type,
            trigger_schedule_type=webhook_trigger.trigger_schedule_type,
            trigger_schedule_settings=webhook_trigger.trigger_schedule_settings,
            created_at=webhook_trigger.created_at,
            updated_at=webhook_trigger.updated_at,
            archived=webhook_trigger.archived,
        )


class AutoReplyChannelSettingAggregate(BaseModel):
    """Aggregate for auto-reply channel settings and validation logic."""

    bot_id: int = Field(..., description="Bot/Channel ID")
    organization_id: int = Field(..., description="Organization ID")
    timezone: str = Field(..., description="Timezone for time-based calculations")
    trigger_settings: list[AutoReplyTriggerSetting] = Field(..., description="All trigger settings for this bot")
    business_hour_checker: Optional[BusinessHourChecker] = Field(None, description="Business hour checker")

    class Config:
        """Pydantic configuration."""

        arbitrary_types_allowed = True

    def validate_trigger(self, event: MessageEvent) -> Optional[AutoReplyTriggerSetting]:
        """Validate trigger and return the first matching trigger setting based on priority.

        Priority system (PRD part2 - 4 levels):
        1. IG Story Keyword (highest priority)
        2. IG Story General (time-based)
        3. General Keyword
        4. General Time-based (lowest priority)

        Within each trigger type, sort by auto_reply_priority (higher number = higher priority).

        Args:
            event: The message event to validate

        Returns:
            The first matching AutoReplyTriggerSetting or None if no match
        """
        # Filter active triggers
        active_triggers = [trigger for trigger in self.trigger_settings if trigger.is_active()]

        if not active_triggers:
            return None

        # Convert event timestamp to bot timezone
        tz = pytz.timezone(self.timezone)
        event_time = event.timestamp.astimezone(tz)

        # Separate triggers by type (4-level priority system)
        ig_story_keyword_triggers = [trigger for trigger in active_triggers if trigger.is_ig_story_keyword_trigger()]
        ig_story_general_triggers = [trigger for trigger in active_triggers if trigger.is_ig_story_general_trigger()]
        general_keyword_triggers = [trigger for trigger in active_triggers if trigger.is_general_keyword_trigger()]
        general_time_triggers = [trigger for trigger in active_triggers if trigger.is_general_time_only_trigger()]

        # Sort triggers by priority (higher number = higher priority)
        ig_story_keyword_triggers.sort(key=lambda x: x.auto_reply_priority, reverse=True)
        ig_story_general_triggers.sort(key=lambda x: x.auto_reply_priority, reverse=True)
        general_keyword_triggers.sort(key=lambda x: x.auto_reply_priority, reverse=True)
        general_time_triggers.sort(key=lambda x: x.auto_reply_priority, reverse=True)

        # Priority 1: IG Story Keyword triggers (highest priority)
        for trigger in ig_story_keyword_triggers:
            if trigger.matches_keyword(event.content) and trigger.matches_ig_story_id(event.ig_story_id):
                return trigger

        # Priority 2: IG Story General triggers
        for trigger in ig_story_general_triggers:
            if self._matches_time_trigger(trigger, event_time) and trigger.matches_ig_story_id(event.ig_story_id):
                return trigger

        # Priority 3: General Keyword triggers
        for trigger in general_keyword_triggers:
            if trigger.matches_keyword(event.content):
                return trigger

        # Priority 4: General Time-based triggers (lowest priority)
        for trigger in general_time_triggers:
            if self._matches_time_trigger(trigger, event_time):
                return trigger

        return None

    def _matches_time_trigger(self, trigger: AutoReplyTriggerSetting, event_time: datetime) -> bool:
        """Check if a time-based trigger matches the given event time."""
        if not trigger.is_general_time_trigger():
            return False

        schedule_type = trigger.trigger_schedule_type
        schedule_settings = trigger.trigger_schedule_settings

        if schedule_type == WebhookTriggerScheduleType.MONTHLY:
            return self._matches_monthly_schedule(schedule_settings, event_time)
        elif schedule_type == WebhookTriggerScheduleType.BUSINESS_HOUR:
            return self._matches_business_hour_schedule(event_time)
        elif schedule_type == WebhookTriggerScheduleType.NON_BUSINESS_HOUR:
            return self._matches_non_business_hour_schedule(event_time)
        elif schedule_type == WebhookTriggerScheduleType.DAILY:
            return self._matches_daily_schedule(schedule_settings, event_time)

        return False

    def _matches_monthly_schedule(
        self, schedule_settings: WebhookTriggerScheduleSettings, event_time: datetime
    ) -> bool:
        """Check if event time matches monthly schedule."""
        if not schedule_settings or not schedule_settings.schedules:
            return False

        for schedule in schedule_settings.schedules:
            if schedule.get_schedule_type() != WebhookTriggerScheduleType.MONTHLY:
                continue

            settings = schedule.get_schedule_settings()
            if not settings:
                continue

            # Check if day matches
            if event_time.day != settings.get("day"):
                continue

            # Check if time is within range
            start_time = time.fromisoformat(settings["start_time"]).replace(
                second=time.min.second, microsecond=time.min.microsecond
            )
            end_time = time.fromisoformat(settings["end_time"]).replace(
                second=time.max.second, microsecond=time.max.microsecond
            )

            # Handle normal time range
            if start_time <= end_time:
                if start_time <= event_time.time() < end_time:
                    return True
            else:
                # Handle midnight crossing (e.g., 22:00 to 06:00)
                if start_time <= event_time.time() or event_time.time() < end_time:
                    return True

        return False

    def _matches_business_hour_schedule(self, event_time: datetime) -> bool:
        """Check if event time is within business hours."""
        if not self.business_hour_checker:
            return False

        return self.business_hour_checker.is_in_business_hours(event_time)

    def _matches_non_business_hour_schedule(self, event_time: datetime) -> bool:
        """Check if event time is outside business hours."""
        if not self.business_hour_checker:
            return False

        return self.business_hour_checker.is_in_non_business_hours(event_time)

    def _matches_daily_schedule(self, schedule_settings: WebhookTriggerScheduleSettings, event_time: datetime) -> bool:
        """Check if event time matches daily schedule."""
        if not schedule_settings or not schedule_settings.schedules:
            return False

        for schedule in schedule_settings.schedules:
            if schedule.get_schedule_type() != WebhookTriggerScheduleType.DAILY:
                continue

            settings = schedule.get_schedule_settings()
            if not settings:
                continue

            start_time = time.fromisoformat(settings["start_time"]).replace(
                second=time.min.second, microsecond=time.min.microsecond
            )
            end_time = time.fromisoformat(settings["end_time"]).replace(
                second=time.max.second, microsecond=time.max.microsecond
            )

            # Handle normal time range
            if start_time <= end_time:
                if start_time <= event_time.time() < end_time:
                    return True
            else:
                # Handle midnight crossing (e.g., 22:00 to 06:00)
                if start_time <= event_time.time() or event_time.time() < end_time:
                    return True

        return False
