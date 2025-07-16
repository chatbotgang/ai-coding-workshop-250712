import pytest
from datetime import datetime, timedelta
from internal.domain.auto_reply.auto_reply import (
    validate_trigger, MessageEvent, ChannelType
)
from internal.domain.auto_reply.webhook_trigger import (
    WebhookTriggerSetting, WebhookTriggerEventType, WebhookTriggerScheduleType
)

# --- helpers ---
def make_trigger(
    event_type=WebhookTriggerEventType.MESSAGE,
    trigger_code=None,
    enable=True,
    archived=False,
    trigger_schedule_type=None,
    trigger_schedule_settings=None,
    name="test",
    extra=None,
    id=1,
    auto_reply_id=1,
):
    return WebhookTriggerSetting(
        id=id,
        auto_reply_id=auto_reply_id,
        bot_id=1,
        enable=enable,
        name=name,
        event_type=event_type,
        trigger_code=trigger_code,
        trigger_schedule_type=trigger_schedule_type,
        trigger_schedule_settings=trigger_schedule_settings,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        archived=archived,
        extra=extra or {},
    )

def make_event(content, ts=None, user_id="u1"):
    return MessageEvent(
        event_id="e1",
        channel_type=ChannelType.LINE,
        user_id=user_id,
        timestamp=ts or datetime.now(),
        content=content,
        message_id="m1",
    )

def make_ig_event(content, ig_story_id=None, ts=None, user_id="u1"):
    # Helper for IG events with optional ig_story_id
    return MessageEvent(
        event_id="e1",
        channel_type=ChannelType.INSTAGRAM,
        user_id=user_id,
        timestamp=ts or datetime.now(),
        content=content,
        message_id="m1",
        ig_story_id=ig_story_id,
    )

# --- PRD Test Cases ---

def test_keyword_case_insensitive_and_trim():
    # [B-P0-7-Test2] keyword match, case insensitive
    trigger = make_trigger(trigger_code="hello")
    event = make_event("  HeLLo  ")
    result = validate_trigger(event, [trigger], bot_timezone="Asia/Taipei")
    assert result is not None
    assert result.trigger_code == "hello"

def test_keyword_trim_spaces():
    # [B-P0-7-Test3] keyword match, trim spaces
    trigger = make_trigger(trigger_code="hello")
    event = make_event(" hello ")
    result = validate_trigger(event, [trigger], bot_timezone="Asia/Taipei")
    assert result is not None

def test_keyword_partial_no_match():
    # [B-P0-7-Test4] partial match should NOT trigger
    trigger = make_trigger(trigger_code="hello")
    event = make_event("hello world")
    result = validate_trigger(event, [trigger], bot_timezone="Asia/Taipei")
    assert result is None

def test_keyword_close_variation_no_match():
    # [B-P0-7-Test5] close variation should NOT trigger
    trigger = make_trigger(trigger_code="hello")
    event = make_event("helloo")
    result = validate_trigger(event, [trigger], bot_timezone="Asia/Taipei")
    assert result is None

def test_multiple_keywords():
    # [Multiple-Keywords-Test1] multiple keywords, any match
    trigger = make_trigger(trigger_code="hello,hi,hey")
    event = make_event("hi")
    result = validate_trigger(event, [trigger], bot_timezone="Asia/Taipei")
    assert result is not None
    assert result.trigger_code == "hello,hi,hey"

def test_multiple_keywords_case_insensitive():
    # [Multiple-Keywords-Test2] case-insensitive match for multiple keywords
    trigger = make_trigger(trigger_code="hello,hi,hey")
    event = make_event("HEY")
    result = validate_trigger(event, [trigger], bot_timezone="Asia/Taipei")
    assert result is not None

def test_multiple_keywords_no_match():
    # [Multiple-Keywords-Test3] no match for any keyword
    trigger = make_trigger(trigger_code="hello,hi,hey")
    event = make_event("yo")
    result = validate_trigger(event, [trigger], bot_timezone="Asia/Taipei")
    assert result is None

def test_general_daily_schedule_match():
    # [B-P0-6-Test3] general reply, daily schedule, in time window
    now = datetime(2024, 6, 1, 10, 0)
    schedule = {"daily": [{"start_time": "09:00", "end_time": "17:00"}]}
    trigger = make_trigger(
        event_type=WebhookTriggerEventType.TIME,
        trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
        trigger_schedule_settings=schedule,
        name="daily"
    )
    event = make_event("hi", ts=now)
    result = validate_trigger(event, [trigger], bot_timezone="Asia/Taipei")
    assert result is not None
    assert result.name == "daily"

