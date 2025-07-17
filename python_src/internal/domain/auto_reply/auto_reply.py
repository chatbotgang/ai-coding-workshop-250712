"""Auto Reply domain models."""

from datetime import datetime, time
from enum import StrEnum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from internal.domain.auto_reply.webhook_trigger import WebhookTriggerScheduleSettings, WebhookTriggerScheduleType
from internal.domain.auto_reply.webhook_event import WebhookEvent, MessageEvent, ChannelType


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
    IG_STORY_KEYWORD = "ig_story_keyword"
    IG_STORY_TIME = "ig_story_time"
    DEFAULT = "default"


class AutoReply(BaseModel):
    """Auto reply domain model.

    Represents an omnichannel rule that associates several
    WebhookTriggerSetting instances. It defines the high-level
    auto-reply configuration for an organization.
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
    ig_story_ids: Optional[List[str]] = Field(None, description="List of IG Story IDs this rule applies to")
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic configuration."""

        use_enum_values = True

    def is_ig_story_specific(self) -> bool:
        """Check if this rule is IG Story-specific."""
        return self.ig_story_ids is not None and len(self.ig_story_ids) > 0


class AutoReplyResponse(BaseModel):
    """Auto reply response model."""

    reply_text: str
    reply_type: str
    confidence_score: float
    matched_keyword: Optional[str] = None

    class Config:
        """Pydantic configuration."""

        use_enum_values = True


class TriggerType(StrEnum):
    """Trigger type enumeration for validation results."""

    IG_STORY_KEYWORD = "ig_story_keyword"
    IG_STORY_GENERAL = "ig_story_general"
    KEYWORD = "keyword"
    GENERAL_TIME = "general_time"
    FOLLOW = "follow"
    POSTBACK = "postback"


class TriggerValidationResult(BaseModel):
    """Result of trigger validation containing matched rule and context."""

    matched_rule: AutoReply = Field(..., description="The auto-reply rule that matched")
    trigger_type: TriggerType = Field(..., description="Type of trigger that matched")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Match confidence score")
    matched_keyword: Optional[str] = Field(None, description="Keyword that triggered the match")
    reply_content: str = Field(..., description="Content to reply with")
    should_send_reply: bool = Field(..., description="Whether reply should be sent considering all constraints")

    class Config:
        """Pydantic configuration."""

        use_enum_values = True


class TriggerMatchContext(BaseModel):
    """Context information for trigger matching process."""

    event_content: Optional[str] = Field(None, description="Extracted content from the event")
    event_time: datetime = Field(..., description="When the event occurred")
    user_id: str = Field(..., description="User identifier from the channel")
    channel_type: ChannelType = Field(..., description="Channel type (LINE/FB/IG)")
    message_id: Optional[str] = Field(None, description="Message identifier if applicable")
    ig_story_id: Optional[str] = Field(None, description="IG Story ID if message is a reply to story")

    class Config:
        """Pydantic configuration."""

        use_enum_values = True


