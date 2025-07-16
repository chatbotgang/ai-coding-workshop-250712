"""Auto Reply domain module."""

from internal.domain.auto_reply.auto_reply import AutoReply, AutoReplyEventType, AutoReplyStatus
from internal.domain.auto_reply.trigger_validation import (
    BusinessHourChecker,
    TriggerValidationResult,
    convert_to_timezone,
    validate_trigger,
)
from internal.domain.auto_reply.webhook_event import (
    BeaconEvent,
    ChannelType,
    FollowEvent,
    MessageEvent,
    PostbackEvent,
    WebhookEvent,
    WebhookEventType,
)
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
    "WebhookEvent",
    "WebhookEventType",
    "MessageEvent",
    "PostbackEvent",
    "FollowEvent",
    "BeaconEvent",
    "ChannelType",
    "validate_trigger",
    "TriggerValidationResult",
    "BusinessHourChecker",
    "convert_to_timezone",
]
