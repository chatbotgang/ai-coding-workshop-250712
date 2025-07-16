"""Auto Reply domain models."""

from datetime import datetime
from enum import StrEnum
from typing import List, Optional

from pydantic import BaseModel, Field

from internal.domain.auto_reply.webhook_trigger import (
    WebhookTriggerSetting,
    WebhookTriggerEventType,
    WebhookTriggerScheduleType,
    WebhookTriggerScheduleSettings,
)
import pytz
from datetime import timedelta


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


class ChannelType(StrEnum):
    LINE = "line"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"

class MessageEvent(BaseModel):
    event_id: str = Field(..., description="Unique event identifier")
    channel_type: ChannelType = Field(..., description="Channel where event originated")
    user_id: str = Field(..., description="User identifier from the channel")
    timestamp: datetime = Field(..., description="Event timestamp")
    content: str = Field(..., description="Message content/text")
    message_id: str = Field(..., description="Unique message identifier")
    ig_story_id: str | None = None  # Optional IG Story context

def _normalize_keyword(s: str) -> str:
    return s.strip().lower()

def _split_keywords(trigger_code: Optional[str]) -> List[str]:
    if not trigger_code:
        return []
    # Support comma or whitespace separated keywords
    if "," in trigger_code:
        return [_normalize_keyword(k) for k in trigger_code.split(",") if k.strip()]
    return [_normalize_keyword(trigger_code)]

def _in_date_range(event_time: datetime, schedule_settings: dict | None) -> bool:
    if not schedule_settings:
        return True
    # schedule_settings is a list of dicts with start_date, end_date (YYYY-MM-DD)
    for s in schedule_settings.get("date_ranges", []):
        start = datetime.fromisoformat(s["start_date"])
        end = datetime.fromisoformat(s["end_date"])
        if start.date() <= event_time.date() <= end.date():
            return True
    return False

def _in_monthly(event_time: datetime, schedule_settings: dict | None) -> bool:
    if not schedule_settings:
        return False
    tzinfo = event_time.tzinfo
    for s in schedule_settings.get("monthly", []):
        if event_time.day == s["day"]:
            st = datetime.combine(event_time.date(), datetime.strptime(s["start_time"], "%H:%M").time())
            et = datetime.combine(event_time.date(), datetime.strptime(s["end_time"], "%H:%M").time())
            if tzinfo is not None:
                st = st.replace(tzinfo=tzinfo)
                et = et.replace(tzinfo=tzinfo)
            if st <= event_time < et:
                return True
    return False

def _in_daily(event_time: datetime, schedule_settings: dict | None) -> bool:
    if not schedule_settings:
        return False
    tzinfo = event_time.tzinfo
    for s in schedule_settings.get("daily", []):
        st = datetime.combine(event_time.date(), datetime.strptime(s["start_time"], "%H:%M").time())
        et = datetime.combine(event_time.date(), datetime.strptime(s["end_time"], "%H:%M").time())
        if tzinfo is not None:
            st = st.replace(tzinfo=tzinfo)
            et = et.replace(tzinfo=tzinfo)
        if st <= et:
            if st <= event_time < et:
                return True
        else:  # crosses midnight
            if event_time >= st or event_time < et:
                return True
    return False

def is_in_business_hour(dt: datetime, org_id: int) -> bool:
    # stub: always True for demo
    return True

def get_last_trigger_time(trigger_id: int, user_id: str) -> datetime | None:
    # stub: always None for demo
    return None

def to_bot_timezone(dt: datetime, bot_timezone: str) -> datetime:
    tz = pytz.timezone(bot_timezone or "Asia/Taipei")
    if dt.tzinfo is None:
        return tz.localize(dt)
    return dt.astimezone(tz)