def keyword_auto_reply(message_text: str) -> Optional[Dict]:
    """
    Handle keyword-based auto-replies for MESSAGE events.

    Args:
        message_text (str): The text content of the user's message

    Returns:
        Dict with structure:
        {
            "reply_text": str,
            "reply_type": "keyword",
            "confidence_score": float (0.0-1.0),
            "matched_keyword": str
        }
        Or None if no keyword match found
    """
    if not message_text:
        return None

    # Normalize message text for matching
    normalized_text = message_text.strip().lower()

    # Define keyword mappings based on business requirements
    keyword_mappings = {
        # Greeting keywords
        "hello": {"reply_text": "Hello! How can I help you today?", "confidence_score": 1.0},
        "hi": {"reply_text": "Hi there! What can I do for you?", "confidence_score": 1.0},
        "hey": {"reply_text": "Hey! How can I assist you?", "confidence_score": 1.0},
        "good morning": {"reply_text": "Good morning! How can I help you today?", "confidence_score": 1.0},
        "good afternoon": {"reply_text": "Good afternoon! What can I assist you with?", "confidence_score": 1.0},
        # Help keywords
        "help": {"reply_text": "I'm here to help! What do you need assistance with?", "confidence_score": 1.0},
        "support": {"reply_text": "Our support team is ready to assist you. How can we help?", "confidence_score": 1.0},
        "assistance": {
            "reply_text": "I'm happy to provide assistance. What do you need help with?",
            "confidence_score": 1.0,
        },
        # Product/Service keywords
        "price": {
            "reply_text": "For pricing information, please visit our website or contact our sales team.",
            "confidence_score": 1.0,
        },
        "pricing": {
            "reply_text": "For pricing information, please visit our website or contact our sales team.",
            "confidence_score": 1.0,
        },
        "cost": {
            "reply_text": "For cost details, please reach out to our sales team for a personalized quote.",
            "confidence_score": 1.0,
        },
        "product": {
            "reply_text": "We offer a variety of products. What specific product are you interested in?",
            "confidence_score": 1.0,
        },
        "service": {
            "reply_text": "We provide comprehensive services. What kind of service are you looking for?",
            "confidence_score": 1.0,
        },
        # Contact keywords
        "contact": {
            "reply_text": "You can reach us at: Email: support@company.com, Phone: (555) 123-4567",
            "confidence_score": 1.0,
        },
        "phone": {
            "reply_text": "Our phone number is: (555) 123-4567. We're available Monday-Friday, 9AM-5PM.",
            "confidence_score": 1.0,
        },
        "email": {
            "reply_text": "You can email us at: support@company.com. We'll respond within 24 hours.",
            "confidence_score": 1.0,
        },
        # Business hours keywords
        "hours": {
            "reply_text": "Our business hours are Monday-Friday, 9AM-5PM. We're closed on weekends.",
            "confidence_score": 1.0,
        },
        "open": {
            "reply_text": "We're open Monday-Friday, 9AM-5PM. How can we help you today?",
            "confidence_score": 1.0,
        },
        # FAQ keywords
        "faq": {
            "reply_text": "You can find frequently asked questions on our website FAQ section.",
            "confidence_score": 1.0,
        },
        "question": {
            "reply_text": "I'm here to answer your questions! What would you like to know?",
            "confidence_score": 1.0,
        },
    }

    # Check for exact keyword matches first (full phrase matching)
    for keyword, response_data in keyword_mappings.items():
        if keyword in normalized_text:
            return {
                "reply_text": response_data["reply_text"],
                "reply_type": "keyword",
                "confidence_score": response_data["confidence_score"],
                "matched_keyword": keyword,
            }

    # No keyword match found
    return None


def general_auto_reply(message_text: str) -> Optional[Dict]:
    """
    Handle general/fallback auto-replies for MESSAGE events.

    Args:
        message_text (str): The text content of the user's message

    Returns:
        Dict with structure:
        {
            "reply_text": str,
            "reply_type": "general",
            "confidence_score": float (0.0-1.0),
            "matched_keyword": None
        }
        Or None if no general reply available
    """
    if not message_text:
        return None

    # Define general reply options
    general_replies = [
        "Thank you for your message! A team member will get back to you soon.",
        "We've received your message and will respond shortly. Thank you for your patience!",
        "Thanks for reaching out! We'll be in touch with you as soon as possible.",
        "Your message is important to us. We'll respond within 24 hours.",
        "Thank you for contacting us! Someone from our team will assist you shortly.",
    ]

    # Simple logic: return first general reply
    # In a production system, this could be more sophisticated
    # (random selection, time-based, user history, etc.)
    return {
        "reply_text": general_replies[0],
        "reply_type": "general",
        "confidence_score": 0.8,  # Lower confidence for general replies
        "matched_keyword": None,
    }


