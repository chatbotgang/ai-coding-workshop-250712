"""Priority sorting functionality for auto-reply triggers."""

from internal.domain.auto_reply.auto_reply import AutoReply, AutoReplyEventType
from internal.domain.auto_reply.webhook_trigger import WebhookTriggerSetting


def sort_triggers_by_priority(
    trigger_settings: list[WebhookTriggerSetting], auto_replies: dict[int, AutoReply]
) -> list[WebhookTriggerSetting]:
    """Sort trigger settings by priority according to PRD rules.

    Priority Logic (per PRD Part 2):
    1. IG Story Keyword (Priority 1 - highest)
    2. IG Story General (Priority 2)
    3. General Keyword (Priority 3)
    4. General Time-based (Priority 4 - lowest)
    5. Within same category, sort by AutoReply.priority (lower number = higher priority)

    Args:
        trigger_settings: List of webhook trigger settings to sort
        auto_replies: Map of auto_reply_id -> AutoReply for priority lookup

    Returns:
        Sorted list of trigger settings by priority
    """

    def get_priority_key(trigger_setting: WebhookTriggerSetting) -> tuple[int, int]:
        """Get priority key for sorting.

        Returns:
            Tuple of (category_priority, auto_reply_priority)
            - category_priority: 0=IG Story Keyword, 1=IG Story General, 2=General Keyword, 3=General Time-based
            - auto_reply_priority: AutoReply.priority value (lower = higher priority)
        """
        auto_reply = auto_replies.get(trigger_setting.auto_reply_id)
        if not auto_reply:
            # If AutoReply not found, treat as lowest priority
            return (999, 999)

        # Check if this is an IG Story trigger
        is_ig_story_trigger = auto_reply.ig_story_ids is not None and len(auto_reply.ig_story_ids) > 0

        # Determine category priority based on PRD Part 2 requirements
        if is_ig_story_trigger and auto_reply.event_type == AutoReplyEventType.KEYWORD:
            category_priority = 0  # IG Story Keyword (Priority 1 - highest)
        elif is_ig_story_trigger and auto_reply.event_type == AutoReplyEventType.TIME:
            category_priority = 1  # IG Story General (Priority 2)
        elif not is_ig_story_trigger and auto_reply.event_type == AutoReplyEventType.KEYWORD:
            category_priority = 2  # General Keyword (Priority 3)
        elif not is_ig_story_trigger and auto_reply.event_type == AutoReplyEventType.TIME:
            category_priority = 3  # General Time-based (Priority 4 - lowest)
        else:
            # Other event types get lower priority
            category_priority = 4

        # Within same category, use AutoReply.priority (lower number = higher priority)
        auto_reply_priority = auto_reply.priority

        return (category_priority, auto_reply_priority)

    # Sort using the priority key
    return sorted(trigger_settings, key=get_priority_key)
