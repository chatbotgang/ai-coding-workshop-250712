"""Auto Reply domain models."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel

from internal.domain.auto_reply.webhook_trigger import (
    WebhookTriggerScheduleSettings,
    WebhookTriggerScheduleType,
    WebhookTriggerSetting,
    WebhookTriggerEventType,
    BusinessHour,
    WebhookEvent,
    MessageEvent,
    ChannelType,
)


class AutoReplyStatus(StrEnum):
    """Auto reply status enumeration."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class AutoReplyEventType(StrEnum):
    """Auto reply event type enumeration."""

    MESSAGE = "message"
    POSTBACK = "postback"
    FOLLOW = "follow"
    BEACON = "beacon"
    TIME = "time"
    KEYWORD = "keyword"
    DEFAULT = "default"


class AutoReply(BaseModel):
    """Auto reply domain model.

    Represents an omnichannel rule that associates several WebhookTriggerSetting instances.
    It defines the high-level auto-reply configuration for an organization.
    """

    id: int
    organization_id: int
    name: str
    status: AutoReplyStatus
    event_type: AutoReplyEventType
    priority: int
    keywords: list[str] | None = None
    trigger_schedule_type: WebhookTriggerScheduleType | None = None
    trigger_schedule_settings: WebhookTriggerScheduleSettings | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic configuration."""

        use_enum_values = True


class AutoReplyTriggerSetting(BaseModel):
    """Merged domain model combining AutoReply and WebhookTriggerSetting.
    
    This provides easy access to both trigger configuration and priority information
    needed for the two-level sorting system.
    """

    # AutoReply fields
    auto_reply_id: int
    auto_reply_name: str
    auto_reply_status: AutoReplyStatus
    auto_reply_event_type: AutoReplyEventType
    auto_reply_priority: int
    keywords: list[str] | None = None
    
    # WebhookTriggerSetting fields
    webhook_trigger_id: int
    bot_id: int
    enable: bool
    webhook_event_type: WebhookTriggerEventType
    trigger_code: str | None = None
    trigger_schedule_type: WebhookTriggerScheduleType | None = None
    trigger_schedule_settings: dict[str, object] | None = None
    archived: bool = False
    
    def is_active(self) -> bool:
        """Check if the trigger setting is active."""
        return (
            self.auto_reply_status == AutoReplyStatus.ACTIVE
            and self.enable
            and not self.archived
        )
    
    def is_keyword_trigger(self) -> bool:
        """Check if this is a keyword-based trigger."""
        return (
            self.auto_reply_event_type == AutoReplyEventType.KEYWORD
            and self.keywords is not None
            and len(self.keywords) > 0
        )
    
    def is_general_time_trigger(self) -> bool:
        """Check if this is a general time-based trigger."""
        return (
            self.auto_reply_event_type == AutoReplyEventType.TIME
            and self.trigger_schedule_type is not None
        )
    
    class Config:
        """Pydantic configuration."""

        use_enum_values = True


class AutoReplyChannelSettingAggregate(BaseModel):
    """Aggregate that manages auto-reply trigger validation for a specific bot/channel.
    
    Contains all trigger settings for a bot and manages the validation logic
    with business rules and priority system.
    """

    bot_id: int
    trigger_settings: list[AutoReplyTriggerSetting]
    business_hours: list[BusinessHour]
    timezone: str  # Bot timezone for general time triggers
    organization_timezone: str | None = None  # Organization timezone for business hours
    
    def validate_trigger(self, event: WebhookEvent) -> AutoReplyTriggerSetting | None:
        """Validate trigger against incoming webhook event.
        
        Returns the first matching trigger setting based on priority system,
        or None if no match found.
        
        Priority system:
        1. Keyword triggers (higher priority)
        2. General time-based triggers (lower priority)
        
        Within each type, triggers are sorted by auto_reply_priority
        (higher number = higher priority).
        
        Args:
            event: Incoming webhook event to match against
            
        Returns:
            First matching AutoReplyTriggerSetting or None
        """
        # Only handle MESSAGE events
        if not isinstance(event, MessageEvent):
            return None
            
        active_triggers = [t for t in self.trigger_settings if t.is_active()]
        
        # Step 1: Check keyword triggers first (higher priority)
        keyword_triggers = [
            t for t in active_triggers 
            if t.is_keyword_trigger()
        ]
        
        # Sort keyword triggers by priority (descending)
        keyword_triggers.sort(key=lambda t: t.auto_reply_priority, reverse=True)
        
        for trigger in keyword_triggers:
            if self._matches_keyword(trigger, event):
                return trigger
        
        # Step 2: Check general time-based triggers (lower priority)
        time_triggers = [
            t for t in active_triggers 
            if t.is_general_time_trigger()
        ]
        
        # Filter triggers that match the time schedule
        matching_time_triggers = [
            t for t in time_triggers
            if self._matches_time_schedule(t, event)
        ]
        
        if not matching_time_triggers:
            return None
        
        # Sort matching triggers by schedule type priority, then by auto_reply_priority
        matching_time_triggers.sort(key=self._get_time_trigger_sort_key, reverse=True)
        
        # Return the highest priority matching trigger
        return matching_time_triggers[0]
    
    def _matches_keyword(self, trigger: AutoReplyTriggerSetting, event: MessageEvent) -> bool:
        """Check if message content matches any of the trigger keywords.
        
        Keyword matching rules:
        - Case insensitive
        - Trim leading/trailing spaces
        - Exact match (no partial matching)
        """
        if not trigger.keywords:
            return False
            
        normalized_content = self._normalize_keyword(event.content)
        
        for keyword in trigger.keywords:
            normalized_keyword = self._normalize_keyword(keyword)
            if normalized_content == normalized_keyword:
                return True
                
        return False
    
    def _normalize_keyword(self, keyword: str) -> str:
        """Normalize keyword for comparison.
        
        - Convert to lowercase
        - Strip leading/trailing whitespace
        """
        return keyword.strip().lower()
    
    def _matches_time_schedule(self, trigger: AutoReplyTriggerSetting, event: WebhookEvent) -> bool:
        """Check if event timestamp matches the trigger's time schedule."""
        if not trigger.trigger_schedule_type:
            return False
            
        # Business hour and non-business hour triggers don't need schedule settings
        if (trigger.trigger_schedule_type in [
            WebhookTriggerScheduleType.BUSINESS_HOUR, 
            WebhookTriggerScheduleType.NON_BUSINESS_HOUR
        ]):
            pass  # No settings required
        elif not trigger.trigger_schedule_settings:
            return False
            
        # Import timezone handling here to avoid circular imports
        from datetime import time
        import pytz
        
        # Convert event timestamp to trigger timezone
        tz = pytz.timezone(self.timezone)
        event_time = event.timestamp.astimezone(tz)
        
        schedule_type = trigger.trigger_schedule_type
        settings = trigger.trigger_schedule_settings
        
        if schedule_type == WebhookTriggerScheduleType.MONTHLY:
            return self._matches_monthly_schedule(event_time, settings)
        elif schedule_type == WebhookTriggerScheduleType.BUSINESS_HOUR:
            return self._matches_business_hour_schedule(event_time)
        elif schedule_type == WebhookTriggerScheduleType.NON_BUSINESS_HOUR:
            return not self._matches_business_hour_schedule(event_time)
        elif schedule_type == WebhookTriggerScheduleType.DAILY:
            return self._matches_daily_schedule(event_time, settings)
            
        return False
    
    def _matches_monthly_schedule(self, event_time, settings) -> bool:
        """Check if event matches monthly schedule."""
        schedules = settings.get("schedules", [settings])
        
        for schedule in schedules:
            day = schedule.get("day")
            start_time = schedule.get("start_time")
            end_time = schedule.get("end_time")
            
            if event_time.day == day:
                if self._time_in_range(event_time.time(), start_time, end_time):
                    return True
                    
        return False
    
    def _matches_business_hour_schedule(self, event_time) -> bool:
        """Check if event is within business hours.
        
        Business hours are interpreted in organization timezone if provided,
        otherwise in bot timezone.
        """
        # Convert event to organization timezone for business hour comparison
        if self.organization_timezone:
            import pytz
            org_tz = pytz.timezone(self.organization_timezone)
            event_time_org = event_time.astimezone(org_tz)
        else:
            # Fallback to bot timezone if organization timezone not specified
            event_time_org = event_time
        
        weekday = event_time_org.isoweekday()  # 1=Monday, 7=Sunday
        current_time = event_time_org.time()
        
        for business_hour in self.business_hours:
            if business_hour.weekday == weekday:
                start_time = self._parse_time(business_hour.start_time)
                end_time = self._parse_time(business_hour.end_time)
                if self._time_in_range(current_time, start_time, end_time):
                    return True
                    
        return False
    
    def _matches_daily_schedule(self, event_time, settings) -> bool:
        """Check if event matches daily schedule."""
        schedules = settings.get("schedules", [settings])
        current_time = event_time.time()
        
        for schedule in schedules:
            start_time = schedule.get("start_time")
            end_time = schedule.get("end_time")
            
            if self._time_in_range(current_time, start_time, end_time):
                return True
                
        return False
    
    def _time_in_range(self, current_time, start_time_str, end_time_str) -> bool:
        """Check if current time is within start and end time range.
        
        Handles midnight crossing (e.g., 22:00 to 06:00).
        """
        from datetime import time
        
        if isinstance(start_time_str, str):
            start_time = self._parse_time(start_time_str)
        else:
            start_time = start_time_str
            
        if isinstance(end_time_str, str):
            end_time = self._parse_time(end_time_str)
        else:
            end_time = end_time_str
        
        # Handle midnight crossing
        if start_time > end_time:
            return current_time >= start_time or current_time < end_time
        else:
            return start_time <= current_time < end_time
    
    def _parse_time(self, time_str: str):
        """Parse time string in HH:MM format."""
        from datetime import time
        
        hour, minute = map(int, time_str.split(":"))
        return time(hour, minute)
    
    def _get_time_trigger_sort_key(self, trigger: AutoReplyTriggerSetting) -> tuple[int, int]:
        """Get sort key for time-based triggers.
        
        Priority order:
        1. MONTHLY (highest)
        2. BUSINESS_HOUR
        3. NON_BUSINESS_HOUR
        4. DAILY (lowest)
        
        Within same schedule type, sort by auto_reply_priority.
        """
        schedule_priority = {
            WebhookTriggerScheduleType.MONTHLY: 4,
            WebhookTriggerScheduleType.BUSINESS_HOUR: 3,
            WebhookTriggerScheduleType.NON_BUSINESS_HOUR: 2,
            WebhookTriggerScheduleType.DAILY: 1,
        }
        
        type_priority = schedule_priority.get(trigger.trigger_schedule_type, 0)
        return (type_priority, trigger.auto_reply_priority)
    
    class Config:
        """Pydantic configuration."""

        use_enum_values = True