def validate_trigger(
    event: WebhookEvent, auto_reply_rules: List[AutoReply], current_time: Optional[datetime] = None
) -> Optional[TriggerValidationResult]:
    """
    Validate if any auto-reply trigger should be activated for the given event.

    This function implements the core trigger logic for Feature 1 & 2:
    LINE/FB/IG Auto-Reply with support for keyword-based, general time-based,
    and IG Story-specific triggers across multiple platforms.

    Priority System (as per PRD Part 2):
    1. IG Story Keyword triggers (Priority 1 - highest)
    2. IG Story General triggers (Priority 2)
    3. General Keyword triggers (Priority 3)
    4. General Time-based triggers (Priority 4 - lowest)

    Args:
        event: The webhook event from any supported platform (LINE/FB/IG)
        auto_reply_rules: List of active auto-reply rules for the
            organization/channel
        current_time: Current time for testing purposes
            (defaults to datetime.now())

    Returns:
        TriggerValidationResult if a trigger matches, None if no triggers match

    Raises:
        ValueError: If event type is not supported or rules are invalid

    Example:
        >>> from internal.domain.auto_reply.webhook_event import (
        ...     MessageEvent, ChannelType
        ... )
        >>> from datetime import datetime
        >>>
        >>> # Create an IG Story message event
        >>> event = MessageEvent(
        ...     event_id="msg_123",
        ...     channel_type=ChannelType.INSTAGRAM,
        ...     user_id="user_456",
        ...     timestamp=datetime.now(),
        ...     content="hello",
        ...     message_id="ig_msg_789",
        ...     ig_story_id="story123"
        ... )
        >>>
        >>> # Create IG Story auto-reply rule
        >>> ig_story_rule = AutoReply(
        ...     id=1,
        ...     organization_id=100,
        ...     name="IG Story Greeting",
        ...     status=AutoReplyStatus.ACTIVE,
        ...     event_type=AutoReplyEventType.IG_STORY_KEYWORD,
        ...     priority=1,
        ...     keywords=["hello", "hi"],
        ...     ig_story_ids=["story123"],
        ...     created_at=datetime.now(),
        ...     updated_at=datetime.now()
        ... )
        >>>
        >>> # Validate trigger
        >>> result = validate_trigger(event, [ig_story_rule])
        >>>
        >>> if result:
        ...     print(f"Matched: {result.trigger_type}")
        ...     print(f"Reply: {result.reply_content}")
        ...     print(f"Keyword: {result.matched_keyword}")
    """
    if current_time is None:
        current_time = datetime.now()

    # Extract context from the event
    context = _extract_trigger_context(event, current_time)

    # Filter active rules only
    active_rules = [rule for rule in auto_reply_rules if rule.status == AutoReplyStatus.ACTIVE]

    # Priority 1: Check IG Story Keyword triggers first (highest priority)
    ig_story_keyword_result = _validate_ig_story_keyword_triggers(context, active_rules)
    if ig_story_keyword_result:
        return ig_story_keyword_result

    # Priority 2: Check IG Story General triggers
    ig_story_general_result = _validate_ig_story_general_triggers(context, active_rules, current_time)
    if ig_story_general_result:
        return ig_story_general_result

    # Priority 3: Check General Keyword triggers
    keyword_result = _validate_keyword_triggers(context, active_rules)
    if keyword_result:
        return keyword_result

    # Priority 4: Check general time-based triggers (lowest priority)
    general_result = _validate_general_time_triggers(context, active_rules, current_time)
    if general_result:
        return general_result

    # No triggers matched
    return None


def _extract_trigger_context(event: WebhookEvent, current_time: datetime) -> TriggerMatchContext:
    """
    Extract trigger matching context from webhook event.

    Handles different event types and platforms to create unified context.

    Args:
        event: The webhook event
        current_time: Current timestamp

    Returns:
        TriggerMatchContext with extracted information

    Raises:
        ValueError: If event type is not supported
    """
    if isinstance(event, MessageEvent):
        return TriggerMatchContext(
            event_content=event.content,
            event_time=event.timestamp,
            user_id=event.user_id,
            channel_type=event.channel_type,
            message_id=event.message_id,
            ig_story_id=event.ig_story_id,
        )
    else:
        # For future event types (PostbackEvent, FollowEvent, etc.)
        raise ValueError(f"Unsupported event type: {type(event)}")


