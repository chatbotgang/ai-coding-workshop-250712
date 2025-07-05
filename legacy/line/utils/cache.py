import re
from collections import defaultdict

from django.core.cache import cache
from django.db.models import Prefetch
from django.forms.models import model_to_dict

from line.models import WebhookTriggerMessage, WebhookTriggerSetting
from rubato.cache_keys import (
    LINE_WEBHOOK_TRIGGER_INFO_V2,
)


def refresh_webhook_trigger_info_v2(bot_id: int = 0, channel_id: str = ""):
    """
    trigger_data_template = {
        "message": {
            "keyword_1": {},
            "keyword_2": {}
        },
        "follow": {
        },
        "postback": {
            "category_action_param": {}
        },
        "beacon": {
            "hw_id1": {
                "id": 1,
                "enable": True,
                "name": "beacon_1",
                "bot": 1,
                "event_type": 4,
                "trigger_code": "000002477b",
                "tag": ["beacon"],
                "messages": {
                    1: {
                        "id": 1,
                        "messages": [
                            {
                                "data": {
                                    "text": "new friend xxxx"
                                },
                                "module_id": 1,
                                "parameters": [],
                            }
                        ],
                        "enable": True,
                        "setting": 1,
                        "message_type": 1,
                    },
                    2: {
                        "id": 2,
                        "messages": [
                            {
                                "data": {
                                    "text": "old friend xxxx"
                                },
                                "module_id": 1,
                                "parameters": [],
                            }
                        ],
                        "enable": True,
                        "setting": 1,
                        "message_type": 2,
                    },
                },
            },
            "hw_id2": {}
        },
        "time": {
            "<T>HH:MM:SS<T>HH:MM:SS<T>": {}
        }
    }
    """
    trigger_settings = WebhookTriggerSetting.objects.filter(
        bot_id=bot_id, enable=True, archived=False
    ).prefetch_related(
        Prefetch(
            "messages",
            queryset=WebhookTriggerMessage.objects.filter(enable=True),
            to_attr="reply_messages",
        )
    )
    trigger_setting_infos = defaultdict(dict)
    for trigger_setting in trigger_settings:
        event_type = trigger_setting.event_type
        trigger_code = trigger_setting.trigger_code
        trigger_setting_dict = model_to_dict(trigger_setting)
        messages = {}
        for reply_message in trigger_setting.reply_messages:
            reply_message_info = model_to_dict(reply_message)
            messages[reply_message_info["trigger_type"]] = reply_message_info
        trigger_setting_dict["messages"] = messages
        if event_type == WebhookTriggerSetting.BEACON:
            trigger_setting_infos["beacon"][trigger_code] = trigger_setting_dict
        elif event_type == WebhookTriggerSetting.FOLLOW:
            trigger_setting_infos["follow"] = trigger_setting_dict
        elif event_type == WebhookTriggerSetting.TIME:
            # Save to cache only if trigger_code is in the format <T>%H:%M:%S<T>%H:%M:%S<T>
            # because the new time trigger structure will not be judged by trigger_code
            if trigger_code and re.fullmatch(
                r"<T>\d{2}:\d{2}:\d{2}<T>\d{2}:\d{2}:\d{2}<T>", trigger_code
            ):
                trigger_setting_infos["time"][trigger_code] = trigger_setting_dict
        elif event_type in [
            WebhookTriggerSetting.POSTBACK,
            WebhookTriggerSetting.POSTBACK_EDITOR,
        ]:
            trigger_setting_infos["postback"][trigger_code] = trigger_setting_dict
        elif event_type in [
            WebhookTriggerSetting.MESSAGE,
            WebhookTriggerSetting.MESSAGE_EDITOR,
        ]:
            trigger_setting_infos["message"][trigger_code] = trigger_setting_dict

    key = LINE_WEBHOOK_TRIGGER_INFO_V2.format(channel_id=channel_id)
    cache.set(key, trigger_setting_infos, timeout=60 * 60 * 48)
    return trigger_setting_infos


def get_webhook_trigger_info_v2(bot_id: int = 0, channel_id: str = ""):
    trigger_setting_info_key = LINE_WEBHOOK_TRIGGER_INFO_V2.format(
        channel_id=channel_id
    )
    trigger_setting_infos = cache.get(trigger_setting_info_key)
    if not trigger_setting_infos:
        trigger_setting_infos = refresh_webhook_trigger_info_v2(
            bot_id=bot_id, channel_id=channel_id
        )
    return trigger_setting_infos
