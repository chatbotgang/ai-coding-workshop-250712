import pytest
from datetime import datetime, timedelta
import pytz
from internal.domain.auto_reply.auto_reply import AutoReply, AutoReplyStatus, AutoReplyEventType
from internal.domain.auto_reply.webhook_trigger import (
    WebhookTriggerScheduleType,
    WebhookTriggerScheduleSettings,
    DailySchedule,
    BusinessHourSchedule,
)
from internal.domain.auto_reply.validate_trigger import validate_trigger, AUTO_REPLY_RULES_CACHE, AutoReplyEvent

tz = pytz.timezone("Asia/Taipei")

class TestIGStoryAutoReply:
    def setup_method(self):
        AUTO_REPLY_RULES_CACHE.clear()

    # 1. IG Story Keyword Logic
    def test_story_keyword_not_triggered_without_story(self):
        AUTO_REPLY_RULES_CACHE["IG"] = [
            AutoReply(
                id=1,
                organization_id=1,
                name="Story Keyword",
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
        assert rule is None and result == "no_match"

    def test_story_keyword_triggered_with_story(self):
        AUTO_REPLY_RULES_CACHE["IG"] = [
            AutoReply(
                id=2,
                organization_id=1,
                name="Story Keyword",
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
        assert rule is not None and result == "ig_story_keyword_match"

    def test_story_keyword_wrong_story(self):
        AUTO_REPLY_RULES_CACHE["IG"] = [
            AutoReply(
                id=3,
                organization_id=1,
                name="Story Keyword",
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
        assert rule is None and result == "no_match"

    def test_story_keyword_multiple_stories(self):
        AUTO_REPLY_RULES_CACHE["IG"] = [
            AutoReply(
                id=100,
                organization_id=1,
                name="Story Keyword Multi-Story",
                status=AutoReplyStatus.ACTIVE,
                event_type=AutoReplyEventType.KEYWORD,
                priority=1,
                keywords=["hello"],
                trigger_schedule_type=None,
                trigger_schedule_settings=None,
                ig_story_ids=["story123", "story456"],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
        ]
        for story_id in ["story123", "story456"]:
            event = AutoReplyEvent(message_text="hello", channel_type="IG", timestamp=datetime.now(), ig_story_id=story_id)
            rule, result = validate_trigger(event)
            assert rule is not None and result == "ig_story_keyword_match"
        # Negative test: wrong story
        event = AutoReplyEvent(message_text="hello", channel_type="IG", timestamp=datetime.now(), ig_story_id="story789")
        rule, result = validate_trigger(event)
        assert rule is None and result == "no_match"

    # 2. IG Story General Logic
    def test_story_general_triggered_within_schedule(self):
        AUTO_REPLY_RULES_CACHE["IG"] = [
            AutoReply(
                id=4,
                organization_id=1,
                name="Story General",
                status=AutoReplyStatus.ACTIVE,
                event_type=AutoReplyEventType.TIME,
                priority=2,
                keywords=None,
                trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
                trigger_schedule_settings=WebhookTriggerScheduleSettings(schedules=[
                    DailySchedule(start_time="09:00", end_time="17:00")
                ]),
                ig_story_ids=["story123"],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
        ]
        event = AutoReplyEvent(message_text="", channel_type="IG", timestamp=tz.localize(datetime(2024, 7, 1, 14, 0)), ig_story_id="story123")
        rule, result = validate_trigger(event)
        assert rule is not None and result == "ig_story_general_match"

    def test_story_general_not_triggered_outside_schedule(self):
        AUTO_REPLY_RULES_CACHE["IG"] = [
            AutoReply(
                id=5,
                organization_id=1,
                name="Story General",
                status=AutoReplyStatus.ACTIVE,
                event_type=AutoReplyEventType.TIME,
                priority=2,
                keywords=None,
                trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
                trigger_schedule_settings=WebhookTriggerScheduleSettings(schedules=[
                    DailySchedule(start_time="09:00", end_time="17:00")
                ]),
                ig_story_ids=["story123"],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
        ]
        event = AutoReplyEvent(message_text="", channel_type="IG", timestamp=tz.localize(datetime(2024, 7, 1, 20, 0)), ig_story_id="story123")
        rule, result = validate_trigger(event)
        assert rule is None and result == "no_match"

    def test_story_general_not_triggered_wrong_story(self):
        AUTO_REPLY_RULES_CACHE["IG"] = [
            AutoReply(
                id=6,
                organization_id=1,
                name="Story General",
                status=AutoReplyStatus.ACTIVE,
                event_type=AutoReplyEventType.TIME,
                priority=2,
                keywords=None,
                trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
                trigger_schedule_settings=WebhookTriggerScheduleSettings(schedules=[
                    DailySchedule(start_time="09:00", end_time="17:00")
                ]),
                ig_story_ids=["story123"],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
        ]
        event = AutoReplyEvent(message_text="", channel_type="IG", timestamp=tz.localize(datetime(2024, 7, 1, 14, 0)), ig_story_id="story456")
        rule, result = validate_trigger(event)
        assert rule is None and result == "no_match"

    # 3. IG Story vs. General Priority
    def test_story_priority_story_keyword_over_general_keyword(self):
        AUTO_REPLY_RULES_CACHE["IG"] = [
            AutoReply(
                id=7,
                organization_id=1,
                name="Story Keyword",
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
                name="General Keyword",
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
        assert rule is not None and result == "ig_story_keyword_match"
        assert rule.ig_story_ids == ["story123"]

    def test_story_priority_story_general_over_general_time(self):
        AUTO_REPLY_RULES_CACHE["IG"] = [
            AutoReply(
                id=9,
                organization_id=1,
                name="Story General",
                status=AutoReplyStatus.ACTIVE,
                event_type=AutoReplyEventType.TIME,
                priority=2,
                keywords=None,
                trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
                trigger_schedule_settings=WebhookTriggerScheduleSettings(schedules=[
                    DailySchedule(start_time="09:00", end_time="17:00")
                ]),
                ig_story_ids=["story123"],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
            AutoReply(
                id=10,
                organization_id=1,
                name="General Time",
                status=AutoReplyStatus.ACTIVE,
                event_type=AutoReplyEventType.TIME,
                priority=2,
                keywords=None,
                trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
                trigger_schedule_settings=WebhookTriggerScheduleSettings(schedules=[
                    DailySchedule(start_time="09:00", end_time="17:00")
                ]),
                ig_story_ids=None,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
        ]
        event = AutoReplyEvent(message_text="", channel_type="IG", timestamp=tz.localize(datetime(2024, 7, 1, 14, 0)), ig_story_id="story123")
        rule, result = validate_trigger(event)
        assert rule is not None and result == "ig_story_general_match"
        assert rule.ig_story_ids == ["story123"]

    # 4. IG Story Multiple Keywords
    def test_story_multiple_keywords_triggered(self):
        AUTO_REPLY_RULES_CACHE["IG"] = [
            AutoReply(
                id=11,
                organization_id=1,
                name="Story Multi-Keyword",
                status=AutoReplyStatus.ACTIVE,
                event_type=AutoReplyEventType.KEYWORD,
                priority=1,
                keywords=["hello", "hi"],
                trigger_schedule_type=None,
                trigger_schedule_settings=None,
                ig_story_ids=["story123"],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
        ]
        for kw in ["hello", "hi"]:
            event = AutoReplyEvent(message_text=kw, channel_type="IG", timestamp=datetime.now(), ig_story_id="story123")
            rule, result = validate_trigger(event)
            assert rule is not None and result == "ig_story_keyword_match"

    def test_story_multiple_keywords_wrong_story(self):
        AUTO_REPLY_RULES_CACHE["IG"] = [
            AutoReply(
                id=12,
                organization_id=1,
                name="Story Multi-Keyword",
                status=AutoReplyStatus.ACTIVE,
                event_type=AutoReplyEventType.KEYWORD,
                priority=1,
                keywords=["hello", "hi"],
                trigger_schedule_type=None,
                trigger_schedule_settings=None,
                ig_story_ids=["story123"],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
        ]
        event = AutoReplyEvent(message_text="hello", channel_type="IG", timestamp=datetime.now(), ig_story_id="story456")
        rule, result = validate_trigger(event)
        assert rule is None and result == "no_match"

    # 5. Complete Priority System
    def test_priority_all_types_only_story_keyword(self):
        AUTO_REPLY_RULES_CACHE["IG"] = [
            AutoReply(
                id=13,
                organization_id=1,
                name="Story Keyword",
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
                id=14,
                organization_id=1,
                name="Story General",
                status=AutoReplyStatus.ACTIVE,
                event_type=AutoReplyEventType.TIME,
                priority=2,
                keywords=None,
                trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
                trigger_schedule_settings=WebhookTriggerScheduleSettings(schedules=[
                    DailySchedule(start_time="09:00", end_time="17:00")
                ]),
                ig_story_ids=["story123"],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
            AutoReply(
                id=15,
                organization_id=1,
                name="General Keyword",
                status=AutoReplyStatus.ACTIVE,
                event_type=AutoReplyEventType.KEYWORD,
                priority=1,
                keywords=["hello"],
                trigger_schedule_type=None,
                trigger_schedule_settings=None,
                ig_story_ids=None,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
            AutoReply(
                id=16,
                organization_id=1,
                name="General Time",
                status=AutoReplyStatus.ACTIVE,
                event_type=AutoReplyEventType.TIME,
                priority=2,
                keywords=None,
                trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
                trigger_schedule_settings=WebhookTriggerScheduleSettings(schedules=[
                    DailySchedule(start_time="09:00", end_time="17:00")
                ]),
                ig_story_ids=None,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
        ]
        event = AutoReplyEvent(message_text="hello", channel_type="IG", timestamp=tz.localize(datetime(2024, 7, 1, 14, 0)), ig_story_id="story123")
        rule, result = validate_trigger(event)
        assert rule is not None and result == "ig_story_keyword_match"
        assert rule.ig_story_ids == ["story123"]

    def test_priority_story_general_over_general(self):
        AUTO_REPLY_RULES_CACHE["IG"] = [
            AutoReply(
                id=17,
                organization_id=1,
                name="Story General",
                status=AutoReplyStatus.ACTIVE,
                event_type=AutoReplyEventType.TIME,
                priority=2,
                keywords=None,
                trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
                trigger_schedule_settings=WebhookTriggerScheduleSettings(schedules=[
                    DailySchedule(start_time="09:00", end_time="17:00")
                ]),
                ig_story_ids=["story123"],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
            AutoReply(
                id=18,
                organization_id=1,
                name="General Keyword",
                status=AutoReplyStatus.ACTIVE,
                event_type=AutoReplyEventType.KEYWORD,
                priority=1,
                keywords=["hello"],
                trigger_schedule_type=None,
                trigger_schedule_settings=None,
                ig_story_ids=None,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
            AutoReply(
                id=19,
                organization_id=1,
                name="General Time",
                status=AutoReplyStatus.ACTIVE,
                event_type=AutoReplyEventType.TIME,
                priority=2,
                keywords=None,
                trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
                trigger_schedule_settings=WebhookTriggerScheduleSettings(schedules=[
                    DailySchedule(start_time="09:00", end_time="17:00")
                ]),
                ig_story_ids=None,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
        ]
        event = AutoReplyEvent(message_text="", channel_type="IG", timestamp=tz.localize(datetime(2024, 7, 1, 14, 0)), ig_story_id="story123")
        rule, result = validate_trigger(event)
        assert rule is not None and result == "ig_story_general_match"
        assert rule.ig_story_ids == ["story123"]

    def test_priority_general_keyword_over_general_time(self):
        AUTO_REPLY_RULES_CACHE["IG"] = [
            AutoReply(
                id=20,
                organization_id=1,
                name="General Keyword",
                status=AutoReplyStatus.ACTIVE,
                event_type=AutoReplyEventType.KEYWORD,
                priority=1,
                keywords=["hello"],
                trigger_schedule_type=None,
                trigger_schedule_settings=None,
                ig_story_ids=None,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
            AutoReply(
                id=21,
                organization_id=1,
                name="General Time",
                status=AutoReplyStatus.ACTIVE,
                event_type=AutoReplyEventType.TIME,
                priority=2,
                keywords=None,
                trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
                trigger_schedule_settings=WebhookTriggerScheduleSettings(schedules=[
                    DailySchedule(start_time="09:00", end_time="17:00")
                ]),
                ig_story_ids=None,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
        ]
        event = AutoReplyEvent(message_text="hello", channel_type="IG", timestamp=tz.localize(datetime(2024, 7, 1, 14, 0)), ig_story_id=None)
        rule, result = validate_trigger(event)
        assert rule is not None and result == "keyword_match"
        assert rule.ig_story_ids is None

    def test_priority_only_general_time(self):
        AUTO_REPLY_RULES_CACHE["IG"] = [
            AutoReply(
                id=22,
                organization_id=1,
                name="General Time",
                status=AutoReplyStatus.ACTIVE,
                event_type=AutoReplyEventType.TIME,
                priority=2,
                keywords=None,
                trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
                trigger_schedule_settings=WebhookTriggerScheduleSettings(schedules=[
                    DailySchedule(start_time="09:00", end_time="17:00")
                ]),
                ig_story_ids=None,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
        ]
        event = AutoReplyEvent(message_text="", channel_type="IG", timestamp=tz.localize(datetime(2024, 7, 1, 14, 0)), ig_story_id=None)
        rule, result = validate_trigger(event)
        assert rule is not None and result == "general_match"
        assert rule.ig_story_ids is None

    # 6. IG Story Exclusion Logic
    def test_story_exclusion_story_keyword_no_story_id(self):
        AUTO_REPLY_RULES_CACHE["IG"] = [
            AutoReply(
                id=23,
                organization_id=1,
                name="Story Keyword",
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
        assert rule is None and result == "no_match"

    def test_story_exclusion_general_keyword(self):
        AUTO_REPLY_RULES_CACHE["IG"] = [
            AutoReply(
                id=24,
                organization_id=1,
                name="General Keyword",
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
        event = AutoReplyEvent(message_text="hello", channel_type="IG", timestamp=datetime.now(), ig_story_id=None)
        rule, result = validate_trigger(event)
        assert rule is not None and result == "keyword_match"
        assert rule.ig_story_ids is None

    def test_story_exclusion_both_story_and_general_keyword(self):
        AUTO_REPLY_RULES_CACHE["IG"] = [
            AutoReply(
                id=25,
                organization_id=1,
                name="Story Keyword",
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
                id=26,
                organization_id=1,
                name="General Keyword",
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
        event = AutoReplyEvent(message_text="hello", channel_type="IG", timestamp=datetime.now(), ig_story_id=None)
        rule, result = validate_trigger(event)
        assert rule is not None and result == "keyword_match"
        assert rule.ig_story_ids is None 