def _validate_ig_story_keyword_triggers(
    context: TriggerMatchContext, active_rules: List[AutoReply]
) -> Optional[TriggerValidationResult]:
    """
    Validate IG Story keyword-based triggers with exact match logic.

    Implements PRD requirements for IG Story keyword triggers:
    - Case insensitive matching
    - Trim leading/trailing spaces
    - Exact match only (not partial)
    - Multiple keywords support
    - Must match both keyword AND story ID

    Args:
        context: Trigger matching context
        active_rules: List of active auto-reply rules

    Returns:
        TriggerValidationResult if IG Story keyword matches, None otherwise
    """
    if not context.event_content or not context.ig_story_id:
        return None

    # Normalize message text for matching (case insensitive + trim)
    normalized_content = context.event_content.strip().lower()

    # Filter IG Story keyword-based rules
    ig_story_keyword_rules = [
        rule
        for rule in active_rules
        if rule.event_type == AutoReplyEventType.IG_STORY_KEYWORD and rule.keywords and rule.is_ig_story_specific()
    ]

    # Check each IG Story keyword rule
    for rule in ig_story_keyword_rules:
        # First check if the story ID matches
        if context.ig_story_id not in rule.ig_story_ids:
            continue

        # Then check keywords
        for keyword in rule.keywords:
            # Normalize keyword for comparison
            normalized_keyword = keyword.strip().lower()

            # Exact match check (as per PRD requirement)
            if normalized_content == normalized_keyword:
                # Generate appropriate reply content
                reply_content = _generate_reply_content(rule, TriggerType.IG_STORY_KEYWORD, keyword)

                return TriggerValidationResult(
                    matched_rule=rule,
                    trigger_type=TriggerType.IG_STORY_KEYWORD,
                    confidence_score=1.0,
                    matched_keyword=keyword,
                    reply_content=reply_content,
                    should_send_reply=True,
                )

    return None


def _validate_ig_story_general_triggers(
    context: TriggerMatchContext, active_rules: List[AutoReply], current_time: datetime
) -> Optional[TriggerValidationResult]:
    """
    Validate IG Story general triggers.

    Implements PRD requirements for IG Story general triggers:
    - Daily schedule
    - Monthly schedule
    - Business hours
    - Must match both schedule AND story ID

    Args:
        context: Trigger matching context
        active_rules: List of active auto-reply rules
        current_time: Current timestamp for schedule validation

    Returns:
        TriggerValidationResult if IG Story schedule matches, None otherwise

    Raises:
        ValueError: If event type is not supported or rules are invalid

    Example:
        >>> from internal.domain.auto_reply.webhook_event import (
        ...     MessageEvent, ChannelType
        ... )
        >>> from datetime import datetime
        >>>
        >>> # Create a message event
        >>> event = MessageEvent(
        ...     event_id="msg_123",
        ...     channel_type=ChannelType.LINE,
        ...     user_id="user_456",
        ...     timestamp=datetime.now(),
        ...     content="hello",
        ...     message_id="line_msg_789"
        ... )
        >>>
        >>> # Create auto-reply rules
        >>> time_rule = AutoReply(
        ...     id=2,
        ...     organization_id=100,
        ...     name="IG Story Business Hours",
        ...     status=AutoReplyStatus.ACTIVE,
        ...     event_type=AutoReplyEventType.IG_STORY_TIME,
        ...     priority=2,
        ...     trigger_schedule_type=WebhookTriggerScheduleType.BUSINESS_HOUR,
        ...     created_at=datetime.now(),
        ...     updated_at=datetime.now()
        ... )
        >>>
        >>> # Validate trigger
        >>> result = validate_trigger(event, [time_rule])
        >>>
        >>> if result:
        ...     print(f"Matched: {result.trigger_type}")
        ...     print(f"Reply: {result.reply_content}")
    """
    if not context.ig_story_id:
        return None

    # Filter IG Story time-based rules
    ig_story_time_rules = [
        rule
        for rule in active_rules
        if (
            rule.event_type == AutoReplyEventType.IG_STORY_TIME
            and rule.trigger_schedule_type
            and rule.is_ig_story_specific()
        )
    ]

    if not ig_story_time_rules:
        return None

    # Group by schedule type and check in priority order
    # Priority order (as per legacy documentation):
    # 1. MONTHLY (highest)
    # 2. BUSINESS_HOUR
    # 3. NON_BUSINESS_HOUR
    # 4. DAILY (lowest)

    priority_order = [
        WebhookTriggerScheduleType.MONTHLY,
        WebhookTriggerScheduleType.BUSINESS_HOUR,
        WebhookTriggerScheduleType.NON_BUSINESS_HOUR,
        WebhookTriggerScheduleType.DAILY,
    ]

    for schedule_type in priority_order:
        matching_rules = [rule for rule in ig_story_time_rules if rule.trigger_schedule_type == schedule_type]

        for rule in matching_rules:
            # First check if the story ID matches
            if context.ig_story_id not in rule.ig_story_ids:
                continue

            # Then check schedule
            if _check_schedule_match(rule, current_time):
                # Generate appropriate reply content
                reply_content = _generate_reply_content(rule, TriggerType.IG_STORY_GENERAL)

                return TriggerValidationResult(
                    matched_rule=rule,
                    trigger_type=TriggerType.IG_STORY_GENERAL,
                    confidence_score=0.8,  # Lower confidence for IG Story time-based
                    matched_keyword=None,
                    reply_content=reply_content,
                    should_send_reply=True,
                )

    return None


