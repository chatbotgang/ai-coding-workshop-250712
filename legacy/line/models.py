import datetime
import logging
import re
from datetime import tzinfo
from typing import Tuple

from line.constants import (
    BotType,
    WebhookTriggerSettingEventType,
    WebhookTriggerSettingTriggerScheduleType,
)
from rubato.cache_keys import (
    LINE_WEBHOOK_TRIGGER_INFO_V2,
    LINE_WEBHOOK_TRIGGER_MEMBER_TIMESTAMP,
    CacheBox,
)
from django.db import models
from django.utils import timezone

logger = logging.getLogger("rubato")


class Bot(models.Model):
    TOKEN_INITIAL_EXPIRED_TIME = timezone.datetime(2017, 5, 17, 0, 0)
    PLAN_CHOICE = ()
    TYPE_CHOICE = ()

    organization = models.ForeignKey(
        "organization.Organization", on_delete=models.CASCADE, related_name="line_bot"
    )
    name = models.CharField(max_length=100)
    type = models.CharField(
        max_length=32, choices=TYPE_CHOICE, default=BotType.LINE.value
    )
    channel_id = models.CharField(max_length=255, unique=True)
    channel_secret = models.CharField(max_length=255)
    access_token = models.TextField(default=EMPTY_TOKEN, blank=True)
    token_expired_time = models.DateTimeField(
        default=TOKEN_INITIAL_EXPIRED_TIME,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expired_at = models.DateTimeField()
    enable = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class WebhookTriggerSetting(models.Model):
    TRIGGER_CODE_LENGTH_LIMIT = 32

    MESSAGE = WebhookTriggerSettingEventType.MESSAGE.value
    POSTBACK = WebhookTriggerSettingEventType.POSTBACK.value
    FOLLOW = WebhookTriggerSettingEventType.FOLLOW.value
    BEACON = WebhookTriggerSettingEventType.BEACON.value
    TIME = WebhookTriggerSettingEventType.TIME.value
    MESSAGE_EDITOR = WebhookTriggerSettingEventType.MESSAGE_EDITOR.value
    POSTBACK_EDITOR = WebhookTriggerSettingEventType.POSTBACK_EDITOR.value
    EVENT_TYPE_CHOICE = (
        (MESSAGE, "Message"),
        (POSTBACK, "Postback"),
        (FOLLOW, "Follow"),
        (BEACON, "Beacon"),
        (TIME, "Time"),
        (MESSAGE_EDITOR, "MessageEditor"),
        (POSTBACK_EDITOR, "PostbackEditor"),
    )
    TIME_SPLIT_SIGN = "<T>"
    TIME_FORMAT = "%H:%M:%S"
    WEBHOOK_POSTBACK_CATEGORY = "trigger"

    ALLOW_SWAP_EVENT_TYPE = {
        MESSAGE: [MESSAGE],
        POSTBACK: [POSTBACK],
        FOLLOW: [FOLLOW],
        BEACON: [BEACON],
        TIME: [TIME],
        MESSAGE_EDITOR: [MESSAGE_EDITOR, MESSAGE],
        POSTBACK_EDITOR: [POSTBACK_EDITOR, POSTBACK],
    }

    TRIGGER_SCHEDULE_TYPE_CHOICES = [
        (schedule_type.value, schedule_type.name)
        for schedule_type in WebhookTriggerSettingTriggerScheduleType
    ]

    enable = models.BooleanField(default=True)
    name = models.CharField(max_length=TRIGGER_CODE_LENGTH_LIMIT)  # Will be deprecated
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE)
    event_type = models.PositiveSmallIntegerField(
        choices=EVENT_TYPE_CHOICE
    )  # Inherit from parent rule (auto_reply.autoreply)
    trigger_code = models.CharField(
        max_length=TRIGGER_CODE_LENGTH_LIMIT, null=True, blank=True
    )  # Will be deprecated

    # Trigger schedule
    # daily -> [{"start_time": "10:00", "end_time": "12:00"}]
    # business_hour -> null
    # non_business_hour -> null
    # monthly -> [{"day": 1, "start_time": "10:00", "end_time": "12:00"}]
    # date_range -> [{"start_date": "2021-01-01", "end_date": "2021-01-31"}]
    trigger_schedule_type = models.CharField(
        max_length=32,
        null=True,
        blank=True,
        default=None,
        choices=TRIGGER_SCHEDULE_TYPE_CHOICES,
    )  # Inherit from parent rule (auto_reply.autoreply)
    trigger_schedule_settings = models.JSONField(
        null=True, blank=True, default=None
    )  # Inherit from parent rule (auto_reply.autoreply)

    no_disturb_interval = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name="觸發間隔(hour)"
    )  # Inherit from parent rule (auto_reply.autoreply)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    archived = models.BooleanField(default=False)
    extra = models.JSONField(null=True, blank=True)

    def delete(self, *args, **kwargs):
        super(WebhookTriggerSetting, self).delete(*args, **kwargs)
        key = LINE_WEBHOOK_TRIGGER_INFO_V2.format(channel_id=self.bot.channel_id)
        cache.delete(key)

    def is_over_midnight(self, tz: tzinfo) -> bool:
        if self.event_type != self.TIME:
            return False
        else:
            start_time, end_time = self.get_trigger_time(
                time_str=self.trigger_code, tz=tz
            )
            return start_time > end_time

    @classmethod
    def get_trigger_time(
        cls, time_str: str, tz: tzinfo
    ) -> Tuple[datetime.datetime, datetime.datetime]:
        if not time_str or not re.fullmatch(
            r"<T>\d{2}:\d{2}:\d{2}<T>\d{2}:\d{2}:\d{2}<T>", time_str
        ):
            return None, None
        else:
            date = datetime.datetime.now(tz=tz).date()
            time_str_list = time_str.split(cls.TIME_SPLIT_SIGN)
            start_time = tz.localize(
                datetime.datetime.combine(
                    date,
                    timezone.datetime.strptime(
                        time_str_list[1], cls.TIME_FORMAT
                    ).time(),
                )
            )
            end_time = tz.localize(
                datetime.datetime.combine(
                    date,
                    timezone.datetime.strptime(
                        time_str_list[2], cls.TIME_FORMAT
                    ).time(),
                )
            )
            return start_time, end_time


class TriggerMemberTimestampCacheBox(CacheBox):
    key_name = LINE_WEBHOOK_TRIGGER_MEMBER_TIMESTAMP
    timeout = 60 * 60 * 24 * 30

    def __init__(self, trigger_setting_id: int, member_id: int):
        super().__init__(trigger_setting_id=trigger_setting_id, member_id=member_id)
        self.trigger_setting_id = trigger_setting_id
        self.member_id = member_id
