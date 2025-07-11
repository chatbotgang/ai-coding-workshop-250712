"""Trigger validation logic for auto-reply system."""

from datetime import datetime, time
from typing import Protocol
from zoneinfo import ZoneInfo

from internal.domain.auto_reply.webhook_event import FollowEvent, MessageEvent, WebhookEvent
from internal.domain.auto_reply.webhook_trigger import (
    WebhookTriggerEventType,
    WebhookTriggerScheduleType,
    WebhookTriggerSetting,
)


class BusinessHourChecker(Protocol):
    """Protocol for checking business hours with timezone support."""

    def is_in_business_hours(
        self,
        timestamp: datetime,
        organization_id: int,
        bot_timezone: str | None = None,
        organization_timezone: str | None = None,
    ) -> bool:
        """Check if timestamp is within business hours with timezone awareness.

        Args:
            timestamp: The timestamp to check (should be in organization timezone)
            organization_id: Organization ID for business hour lookup
            bot_timezone: Bot's configured timezone (for compatibility)
            organization_timezone: Organization's timezone for business hours

        Returns:
            True if timestamp is within business hours
        """
        ...


class TriggerValidationResult:
    """Result of trigger validation."""

    def __init__(self, matched_trigger: WebhookTriggerSetting | None = None, match_type: str | None = None):
        self.matched_trigger = matched_trigger
        self.match_type = match_type  # "keyword", "welcome", or "general"

    @property
    def has_match(self) -> bool:
        """Check if a trigger was matched."""
        return self.matched_trigger is not None


def convert_to_timezone(timestamp: datetime, target_timezone: str | None) -> datetime:
    """Convert timestamp to target timezone.

    Args:
        timestamp: The timestamp to convert
        target_timezone: Target timezone string (e.g., "Asia/Taipei", "UTC")

    Returns:
        Timezone-aware datetime in target timezone
    """
    if not target_timezone:
        # Default to UTC if no timezone specified
        target_timezone = "UTC"

    try:
        target_tz = ZoneInfo(target_timezone)

        # If timestamp is naive, assume it's UTC
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=ZoneInfo("UTC"))

        # Convert to target timezone
        return timestamp.astimezone(target_tz)

    except Exception:
        # Fallback to original timestamp if timezone conversion fails
        return timestamp


def validate_trigger(
    trigger_settings: list[WebhookTriggerSetting],
    message_event: WebhookEvent,
    business_hour_checker: BusinessHourChecker | None = None,
    organization_id: int | None = None,
    bot_timezone: str | None = None,
    organization_timezone: str | None = None,
) -> TriggerValidationResult:
    """Validate trigger settings against a webhook event with priority system.

    Priority order according to PRD:
    1. Keyword triggers (highest priority)
    2. Welcome triggers (FOLLOW events only)
    3. General time-based triggers (lowest priority)

    Args:
        trigger_settings: List of trigger settings to evaluate
        message_event: The webhook event to match against
        business_hour_checker: Optional business hour checker for time-based triggers
        organization_id: Optional organization ID for business hour checking
        bot_timezone: Optional bot timezone (e.g., "Asia/Taipei") for time-based triggers
        organization_timezone: Optional organization timezone for business hour checking

    Returns:
        TriggerValidationResult with the first matching trigger or None
    """
    # Filter only active triggers
    active_triggers = [t for t in trigger_settings if t.is_active()]

    # Phase 1: Check keyword triggers (highest priority)
    keyword_triggers = [t for t in active_triggers if is_keyword_trigger(t)]
    for trigger in keyword_triggers:
        if matches_keyword_trigger(message_event, trigger):
            # Check schedule constraints for keyword triggers (DATE_RANGE only)
            if trigger.trigger_schedule_type == WebhookTriggerScheduleType.DATE_RANGE and not matches_time_schedule(
                message_event, trigger, business_hour_checker, organization_id, bot_timezone, organization_timezone
            ):
                continue
            return TriggerValidationResult(trigger, "keyword")

    # Phase 2: Check welcome triggers (FOLLOW events only)
    if isinstance(message_event, FollowEvent):
        welcome_triggers = [t for t in active_triggers if is_welcome_trigger(t)]
        for trigger in welcome_triggers:
            if matches_welcome_trigger(message_event, trigger):
                return TriggerValidationResult(trigger, "welcome")

    # Phase 3: Check general time-based triggers (lowest priority)
    # According to Feature KB priority: MONTHLY > BUSINESS_HOUR > NON_BUSINESS_HOUR > DAILY
    general_triggers = [t for t in active_triggers if is_general_trigger(t)]

    # Group by schedule type and check in priority order
    schedule_priority = [
        WebhookTriggerScheduleType.MONTHLY,
        WebhookTriggerScheduleType.BUSINESS_HOUR,
        WebhookTriggerScheduleType.NON_BUSINESS_HOUR,
        WebhookTriggerScheduleType.DAILY,
    ]

    for schedule_type in schedule_priority:
        type_triggers = [t for t in general_triggers if t.trigger_schedule_type == schedule_type]
        for trigger in type_triggers:
            if matches_general_trigger(
                message_event, trigger, business_hour_checker, organization_id, bot_timezone, organization_timezone
            ):
                return TriggerValidationResult(trigger, "general")

    # No triggers matched
    return TriggerValidationResult()