def _validate_keyword_triggers(
    context: TriggerMatchContext, active_rules: List[AutoReply]
) -> Optional[TriggerValidationResult]:
    """
    Validate keyword-based triggers with exact match logic.

    Implements PRD requirements:
    - Case insensitive matching
    - Trim leading/trailing spaces
    - Exact match only (not partial)
    - Multiple keywords support

    Args:
        context: Trigger matching context
        active_rules: List of active auto-reply rules

    Returns:
        TriggerValidationResult if keyword matches, None otherwise
    """
    if not context.event_content:
        return None

    # Normalize message text for matching (case insensitive + trim)
    normalized_content = context.event_content.strip().lower()

    # Filter keyword-based rules
    keyword_rules = [rule for rule in active_rules if rule.event_type == AutoReplyEventType.KEYWORD and rule.keywords]

    # Check each keyword rule
    for rule in keyword_rules:
        for keyword in rule.keywords:
            # Normalize keyword for comparison
            normalized_keyword = keyword.strip().lower()

            # Exact match check (as per PRD requirement)
            if normalized_content == normalized_keyword:
                # Generate appropriate reply content
                reply_content = _generate_reply_content(rule, TriggerType.KEYWORD, keyword)

                return TriggerValidationResult(
                    matched_rule=rule,
                    trigger_type=TriggerType.KEYWORD,
                    confidence_score=1.0,
                    matched_keyword=keyword,
                    reply_content=reply_content,
                    should_send_reply=True,
                )

    return None


