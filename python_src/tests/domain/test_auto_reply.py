import pytest
from datetime import datetime
from internal.domain.auto_reply.auto_reply import AutoReply, AutoReplyStatus, AutoReplyEventType
from internal.domain.auto_reply.webhook_trigger import WebhookTriggerScheduleType, WebhookTriggerScheduleSettings
from internal.domain.auto_reply.validate_trigger import validate_trigger, AUTO_REPLY_RULES_CACHE, AutoReplyEvent

class TestValidateTrigger:
    def setup_method(self):
        # Reset the cache before each test
        AUTO_REPLY_RULES_CACHE.clear()

    def test_keyword_match(self):
        AUTO_REPLY_RULES_CACHE["LINE"] = [
            AutoReply(
                id=1,
                organization_id=1,
                name="Hello Rule",
                status=AutoReplyStatus.ACTIVE,
                event_type=AutoReplyEventType.KEYWORD,
                priority=1,
                keywords=["hello", "hi"],
                trigger_schedule_type=None,
                trigger_schedule_settings=None,
                ig_story_ids=None,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
        ]
        event = AutoReplyEvent(message_text="  HeLLo  ", channel_type="LINE", timestamp=datetime.now())
        rule, result = validate_trigger(event)
        assert rule is not None
        assert result == "keyword_match"
        assert "hello" in rule.keywords

    def test_no_match(self):
        AUTO_REPLY_RULES_CACHE["LINE"] = [
            AutoReply(
                id=2,
                organization_id=1,
                name="Hello Rule",
                status=AutoReplyStatus.ACTIVE,
                event_type=AutoReplyEventType.KEYWORD,
                priority=1,
                keywords=["hello", "hi"],
                trigger_schedule_type=None,
                trigger_schedule_settings=None,
                ig_story_ids=None,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
        ]
        event = AutoReplyEvent(message_text="bye", channel_type="LINE", timestamp=datetime.now())
        rule, result = validate_trigger(event)
        assert rule is None
        assert result == "no_match"

    def test_general_match(self):
        # Simulate a general rule (time-based) with a valid daily schedule covering now
        from internal.domain.auto_reply.webhook_trigger import DailySchedule
        now = datetime.now()
        start_time = (now.replace(second=0, microsecond=0)).time().strftime("%H:%M")
        from datetime import timedelta
        end_time_obj = (now + timedelta(hours=1)).time()
        end_time = end_time_obj.strftime("%H:%M")
        AUTO_REPLY_RULES_CACHE["FB"] = [
            AutoReply(
                id=3,
                organization_id=1,
                name="General Rule",
                status=AutoReplyStatus.ACTIVE,
                event_type=AutoReplyEventType.TIME,
                priority=2,
                keywords=None,
                trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
                trigger_schedule_settings=WebhookTriggerScheduleSettings(schedules=[
                    DailySchedule(start_time=start_time, end_time=end_time)
                ]),
                ig_story_ids=None,
                created_at=now,
                updated_at=now,
            )
        ]
        event = AutoReplyEvent(message_text="any message", channel_type="FB", timestamp=now)
        rule, result = validate_trigger(event)
        assert rule is not None
        assert result == "general_match"
        assert rule.event_type == AutoReplyEventType.TIME

    # IG-Story-Keyword-Test1: IG Story Keyword Reply rule for story "story123" with keyword "hello". Send message with keyword "hello" and ig_story_id "story123".
    def test_ig_story_keyword_match(self):
        AUTO_REPLY_RULES_CACHE["IG"] = [
            AutoReply(
                id=4,
                organization_id=1,
                name="IG Story Keyword Rule",
                status=AutoReplyStatus.ACTIVE,
                event_type=AutoReplyEventType.KEYWORD,
                priority=1,
                keywords=["hello"],
                trigger_schedule_type=None,
                trigger_schedule_settings=None,
                ig_story_ids=["story123"],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
        ]
        event = AutoReplyEvent(message_text="hello", channel_type="IG", timestamp=datetime.now(), ig_story_id="story123")
        rule, result = validate_trigger(event)
        assert rule is not None
        assert result == "ig_story_keyword_match"
        assert rule.ig_story_ids == ["story123"]

    # IG-Story-Keyword-Test2: IG Story Keyword Reply rule for story "story123" with keyword "hello". Send message with keyword "hello" and ig_story_id "story456" (wrong story).
    def test_ig_story_keyword_wrong_story(self):
        AUTO_REPLY_RULES_CACHE["IG"] = [
            AutoReply(
                id=5,
                organization_id=1,
                name="IG Story Keyword Rule",
                status=AutoReplyStatus.ACTIVE,
                event_type=AutoReplyEventType.KEYWORD,
                priority=1,
                keywords=["hello"],
                trigger_schedule_type=None,
                trigger_schedule_settings=None,
                ig_story_ids=["story123"],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
        ]
        event = AutoReplyEvent(message_text="hello", channel_type="IG", timestamp=datetime.now(), ig_story_id="story456")
        rule, result = validate_trigger(event)
        assert rule is None
        assert result == "no_match"

    # IG-Story-Exclusion-Test1: IG story-specific keyword setting with keyword "hello". Send normal message with keyword "hello" (no IG story ID).
    def test_ig_story_keyword_exclusion(self):
        AUTO_REPLY_RULES_CACHE["IG"] = [
            AutoReply(
                id=6,
                organization_id=1,
                name="IG Story Keyword Rule",
                status=AutoReplyStatus.ACTIVE,
                event_type=AutoReplyEventType.KEYWORD,
                priority=1,
                keywords=["hello"],
                trigger_schedule_type=None,
                trigger_schedule_settings=None,
                ig_story_ids=["story123"],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
        ]
        event = AutoReplyEvent(message_text="hello", channel_type="IG", timestamp=datetime.now(), ig_story_id=None)
        rule, result = validate_trigger(event)
        assert rule is None
        assert result == "no_match"

    # IG-Story-Priority-Test1: Both IG story keyword rule and general keyword rule for same keyword. Send message with keyword and matching story ID.
    def test_ig_story_priority(self):
        AUTO_REPLY_RULES_CACHE["IG"] = [
            AutoReply(
                id=7,
                organization_id=1,
                name="IG Story Keyword Rule",
                status=AutoReplyStatus.ACTIVE,
                event_type=AutoReplyEventType.KEYWORD,
                priority=1,
                keywords=["hello"],
                trigger_schedule_type=None,
                trigger_schedule_settings=None,
                ig_story_ids=["story123"],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
            AutoReply(
                id=8,
                organization_id=1,
                name="General Keyword Rule",
                status=AutoReplyStatus.ACTIVE,
                event_type=AutoReplyEventType.KEYWORD,
                priority=1,
                keywords=["hello"],
                trigger_schedule_type=None,
                trigger_schedule_settings=None,
                ig_story_ids=None,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
        ]
        event = AutoReplyEvent(message_text="hello", channel_type="IG", timestamp=datetime.now(), ig_story_id="story123")
        rule, result = validate_trigger(event)
        assert rule is not None
        assert result == "ig_story_keyword_match"
        assert rule.ig_story_ids == ["story123"]

    def test_daily_trigger_midnight_crossing(self):
        # Setup: trigger from 22:00 to 06:00 (crosses midnight)
        from internal.domain.auto_reply.webhook_trigger import DailySchedule, WebhookTriggerScheduleSettings, WebhookTriggerScheduleType
        import pytz
        tz = pytz.timezone("Asia/Taipei")
        AUTO_REPLY_RULES_CACHE["LINE"] = [
            AutoReply(
                id=100,
                organization_id=1,
                name="Overnight Rule",
                status=AutoReplyStatus.ACTIVE,
                event_type=AutoReplyEventType.TIME,
                priority=2,
                keywords=None,
                trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
                trigger_schedule_settings=WebhookTriggerScheduleSettings(schedules=[
                    DailySchedule(start_time="22:00", end_time="06:00")
                ]),
                ig_story_ids=None,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
        ]
        # Event at 23:00 (should match)
        event1 = AutoReplyEvent(message_text="", channel_type="LINE", timestamp=tz.localize(datetime(2024, 7, 1, 23, 0)), ig_story_id=None)
        # Event at 05:00 (should match)
        event2 = AutoReplyEvent(message_text="", channel_type="LINE", timestamp=tz.localize(datetime(2024, 7, 2, 5, 0)), ig_story_id=None)
        # Event at 12:00 (should NOT match)
        event3 = AutoReplyEvent(message_text="", channel_type="LINE", timestamp=tz.localize(datetime(2024, 7, 2, 12, 0)), ig_story_id=None)
        rule1, result1 = validate_trigger(event1)
        rule2, result2 = validate_trigger(event2)
        rule3, result3 = validate_trigger(event3)
        assert rule1 is not None and result1 == "general_match"
        assert rule2 is not None and result2 == "general_match"
        assert rule3 is None and result3 == "no_match"

    def test_business_hour_trigger_timezone(self):
        # Setup: business hour is 09:00-18:00 Asia/Taipei
        from internal.domain.auto_reply.webhook_trigger import BusinessHourSchedule, WebhookTriggerScheduleSettings, WebhookTriggerScheduleType
        import pytz
        tz = pytz.timezone("Asia/Taipei")
        AUTO_REPLY_RULES_CACHE["FB"] = [
            AutoReply(
                id=101,
                organization_id=1,
                name="Business Hour Rule",
                status=AutoReplyStatus.ACTIVE,
                event_type=AutoReplyEventType.TIME,
                priority=2,
                keywords=None,
                trigger_schedule_type=WebhookTriggerScheduleType.BUSINESS_HOUR,
                trigger_schedule_settings=WebhookTriggerScheduleSettings(schedules=[
                    BusinessHourSchedule(weekday=1, start_time="09:00", end_time="18:00")
                ]),
                ig_story_ids=None,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
        ]
        # Monday at 10:00 Asia/Taipei (should match)
        event1 = AutoReplyEvent(message_text="", channel_type="FB", timestamp=tz.localize(datetime(2024, 7, 1, 10, 0)), ig_story_id=None)
        # Monday at 20:00 Asia/Taipei (should NOT match)
        event2 = AutoReplyEvent(message_text="", channel_type="FB", timestamp=tz.localize(datetime(2024, 7, 1, 20, 0)), ig_story_id=None)
        rule1, result1 = validate_trigger(event1)
        rule2, result2 = validate_trigger(event2)
        assert rule1 is not None and result1 == "general_match"
        assert rule2 is None and result2 == "no_match" 