def normalize_keyword(keyword: str) -> str:
    """Normalize keyword for matching.

    Normalization rules:
    - Convert to lowercase
    - Trim leading and trailing spaces

    Args:
        keyword: The keyword to normalize

    Returns:
        Normalized keyword
    """
    return keyword.strip().lower()


def normalize_keywords(keywords: list[str]) -> list[str]:
    """Normalize a list of keywords.

    Args:
        keywords: List of keywords to normalize

    Returns:
        List of normalized keywords
    """
    return [normalize_keyword(keyword) for keyword in keywords]


def matches_keyword(message_content: str, keywords: list[str]) -> bool:
    """Check if message content matches any of the keywords.

    Matching rules according to PRD:
    - Case insensitive
    - Trim spaces from message content
    - Exact match only (not partial)
    - Any keyword in the list can match

    Args:
        message_content: The message content to check
        keywords: List of keywords to match against

    Returns:
        True if message content exactly matches any keyword
    """
    if not keywords:
        return False

    normalized_content = normalize_keyword(message_content)
    normalized_keywords = normalize_keywords(keywords)

    return normalized_content in normalized_keywords


def matches_keyword_trigger(event: WebhookEvent, trigger_setting: WebhookTriggerSetting) -> bool:
    """Check if an event matches a keyword trigger setting.

    Args:
        event: The webhook event to check
        trigger_setting: The trigger setting to match against

    Returns:
        True if the event matches the keyword trigger
    """
    # Only MESSAGE events can match keyword triggers according to PRD
    if not isinstance(event, MessageEvent):
        return False

    # Event type must match trigger event type
    if event.get_trigger_event_type() != trigger_setting.event_type:
        return False

    # Must have keywords to match against
    if not trigger_setting.trigger_code:
        return False

    # For now, treat trigger_code as a single keyword
    # TODO: Support multiple keywords when AutoReply.keywords is implemented
    keywords = [trigger_setting.trigger_code]

    return matches_keyword(event.content, keywords)


def matches_welcome_trigger(event: WebhookEvent, trigger_setting: WebhookTriggerSetting) -> bool:
    """Check if an event matches a welcome trigger setting.

    Args:
        event: The webhook event to check
        trigger_setting: The trigger setting to match against

    Returns:
        True if the event matches the welcome trigger
    """
    # Only FOLLOW events can match welcome triggers
    if not isinstance(event, FollowEvent):
        return False

    # Event type must match trigger event type
    return event.get_trigger_event_type() == trigger_setting.event_type


def parse_time_string(time_str: str) -> time:
    """Parse time string in HH:MM format.

    Args:
        time_str: Time string in HH:MM format

    Returns:
        time object

    Raises:
        ValueError: If time string format is invalid
    """
    try:
        hour, minute = time_str.split(":")
        return time(int(hour), int(minute))
    except (ValueError, IndexError) as e:
        raise ValueError(f"Invalid time format: {time_str}. Expected HH:MM format") from e