def _validate_general_time_triggers(
    context: TriggerMatchContext, active_rules: List[AutoReply], current_time: datetime
) -> Optional[TriggerValidationResult]:
    """
    Validate general time-based triggers.

    Implements PRD requirements for time-based triggers:
    - Daily schedule
    - Monthly schedule
    - Business hours
    - Priority system for time triggers

    Args:
        context: Trigger matching context
        active_rules: List of active auto-reply rules
        current_time: Current timestamp for schedule validation

    Returns:
        TriggerValidationResult if schedule matches, None otherwise

    Raises:
        ValueError: If event type is not supported or rules are invalid

    Example:
        >>> from internal.domain.auto_reply.webhook_event import (
        ...     MessageEvent, ChannelType
        ... )
        >>> from datetime import datetime
        >>>
        >>> # Create a message event
        >>> event = MessageEvent(
        ...     event_id="msg_123",
        ...     channel_type=ChannelType.LINE,
        ...     user_id="user_456",
        ...     timestamp=datetime.now(),
        ...     content="hello",
        ...     message_id="line_msg_789"
        ... )
        >>>
        >>> # Create auto-reply rules
        >>> time_rule = AutoReply(
        ...     id=2,
        ...     organization_id=100,
        ...     name="Business Hours",
        ...     status=AutoReplyStatus.ACTIVE,
        ...     event_type=AutoReplyEventType.TIME,
        ...     priority=2,
        ...     trigger_schedule_type=WebhookTriggerScheduleType.BUSINESS_HOUR,
        ...     created_at=datetime.now(),
        ...     updated_at=datetime.now()
        ... )
        >>>
        >>> # Validate trigger
        >>> result = validate_trigger(event, [time_rule])
        >>>
        >>> if result:
        ...     print(f"Matched: {result.trigger_type}")
        ...     print(f"Reply: {result.reply_content}")
    """
    # Filter time-based rules
    time_rules = [
        rule for rule in active_rules if (rule.event_type == AutoReplyEventType.TIME and rule.trigger_schedule_type)
    ]

    if not time_rules:
        return None

    # Group by schedule type and check in priority order
    # Priority order (as per legacy documentation):
    # 1. MONTHLY (highest)
    # 2. BUSINESS_HOUR
    # 3. NON_BUSINESS_HOUR
    # 4. DAILY (lowest)

    priority_order = [
        WebhookTriggerScheduleType.MONTHLY,
        WebhookTriggerScheduleType.BUSINESS_HOUR,
        WebhookTriggerScheduleType.NON_BUSINESS_HOUR,
        WebhookTriggerScheduleType.DAILY,
    ]

    for schedule_type in priority_order:
        matching_rules = [rule for rule in time_rules if rule.trigger_schedule_type == schedule_type]

        for rule in matching_rules:
            if _check_schedule_match(rule, current_time):
                # Generate appropriate reply content
                reply_content = _generate_reply_content(rule, TriggerType.GENERAL_TIME)

                return TriggerValidationResult(
                    matched_rule=rule,
                    trigger_type=TriggerType.GENERAL_TIME,
                    confidence_score=0.8,  # Lower confidence for time-based
                    matched_keyword=None,
                    reply_content=reply_content,
                    should_send_reply=True,
                )

    return None


def _check_schedule_match(rule: AutoReply, current_time: datetime) -> bool:
    """
    Check if current time matches the rule's schedule.

    Implements full schedule validation for all schedule types based on
    legacy documentation and PRD requirements.

    Args:
        rule: Auto-reply rule with schedule configuration
        current_time: Current timestamp

    Returns:
        True if schedule matches, False otherwise
    """
    if not rule.trigger_schedule_type or not rule.trigger_schedule_settings:
        return False

    schedule_settings = rule.trigger_schedule_settings.schedules
    if not schedule_settings:
        return False

    if rule.trigger_schedule_type == WebhookTriggerScheduleType.DAILY:
        return _check_daily_schedule(schedule_settings, current_time)
    elif rule.trigger_schedule_type == WebhookTriggerScheduleType.MONTHLY:
        return _check_monthly_schedule(schedule_settings, current_time)
    elif rule.trigger_schedule_type == WebhookTriggerScheduleType.BUSINESS_HOUR:
        return _check_business_hour_schedule(current_time)
    elif rule.trigger_schedule_type == WebhookTriggerScheduleType.NON_BUSINESS_HOUR:
        return _check_non_business_hour_schedule(current_time)
    elif rule.trigger_schedule_type == WebhookTriggerScheduleType.DATE_RANGE:
        return _check_date_range_schedule(schedule_settings, current_time)

    return False


