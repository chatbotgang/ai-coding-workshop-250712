from enum import Enum, IntEnum


class BotType(str, Enum):
    LINE = "line"
    FB = "fb"
    IG = "ig"


class WebhookTriggerSettingEventType(IntEnum):
    MESSAGE = 1
    POSTBACK = 2
    FOLLOW = 3
    BEACON = 4
    TIME = 100
    MESSAGE_EDITOR = 101
    POSTBACK_EDITOR = 102


class WebhookTriggerSettingTriggerScheduleType(str, Enum):
    DAILY = "daily"
    MONTHLY = "monthly"
    BUSINESS_HOUR = "business_hour"
    NON_BUSINESS_HOUR = "non_business_hour"
    DATE_RANGE = "date_range"
    NON_DATE_RANGE = "non_date_range"
