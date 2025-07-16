import pytest
from datetime import datetime
import pytz

from internal.domain.auto_reply.webhook_trigger import (
    find_first_matched_trigger,
    MessageEvent,
    WebhookTriggerSetting,
    WebhookTriggerEventType,
    WebhookTriggerScheduleType,
)
from internal.domain.auto_reply.auto_reply import AutoReply, AutoReplyStatus, AutoReplyEventType
from internal.domain.organization import BusinessHour

# Helper: 构造 AutoReply

def make_auto_reply(id, keywords=None):
    return AutoReply(
        id=id,
        organization_id=1,
        name=f"ar-{id}",
        status=AutoReplyStatus.ACTIVE,
        event_type=AutoReplyEventType.MESSAGE,
        priority=1,
        keywords=keywords,
        trigger_schedule_type=None,
        trigger_schedule_settings=None,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

# Helper: 构造 WebhookTriggerSetting

def make_trigger(id, auto_reply_id, event_type=WebhookTriggerEventType.MESSAGE, schedule_type=None, schedule_settings=None):
    return WebhookTriggerSetting(
        id=id,
        auto_reply_id=auto_reply_id,
        bot_id=1,
        enable=True,
        name=f"trigger-{id}",
        event_type=event_type,
        trigger_code=None,
        trigger_schedule_type=schedule_type,
        trigger_schedule_settings=schedule_settings,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        archived=False,
        extra=None,
    )

# Helper: 构造 MessageEvent

def make_event(content, event_type="message", ts=None, timezone="Asia/Taipei"):
    return MessageEvent(
        bot_id=1,
        organization_id=1,
        channel="line",
        user_id="u1",
        event_type=event_type,
        content=content,
        timestamp=ts or datetime.now(),
        bot_timezone=timezone,
        raw_event=None,
    )

# --- PRD Test Cases ---

# [B-P0-7-Test2]: 关键词大小写不敏感
def test_keyword_case_insensitive():
    ar = make_auto_reply(1, ["hello"])
    trigger = make_trigger(1, 1)
    event = make_event("HELLO")
    result = find_first_matched_trigger(event, [trigger], {1: ar})
    assert result is not None

# [B-P0-7-Test3]: 关键词前后空格
def test_keyword_trim_spaces():
    ar = make_auto_reply(1, ["hello"])
    trigger = make_trigger(1, 1)
    event = make_event(" hello ")
    result = find_first_matched_trigger(event, [trigger], {1: ar})
    assert result is not None

# [B-P0-7-Test4]: 关键词部分匹配不触发
def test_keyword_partial_match():
    ar = make_auto_reply(1, ["hello"])
    trigger = make_trigger(1, 1)
    event = make_event("hello world")
    result = find_first_matched_trigger(event, [trigger], {1: ar})
    assert result is None

# [B-P0-7-Test5]: 关键词近似不触发
def test_keyword_close_variation():
    ar = make_auto_reply(1, ["hello"])
    trigger = make_trigger(1, 1)
    event = make_event("helloo")
    result = find_first_matched_trigger(event, [trigger], {1: ar})
    assert result is None

# [Multiple-Keywords-Test1]: 多关键词任意命中
def test_multiple_keywords_any_match():
    ar = make_auto_reply(1, ["hello", "hi", "hey"])
    trigger = make_trigger(1, 1)
    for word in ["hello", "hi", "hey"]:
        event = make_event(word)
        result = find_first_matched_trigger(event, [trigger], {1: ar})
        assert result is not None

# [Multiple-Keywords-Test2]: 多关键词大小写
def test_multiple_keywords_case_insensitive():
    ar = make_auto_reply(1, ["hello", "hi"])
    trigger = make_trigger(1, 1)
    event = make_event("HI")
    result = find_first_matched_trigger(event, [trigger], {1: ar})
    assert result is not None

# [Multiple-Keywords-Test3]: 多关键词无匹配
def test_multiple_keywords_no_match():
    ar = make_auto_reply(1, ["hello", "hi"])
    trigger = make_trigger(1, 1)
    event = make_event("bye")
    result = find_first_matched_trigger(event, [trigger], {1: ar})
    assert result is None

# [B-P0-6-Test3]: daily 时间段内触发
def test_daily_schedule_match():
    ar = make_auto_reply(1)
    # 09:00-17:00
    trigger = make_trigger(1, 1, schedule_type=WebhookTriggerScheduleType.DAILY, schedule_settings={"start_time": "09:00", "end_time": "17:00"})
    event = make_event("hi", ts=datetime.now().replace(hour=10, minute=0, second=0, microsecond=0))
    result = find_first_matched_trigger(event, [trigger], {1: ar})
    assert result is not None

# [B-P0-6-Test3]: daily 时间段外不触发
def test_daily_schedule_no_match():
    ar = make_auto_reply(1)
    trigger = make_trigger(1, 1, schedule_type=WebhookTriggerScheduleType.DAILY, schedule_settings={"start_time": "09:00", "end_time": "17:00"})
    event = make_event("hi", ts=datetime.now().replace(hour=18, minute=0, second=0, microsecond=0))
    result = find_first_matched_trigger(event, [trigger], {1: ar})
    assert result is None

# [Priority-Test1]: 关键词优先于 general
def test_priority_keyword_over_general():
    ar1 = make_auto_reply(1, ["hello"])
    ar2 = make_auto_reply(2)
    trigger_keyword = make_trigger(1, 1)
    trigger_general = make_trigger(2, 2, schedule_type=WebhookTriggerScheduleType.DAILY, schedule_settings={"start_time": "09:00", "end_time": "17:00"})
    event = make_event("hello", ts=datetime.now().replace(hour=10, minute=0, second=0, microsecond=0))
    # 两个都能命中，但应优先返回关键词
    result = find_first_matched_trigger(event, [trigger_keyword, trigger_general], {1: ar1, 2: ar2}, business_hours=None)
    assert result == trigger_keyword

# --- Custom Test Cases ---

# [B-P0-6-Test3-Midnight-In-Range]: daily 时间段跨夜触发
def test_daily_schedule_midnight_crossing_match():
    ar = make_auto_reply(1)
    # 22:00 - 06:00
    trigger = make_trigger(1, 1, schedule_type=WebhookTriggerScheduleType.DAILY, schedule_settings={"start_time": "22:00", "end_time": "06:00"})
    # 在 23:00 触发
    event1 = make_event("hi", ts=datetime.now().replace(hour=23, minute=0, second=0, microsecond=0))
    result1 = find_first_matched_trigger(event1, [trigger], {1: ar})
    assert result1 is not None
    # 在 04:00 触发
    event2 = make_event("hi", ts=datetime.now().replace(hour=4, minute=0, second=0, microsecond=0))
    result2 = find_first_matched_trigger(event2, [trigger], {1: ar})
    assert result2 is not None

# [B-P0-6-Test3-Midnight-Out-Range]: daily 时间段跨夜不触发
def test_daily_schedule_midnight_crossing_no_match():
    ar = make_auto_reply(1)
    # 22:00 - 06:00
    trigger = make_trigger(1, 1, schedule_type=WebhookTriggerScheduleType.DAILY, schedule_settings={"start_time": "22:00", "end_time": "06:00"})
    # 在 20:00 不触发
    event = make_event("hi", ts=datetime.now().replace(hour=20, minute=0, second=0, microsecond=0))
    result = find_first_matched_trigger(event, [trigger], {1: ar}, business_hours=None)
    assert result is None

# --- New Test Cases for Timezone and Schedules ---

# [B-P0-6-Test4-UTC]: monthly 时间段在 UTC 时间下触发
def test_monthly_schedule_match_with_utc():
    ar = make_auto_reply(1)
    # 15号 10:00-12:00
    trigger = make_trigger(1, 1, schedule_type=WebhookTriggerScheduleType.MONTHLY, schedule_settings={"day": 15, "start_time": "10:00", "end_time": "12:00"})
    # 传入 UTC 时间 2024-07-15 03:00 (等于 Asia/Taipei 11:00)
    utc_time = datetime(2024, 7, 15, 3, 0, 0, tzinfo=pytz.UTC)
    event = make_event("hi", ts=utc_time, timezone="Asia/Taipei")
    result = find_first_matched_trigger(event, [trigger], {1: ar})
    assert result is not None

# [B-P0-6-Test5-In-Business-Hour]: business_hour 时间段内触发
def test_business_hour_schedule_match():
    ar = make_auto_reply(1)
    trigger = make_trigger(1, 1, schedule_type=WebhookTriggerScheduleType.BUSINESS_HOUR)
    # 周二 09:00-18:00
    bh = BusinessHour(id=1, organization_id=1, weekday=2, start_time="09:00", end_time="18:00")
    # 传入 UTC 时间 2024-07-16 03:00 (周二, Asia/Taipei 11:00)
    utc_time = datetime(2024, 7, 16, 3, 0, 0, tzinfo=pytz.UTC)
    event = make_event("hi", ts=utc_time, timezone="Asia/Taipei")
    result = find_first_matched_trigger(event, [trigger], {1: ar}, business_hours=[bh])
    assert result is not None

# [B-P0-6-Test5-Out-Of-Business-Hour]: business_hour 时间段外不触发
def test_non_business_hour_schedule_match():
    ar = make_auto_reply(1)
    trigger = make_trigger(1, 1, schedule_type=WebhookTriggerScheduleType.NON_BUSINESS_HOUR)
    # 周二 09:00-18:00
    bh = BusinessHour(id=1, organization_id=1, weekday=2, start_time="09:00", end_time="18:00")
    # 传入 UTC 时间 2024-07-16 12:00 (周二, Asia/Taipei 20:00)
    utc_time = datetime(2024, 7, 16, 12, 0, 0, tzinfo=pytz.UTC)
    event = make_event("hi", ts=utc_time, timezone="Asia/Taipei")
    result = find_first_matched_trigger(event, [trigger], {1: ar}, business_hours=[bh])
    assert result is not None 