def test_general_daily_schedule_outside():
    # [B-P0-6-Test3] general reply, daily schedule, outside time window
    now = datetime(2024, 6, 1, 8, 0)
    schedule = {"daily": [{"start_time": "09:00", "end_time": "17:00"}]}
    trigger = make_trigger(
        event_type=WebhookTriggerEventType.TIME,
        trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
        trigger_schedule_settings=schedule,
        name="daily"
    )
    event = make_event("hi", ts=now)
    result = validate_trigger(event, [trigger], bot_timezone="Asia/Taipei")
    assert result is None

def test_keyword_date_range_match():
    # [date_range] keyword trigger, in date range
    now = datetime(2024, 6, 10)
    schedule = {"date_ranges": [{"start_date": "2024-06-01", "end_date": "2024-06-30"}]}
    trigger = make_trigger(
        trigger_code="hello",
        trigger_schedule_type=WebhookTriggerScheduleType.DATE_RANGE,
        trigger_schedule_settings=schedule,
    )
    event = make_event("hello", ts=now)
    result = validate_trigger(event, [trigger], bot_timezone="Asia/Taipei")
    assert result is not None

def test_keyword_date_range_outside():
    # [date_range] keyword trigger, outside date range
    now = datetime(2024, 7, 1)
    schedule = {"date_ranges": [{"start_date": "2024-06-01", "end_date": "2024-06-30"}]}
    trigger = make_trigger(
        trigger_code="hello",
        trigger_schedule_type=WebhookTriggerScheduleType.DATE_RANGE,
        trigger_schedule_settings=schedule,
    )
    event = make_event("hello", ts=now)
    result = validate_trigger(event, [trigger], bot_timezone="Asia/Taipei")
    assert result is None

def test_no_disturb(monkeypatch):
    # [no_disturb_interval] should not trigger if within interval
    now = datetime(2024, 6, 1, 10, 0)
    trigger = make_trigger(
        trigger_code="hello",
        extra={"no_disturb_interval": 10},
        id=99
    )
    event = make_event("hello", ts=now, user_id="u1")
    # Patch get_last_trigger_time to simulate last trigger 5 min ago
    import internal.domain.auto_reply.auto_reply as ar
    monkeypatch.setattr(ar, "get_last_trigger_time", lambda tid, uid: now - timedelta(minutes=5))
    result = validate_trigger(event, [trigger], bot_timezone="Asia/Taipei")
    assert result is None

def test_no_disturb_expired(monkeypatch):
    # [no_disturb_interval] should trigger if interval expired
    now = datetime(2024, 6, 1, 10, 0)
    trigger = make_trigger(
        trigger_code="hello",
        extra={"no_disturb_interval": 10},
        id=99
    )
    event = make_event("hello", ts=now, user_id="u1")
    import internal.domain.auto_reply.auto_reply as ar
    monkeypatch.setattr(ar, "get_last_trigger_time", lambda tid, uid: now - timedelta(minutes=15))
    result = validate_trigger(event, [trigger], bot_timezone="Asia/Taipei")
    assert result is not None 

def test_general_monthly_schedule_match():
    # [B-P0-6-Test4] monthly schedule, in time window
    now = datetime(2024, 6, 15, 15, 0)
    schedule = {"monthly": [{"day": 15, "start_time": "14:00", "end_time": "16:00"}]}
    trigger = WebhookTriggerSetting(
        id=1,
        auto_reply_id=1,
        bot_id=1,
        enable=True,
        name="monthly",
        event_type=WebhookTriggerEventType.TIME,
        trigger_code=None,
        trigger_schedule_type=WebhookTriggerScheduleType.MONTHLY,
        trigger_schedule_settings=schedule,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        archived=False,
        extra={},
    )
    event = MessageEvent(
        event_id="e1",
        channel_type=ChannelType.LINE,
        user_id="u1",
        timestamp=now,
        content="hi",
        message_id="m1",
    )
    result = validate_trigger(event, [trigger], bot_timezone="Asia/Taipei")
    assert result is not None
    assert result.name == "monthly"