def _check_daily_schedule(schedules: List[Dict], current_time: datetime) -> bool:
    """
    Check if current time matches daily schedule.

    Supports multiple time ranges within a day and midnight crossing.

    Args:
        schedules: List of daily schedule settings (could be Pydantic objects or dicts)
        current_time: Current timestamp

    Returns:
        True if current time is within any daily schedule range
    """
    current_time_obj = current_time.time()

    for schedule in schedules:
        # Handle both Pydantic objects and dictionary formats
        if hasattr(schedule, "start_time") and hasattr(schedule, "end_time"):
            # Pydantic object (DailySchedule)
            start_time_str = schedule.start_time
            end_time_str = schedule.end_time
        else:
            # Dictionary format
            start_time_str = schedule.get("start_time")
            end_time_str = schedule.get("end_time")

        if not start_time_str or not end_time_str:
            continue

        try:
            start_time = time.fromisoformat(start_time_str)
            end_time = time.fromisoformat(end_time_str)

            # Handle midnight crossing (e.g., 22:00 to 06:00)
            if start_time > end_time:
                # Range crosses midnight
                if current_time_obj >= start_time or current_time_obj < end_time:
                    return True
            else:
                # Normal range within same day
                if start_time <= current_time_obj < end_time:
                    return True

        except ValueError:
            # Invalid time format, skip this schedule
            continue

    return False


def _check_monthly_schedule(schedules: List[Dict], current_time: datetime) -> bool:
    """
    Check if current time matches monthly schedule.

    Args:
        schedules: List of monthly schedule settings (could be Pydantic objects or dicts)
        current_time: Current timestamp

    Returns:
        True if current day and time matches any monthly schedule
    """
    current_day = current_time.day
    current_time_obj = current_time.time()

    for schedule in schedules:
        # Handle both Pydantic objects and dictionary formats
        if hasattr(schedule, "day") and hasattr(schedule, "start_time") and hasattr(schedule, "end_time"):
            # Pydantic object (MonthlySchedule)
            day = schedule.day
            start_time_str = schedule.start_time
            end_time_str = schedule.end_time
        else:
            # Dictionary format
            day = schedule.get("day")
            start_time_str = schedule.get("start_time")
            end_time_str = schedule.get("end_time")

        if day != current_day:
            continue

        if not start_time_str or not end_time_str:
            continue

        try:
            start_time = time.fromisoformat(start_time_str)
            end_time = time.fromisoformat(end_time_str)

            # Check if current time is within the range
            if start_time <= current_time_obj < end_time:
                return True

        except ValueError:
            # Invalid time format, skip this schedule
            continue

    return False


def _check_business_hour_schedule(current_time: datetime) -> bool:
    """
    Check if current time is within business hours.

    For now, implements basic business hours (Mon-Fri, 9AM-5PM).
    In production, this would fetch BusinessHour records from the database.

    Args:
        current_time: Current timestamp

    Returns:
        True if current time is within business hours
    """
    # Basic business hours: Monday-Friday, 9AM-5PM
    weekday = current_time.isoweekday()  # 1=Monday, 7=Sunday
    if weekday > 5:  # Weekend
        return False

    current_time_obj = current_time.time()
    business_start = time(9, 0)  # 9:00 AM
    business_end = time(17, 0)  # 5:00 PM

    return business_start <= current_time_obj < business_end


def _check_non_business_hour_schedule(current_time: datetime) -> bool:
    """
    Check if current time is outside business hours.

    Args:
        current_time: Current timestamp

    Returns:
        True if current time is outside business hours
    """
    return not _check_business_hour_schedule(current_time)


def _check_date_range_schedule(schedules: List[Dict], current_time: datetime) -> bool:
    """
    Check if current date is within date range schedule.

    Args:
        schedules: List of date range schedule settings (could be Pydantic objects or dicts)
        current_time: Current timestamp

    Returns:
        True if current date is within any date range
    """
    current_date = current_time.date()

    for schedule in schedules:
        # Handle both Pydantic objects and dictionary formats
        if hasattr(schedule, "start_date") and hasattr(schedule, "end_date"):
            # Pydantic object (DateRangeSchedule)
            start_date_str = schedule.start_date
            end_date_str = schedule.end_date
        else:
            # Dictionary format
            start_date_str = schedule.get("start_date")
            end_date_str = schedule.get("end_date")

        if not start_date_str or not end_date_str:
            continue

        try:
            start_date = datetime.fromisoformat(start_date_str).date()
            end_date = datetime.fromisoformat(end_date_str).date()

            if start_date <= current_date <= end_date:
                return True

        except ValueError:
            # Invalid date format, skip this schedule
            continue

    return False