def validate_trigger(
    message_event: MessageEvent,
    trigger_settings: List[WebhookTriggerSetting],
    bot_timezone: str = "Asia/Taipei",
) -> Optional[WebhookTriggerSetting]:
    """
    Returns the first matching WebhookTriggerSetting for the given message_event, or None if no match.
    Implements 4-level priority: IG Story Keyword > IG Story General > General Keyword > General Time-based.
    All schedule matching uses bot_timezone.
    """
    candidates = [t for t in trigger_settings if t.enable and not t.archived]
    if message_event.content is None:
        return None
    content_norm = _normalize_keyword(message_event.content)
    now = to_bot_timezone(message_event.timestamp, bot_timezone)
    user_id = message_event.user_id
    ig_story_id = getattr(message_event, "ig_story_id", None)

    def get_ig_story_ids(t):
        if t.extra and "ig_story_ids" in t.extra:
            return t.extra["ig_story_ids"]
        return []

    # 1. IG Story Keyword (Priority 1)
    if ig_story_id:
        for t in candidates:
            if t.event_type == WebhookTriggerEventType.MESSAGE and get_ig_story_ids(t):
                if ig_story_id in get_ig_story_ids(t):
                    keywords = _split_keywords(t.trigger_code)
                    if content_norm in keywords:
                        # date_range
                        if t.trigger_schedule_type == WebhookTriggerScheduleType.DATE_RANGE:
                            if not _in_date_range(now, t.trigger_schedule_settings):
                                continue
                        # schedule (if present)
                        if t.trigger_schedule_type == WebhookTriggerScheduleType.MONTHLY:
                            if not _in_monthly(now, t.trigger_schedule_settings):
                                continue
                        if t.trigger_schedule_type == WebhookTriggerScheduleType.DAILY:
                            if not _in_daily(now, t.trigger_schedule_settings):
                                continue
                        interval = (t.extra or {}).get("no_disturb_interval")
                        if interval:
                            last = get_last_trigger_time(t.id, user_id)
                            if last is not None:
                                if last.tzinfo is None:
                                    last = last.replace(tzinfo=now.tzinfo)
                                if (now - last) < timedelta(minutes=interval):
                                    continue
                        return t
    # 2. IG Story General (Priority 2)
    if ig_story_id:
        schedule_priority = [
            WebhookTriggerScheduleType.MONTHLY,
            WebhookTriggerScheduleType.BUSINESS_HOUR,
            WebhookTriggerScheduleType.NON_BUSINESS_HOUR,
            WebhookTriggerScheduleType.DAILY,
        ]
        for schedule_type in schedule_priority:
            for t in candidates:
                if (
                    t.event_type == WebhookTriggerEventType.TIME
                    and t.trigger_schedule_type == schedule_type
                    and get_ig_story_ids(t)
                    and ig_story_id in get_ig_story_ids(t)
                ):
                    match = False
                    if schedule_type == WebhookTriggerScheduleType.MONTHLY:
                        match = _in_monthly(now, t.trigger_schedule_settings)
                    elif schedule_type == WebhookTriggerScheduleType.DAILY:
                        match = _in_daily(now, t.trigger_schedule_settings)
                    elif schedule_type == WebhookTriggerScheduleType.BUSINESS_HOUR:
                        match = is_in_business_hour(now, t.auto_reply_id)
                    elif schedule_type == WebhookTriggerScheduleType.NON_BUSINESS_HOUR:
                        match = not is_in_business_hour(now, t.auto_reply_id)
                    if match:
                        interval = (t.extra or {}).get("no_disturb_interval")
                        if interval:
                            last = get_last_trigger_time(t.id, user_id)
                            if last is not None:
                                if last.tzinfo is None:
                                    last = last.replace(tzinfo=now.tzinfo)
                                if (now - last) < timedelta(minutes=interval):
                                    continue
                        return t
    # 3. General Keyword (Priority 3)
    for t in candidates:
        if t.event_type == WebhookTriggerEventType.MESSAGE and not get_ig_story_ids(t):
            keywords = _split_keywords(t.trigger_code)
            if content_norm in keywords:
                if t.trigger_schedule_type == WebhookTriggerScheduleType.DATE_RANGE:
                    if not _in_date_range(now, t.trigger_schedule_settings):
                        continue
                if t.trigger_schedule_type == WebhookTriggerScheduleType.MONTHLY:
                    if not _in_monthly(now, t.trigger_schedule_settings):
                        continue
                if t.trigger_schedule_type == WebhookTriggerScheduleType.DAILY:
                    if not _in_daily(now, t.trigger_schedule_settings):
                        continue
                interval = (t.extra or {}).get("no_disturb_interval")
                if interval:
                    last = get_last_trigger_time(t.id, user_id)
                    if last is not None:
                        if last.tzinfo is None:
                            last = last.replace(tzinfo=now.tzinfo)
                        if (now - last) < timedelta(minutes=interval):
                            continue
                return t
    # 4. General Time-based (Priority 4)
    schedule_priority = [
        WebhookTriggerScheduleType.MONTHLY,
        WebhookTriggerScheduleType.BUSINESS_HOUR,
        WebhookTriggerScheduleType.NON_BUSINESS_HOUR,
        WebhookTriggerScheduleType.DAILY,
    ]
    for schedule_type in schedule_priority:
        for t in candidates:
            if (
                t.event_type == WebhookTriggerEventType.TIME
                and t.trigger_schedule_type == schedule_type
                and not get_ig_story_ids(t)
            ):
                match = False
                if schedule_type == WebhookTriggerScheduleType.MONTHLY:
                    match = _in_monthly(now, t.trigger_schedule_settings)
                elif schedule_type == WebhookTriggerScheduleType.DAILY:
                    match = _in_daily(now, t.trigger_schedule_settings)
                elif schedule_type == WebhookTriggerScheduleType.BUSINESS_HOUR:
                    match = is_in_business_hour(now, t.auto_reply_id)
                elif schedule_type == WebhookTriggerScheduleType.NON_BUSINESS_HOUR:
                    match = not is_in_business_hour(now, t.auto_reply_id)
                if match:
                    interval = (t.extra or {}).get("no_disturb_interval")
                    if interval:
                        last = get_last_trigger_time(t.id, user_id)
                        if last is not None:
                            if last.tzinfo is None:
                                last = last.replace(tzinfo=now.tzinfo)
                            if (now - last) < timedelta(minutes=interval):
                                continue
                    return t
    return None