def test_general_monthly_schedule_outside():
    # [B-P0-6-Test4] monthly schedule, outside time window
    now = datetime(2024, 6, 15, 13, 0)
    schedule = {"monthly": [{"day": 15, "start_time": "14:00", "end_time": "16:00"}]}
    trigger = WebhookTriggerSetting(
        id=1,
        auto_reply_id=1,
        bot_id=1,
        enable=True,
        name="monthly",
        event_type=WebhookTriggerEventType.TIME,
        trigger_code=None,
        trigger_schedule_type=WebhookTriggerScheduleType.MONTHLY,
        trigger_schedule_settings=schedule,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        archived=False,
        extra={},
    )
    event = MessageEvent(
        event_id="e1",
        channel_type=ChannelType.LINE,
        user_id="u1",
        timestamp=now,
        content="hi",
        message_id="m1",
    )
    result = validate_trigger(event, [trigger], bot_timezone="Asia/Taipei")
    assert result is None

def test_general_business_hour(monkeypatch):
    # [B-P0-6-Test5] business hour schedule, in business hour
    now = datetime(2024, 6, 1, 10, 0)
    trigger = WebhookTriggerSetting(
        id=1,
        auto_reply_id=1,
        bot_id=1,
        enable=True,
        name="bizhr",
        event_type=WebhookTriggerEventType.TIME,
        trigger_code=None,
        trigger_schedule_type=WebhookTriggerScheduleType.BUSINESS_HOUR,
        trigger_schedule_settings=None,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        archived=False,
        extra={},
    )
    event = MessageEvent(
        event_id="e1",
        channel_type=ChannelType.LINE,
        user_id="u1",
        timestamp=now,
        content="hi",
        message_id="m1",
    )
    import internal.domain.auto_reply.auto_reply as ar
    monkeypatch.setattr(ar, "is_in_business_hour", lambda dt, org_id: True)
    result = validate_trigger(event, [trigger], bot_timezone="Asia/Taipei")
    assert result is not None
    assert result.name == "bizhr"

def test_general_non_business_hour(monkeypatch):
    # [B-P0-6-Test5] non-business hour schedule, outside business hour
    now = datetime(2024, 6, 1, 22, 0)
    trigger = WebhookTriggerSetting(
        id=1,
        auto_reply_id=1,
        bot_id=1,
        enable=True,
        name="nonbizhr",
        event_type=WebhookTriggerEventType.TIME,
        trigger_code=None,
        trigger_schedule_type=WebhookTriggerScheduleType.NON_BUSINESS_HOUR,
        trigger_schedule_settings=None,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        archived=False,
        extra={},
    )
    event = MessageEvent(
        event_id="e1",
        channel_type=ChannelType.LINE,
        user_id="u1",
        timestamp=now,
        content="hi",
        message_id="m1",
    )
    import internal.domain.auto_reply.auto_reply as ar
    monkeypatch.setattr(ar, "is_in_business_hour", lambda dt, org_id: False)
    result = validate_trigger(event, [trigger], bot_timezone="Asia/Taipei")
    assert result is not None
    assert result.name == "nonbizhr"

def test_priority_keyword_over_general():
    # [Priority-Test1] keyword and general, keyword match during general window
    now = datetime(2024, 6, 1, 10, 0)
    kw_trigger = WebhookTriggerSetting(
        id=1,
        auto_reply_id=1,
        bot_id=1,
        enable=True,
        name="kw",
        event_type=WebhookTriggerEventType.MESSAGE,
        trigger_code="hello",
        trigger_schedule_type=None,
        trigger_schedule_settings=None,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        archived=False,
        extra={},
    )
    gen_trigger = WebhookTriggerSetting(
        id=2,
        auto_reply_id=1,
        bot_id=1,
        enable=True,
        name="gen",
        event_type=WebhookTriggerEventType.TIME,
        trigger_code=None,
        trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
        trigger_schedule_settings={"daily": [{"start_time": "09:00", "end_time": "17:00"}]},
        created_at=datetime.now(),
        updated_at=datetime.now(),
        archived=False,
        extra={},
    )
    event = MessageEvent(
        event_id="e1",
        channel_type=ChannelType.LINE,
        user_id="u1",
        timestamp=now,
        content="hello",
        message_id="m1",
    )
    result = validate_trigger(event, [kw_trigger, gen_trigger], bot_timezone="Asia/Taipei")
    assert result is not None
    assert result.name == "kw"

