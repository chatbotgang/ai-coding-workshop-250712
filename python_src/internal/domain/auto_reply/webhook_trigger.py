"""Webhook Trigger domain models."""

from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime
from enum import IntEnum, StrEnum
from typing import Sequence

from pydantic import BaseModel
import pytz
from internal.domain.organization import BusinessHour
# from internal.domain.auto_reply.auto_reply import AutoReply # This causes circular import


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


class MessageEvent(BaseModel):
    """消息事件输入结构，用于触发判定主入口函数。"""
    bot_id: int
    organization_id: int
    bot_timezone: str = "Asia/Taipei"  # Bot 的时区
    channel: str  # "line" / "facebook" / "instagram"
    user_id: str
    event_type: str  # "message" / "postback" / ...
    content: str     # 消息内容
    timestamp: datetime  # 建议统一传入 UTC 时间
    raw_event: dict | None = None


def validate_trigger(
    event: MessageEvent,
    trigger: WebhookTriggerSetting,
    auto_reply: "AutoReply" | None = None,
    business_hours: list["BusinessHour"] | None = None,
) -> bool:
    """
    判断单条规则是否命中。
    - Keyword: 精确匹配（忽略大小写，去除首尾空格），支持多关键词
    - General: 判断 schedule 是否命中，并处理时区
    - business_hours: 可选，用于 business_hour/non_business_hour 判定
    """
    # 只处理启用且未归档规则
    if not trigger.is_active():
        return False

    # 事件类型不符直接跳过
    if trigger.event_type == WebhookTriggerEventType.MESSAGE:
        if event.event_type.lower() != "message":
            return False
    elif trigger.event_type == WebhookTriggerEventType.POSTBACK:
        if event.event_type.lower() != "postback":
            return False
    elif trigger.event_type == WebhookTriggerEventType.FOLLOW:
        if event.event_type.lower() != "follow":
            return False
    elif trigger.event_type == WebhookTriggerEventType.BEACON:
        if event.event_type.lower() != "beacon":
            return False
    elif trigger.event_type == WebhookTriggerEventType.TIME:
        # TIME 事件由外部调度，不直接由消息事件触发
        return False
    # 其他类型暂不支持

    # 关键词判定（优先级最高）
    if auto_reply and auto_reply.keywords:
        msg = event.content.strip().lower()
        for kw in auto_reply.keywords:
            if msg == kw.strip().lower():
                return True
        return False

    # 时间类判定（General）
    tz = pytz.timezone(event.bot_timezone)
    event_time_local = event.timestamp.astimezone(tz)

    # Daily Schedule
    if trigger.trigger_schedule_type == WebhookTriggerScheduleType.DAILY and trigger.trigger_schedule_settings:
        try:
            from datetime import time
            st = trigger.trigger_schedule_settings.get("start_time")
            et = trigger.trigger_schedule_settings.get("end_time")
            if not (st and et):
                return False
            t_start = time.fromisoformat(st)
            t_end = time.fromisoformat(et)
            t_event = event_time_local.time()
            if t_start <= t_end:
                return t_start <= t_event < t_end
            else:
                return t_event >= t_start or t_event < t_end
        except Exception:
            return False

    # Monthly Schedule
    if trigger.trigger_schedule_type == WebhookTriggerScheduleType.MONTHLY and trigger.trigger_schedule_settings:
        try:
            from datetime import time
            day = trigger.trigger_schedule_settings.get("day")
            st = trigger.trigger_schedule_settings.get("start_time")
            et = trigger.trigger_schedule_settings.get("end_time")
            if not (day and st and et):
                return False
            if event_time_local.day != day:
                return False
            t_start = time.fromisoformat(st)
            t_end = time.fromisoformat(et)
            t_event = event_time_local.time()
            if t_start <= t_end:
                return t_start <= t_event < t_end
            else:
                return t_event >= t_start or t_event < t_end
        except Exception:
            return False

    # Business Hour Schedule
    if trigger.trigger_schedule_type == WebhookTriggerScheduleType.BUSINESS_HOUR:
        if not business_hours:
            return False
        is_in_business_hour = False
        for bh in business_hours:
            if bh.is_active and bh.weekday == event_time_local.isoweekday():
                if bh.start_time <= event_time_local.time() < bh.end_time:
                    is_in_business_hour = True
                    break
        return is_in_business_hour

    # Non-Business Hour Schedule
    if trigger.trigger_schedule_type == WebhookTriggerScheduleType.NON_BUSINESS_HOUR:
        if not business_hours:
            return True  # 没有营业时间=全天都是非营业时间
        is_in_business_hour = False
        for bh in business_hours:
            if bh.is_active and bh.weekday == event_time_local.isoweekday():
                if bh.start_time <= event_time_local.time() < bh.end_time:
                    is_in_business_hour = True
                    break
        return not is_in_business_hour

    return False


def find_first_matched_trigger(
    event: MessageEvent,
    triggers: Sequence[WebhookTriggerSetting],
    auto_reply_map: dict[int, "AutoReply"] | None = None,
    business_hours: list["BusinessHour"] | None = None,
) -> WebhookTriggerSetting | None:
    """
    根据事件和规则列表，自动遍历并按优先级判定，返回第一个命中的规则对象。
    - 优先级：Keyword > General（时间类，内部再按 monthly > business_hour > ...）
    - 无匹配时返回 None
    - auto_reply_map: 可选，auto_reply_id -> AutoReply，用于获取关键词等高层信息
    """
    # 1. 先筛选所有 keyword 规则（有 keywords 的 AutoReply）
    keyword_triggers = []
    for t in triggers:
        ar = auto_reply_map.get(t.auto_reply_id) if auto_reply_map else None
        if ar and ar.keywords:
            keyword_triggers.append((t, ar))
    for t, ar in keyword_triggers:
        if validate_trigger(event, t, ar, business_hours):
            return t
    # 2. 再筛选 General（时间类）规则，按 schedule_type 优先级
    # 优先级顺序
    schedule_priority = [
        WebhookTriggerScheduleType.MONTHLY,
        WebhookTriggerScheduleType.BUSINESS_HOUR,
        WebhookTriggerScheduleType.NON_BUSINESS_HOUR,
        WebhookTriggerScheduleType.DAILY,
    ]
    for stype in schedule_priority:
        for t in triggers:
            if t.trigger_schedule_type == stype:
                ar = auto_reply_map.get(t.auto_reply_id) if auto_reply_map else None
                if validate_trigger(event, t, ar, business_hours):
                    return t
    return None