def _generate_reply_content(rule: AutoReply, trigger_type: TriggerType, matched_keyword: Optional[str] = None) -> str:
    """
    Generate appropriate reply content based on rule and trigger type.

    Args:
        rule: The matched auto-reply rule
        trigger_type: Type of trigger that matched
        matched_keyword: Keyword that triggered the match (if applicable)

    Returns:
        Generated reply content string
    """
    if trigger_type == TriggerType.IG_STORY_KEYWORD and matched_keyword:
        # IG Story-specific keyword responses
        ig_story_keyword_responses = {
            "hello": "Hello! Thanks for replying to our story! How can I help you today?",
            "hi": "Hi there! Great to see you engaged with our story! What can I do for you?",
            "hey": "Hey! Thanks for your story reply! How can I assist you?",
            "help": "I'm here to help! Thanks for reaching out through our story. What do you need assistance with?",
            "support": "Our support team is ready to assist you. Thanks for engaging with our story! How can we help?",
            "interested": "Thank you for showing interest in our story! Let me know how I can help you.",
            "more info": "Thanks for asking! I'd be happy to provide more information about what you saw in our story.",
            "price": "Thanks for your interest! For pricing information about what you saw in our story, please contact our sales team.",
            "contact": "You can reach us at: Email: support@company.com, Phone: (555) 123-4567. Thanks for engaging with our story!",
        }

        normalized_keyword = matched_keyword.strip().lower()
        if normalized_keyword in ig_story_keyword_responses:
            return ig_story_keyword_responses[normalized_keyword]
        else:
            return f"Thank you for replying to our story about '{matched_keyword}'! How can I help you?"

    elif trigger_type == TriggerType.IG_STORY_GENERAL:
        # IG Story-specific general responses based on time
        current_hour = datetime.now().hour
        if 5 <= current_hour < 12:
            return "Good morning! Thanks for replying to our story. How can I assist you today?"
        elif 12 <= current_hour < 17:
            return "Good afternoon! Thanks for engaging with our story. What can I help you with?"
        elif 17 <= current_hour < 22:
            return "Good evening! Thanks for your story reply. How can I help you?"
        else:
            return "Thank you for replying to our story! A team member will get back to you soon."

    elif trigger_type == TriggerType.KEYWORD and matched_keyword:
        # Use predefined keyword responses from the legacy keyword_auto_reply function
        keyword_responses = {
            "hello": "Hello! How can I help you today?",
            "hi": "Hi there! What can I do for you?",
            "hey": "Hey! How can I assist you?",
            "help": "I'm here to help! What do you need assistance with?",
            "support": "Our support team is ready to assist you. How can we help?",
            "price": "For pricing information, please visit our website or contact our sales team.",
            "pricing": "For pricing information, please visit our website or contact our sales team.",
            "contact": "You can reach us at: Email: support@company.com, Phone: (555) 123-4567",
            "hours": "Our business hours are Monday-Friday, 9AM-5PM. We're closed on weekends.",
        }

        normalized_keyword = matched_keyword.strip().lower()
        if normalized_keyword in keyword_responses:
            return keyword_responses[normalized_keyword]
        else:
            return f"Thank you for your message about '{matched_keyword}'. How can I help you?"

    elif trigger_type == TriggerType.GENERAL_TIME:
        # Time-based general responses
        current_hour = datetime.now().hour
        if 5 <= current_hour < 12:
            return "Good morning! Thank you for your message. How can I assist you today?"
        elif 12 <= current_hour < 17:
            return "Good afternoon! Thank you for reaching out. What can I help you with?"
        elif 17 <= current_hour < 22:
            return "Good evening! Thanks for your message. How can I help you?"
        else:
            return "Thank you for your message! A team member will get back to you soon."

    # Fallback generic response
    return f"Thank you for your message! This is an automated response from rule '{rule.name}'."