def test_priority_general_when_no_keyword():
    # [Priority-Test2] keyword and general, no keyword match, general triggers
    now = datetime(2024, 6, 1, 10, 0)
    kw_trigger = WebhookTriggerSetting(
        id=1,
        auto_reply_id=1,
        bot_id=1,
        enable=True,
        name="kw",
        event_type=WebhookTriggerEventType.MESSAGE,
        trigger_code="hello",
        trigger_schedule_type=None,
        trigger_schedule_settings=None,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        archived=False,
        extra={},
    )
    gen_trigger = WebhookTriggerSetting(
        id=2,
        auto_reply_id=1,
        bot_id=1,
        enable=True,
        name="gen",
        event_type=WebhookTriggerEventType.TIME,
        trigger_code=None,
        trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
        trigger_schedule_settings={"daily": [{"start_time": "09:00", "end_time": "17:00"}]},
        created_at=datetime.now(),
        updated_at=datetime.now(),
        archived=False,
        extra={},
    )
    event = MessageEvent(
        event_id="e1",
        channel_type=ChannelType.LINE,
        user_id="u1",
        timestamp=now,
        content="notmatch",
        message_id="m1",
    )
    result = validate_trigger(event, [kw_trigger, gen_trigger], bot_timezone="Asia/Taipei")
    assert result is not None
    assert result.name == "gen"

def test_priority_keyword_outside_general():
    # [Priority-Test3] keyword and general, keyword match outside general window
    now = datetime(2024, 6, 1, 8, 0)
    kw_trigger = WebhookTriggerSetting(
        id=1,
        auto_reply_id=1,
        bot_id=1,
        enable=True,
        name="kw",
        event_type=WebhookTriggerEventType.MESSAGE,
        trigger_code="hello",
        trigger_schedule_type=None,
        trigger_schedule_settings=None,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        archived=False,
        extra={},
    )
    gen_trigger = WebhookTriggerSetting(
        id=2,
        auto_reply_id=1,
        bot_id=1,
        enable=True,
        name="gen",
        event_type=WebhookTriggerEventType.TIME,
        trigger_code=None,
        trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
        trigger_schedule_settings={"daily": [{"start_time": "09:00", "end_time": "17:00"}]},
        created_at=datetime.now(),
        updated_at=datetime.now(),
        archived=False,
        extra={},
    )
    event = MessageEvent(
        event_id="e1",
        channel_type=ChannelType.LINE,
        user_id="u1",
        timestamp=now,
        content="hello",
        message_id="m1",
    )
    result = validate_trigger(event, [kw_trigger, gen_trigger], bot_timezone="Asia/Taipei")
    assert result is not None
    assert result.name == "kw"

def test_message_content_exact():
    # [Message-Content-Test1] keyword rule, message contains the exact keyword
    trigger = WebhookTriggerSetting(
        id=1,
        auto_reply_id=1,
        bot_id=1,
        enable=True,
        name="kw",
        event_type=WebhookTriggerEventType.MESSAGE,
        trigger_code="hello",
        trigger_schedule_type=None,
        trigger_schedule_settings=None,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        archived=False,
        extra={},
    )
    event = MessageEvent(
        event_id="e1",
        channel_type=ChannelType.LINE,
        user_id="u1",
        timestamp=datetime.now(),
        content="hello",
        message_id="m1",
    )
    result = validate_trigger(event, [trigger], bot_timezone="Asia/Taipei")
    assert result is not None
    assert result.name == "kw"

def test_message_content_no_keyword():
    # [Message-Content-Test2] message without any keyword to a channel with keyword rules
    trigger = WebhookTriggerSetting(
        id=1,
        auto_reply_id=1,
        bot_id=1,
        enable=True,
        name="kw",
        event_type=WebhookTriggerEventType.MESSAGE,
        trigger_code="hello",
        trigger_schedule_type=None,
        trigger_schedule_settings=None,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        archived=False,
        extra={},
    )
    event = MessageEvent(
        event_id="e1",
        channel_type=ChannelType.LINE,
        user_id="u1",
        timestamp=datetime.now(),
        content="notmatch",
        message_id="m1",
    )
    result = validate_trigger(event, [trigger], bot_timezone="Asia/Taipei")
    assert result is None

