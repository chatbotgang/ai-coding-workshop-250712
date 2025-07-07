"""Auto Reply domain module."""

from internal.domain.auto_reply.auto_reply import AutoReply, AutoReplyEventType, AutoReplyStatus
from internal.domain.auto_reply.trigger_validator import TriggerValidationResult, TriggerValidator
from internal.domain.auto_reply.webhook_event import ChannelType, WebhookEvent, WebhookEventBuilder, WebhookEventType
from internal.domain.auto_reply.webhook_trigger import (
    BusinessHourSchedule,
    DailySchedule,
    DateRangeSchedule,
    MonthlySchedule,
    NonBusinessHourSchedule,
    WebhookTriggerEventType,
    WebhookTriggerSchedule,
    WebhookTriggerScheduleSettings,
    WebhookTriggerScheduleType,
    WebhookTriggerSetting,
)

__all__ = [
    "AutoReply",
    "AutoReplyStatus",
    "AutoReplyEventType",
    "TriggerValidator",
    "TriggerValidationResult",
    "WebhookEvent",
    "WebhookEventBuilder",
    "WebhookEventType",
    "ChannelType",
    "WebhookTriggerSetting",
    "WebhookTriggerEventType",
    "WebhookTriggerScheduleType",
    "WebhookTriggerScheduleSettings",
    "WebhookTriggerSchedule",
    "DailySchedule",
    "MonthlySchedule",
    "DateRangeSchedule",
    "BusinessHourSchedule",
    "NonBusinessHourSchedule",
]
