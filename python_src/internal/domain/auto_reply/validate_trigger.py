"""Main validate_trigger function implementation."""

from datetime import datetime
from typing import Optional

from internal.domain.auto_reply.auto_reply import AutoReply, AutoReplyEventType, AutoReplyStatus
from internal.domain.auto_reply.webhook_trigger import WebhookTriggerSetting, WebhookTriggerScheduleSettings
from internal.domain.auto_reply.keyword_matcher import match_keywords
from internal.domain.auto_reply.priority_sorter import sort_triggers_by_priority


def validate_trigger(
    trigger_settings: list[WebhookTriggerSetting], 
    auto_replies: dict[int, AutoReply],
    message_content: str, 
    event_time: datetime,
    organization_timezone: str = "Asia/Taipei",
    ig_story_id: str | None = None
) -> WebhookTriggerSetting | None:
    """Validate triggers and return the highest priority matching trigger.
    
    This function implements the core trigger validation logic per PRD requirements:
    
    1. Priority System (PRD Priority Logic):
       - IG Story Keyword (Priority 1 - highest)
       - IG Story General (Priority 2)  
       - General Keyword (Priority 3)
       - General Time-based (Priority 4 - lowest)
       - Within same category, lower priority number = higher priority
       - Only the first matching trigger is executed
    
    2. IG Story Logic (PRD Part 2):
       - IG Story triggers require ig_story_id parameter
       - IG Story keyword: matches keyword AND story ID
       - IG Story general: matches schedule AND story ID
       - IG Story triggers excluded from general validation
    
    3. Keyword Matching (PRD Story 1 & 2):
       - Exact match, case insensitive, trim spaces
       - Support multiple keywords per rule
       - Partial matches do not trigger
    
    4. Time-based Logic (PRD Story 3):
       - Daily schedule support with midnight crossing
       - Monthly schedule support  
       - Business hours (placeholder implementation)
    
    5. Message Content Handling (PRD Story 5):
       - KEYWORD triggers: check message content against keywords
       - TIME triggers: trigger regardless of message content if schedule matches
    
    Args:
        trigger_settings: List of webhook trigger settings to evaluate
        auto_replies: Map of auto_reply_id -> AutoReply for trigger lookup
        message_content: The message content to check against keywords
        event_time: The time when the message was received (timezone-aware preferred)
        organization_timezone: Organization's timezone for time-based triggers (default: "Asia/Taipei")
        ig_story_id: IG story ID if message is a reply to story (default: None)
        
    Returns:
        The highest priority WebhookTriggerSetting that matches, or None if no match
        
    PRD Test Cases covered:
    - [B-P0-7-Test2,3,4,5]: Keyword matching logic
    - [Multiple-Keywords-Test1,2,3]: Multiple keywords support
    - [B-P0-6-Test3,4]: Daily/Monthly schedule logic
    - [Priority-Test1,2,3]: Priority system (KEYWORD > TIME)
    - [Message-Content-Test1,2,3]: Message content handling
    - [IG-Story-*]: IG Story specific logic (PRD Part 2)
    """
    if not trigger_settings:
        return None
    
    # Step 1: Filter only enabled triggers
    active_triggers = [
        trigger for trigger in trigger_settings 
        if trigger.enable
    ]
    
    if not active_triggers:
        return None
    
    # Step 2: Sort triggers by priority (KEYWORD > TIME, then by priority number)
    sorted_triggers = sort_triggers_by_priority(active_triggers, auto_replies)
    
    # Step 3: Evaluate triggers in priority order, return first match
    for trigger_setting in sorted_triggers:
        auto_reply = auto_replies.get(trigger_setting.auto_reply_id)
        if not auto_reply or auto_reply.status != AutoReplyStatus.ACTIVE:
            continue
            
        # Check if this trigger matches
        if _evaluate_trigger(trigger_setting, auto_reply, message_content, event_time, organization_timezone, ig_story_id):
            return trigger_setting
    
    return None


def _evaluate_trigger(
    trigger_setting: WebhookTriggerSetting,
    auto_reply: AutoReply, 
    message_content: str,
    event_time: datetime,
    organization_timezone: str,
    ig_story_id: str | None = None
) -> bool:
    """Evaluate a single trigger to see if it matches.
    
    Args:
        trigger_setting: The trigger setting to evaluate
        auto_reply: The corresponding AutoReply configuration
        message_content: The message content
        event_time: The event time (timezone-aware preferred)
        organization_timezone: Organization's timezone for time-based triggers
        ig_story_id: IG story ID if message is a reply to story
        
    Returns:
        True if the trigger matches, False otherwise
    """
    # IG Story specific logic
    is_ig_story_trigger = auto_reply.ig_story_ids is not None and len(auto_reply.ig_story_ids) > 0
    
    if is_ig_story_trigger:
        # IG Story triggers require ig_story_id and matching story ID
        if ig_story_id is None or ig_story_id not in auto_reply.ig_story_ids:
            return False
    else:
        # General triggers: exclude IG story messages (when ig_story_id is provided)
        # This implements IG Story Exclusion Logic per PRD Story 11
        if ig_story_id is not None:
            return False
    
    # KEYWORD triggers: check message content against keywords
    if auto_reply.event_type == AutoReplyEventType.KEYWORD:
        return match_keywords(auto_reply.keywords, message_content)
    
    # TIME triggers: check schedule, ignore message content
    elif auto_reply.event_type == AutoReplyEventType.TIME:
        return _check_schedule_match(auto_reply, event_time, organization_timezone)
    
    # Other event types not supported in current scope
    return False


def _check_schedule_match(auto_reply: AutoReply, event_time: datetime, organization_timezone: str) -> bool:
    """Check if the current time matches the auto-reply schedule.
    
    Args:
        auto_reply: The AutoReply with schedule configuration
        event_time: The event time to check against (timezone-aware preferred)
        organization_timezone: Organization's timezone for schedule evaluation
        
    Returns:
        True if the schedule matches, False otherwise
    """
    if not auto_reply.trigger_schedule_settings:
        # No schedule configured, always match
        return True
    
    # Get schedule settings
    schedule_settings = auto_reply.trigger_schedule_settings
    if not schedule_settings.schedules:
        return True
    
    # Check if any schedule in the settings is active
    for schedule in schedule_settings.schedules:
        try:
            if schedule.is_active(event_time, organization_timezone):
                return True
        except Exception:
            # If schedule check fails, continue to next schedule
            continue
    
    return False