def test_message_content_general_any():
    # [Message-Content-Test3] general rule, any message content during schedule triggers
    now = datetime(2024, 6, 1, 10, 0)
    trigger = WebhookTriggerSetting(
        id=1,
        auto_reply_id=1,
        bot_id=1,
        enable=True,
        name="gen",
        event_type=WebhookTriggerEventType.TIME,
        trigger_code=None,
        trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
        trigger_schedule_settings={"daily": [{"start_time": "09:00", "end_time": "17:00"}]},
        created_at=datetime.now(),
        updated_at=datetime.now(),
        archived=False,
        extra={},
    )
    event = MessageEvent(
        event_id="e1",
        channel_type=ChannelType.LINE,
        user_id="u1",
        timestamp=now,
        content="anything",
        message_id="m1",
    )
    result = validate_trigger(event, [trigger], bot_timezone="Asia/Taipei")
    assert result is not None
    assert result.name == "gen" 

def test_daily_schedule_timezone_aware():
    # Asia/Taipei is UTC+8
    import pytz
    tz = pytz.timezone("Asia/Taipei")
    # 10:00 Asia/Taipei == 02:00 UTC
    utc_time = datetime(2024, 6, 1, 2, 0, tzinfo=pytz.UTC)
    schedule = {"daily": [{"start_time": "09:00", "end_time": "17:00"}]}
    trigger = make_trigger(
        event_type=WebhookTriggerEventType.TIME,
        trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
        trigger_schedule_settings=schedule,
        name="daily"
    )
    event = make_event("hi", ts=utc_time)
    # Should match because 10:00 Asia/Taipei is within 09:00-17:00
    result = validate_trigger(event, [trigger], bot_timezone="Asia/Taipei")
    assert result is not None
    assert result.name == "daily" 

# --- IG Story-Specific Auto-Reply Tests (PRD-part2) ---

def test_ig_story_keyword_only_triggers_on_story():
    # [B-P1-18-Test7] IG Story Keyword rule, message matches keyword but NOT a reply to selected story
    trigger = make_trigger(
        event_type=WebhookTriggerEventType.MESSAGE,
        trigger_code="hello",
        extra={"ig_story_ids": ["story123"]},
    )
    event = make_ig_event("hello")  # No ig_story_id
    result = validate_trigger(event, [trigger], bot_timezone="Asia/Taipei")
    assert result is None

def test_ig_story_keyword_triggers_on_story():
    # [B-P1-18-Test8a] IG Story Keyword rule, message is reply to selected story and matches keyword
    trigger = make_trigger(
        event_type=WebhookTriggerEventType.MESSAGE,
        trigger_code="hello",
        extra={"ig_story_ids": ["story123"]},
    )
    event = make_ig_event("hello", ig_story_id="story123")
    result = validate_trigger(event, [trigger], bot_timezone="Asia/Taipei")
    assert result is not None

def test_ig_story_keyword_wrong_story():
    # [IG-Story-Keyword-Test2] IG Story Keyword rule, wrong story id
    trigger = make_trigger(
        event_type=WebhookTriggerEventType.MESSAGE,
        trigger_code="hello",
        extra={"ig_story_ids": ["story123"]},
    )
    event = make_ig_event("hello", ig_story_id="story456")
    result = validate_trigger(event, [trigger], bot_timezone="Asia/Taipei")
    assert result is None

def test_ig_story_keyword_no_story_id():
    # [IG-Story-Keyword-Test3] IG Story Keyword rule, no ig_story_id
    trigger = make_trigger(
        event_type=WebhookTriggerEventType.MESSAGE,
        trigger_code="hello",
        extra={"ig_story_ids": ["story123"]},
    )
    event = make_ig_event("hello")
    result = validate_trigger(event, [trigger], bot_timezone="Asia/Taipei")
    assert result is None

def test_ig_story_general_triggers_on_story():
    # [B-P1-18-Test8b] IG Story General rule, reply to selected story and within schedule
    now = datetime(2024, 6, 1, 14, 0)
    schedule = {"daily": [{"start_time": "09:00", "end_time": "17:00"}]}
    trigger = make_trigger(
        event_type=WebhookTriggerEventType.TIME,
        trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
        trigger_schedule_settings=schedule,
        extra={"ig_story_ids": ["story123"]},
    )
    event = make_ig_event("hi", ig_story_id="story123", ts=now)
    result = validate_trigger(event, [trigger], bot_timezone="Asia/Taipei")
    assert result is not None