def time_in_range(current_time: time, start_time: time, end_time: time) -> bool:
    """Check if current time is within time range.

    Handles midnight crossing ranges (e.g., 22:00 to 06:00).

    Args:
        current_time: Current time to check
        start_time: Range start time
        end_time: Range end time

    Returns:
        True if current time is within range
    """
    if start_time <= end_time:
        # Normal range (e.g., 09:00 to 17:00)
        return start_time <= current_time < end_time
    else:
        # Midnight crossing range (e.g., 22:00 to 06:00)
        return current_time >= start_time or current_time < end_time


def matches_monthly_schedule(event_time: datetime, schedule_settings: dict[str, object] | None) -> bool:
    """Check if event time matches monthly schedule.

    Args:
        event_time: Event timestamp
        schedule_settings: Monthly schedule settings with day, start_time, end_time

    Returns:
        True if event time matches monthly schedule
    """
    if not schedule_settings:
        return False

    day = schedule_settings.get("day")
    start_time_str = schedule_settings.get("start_time")
    end_time_str = schedule_settings.get("end_time")

    if not all([day, start_time_str, end_time_str]):
        return False

    try:
        # Check if day matches
        day_int = int(str(day))
        if event_time.day != day_int:
            return False

        # Check if time is within range
        start_time = parse_time_string(str(start_time_str))
        end_time = parse_time_string(str(end_time_str))
        current_time = event_time.time()

        return time_in_range(current_time, start_time, end_time)

    except (ValueError, TypeError):
        return False


def matches_daily_schedule(event_time: datetime, schedule_settings: dict[str, object] | None) -> bool:
    """Check if event time matches daily schedule.

    Args:
        event_time: Event timestamp
        schedule_settings: Daily schedule settings with start_time, end_time

    Returns:
        True if event time matches daily schedule
    """
    if not schedule_settings:
        return False

    start_time_str = schedule_settings.get("start_time")
    end_time_str = schedule_settings.get("end_time")

    if not all([start_time_str, end_time_str]):
        return False

    try:
        start_time = parse_time_string(str(start_time_str))
        end_time = parse_time_string(str(end_time_str))
        current_time = event_time.time()

        return time_in_range(current_time, start_time, end_time)

    except (ValueError, TypeError):
        return False


def matches_date_range_schedule(event_time: datetime, schedule_settings: dict[str, object] | None) -> bool:
    """Check if event time matches date range schedule.

    Args:
        event_time: Event timestamp
        schedule_settings: Date range settings with start_date, end_date

    Returns:
        True if event time matches date range
    """
    if not schedule_settings:
        return False

    start_date_str = schedule_settings.get("start_date")
    end_date_str = schedule_settings.get("end_date")

    if not all([start_date_str, end_date_str]):
        return False

    try:
        start_date = datetime.fromisoformat(str(start_date_str)).date()
        end_date = datetime.fromisoformat(str(end_date_str)).date()
        event_date = event_time.date()

        return start_date <= event_date <= end_date

    except (ValueError, TypeError):
        return False


