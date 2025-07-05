import json
from datetime import date, datetime, time
from typing import Optional

import pytz
from celery.utils.log import get_task_logger
from django.db.models import Prefetch
from django.forms import model_to_dict
from django.utils import timezone

from line.constants import (
    MessageRecordType,
    WebhookTriggerFriendType,
    WebhookTriggerSettingEventType,
    WebhookTriggerSettingTriggerScheduleType,
)
from line.models import (
    TriggerMemberTimestampCacheBox,
    WebhookTriggerMessage,
    WebhookTriggerSetting,
)
from line.utils.cache import get_webhook_trigger_info_v2
from line.webhook.base import BaseWebhookHandler
from organization.models import BusinessHour

logger = get_task_logger("rubato_celery")


class Handler(BaseWebhookHandler):
    def beacon(self, process_data: dict) -> dict:
        hw_id = self.event["beacon"].get("hwid")
        trigger_setting_infos = get_webhook_trigger_info_v2(
            bot_id=self.bot["id"], channel_id=self.bot["channel_id"]
        )
        if not trigger_setting_infos["beacon"].get(hw_id):
            return process_data
        else:
            trigger_setting = trigger_setting_infos["beacon"].get(hw_id)
            if not trigger_setting:
                return process_data
            else:
                return self.__update_process_data(process_data, trigger_setting)

    def message(self, process_data: dict) -> dict:
        message: dict = self.event_instance.message

        # Handle location message in location module
        if message["type"] == "location":
            return process_data

        # Get all enabled webhook trigger settings
        trigger_setting_infos: dict = get_webhook_trigger_info_v2(
            bot_id=self.bot["id"], channel_id=self.bot["channel_id"]
        )

        # Handle text message
        if message["type"] == "text":
            text: str = message["text"]

            member_info = process_data.get("member_info")
            logger.info(
                {
                    "message": "[WebhookModuleTrigger] check different trigger type",
                    "uuid": self.uuid,
                    "active_trigger_msg_size": len(trigger_setting_infos["message"]),
                    "active_trigger_msgs": list(
                        trigger_setting_infos["message"].keys()
                    ),
                    "bot_id": self.bot["id"],
                    "member_line_id": member_info.get_line_id(),
                    "target_msg": text,
                }
            )

            # Check if the message matches the keyword
            webhook_trigger_setting: Optional[dict] = trigger_setting_infos.get(
                "message", {}
            ).get(text)
            if webhook_trigger_setting:
                logger.info(
                    {
                        "message": "[WebhookModuleTrigger] matched keyword",
                        "uuid": self.uuid,
                        "trigger_setting_id": webhook_trigger_setting.get("id"),
                    }
                )

                if (
                    webhook_trigger_setting["trigger_schedule_type"]
                    == WebhookTriggerSettingTriggerScheduleType.DATE_RANGE.value
                ):
                    tz = pytz.timezone(self.bot_instance.timezone)
                    event_time: datetime = self.event_instance.timestamp.astimezone(
                        tz=tz
                    )

                    # Example: [{"start_date": "2021-01-01", "end_date": "2021-01-31"}]
                    trigger_schedule_setting: dict = webhook_trigger_setting[
                        "trigger_schedule_settings"
                    ][0]
                    # check if the event_time is in the date range
                    start_date: date = date.fromisoformat(
                        trigger_schedule_setting["start_date"]
                    )
                    end_date: date = date.fromisoformat(
                        trigger_schedule_setting["end_date"]
                    )
                    # If the event_time is not in the date range, means the trigger is not matched
                    # and need to check the time trigger
                    if event_time.date() < start_date or end_date < event_time.date():
                        return self.__check_trigger_schedule(process_data)

                process_data = self.__update_process_data(
                    process_data, webhook_trigger_setting
                )

                # If the event_type is WebhookTriggerSettingEventType.MESSAGE, then
                # 1. Mark the message as `auto_reply_triggered` to ignore the message in CAAC
                # 2. No need to check trigger schedule
                if (
                    webhook_trigger_setting["event_type"]
                    == WebhookTriggerSettingEventType.MESSAGE.value
                ):
                    process_data["auto_reply_triggered"] = True
                    return process_data

        return self.__check_trigger_schedule(process_data)

    def postback(self, process_data: dict) -> dict:
        postback_data = self.event["postback"]["data"]
        try:
            data = json.loads(postback_data)
        except json.decoder.JSONDecodeError:
            logger.warning(f"[postback decode error]: {self.uuid}")
            process_data["continue_process"] = False
            return process_data

        if not isinstance(data, dict):
            logger.warning(f"[postback content error]: {self.uuid}")
            process_data["continue_process"] = False
            return process_data

        category = data.get("category")
        if category != WebhookTriggerSetting.WEBHOOK_POSTBACK_CATEGORY:
            return process_data

        trigger_setting_infos = get_webhook_trigger_info_v2(
            bot_id=self.bot["id"], channel_id=self.bot["channel_id"]
        )
        if trigger_setting_infos["postback"].get(postback_data):
            return self.__update_process_data(
                process_data, trigger_setting_infos["postback"].get(postback_data)
            )
        return self.__check_time_trigger(process_data, trigger_setting_infos["time"])

    def follow(self, process_data: dict) -> dict:
        trigger_setting_infos = get_webhook_trigger_info_v2(
            bot_id=self.bot["id"], channel_id=self.bot["channel_id"]
        )

        if not trigger_setting_infos["follow"]:
            return process_data
        else:
            trigger_setting = trigger_setting_infos["follow"]
            return self.__update_process_data(process_data, trigger_setting)

    def __check_time_trigger(self, process_data, time_trigger_settings):
        timestamp = self.event["timestamp"]
        tz = pytz.timezone(self.bot["timezone"])
        event_time = timezone.datetime.fromtimestamp(int(timestamp) / 1000, tz)

        for trigger_code, trigger_setting in time_trigger_settings.items():
            check_time = event_time
            start_time, end_time = WebhookTriggerSetting.get_trigger_time(
                time_str=trigger_code, tz=tz
            )
            # over midnight
            if start_time > end_time:
                end_time += timezone.timedelta(days=1)

            # ex: 2020-05-10 21:00 -> 2020-05-11 08:00 trigger_at 2020-05-10 7:30
            if start_time > check_time:
                check_time += timezone.timedelta(days=1)

            if end_time > check_time >= start_time:
                logger.info(
                    {
                        "message": "[WebhookModuleTrigger] matched time trigger",
                        "uuid": self.uuid,
                    }
                )
                return self.__update_process_data(process_data, trigger_setting)
        return process_data

    def __check_trigger_schedule(self, process_data) -> dict:
        # TODO: Because the number of trigger settings is not too many,
        # implement the basic version first, and then implement the advanced data structure
        tz = pytz.timezone(self.bot_instance.timezone)
        event_time: datetime = self.event_instance.timestamp.astimezone(tz=tz)

        # Get all time trigger settings and group them by trigger_schedule_type
        webhook_trigger_settings = WebhookTriggerSetting.objects.filter(
            bot_id=self.bot_instance.id,
            event_type=WebhookTriggerSettingEventType.TIME,
            enable=True,
            archived=False,
        ).prefetch_related(
            Prefetch(
                "messages",
                queryset=WebhookTriggerMessage.objects.filter(enable=True),
                to_attr="reply_messages",
            )
        )
        monthly_trigger_settings = []
        business_hour_trigger_settings = []
        non_business_hour_trigger_settings = []
        daily_trigger_settings = []
        for webhook_trigger_setting in webhook_trigger_settings:
            if (
                webhook_trigger_setting.trigger_schedule_type
                == WebhookTriggerSettingTriggerScheduleType.MONTHLY
            ):
                monthly_trigger_settings.append(webhook_trigger_setting)
            elif (
                webhook_trigger_setting.trigger_schedule_type
                == WebhookTriggerSettingTriggerScheduleType.BUSINESS_HOUR
            ):
                business_hour_trigger_settings.append(webhook_trigger_setting)
            elif (
                webhook_trigger_setting.trigger_schedule_type
                == WebhookTriggerSettingTriggerScheduleType.NON_BUSINESS_HOUR
            ):
                non_business_hour_trigger_settings.append(webhook_trigger_setting)
            elif (
                webhook_trigger_setting.trigger_schedule_type
                == WebhookTriggerSettingTriggerScheduleType.DAILY
            ):
                daily_trigger_settings.append(webhook_trigger_setting)

        # Priority: Monthly > Business Hour (Non-Business Hour) > Daily
        for trigger_setting in monthly_trigger_settings:
            for schedule_setting in trigger_setting.trigger_schedule_settings:
                if event_time.day != schedule_setting["day"]:
                    continue

                start_time: time = time.fromisoformat(
                    schedule_setting["start_time"]
                ).replace(second=time.min.second, microsecond=time.min.microsecond)
                end_time: time = time.fromisoformat(
                    schedule_setting["end_time"]
                ).replace(second=time.max.second, microsecond=time.max.microsecond)

                if start_time <= event_time.time() < end_time:
                    return self.__update_process_data(
                        process_data,
                        self.__convert_to_trigger_setting_dict(trigger_setting),
                    )

        business_hours = BusinessHour.objects.filter(
            organization_id=self.organization.id
        )
        for trigger_setting in business_hour_trigger_settings:
            for business_hour in business_hours:
                if business_hour.weekday != event_time.isoweekday():
                    continue

                start_time: time = business_hour.start_time.replace(
                    second=time.min.second, microsecond=time.min.microsecond
                )
                end_time: time = business_hour.end_time.replace(
                    second=time.max.second, microsecond=time.max.microsecond
                )

                if start_time <= event_time.time() < end_time:
                    return self.__update_process_data(
                        process_data,
                        self.__convert_to_trigger_setting_dict(trigger_setting),
                    )

        for trigger_setting in non_business_hour_trigger_settings:
            is_in_business_hour = False
            for business_hour in business_hours:
                if business_hour.weekday != event_time.isoweekday():
                    continue

                start_time: time = business_hour.start_time.replace(
                    second=time.min.second, microsecond=time.min.microsecond
                )
                end_time: time = business_hour.end_time.replace(
                    second=time.max.second, microsecond=time.max.microsecond
                )

                if start_time <= event_time.time() < end_time:
                    is_in_business_hour = True
                    break

            if not is_in_business_hour:
                return self.__update_process_data(
                    process_data,
                    self.__convert_to_trigger_setting_dict(trigger_setting),
                )

        for trigger_setting in daily_trigger_settings:
            for schedule_setting in trigger_setting.trigger_schedule_settings:
                start_time: time = time.fromisoformat(
                    schedule_setting["start_time"]
                ).replace(second=time.min.second, microsecond=time.min.microsecond)
                end_time: time = time.fromisoformat(
                    schedule_setting["end_time"]
                ).replace(second=time.max.second, microsecond=time.max.microsecond)

                if start_time <= end_time:
                    if start_time <= event_time.time() < end_time:
                        return self.__update_process_data(
                            process_data,
                            self.__convert_to_trigger_setting_dict(trigger_setting),
                        )
                else:
                    # over midnight
                    if start_time <= event_time.time() or event_time.time() < end_time:
                        return self.__update_process_data(
                            process_data,
                            self.__convert_to_trigger_setting_dict(trigger_setting),
                        )

        return process_data

    def __convert_to_trigger_setting_dict(self, webhook_trigger_setting) -> dict:
        # Compatible with past code
        trigger_setting_dict = model_to_dict(webhook_trigger_setting)
        messages = {}
        for reply_message in webhook_trigger_setting.reply_messages:
            reply_message_info = model_to_dict(reply_message)
            messages[reply_message_info["trigger_type"]] = reply_message_info
        trigger_setting_dict["messages"] = messages
        return trigger_setting_dict

    def __set_last_trigger(self, process_data, trigger_setting):
        member_info = process_data.get("member_info")
        timestamp_cache_box = TriggerMemberTimestampCacheBox(
            member_id=member_info.get_id(), trigger_setting_id=trigger_setting.get("id")
        )
        timestamp_cache_box.set(self.event["timestamp"])

    def __check_in_no_disturb_interval(self, process_data, trigger_setting):
        member_info = process_data.get("member_info")
        timestamp_cache_box = TriggerMemberTimestampCacheBox(
            member_id=member_info.get_id(), trigger_setting_id=trigger_setting.get("id")
        )
        last_trigger = timestamp_cache_box.get()
        no_disturb_interval = trigger_setting.get("no_disturb_interval")
        if last_trigger and no_disturb_interval:
            last_trigger_time = timezone.datetime.fromtimestamp(
                last_trigger / 1000, timezone.get_current_timezone()
            )
            return timezone.localtime() - last_trigger_time < timezone.timedelta(
                hours=no_disturb_interval
            )
        else:
            return False

    def __get_reply_message_type(self, process_data) -> int:
        BEACON = "beacon"
        BANNER = "banner"
        FOLLOW = "follow"
        member_info = process_data.get("member_info")

        # Beacon
        if self.event["type"] == BEACON and self.event["beacon"].get("type") == BANNER:
            now = timezone.localtime()
            if now - member_info.get_created_at() < timezone.timedelta(minutes=5):
                return WebhookTriggerFriendType.NEW_FRIEND.value

        # Follow
        if self.event["type"] == FOLLOW:
            return WebhookTriggerFriendType.NEW_FRIEND.value

        # Check bound
        if member_info.get_bind_id():
            return WebhookTriggerFriendType.BOUND_FRIEND.value

        return WebhookTriggerFriendType.ORIGINAL_FRIEND.value

    # Process
    def __update_process_data(self, process_data: dict, trigger_setting: dict) -> dict:
        reply_message_type: int = self.__get_reply_message_type(process_data)
        message_replied_flag = False
        if messages.get(reply_message_type, {}).get(
            "enable"
        ) and not self.__check_in_no_disturb_interval(process_data, trigger_setting):
            try:
                reply_message_info = messages.get(reply_message_type)
                reply_message_info["setting_id"] = reply_message_info.pop("setting")
                reply_message = WebhookTriggerMessage(**reply_message_info)
                logger.debug(
                    {
                        "message": "[WebhookModuleTrigger] pop messages trigger_setting",
                        "uuid": self.uuid,
                        "reply_message": reply_message,
                        "reply_message_info": reply_message_info,
                        "member_info": process_data["member_info"],
                        "messages_size": len(messages),
                        "reply_message_type": reply_message_type,
                        "language_code": self.bot["language_code"],
                    }
                )
                message_builder, _ = reply_message.get_message_builder()
                kwargs = {
                    "member_info": process_data["member_info"],
                    "language_code": self.bot["language_code"],
                }
                messages = message_builder.build_messages(**kwargs)
                logger.debug(
                    {
                        "message": "[WebhookModuleTrigger] send reply message",
                        "uuid": self.uuid,
                        "messages": messages,
                        "messages_size": len(messages),
                        "reply_message_type": reply_message_type,
                    }
                )
                validation_errors, is_valid = reply_message.validate_messages(
                    messages=messages
                )
                if is_valid and len(messages) > 0:
                    process_data = self.add_messages(
                        process_data=process_data,
                        messages=messages,
                        type=MessageRecordType.WEBHOOK_TRIGGER.value,
                        ref_id=trigger_setting["id"],
                    )
                    message_replied_flag = True
                    self.__set_last_trigger(process_data, trigger_setting)
                else:
                    err_msg = (
                        f"[Handler.__update_process_data()]:"
                        f"webhook trigger fail, {validation_errors}"
                    )
                    logger.warning(err_msg)
            except Exception as e:
                message_replied_flag = False
                logger.exception(
                    {
                        "message": "[WebhookModuleTrigger] fail to send reply message",
                        "uuid": self.uuid,
                        "error": str(e),
                    }
                )
        return process_data