def test_ig_story_general_wrong_story():
    # [IG-Story-General-Test3] IG Story General rule, wrong story id
    now = datetime(2024, 6, 1, 14, 0)
    schedule = {"daily": [{"start_time": "09:00", "end_time": "17:00"}]}
    trigger = make_trigger(
        event_type=WebhookTriggerEventType.TIME,
        trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
        trigger_schedule_settings=schedule,
        extra={"ig_story_ids": ["story123"]},
    )
    event = make_ig_event("hi", ig_story_id="story456", ts=now)
    result = validate_trigger(event, [trigger], bot_timezone="Asia/Taipei")
    assert result is None

def test_ig_story_priority_over_general():
    # [B-P1-18-Test9] IG Story Keyword and General Keyword, both match, only IG Story triggers
    ig_trigger = make_trigger(
        event_type=WebhookTriggerEventType.MESSAGE,
        trigger_code="hello",
        extra={"ig_story_ids": ["story123"]},
        name="ig_story_kw",
    )
    gen_trigger = make_trigger(
        event_type=WebhookTriggerEventType.MESSAGE,
        trigger_code="hello",
        name="general_kw",
    )
    event = make_ig_event("hello", ig_story_id="story123")
    result = validate_trigger(event, [ig_trigger, gen_trigger], bot_timezone="Asia/Taipei")
    assert result is not None
    assert result.name == "ig_story_kw"

def test_ig_story_multiple_keywords():
    # [IG-Story-Multiple-Keywords-Test1] IG Story Keyword rule with multiple keywords
    trigger = make_trigger(
        event_type=WebhookTriggerEventType.MESSAGE,
        trigger_code="hello,hi",
        extra={"ig_story_ids": ["story123"]},
    )
    event1 = make_ig_event("hello", ig_story_id="story123")
    event2 = make_ig_event("hi", ig_story_id="story123")
    assert validate_trigger(event1, [trigger], bot_timezone="Asia/Taipei") is not None
    assert validate_trigger(event2, [trigger], bot_timezone="Asia/Taipei") is not None

def test_ig_story_multiple_keywords_wrong_story():
    # [IG-Story-Multiple-Keywords-Test2] IG Story Keyword rule, wrong story id
    trigger = make_trigger(
        event_type=WebhookTriggerEventType.MESSAGE,
        trigger_code="hello,hi",
        extra={"ig_story_ids": ["story123"]},
    )
    event = make_ig_event("hi", ig_story_id="story456")
    result = validate_trigger(event, [trigger], bot_timezone="Asia/Taipei")
    assert result is None

def test_ig_story_exclusion_logic():
    # [IG-Story-Exclusion-Test1] IG Story-specific keyword, normal message (no ig_story_id)
    trigger = make_trigger(
        event_type=WebhookTriggerEventType.MESSAGE,
        trigger_code="hello",
        extra={"ig_story_ids": ["story123"]},
    )
    event = make_ig_event("hello")
    result = validate_trigger(event, [trigger], bot_timezone="Asia/Taipei")
    assert result is None

def test_ig_story_priority_system():
    # [Complete-Priority-Test1] All 4 types, only IG Story Keyword triggers
    now = datetime(2024, 6, 1, 14, 0)
    ig_kw = make_trigger(
        event_type=WebhookTriggerEventType.MESSAGE,
        trigger_code="hello",
        extra={"ig_story_ids": ["story123"]},
        name="ig_kw",
    )
    ig_gen = make_trigger(
        event_type=WebhookTriggerEventType.TIME,
        trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
        trigger_schedule_settings={"daily": [{"start_time": "09:00", "end_time": "17:00"}]},
        extra={"ig_story_ids": ["story123"]},
        name="ig_gen",
    )
    gen_kw = make_trigger(
        event_type=WebhookTriggerEventType.MESSAGE,
        trigger_code="hello",
        name="gen_kw",
    )
    gen_time = make_trigger(
        event_type=WebhookTriggerEventType.TIME,
        trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
        trigger_schedule_settings={"daily": [{"start_time": "09:00", "end_time": "17:00"}]},
        name="gen_time",
    )
    event = make_ig_event("hello", ig_story_id="story123", ts=now)
    triggers = [ig_kw, ig_gen, gen_kw, gen_time]
    result = validate_trigger(event, triggers, bot_timezone="Asia/Taipei")
    assert result is not None
    assert result.name == "ig_kw" 