def matches_time_schedule(
    event: WebhookEvent,
    trigger_setting: WebhookTriggerSetting,
    business_hour_checker: BusinessHourChecker | None = None,
    organization_id: int | None = None,
    bot_timezone: str | None = None,
    organization_timezone: str | None = None,
) -> bool:
    """Check if an event matches a time-based schedule with timezone awareness.

    Args:
        event: The webhook event to check
        trigger_setting: The trigger setting with schedule
        business_hour_checker: Business hour checker implementation
        organization_id: Organization ID for business hour checking
        bot_timezone: Bot's configured timezone for time-based comparisons
        organization_timezone: Organization's timezone for business hour checking

    Returns:
        True if event matches the schedule
    """
    if not trigger_setting.trigger_schedule_type:
        return True  # No schedule restriction

    schedule_type = trigger_setting.trigger_schedule_type
    schedule_settings = trigger_setting.trigger_schedule_settings

    # Convert event timestamp to appropriate timezone based on schedule type
    if schedule_type in [WebhookTriggerScheduleType.BUSINESS_HOUR, WebhookTriggerScheduleType.NON_BUSINESS_HOUR]:
        # Use organization timezone for business hour checking
        event_time = convert_to_timezone(event.timestamp, organization_timezone)
    else:
        # Use bot timezone for other time-based comparisons (monthly, daily, date range)
        event_time = convert_to_timezone(event.timestamp, bot_timezone)

    if schedule_type == WebhookTriggerScheduleType.MONTHLY:
        return matches_monthly_schedule(event_time, schedule_settings)

    elif schedule_type == WebhookTriggerScheduleType.BUSINESS_HOUR:
        if business_hour_checker and organization_id:
            return business_hour_checker.is_in_business_hours(
                event_time, organization_id, bot_timezone, organization_timezone
            )
        return False

    elif schedule_type == WebhookTriggerScheduleType.NON_BUSINESS_HOUR:
        if business_hour_checker and organization_id:
            return not business_hour_checker.is_in_business_hours(
                event_time, organization_id, bot_timezone, organization_timezone
            )
        return False

    elif schedule_type == WebhookTriggerScheduleType.DAILY:
        return matches_daily_schedule(event_time, schedule_settings)

    elif schedule_type == WebhookTriggerScheduleType.DATE_RANGE:
        return matches_date_range_schedule(event_time, schedule_settings)

    return False


def matches_general_trigger(
    event: WebhookEvent,
    trigger_setting: WebhookTriggerSetting,
    business_hour_checker: BusinessHourChecker | None = None,
    organization_id: int | None = None,
    bot_timezone: str | None = None,
    organization_timezone: str | None = None,
) -> bool:
    """Check if an event matches a general (time-based) trigger.

    Args:
        event: The webhook event to check
        trigger_setting: The trigger setting to match against
        business_hour_checker: Business hour checker implementation
        organization_id: Organization ID for business hour checking
        bot_timezone: Bot's configured timezone for time-based comparisons
        organization_timezone: Organization's timezone for business hour checking

    Returns:
        True if the event matches the general trigger
    """
    # General triggers only apply to MESSAGE events according to KB
    if not isinstance(event, MessageEvent):
        return False

    # Event type must be TIME
    if trigger_setting.event_type != WebhookTriggerEventType.TIME:
        return False

    # Check schedule constraints
    return matches_time_schedule(
        event, trigger_setting, business_hour_checker, organization_id, bot_timezone, organization_timezone
    )


def is_keyword_trigger(trigger_setting: WebhookTriggerSetting) -> bool:
    """Check if a trigger setting is a keyword trigger.

    Args:
        trigger_setting: The trigger setting to check

    Returns:
        True if this is a keyword trigger
    """
    # Keyword triggers are MESSAGE, POSTBACK, or BEACON events with trigger_code
    keyword_event_types = {
        WebhookTriggerEventType.MESSAGE,
        WebhookTriggerEventType.POSTBACK,
        WebhookTriggerEventType.BEACON,
        WebhookTriggerEventType.MESSAGE_EDITOR,
        WebhookTriggerEventType.POSTBACK_EDITOR,
    }

    return (
        trigger_setting.event_type in keyword_event_types
        and trigger_setting.trigger_code is not None
        and trigger_setting.trigger_code.strip() != ""
    )


def is_general_trigger(trigger_setting: WebhookTriggerSetting) -> bool:
    """Check if a trigger setting is a general (time-based) trigger.

    Args:
        trigger_setting: The trigger setting to check

    Returns:
        True if this is a general trigger
    """
    return trigger_setting.event_type == WebhookTriggerEventType.TIME


def is_welcome_trigger(trigger_setting: WebhookTriggerSetting) -> bool:
    """Check if a trigger setting is a welcome trigger.

    Args:
        trigger_setting: The trigger setting to check

    Returns:
        True if this is a welcome trigger
    """
    return trigger_setting.event_type == WebhookTriggerEventType.FOLLOW
