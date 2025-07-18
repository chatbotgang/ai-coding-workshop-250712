from typing import Optional, Tuple, Literal, List, Dict
from datetime import datetime, time
from pydantic import BaseModel
from internal.domain.auto_reply.auto_reply import AutoReply, AutoReplyEventType
from internal.domain.auto_reply.webhook_trigger import WebhookTriggerScheduleType, WebhookTriggerScheduleSettings

# Event model for trigger validation
class AutoReplyEvent(BaseModel):
    message_text: str
    channel_type: Literal["LINE", "FB", "IG"]
    timestamp: datetime
    ig_story_id: str | None = None

# Mock in-memory cache for auto-reply rules, keyed by channel type
AUTO_REPLY_RULES_CACHE: Dict[str, List[AutoReply]] = {
    # Example: 'LINE': [AutoReply(...), ...]
}

def normalize_keyword(text: str) -> str:
    """Normalize keyword for matching: trim and lowercase."""
    return text.strip().lower()

def is_time_in_range(start: time, end: time, check: time) -> bool:
    """Check if check is within [start, end), supporting midnight crossing."""
    if start <= end:
        return start <= check < end
    else:
        # Midnight crossing: e.g., 22:00-06:00
        return check >= start or check < end

def match_monthly(schedule_settings, event_dt: datetime) -> bool:
    for s in schedule_settings:
        if s.day == event_dt.day:
            start = time.fromisoformat(s.start_time)
            end = time.fromisoformat(s.end_time)
            if is_time_in_range(start, end, event_dt.time()):
                return True
    return False

def match_daily(schedule_settings, event_dt: datetime) -> bool:
    for s in schedule_settings:
        start = time.fromisoformat(s.start_time)
        end = time.fromisoformat(s.end_time)
        if is_time_in_range(start, end, event_dt.time()):
            return True
    return False

def match_business_hour(schedule_settings, event_dt: datetime) -> bool:
    weekday = event_dt.isoweekday()  # 1=Monday, 7=Sunday
    for s in schedule_settings:
        if hasattr(s, "weekday") and s.weekday == weekday:
            start = time.fromisoformat(s.start_time)
            end = time.fromisoformat(s.end_time)
            if is_time_in_range(start, end, event_dt.time()):
                return True
    return False

def validate_trigger(
    event: AutoReplyEvent,
) -> Tuple[Optional[AutoReply], Literal["ig_story_keyword_match", "ig_story_general_match", "keyword_match", "general_match", "no_match"]]:
    """
    Determines if an auto-reply should be triggered for the given event.
    Implements PRD/KB-compliant logic for IG Story, keyword, and general (time-based) triggers.
    Only MESSAGE events are in scope.
    """
    rules = AUTO_REPLY_RULES_CACHE.get(event.channel_type, [])
    normalized_message = normalize_keyword(event.message_text)
    ig_story_id = event.ig_story_id

    # 1. IG Story Keyword triggers (highest priority)
    for rule in rules:
        if (
            rule.event_type == AutoReplyEventType.KEYWORD
            and rule.ig_story_ids
            and ig_story_id is not None
            and ig_story_id in rule.ig_story_ids
            and rule.keywords
        ):
            for kw in rule.keywords:
                if normalize_keyword(kw) == normalized_message:
                    return rule, "ig_story_keyword_match"

    # 2. IG Story General triggers (priority 2)
    for rule in rules:
        if (
            rule.event_type == AutoReplyEventType.TIME
            and rule.ig_story_ids
            and ig_story_id is not None
            and ig_story_id in rule.ig_story_ids
            and rule.trigger_schedule_type
            and rule.trigger_schedule_settings
        ):
            settings = rule.trigger_schedule_settings.schedules
            if rule.trigger_schedule_type == WebhookTriggerScheduleType.MONTHLY:
                if match_monthly(settings, event.timestamp):
                    return rule, "ig_story_general_match"
            elif rule.trigger_schedule_type == WebhookTriggerScheduleType.DAILY:
                if match_daily(settings, event.timestamp):
                    return rule, "ig_story_general_match"
            elif rule.trigger_schedule_type == WebhookTriggerScheduleType.BUSINESS_HOUR:
                if match_business_hour(settings, event.timestamp):
                    return rule, "ig_story_general_match"
            elif rule.trigger_schedule_type == WebhookTriggerScheduleType.NON_BUSINESS_HOUR:
                # TODO: Implement non-business hour logic
                continue

    # 3. General Keyword triggers (priority 3, exclude IG Story-specific)
    for rule in rules:
        if (
            rule.event_type == AutoReplyEventType.KEYWORD
            and (not rule.ig_story_ids or len(rule.ig_story_ids) == 0)
            and rule.keywords
        ):
            for kw in rule.keywords:
                if normalize_keyword(kw) == normalized_message:
                    return rule, "keyword_match"

    # 4. General (time-based) triggers (priority 4, exclude IG Story-specific)
    general_rules = [
        r for r in rules
        if r.event_type == AutoReplyEventType.TIME and (not r.ig_story_ids or len(r.ig_story_ids) == 0) and r.trigger_schedule_type and r.trigger_schedule_settings
    ]
    priority_order = [
        WebhookTriggerScheduleType.MONTHLY,
        WebhookTriggerScheduleType.BUSINESS_HOUR,
        WebhookTriggerScheduleType.NON_BUSINESS_HOUR,
        WebhookTriggerScheduleType.DAILY,
    ]
    for schedule_type in priority_order:
        for rule in general_rules:
            if rule.trigger_schedule_type == schedule_type:
                settings = rule.trigger_schedule_settings.schedules
                if schedule_type == WebhookTriggerScheduleType.MONTHLY:
                    if match_monthly(settings, event.timestamp):
                        return rule, "general_match"
                elif schedule_type == WebhookTriggerScheduleType.DAILY:
                    if match_daily(settings, event.timestamp):
                        return rule, "general_match"
                elif schedule_type == WebhookTriggerScheduleType.BUSINESS_HOUR:
                    if match_business_hour(settings, event.timestamp):
                        return rule, "general_match"
                elif schedule_type == WebhookTriggerScheduleType.NON_BUSINESS_HOUR:
                    # TODO: Implement non-business hour logic
                    continue
    # 5. No match
    return None, "no_match"

# Example usage/test (to be replaced with real tests)
if __name__ == "__main__":
    from datetime import datetime
    from internal.domain.auto_reply.auto_reply import AutoReply, AutoReplyStatus, AutoReplyEventType
    from internal.domain.auto_reply.webhook_trigger import WebhookTriggerScheduleType, WebhookTriggerScheduleSettings

    # Add a keyword rule for LINE
    AUTO_REPLY_RULES_CACHE["LINE"] = [
        AutoReply(
            id=1,
            organization_id=1,
            name="Hello Rule",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD,
            priority=1,
            keywords=["hello", "hi"],
            trigger_schedule_type=None,
            trigger_schedule_settings=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
    ]
    # Test keyword match
    rule, result = validate_trigger(AutoReplyEvent(message_text="  HeLLo  ", channel_type="LINE", timestamp=datetime.now()))
    print(rule, result)  # Should print the rule and 'keyword_match'
    # Test no match
    rule, result = validate_trigger(AutoReplyEvent(message_text="bye", channel_type="LINE", timestamp=datetime.now()))
    print(rule, result)  # Should print None and 'no_match' 