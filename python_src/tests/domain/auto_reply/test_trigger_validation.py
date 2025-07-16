"""Tests for auto-reply trigger validation based on PRD part1 test cases."""

from datetime import datetime, time

import pytest
import pytz

from internal.domain.auto_reply.auto_reply import AutoReply, AutoReplyEventType, AutoReplyStatus
from internal.domain.auto_reply.trigger_validation import AutoReplyChannelSettingAggregate, AutoReplyTriggerSetting
from internal.domain.auto_reply.webhook_trigger import (
    BusinessHourSchedule,
    ChannelType,
    DailySchedule,
    MessageEvent,
    MonthlySchedule,
    NonBusinessHourSchedule,
    WebhookTriggerEventType,
    WebhookTriggerScheduleSettings,
    WebhookTriggerScheduleType,
    WebhookTriggerSetting,
)
from internal.domain.organization.business_hour import BusinessHour, WeekDay
from internal.domain.organization.business_hour_checker import BusinessHourChecker


class TestAutoReplyTriggerSetting:
    """Test AutoReplyTriggerSetting domain model."""

    def test_is_active_when_enabled_and_not_archived(self):
        """Test that trigger is active when enabled and not archived."""
        trigger = AutoReplyTriggerSetting(
            auto_reply_id=1,
            auto_reply_name="Test",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.KEYWORD,
            auto_reply_priority=10,
            keywords=["hello"],
            webhook_trigger_id=1,
            bot_id=1,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            archived=False,
        )
        assert trigger.is_active() is True

    def test_is_not_active_when_disabled(self):
        """Test that trigger is not active when disabled."""
        trigger = AutoReplyTriggerSetting(
            auto_reply_id=1,
            auto_reply_name="Test",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.KEYWORD,
            auto_reply_priority=10,
            keywords=["hello"],
            webhook_trigger_id=1,
            bot_id=1,
            enable=False,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            archived=False,
        )
        assert trigger.is_active() is False

    def test_is_not_active_when_archived(self):
        """Test that trigger is not active when archived."""
        trigger = AutoReplyTriggerSetting(
            auto_reply_id=1,
            auto_reply_name="Test",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.KEYWORD,
            auto_reply_priority=10,
            keywords=["hello"],
            webhook_trigger_id=1,
            bot_id=1,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            archived=True,
        )
        assert trigger.is_active() is False

    def test_is_keyword_trigger(self):
        """Test keyword trigger identification."""
        trigger = AutoReplyTriggerSetting(
            auto_reply_id=1,
            auto_reply_name="Test",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.KEYWORD,
            auto_reply_priority=10,
            keywords=["hello"],
            webhook_trigger_id=1,
            bot_id=1,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert trigger.is_keyword_trigger() is True

    def test_is_general_time_trigger(self):
        """Test general time trigger identification."""
        trigger = AutoReplyTriggerSetting(
            auto_reply_id=1,
            auto_reply_name="Test",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.TIME,
            auto_reply_priority=10,
            webhook_trigger_id=1,
            bot_id=1,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
            trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert trigger.is_general_time_trigger() is True

    def test_normalize_keyword(self):
        """Test keyword normalization."""
        trigger = AutoReplyTriggerSetting(
            auto_reply_id=1,
            auto_reply_name="Test",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.KEYWORD,
            auto_reply_priority=10,
            keywords=["hello"],
            webhook_trigger_id=1,
            bot_id=1,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert trigger.normalize_keyword("  HELLO  ") == "hello"
        assert trigger.normalize_keyword("Hello") == "hello"
        assert trigger.normalize_keyword(" hello ") == "hello"

    def test_matches_keyword_case_insensitive(self):
        """Test B-P0-7-Test2: Keyword matching with various cases."""
        trigger = AutoReplyTriggerSetting(
            auto_reply_id=1,
            auto_reply_name="Test",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.KEYWORD,
            auto_reply_priority=10,
            keywords=["hello"],
            webhook_trigger_id=1,
            bot_id=1,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert trigger.matches_keyword("hello") is True
        assert trigger.matches_keyword("HELLO") is True
        assert trigger.matches_keyword("Hello") is True
        assert trigger.matches_keyword("HeLLo") is True

    def test_matches_keyword_trim_spaces(self):
        """Test B-P0-7-Test3: Keyword matching with leading/trailing spaces."""
        trigger = AutoReplyTriggerSetting(
            auto_reply_id=1,
            auto_reply_name="Test",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.KEYWORD,
            auto_reply_priority=10,
            keywords=["hello"],
            webhook_trigger_id=1,
            bot_id=1,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert trigger.matches_keyword(" hello ") is True
        assert trigger.matches_keyword("  hello  ") is True
        assert trigger.matches_keyword("\thello\n") is True

    def test_matches_keyword_exact_match_only(self):
        """Test B-P0-7-Test4: Keyword matching requires exact match."""
        trigger = AutoReplyTriggerSetting(
            auto_reply_id=1,
            auto_reply_name="Test",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.KEYWORD,
            auto_reply_priority=10,
            keywords=["hello"],
            webhook_trigger_id=1,
            bot_id=1,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert trigger.matches_keyword("hello world") is False
        assert trigger.matches_keyword("say hello") is False
        assert trigger.matches_keyword("hello!") is False

    def test_matches_keyword_no_partial_match(self):
        """Test B-P0-7-Test5: No partial or close variation matching."""
        trigger = AutoReplyTriggerSetting(
            auto_reply_id=1,
            auto_reply_name="Test",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.KEYWORD,
            auto_reply_priority=10,
            keywords=["hello"],
            webhook_trigger_id=1,
            bot_id=1,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert trigger.matches_keyword("hell") is False
        assert trigger.matches_keyword("helo") is False
        assert trigger.matches_keyword("helloo") is False

    def test_matches_multiple_keywords(self):
        """Test Multiple-Keywords-Test1: Multiple keywords support."""
        trigger = AutoReplyTriggerSetting(
            auto_reply_id=1,
            auto_reply_name="Test",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.KEYWORD,
            auto_reply_priority=10,
            keywords=["hello", "hi", "hey"],
            webhook_trigger_id=1,
            bot_id=1,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert trigger.matches_keyword("hello") is True
        assert trigger.matches_keyword("hi") is True
        assert trigger.matches_keyword("hey") is True

    def test_matches_multiple_keywords_case_insensitive(self):
        """Test Multiple-Keywords-Test2: Multiple keywords with case insensitive."""
        trigger = AutoReplyTriggerSetting(
            auto_reply_id=1,
            auto_reply_name="Test",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.KEYWORD,
            auto_reply_priority=10,
            keywords=["hello", "hi"],
            webhook_trigger_id=1,
            bot_id=1,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert trigger.matches_keyword("HELLO") is True
        assert trigger.matches_keyword("HI") is True

    def test_no_match_multiple_keywords(self):
        """Test Multiple-Keywords-Test3: No match when none of keywords match."""
        trigger = AutoReplyTriggerSetting(
            auto_reply_id=1,
            auto_reply_name="Test",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.KEYWORD,
            auto_reply_priority=10,
            keywords=["hello", "hi"],
            webhook_trigger_id=1,
            bot_id=1,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert trigger.matches_keyword("goodbye") is False
        assert trigger.matches_keyword("bye") is False


class TestAutoReplyChannelSettingAggregate:
    """Test AutoReplyChannelSettingAggregate validation logic."""

    def create_message_event(self, content: str, timestamp: datetime = None, ig_story_id: str = None) -> MessageEvent:
        """Helper to create MessageEvent."""
        if timestamp is None:
            timestamp = datetime.now(pytz.UTC)

        return MessageEvent(
            event_id="test-event-1",
            channel_type=ChannelType.LINE,
            user_id="test-user-1",
            timestamp=timestamp,
            content=content,
            message_id="test-msg-1",
            ig_story_id=ig_story_id,
        )

    def create_keyword_trigger(self, priority: int, keywords: list[str], ig_story_ids: list[str] = None) -> AutoReplyTriggerSetting:
        """Helper to create keyword trigger."""
        return AutoReplyTriggerSetting(
            auto_reply_id=1,
            auto_reply_name="Keyword Test",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.KEYWORD,
            auto_reply_priority=priority,
            keywords=keywords,
            ig_story_ids=ig_story_ids,
            webhook_trigger_id=1,
            bot_id=1,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    def create_ig_story_keyword_trigger(self, priority: int, keywords: list[str], ig_story_ids: list[str]) -> AutoReplyTriggerSetting:
        """Helper to create IG Story keyword trigger."""
        return self.create_keyword_trigger(priority, keywords, ig_story_ids)

    def create_daily_time_trigger(self, priority: int, start_time: str, end_time: str, ig_story_ids: list[str] = None) -> AutoReplyTriggerSetting:
        """Helper to create daily time trigger."""
        schedule_settings = WebhookTriggerScheduleSettings(
            schedules=[DailySchedule(start_time=start_time, end_time=end_time)]
        )
        return AutoReplyTriggerSetting(
            auto_reply_id=2,
            auto_reply_name="Daily Test",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.TIME,
            auto_reply_priority=priority,
            ig_story_ids=ig_story_ids,
            webhook_trigger_id=2,
            bot_id=1,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
            trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
            trigger_schedule_settings=schedule_settings,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    def create_ig_story_general_trigger(self, priority: int, start_time: str, end_time: str, ig_story_ids: list[str]) -> AutoReplyTriggerSetting:
        """Helper to create IG Story general trigger."""
        return self.create_daily_time_trigger(priority, start_time, end_time, ig_story_ids)

    def create_monthly_time_trigger(
        self, priority: int, day: int, start_time: str, end_time: str, ig_story_ids: list[str] = None
    ) -> AutoReplyTriggerSetting:
        """Helper to create monthly time trigger."""
        schedule_settings = WebhookTriggerScheduleSettings(
            schedules=[MonthlySchedule(day=day, start_time=start_time, end_time=end_time)]
        )
        return AutoReplyTriggerSetting(
            auto_reply_id=3,
            auto_reply_name="Monthly Test",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.TIME,
            auto_reply_priority=priority,
            ig_story_ids=ig_story_ids,
            webhook_trigger_id=3,
            bot_id=1,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
            trigger_schedule_type=WebhookTriggerScheduleType.MONTHLY,
            trigger_schedule_settings=schedule_settings,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    def create_business_hour_trigger(self, priority: int, ig_story_ids: list[str] = None) -> AutoReplyTriggerSetting:
        """Helper to create business hour trigger."""
        schedule_settings = WebhookTriggerScheduleSettings(schedules=[BusinessHourSchedule()])
        return AutoReplyTriggerSetting(
            auto_reply_id=4,
            auto_reply_name="Business Hour Test",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.TIME,
            auto_reply_priority=priority,
            ig_story_ids=ig_story_ids,
            webhook_trigger_id=4,
            bot_id=1,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
            trigger_schedule_type=WebhookTriggerScheduleType.BUSINESS_HOUR,
            trigger_schedule_settings=schedule_settings,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    def create_aggregate_with_business_hours(
        self, triggers: list[AutoReplyTriggerSetting]
    ) -> AutoReplyChannelSettingAggregate:
        """Helper to create aggregate with business hours."""
        business_hours = [
            BusinessHour(
                id=1,
                organization_id=1,
                day_of_week=WeekDay.MONDAY,  # Monday = 1
                start_time=time(9, 0),
                end_time=time(17, 0),
                is_active=True,
            ),
            BusinessHour(
                id=2,
                organization_id=1,
                day_of_week=WeekDay.TUESDAY,  # Tuesday = 2
                start_time=time(9, 0),
                end_time=time(17, 0),
                is_active=True,
            ),
        ]

        business_hour_checker = BusinessHourChecker(
            organization_id=1, timezone="Asia/Taipei", business_hours=business_hours
        )

        return AutoReplyChannelSettingAggregate(
            bot_id=1,
            organization_id=1,
            timezone="Asia/Taipei",
            trigger_settings=triggers,
            business_hour_checker=business_hour_checker,
        )

    def test_keyword_trigger_priority_over_general(self):
        """Test Priority-Test1: Keyword trigger has priority over general trigger."""
        keyword_trigger = self.create_keyword_trigger(priority=10, keywords=["hello"])
        daily_trigger = self.create_daily_time_trigger(priority=20, start_time="09:00", end_time="17:00")

        aggregate = AutoReplyChannelSettingAggregate(
            bot_id=1, organization_id=1, timezone="Asia/Taipei", trigger_settings=[keyword_trigger, daily_trigger]
        )

        # Message matches keyword and is within time window
        tz = pytz.timezone("Asia/Taipei")
        event_time = tz.localize(datetime(2024, 1, 15, 14, 0))  # Monday 2PM
        event = self.create_message_event("hello", event_time)

        result = aggregate.validate_trigger(event)
        assert result is not None
        assert result.auto_reply_id == keyword_trigger.auto_reply_id  # Keyword trigger wins

    def test_general_trigger_when_no_keyword_match(self):
        """Test Priority-Test2: General trigger when no keyword match."""
        keyword_trigger = self.create_keyword_trigger(priority=10, keywords=["hello"])
        daily_trigger = self.create_daily_time_trigger(priority=20, start_time="09:00", end_time="17:00")

        aggregate = AutoReplyChannelSettingAggregate(
            bot_id=1, organization_id=1, timezone="Asia/Taipei", trigger_settings=[keyword_trigger, daily_trigger]
        )

        # Message doesn't match keyword but is within time window
        tz = pytz.timezone("Asia/Taipei")
        event_time = tz.localize(datetime(2024, 1, 15, 14, 0))  # Monday 2PM
        event = self.create_message_event("goodbye", event_time)

        result = aggregate.validate_trigger(event)
        assert result is not None
        assert result.auto_reply_id == daily_trigger.auto_reply_id  # General trigger wins

    def test_keyword_trigger_outside_time_window(self):
        """Test Priority-Test3: Keyword trigger works outside time window."""
        keyword_trigger = self.create_keyword_trigger(priority=10, keywords=["hello"])
        daily_trigger = self.create_daily_time_trigger(priority=20, start_time="09:00", end_time="17:00")

        aggregate = AutoReplyChannelSettingAggregate(
            bot_id=1, organization_id=1, timezone="Asia/Taipei", trigger_settings=[keyword_trigger, daily_trigger]
        )

        # Message matches keyword but is outside time window
        tz = pytz.timezone("Asia/Taipei")
        event_time = tz.localize(datetime(2024, 1, 15, 20, 0))  # Monday 8PM
        event = self.create_message_event("hello", event_time)

        result = aggregate.validate_trigger(event)
        assert result is not None
        assert result.auto_reply_id == keyword_trigger.auto_reply_id  # Keyword trigger still wins

    def test_daily_schedule_matching(self):
        """Test B-P0-6-Test3: Daily schedule matching."""
        daily_trigger = self.create_daily_time_trigger(priority=10, start_time="09:00", end_time="17:00")

        aggregate = AutoReplyChannelSettingAggregate(
            bot_id=1, organization_id=1, timezone="Asia/Taipei", trigger_settings=[daily_trigger]
        )

        # Message within daily schedule
        tz = pytz.timezone("Asia/Taipei")
        event_time = tz.localize(datetime(2024, 1, 15, 14, 0))  # Monday 2PM
        event = self.create_message_event("any message", event_time)

        result = aggregate.validate_trigger(event)
        assert result is not None
        assert result.auto_reply_id == daily_trigger.auto_reply_id

    def test_daily_schedule_outside_window(self):
        """Test daily schedule outside time window."""
        daily_trigger = self.create_daily_time_trigger(priority=10, start_time="09:00", end_time="17:00")

        aggregate = AutoReplyChannelSettingAggregate(
            bot_id=1, organization_id=1, timezone="Asia/Taipei", trigger_settings=[daily_trigger]
        )

        # Message outside daily schedule
        tz = pytz.timezone("Asia/Taipei")
        event_time = tz.localize(datetime(2024, 1, 15, 20, 0))  # Monday 8PM
        event = self.create_message_event("any message", event_time)

        result = aggregate.validate_trigger(event)
        assert result is None

    def test_monthly_schedule_matching(self):
        """Test B-P0-6-Test4: Monthly schedule matching."""
        monthly_trigger = self.create_monthly_time_trigger(priority=10, day=15, start_time="10:00", end_time="12:00")

        aggregate = AutoReplyChannelSettingAggregate(
            bot_id=1, organization_id=1, timezone="Asia/Taipei", trigger_settings=[monthly_trigger]
        )

        # Message on scheduled date and time
        tz = pytz.timezone("Asia/Taipei")
        event_time = tz.localize(datetime(2024, 1, 15, 11, 0))  # 15th day, 11AM
        event = self.create_message_event("any message", event_time)

        result = aggregate.validate_trigger(event)
        assert result is not None
        assert result.auto_reply_id == monthly_trigger.auto_reply_id

    def test_monthly_schedule_wrong_day(self):
        """Test monthly schedule on wrong day."""
        monthly_trigger = self.create_monthly_time_trigger(priority=10, day=15, start_time="10:00", end_time="12:00")

        aggregate = AutoReplyChannelSettingAggregate(
            bot_id=1, organization_id=1, timezone="Asia/Taipei", trigger_settings=[monthly_trigger]
        )

        # Message on wrong day
        tz = pytz.timezone("Asia/Taipei")
        event_time = tz.localize(datetime(2024, 1, 14, 11, 0))  # 14th day, 11AM
        event = self.create_message_event("any message", event_time)

        result = aggregate.validate_trigger(event)
        assert result is None

    def test_business_hour_schedule_matching(self):
        """Test B-P0-6-Test5: Business hour schedule matching."""
        business_hour_trigger = self.create_business_hour_trigger(priority=10)

        aggregate = self.create_aggregate_with_business_hours([business_hour_trigger])

        # Message during business hours (Monday 2PM)
        tz = pytz.timezone("Asia/Taipei")
        event_time = tz.localize(datetime(2024, 1, 15, 14, 0))  # Monday 2PM
        event = self.create_message_event("any message", event_time)

        result = aggregate.validate_trigger(event)
        assert result is not None
        assert result.auto_reply_id == business_hour_trigger.auto_reply_id

    def test_business_hour_schedule_outside_hours(self):
        """Test business hour schedule outside hours."""
        business_hour_trigger = self.create_business_hour_trigger(priority=10)

        aggregate = self.create_aggregate_with_business_hours([business_hour_trigger])

        # Message outside business hours (Monday 8PM)
        tz = pytz.timezone("Asia/Taipei")
        event_time = tz.localize(datetime(2024, 1, 15, 20, 0))  # Monday 8PM
        event = self.create_message_event("any message", event_time)

        result = aggregate.validate_trigger(event)
        assert result is None

    def test_priority_sorting_within_keyword_triggers(self):
        """Test priority sorting within keyword triggers."""
        low_priority_trigger = self.create_keyword_trigger(priority=5, keywords=["hello"])
        high_priority_trigger = self.create_keyword_trigger(priority=10, keywords=["hello"])

        aggregate = AutoReplyChannelSettingAggregate(
            bot_id=1,
            organization_id=1,
            timezone="Asia/Taipei",
            trigger_settings=[low_priority_trigger, high_priority_trigger],
        )

        event = self.create_message_event("hello")
        result = aggregate.validate_trigger(event)

        assert result is not None
        assert result.auto_reply_priority == 10  # Higher priority wins

    def test_priority_sorting_within_time_triggers(self):
        """Test priority sorting within time triggers."""
        low_priority_trigger = self.create_daily_time_trigger(priority=5, start_time="09:00", end_time="17:00")
        high_priority_trigger = self.create_daily_time_trigger(priority=10, start_time="09:00", end_time="17:00")

        aggregate = AutoReplyChannelSettingAggregate(
            bot_id=1,
            organization_id=1,
            timezone="Asia/Taipei",
            trigger_settings=[low_priority_trigger, high_priority_trigger],
        )

        # Message within time window
        tz = pytz.timezone("Asia/Taipei")
        event_time = tz.localize(datetime(2024, 1, 15, 14, 0))
        event = self.create_message_event("any message", event_time)

        result = aggregate.validate_trigger(event)
        assert result is not None
        assert result.auto_reply_priority == 10  # Higher priority wins

    def test_no_match_when_no_active_triggers(self):
        """Test no match when no active triggers."""
        # Create inactive trigger
        inactive_trigger = self.create_keyword_trigger(priority=10, keywords=["hello"])
        inactive_trigger.enable = False

        aggregate = AutoReplyChannelSettingAggregate(
            bot_id=1, organization_id=1, timezone="Asia/Taipei", trigger_settings=[inactive_trigger]
        )

        event = self.create_message_event("hello")
        result = aggregate.validate_trigger(event)
        assert result is None

    def test_message_content_handling_keyword_match(self):
        """Test Message-Content-Test1: Keyword trigger with matching content."""
        keyword_trigger = self.create_keyword_trigger(priority=10, keywords=["hello"])

        aggregate = AutoReplyChannelSettingAggregate(
            bot_id=1, organization_id=1, timezone="Asia/Taipei", trigger_settings=[keyword_trigger]
        )

        event = self.create_message_event("hello")
        result = aggregate.validate_trigger(event)
        assert result is not None
        assert result.auto_reply_id == keyword_trigger.auto_reply_id

    def test_message_content_handling_no_keyword_match(self):
        """Test Message-Content-Test2: No keyword match."""
        keyword_trigger = self.create_keyword_trigger(priority=10, keywords=["hello"])

        aggregate = AutoReplyChannelSettingAggregate(
            bot_id=1, organization_id=1, timezone="Asia/Taipei", trigger_settings=[keyword_trigger]
        )

        event = self.create_message_event("goodbye")
        result = aggregate.validate_trigger(event)
        assert result is None

    def test_message_content_handling_general_trigger(self):
        """Test Message-Content-Test3: General trigger ignores content."""
        daily_trigger = self.create_daily_time_trigger(priority=10, start_time="09:00", end_time="17:00")

        aggregate = AutoReplyChannelSettingAggregate(
            bot_id=1, organization_id=1, timezone="Asia/Taipei", trigger_settings=[daily_trigger]
        )

        # Message within time window - content doesn't matter
        tz = pytz.timezone("Asia/Taipei")
        event_time = tz.localize(datetime(2024, 1, 15, 14, 0))
        event = self.create_message_event("any content", event_time)

        result = aggregate.validate_trigger(event)
        assert result is not None
        assert result.auto_reply_id == daily_trigger.auto_reply_id

    def test_daily_schedule_midnight_crossing(self):
        """Test daily schedule with midnight crossing."""
        daily_trigger = self.create_daily_time_trigger(priority=10, start_time="22:00", end_time="06:00")

        aggregate = AutoReplyChannelSettingAggregate(
            bot_id=1, organization_id=1, timezone="Asia/Taipei", trigger_settings=[daily_trigger]
        )

        # Test late night (after start time)
        tz = pytz.timezone("Asia/Taipei")
        event_time = tz.localize(datetime(2024, 1, 15, 23, 0))  # 11PM
        event = self.create_message_event("any message", event_time)

        result = aggregate.validate_trigger(event)
        assert result is not None
        assert result.auto_reply_id == daily_trigger.auto_reply_id

        # Test early morning (before end time)
        event_time = tz.localize(datetime(2024, 1, 15, 5, 0))  # 5AM
        event = self.create_message_event("any message", event_time)

        result = aggregate.validate_trigger(event)
        assert result is not None
        assert result.auto_reply_id == daily_trigger.auto_reply_id

    def test_monthly_schedule_midnight_crossing(self):
        """Test monthly schedule with midnight crossing."""
        monthly_trigger = self.create_monthly_time_trigger(priority=10, day=15, start_time="22:00", end_time="06:00")

        aggregate = AutoReplyChannelSettingAggregate(
            bot_id=1, organization_id=1, timezone="Asia/Taipei", trigger_settings=[monthly_trigger]
        )

        # Test late night (after start time)
        tz = pytz.timezone("Asia/Taipei")
        event_time = tz.localize(datetime(2024, 1, 15, 23, 0))  # 15th day, 11PM
        event = self.create_message_event("any message", event_time)

        result = aggregate.validate_trigger(event)
        assert result is not None
        assert result.auto_reply_id == monthly_trigger.auto_reply_id

        # Test early morning (before end time)
        event_time = tz.localize(datetime(2024, 1, 15, 5, 0))  # 15th day, 5AM
        event = self.create_message_event("any message", event_time)

        result = aggregate.validate_trigger(event)
        assert result is not None
        assert result.auto_reply_id == monthly_trigger.auto_reply_id

    def test_timezone_conversion(self):
        """Test timezone conversion works correctly."""
        daily_trigger = self.create_daily_time_trigger(priority=10, start_time="09:00", end_time="17:00")

        aggregate = AutoReplyChannelSettingAggregate(
            bot_id=1, organization_id=1, timezone="Asia/Taipei", trigger_settings=[daily_trigger]
        )

        # Message in UTC that should be within Asia/Taipei business hours
        utc_time = datetime(2024, 1, 15, 6, 0, tzinfo=pytz.UTC)  # 6AM UTC = 2PM Taipei
        event = self.create_message_event("any message", utc_time)

        result = aggregate.validate_trigger(event)
        assert result is not None
        assert result.auto_reply_id == daily_trigger.auto_reply_id

    def test_timezone_conversion_different_timezones(self):
        """Test timezone conversion with different timezones."""
        daily_trigger = self.create_daily_time_trigger(priority=10, start_time="09:00", end_time="17:00")

        # Test with US/Eastern timezone
        aggregate = AutoReplyChannelSettingAggregate(
            bot_id=1, organization_id=1, timezone="US/Eastern", trigger_settings=[daily_trigger]
        )

        # UTC time that should be within US/Eastern business hours
        utc_time = datetime(2024, 1, 15, 19, 0, tzinfo=pytz.UTC)  # 7PM UTC = 2PM EST
        event = self.create_message_event("any message", utc_time)

        result = aggregate.validate_trigger(event)
        assert result is not None
        assert result.auto_reply_id == daily_trigger.auto_reply_id

        # UTC time that should be outside US/Eastern business hours
        utc_time = datetime(2024, 1, 15, 4, 0, tzinfo=pytz.UTC)  # 4AM UTC = 11PM EST (previous day)
        event = self.create_message_event("any message", utc_time)

        result = aggregate.validate_trigger(event)
        assert result is None

    def test_business_hour_timezone_consistency(self):
        """Test business hour timezone consistency with organization timezone."""
        business_hour_trigger = self.create_business_hour_trigger(priority=10)

        # Create aggregate with different timezone
        business_hours = [
            BusinessHour(
                id=1,
                organization_id=1,
                day_of_week=WeekDay.MONDAY,  # Monday = 1
                start_time=time(9, 0),
                end_time=time(17, 0),
                is_active=True,
            )
        ]

        business_hour_checker = BusinessHourChecker(
            organization_id=1, timezone="US/Eastern", business_hours=business_hours
        )

        aggregate = AutoReplyChannelSettingAggregate(
            bot_id=1,
            organization_id=1,
            timezone="US/Eastern",
            trigger_settings=[business_hour_trigger],
            business_hour_checker=business_hour_checker,
        )

        # Test message during business hours in US/Eastern
        est_tz = pytz.timezone("US/Eastern")
        event_time = est_tz.localize(datetime(2024, 1, 15, 14, 0))  # Monday 2PM EST
        event = self.create_message_event("any message", event_time)

        result = aggregate.validate_trigger(event)
        assert result is not None
        assert result.auto_reply_id == business_hour_trigger.auto_reply_id

    def test_daylight_saving_time_handling(self):
        """Test handling of daylight saving time transitions."""
        daily_trigger = self.create_daily_time_trigger(priority=10, start_time="09:00", end_time="17:00")

        aggregate = AutoReplyChannelSettingAggregate(
            bot_id=1, organization_id=1, timezone="US/Eastern", trigger_settings=[daily_trigger]
        )

        # Test during standard time (EST)
        est_time = datetime(2024, 1, 15, 14, 0)  # January is EST
        est_tz = pytz.timezone("US/Eastern")
        event_time = est_tz.localize(est_time)
        event = self.create_message_event("any message", event_time)

        result = aggregate.validate_trigger(event)
        assert result is not None
        assert result.auto_reply_id == daily_trigger.auto_reply_id

        # Test during daylight time (EDT)
        edt_time = datetime(2024, 7, 15, 14, 0)  # July is EDT
        event_time = est_tz.localize(edt_time)
        event = self.create_message_event("any message", event_time)

        result = aggregate.validate_trigger(event)
        assert result is not None
        assert result.auto_reply_id == daily_trigger.auto_reply_id


class TestIGStoryTriggerValidation:
    """Test IG Story-specific trigger validation based on PRD part2."""

    def create_message_event(self, content: str, timestamp: datetime = None, ig_story_id: str = None) -> MessageEvent:
        """Helper to create MessageEvent."""
        if timestamp is None:
            timestamp = datetime.now(pytz.UTC)

        return MessageEvent(
            event_id="test-event-1",
            channel_type=ChannelType.IG,
            user_id="test-user-1",
            timestamp=timestamp,
            content=content,
            message_id="test-msg-1",
            ig_story_id=ig_story_id,
        )

    def create_ig_story_keyword_trigger(self, priority: int, keywords: list[str], ig_story_ids: list[str]) -> AutoReplyTriggerSetting:
        """Helper to create IG Story keyword trigger."""
        return AutoReplyTriggerSetting(
            auto_reply_id=101,
            auto_reply_name="IG Story Keyword Test",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.KEYWORD,
            auto_reply_priority=priority,
            keywords=keywords,
            ig_story_ids=ig_story_ids,
            webhook_trigger_id=101,
            bot_id=1,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    def create_ig_story_general_trigger(self, priority: int, start_time: str, end_time: str, ig_story_ids: list[str]) -> AutoReplyTriggerSetting:
        """Helper to create IG Story general trigger."""
        schedule_settings = WebhookTriggerScheduleSettings(
            schedules=[DailySchedule(start_time=start_time, end_time=end_time)]
        )
        return AutoReplyTriggerSetting(
            auto_reply_id=102,
            auto_reply_name="IG Story General Test",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.TIME,
            auto_reply_priority=priority,
            ig_story_ids=ig_story_ids,
            webhook_trigger_id=102,
            bot_id=1,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
            trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
            trigger_schedule_settings=schedule_settings,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    def create_general_keyword_trigger(self, priority: int, keywords: list[str]) -> AutoReplyTriggerSetting:
        """Helper to create general keyword trigger."""
        return AutoReplyTriggerSetting(
            auto_reply_id=103,
            auto_reply_name="General Keyword Test",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.KEYWORD,
            auto_reply_priority=priority,
            keywords=keywords,
            webhook_trigger_id=103,
            bot_id=1,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    def create_general_time_trigger(self, priority: int, start_time: str, end_time: str) -> AutoReplyTriggerSetting:
        """Helper to create general time trigger."""
        schedule_settings = WebhookTriggerScheduleSettings(
            schedules=[DailySchedule(start_time=start_time, end_time=end_time)]
        )
        return AutoReplyTriggerSetting(
            auto_reply_id=104,
            auto_reply_name="General Time Test",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.TIME,
            auto_reply_priority=priority,
            webhook_trigger_id=104,
            bot_id=1,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
            trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
            trigger_schedule_settings=schedule_settings,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    @pytest.mark.parametrize("test_case_id,keyword,story_id_configured,story_id_sent,expected_result", [
        ("B-P1-18-Test7", "hello", "story123", "story456", False),  # Wrong story
        ("B-P1-18-Test8a", "hello", "story123", "story123", True),   # Matching story and keyword
        ("IG-Story-Keyword-Test1", "hello", "story123", "story123", True),  # Basic match
        ("IG-Story-Keyword-Test2", "hello", "story123", "story456", False), # Wrong story ID
        ("IG-Story-Keyword-Test3", "hello", "story123", None, False),       # No story context
    ])
    def test_ig_story_keyword_scenarios(self, test_case_id, keyword, story_id_configured, story_id_sent, expected_result):
        """Test various IG Story keyword scenarios using parametrized tests."""
        ig_story_trigger = self.create_ig_story_keyword_trigger(
            priority=10, keywords=[keyword], ig_story_ids=[story_id_configured]
        )
        
        aggregate = AutoReplyChannelSettingAggregate(
            bot_id=1, 
            organization_id=1, 
            timezone="Asia/Taipei", 
            trigger_settings=[ig_story_trigger]
        )
        
        event = self.create_message_event(keyword, ig_story_id=story_id_sent)
        result = aggregate.validate_trigger(event)
        
        if expected_result:
            assert result is not None, f"Test {test_case_id} failed: expected trigger to activate"
            assert result.auto_reply_id == ig_story_trigger.auto_reply_id
        else:
            assert result is None, f"Test {test_case_id} failed: expected trigger NOT to activate"

    @pytest.mark.parametrize("test_case_id,event_hour,story_id_configured,story_id_sent,expected_result", [
        ("B-P1-18-Test8b", 14, "story123", "story123", True),   # Matching story and schedule
        ("IG-Story-General-Test1", 14, "story123", "story123", True),  # Basic match
        ("IG-Story-General-Test2", 20, "story123", "story123", False), # Outside schedule
        ("IG-Story-General-Test3", 14, "story123", "story456", False), # Wrong story ID
    ])
    def test_ig_story_general_scenarios(self, test_case_id, event_hour, story_id_configured, story_id_sent, expected_result):
        """Test various IG Story general trigger scenarios using parametrized tests."""
        ig_story_general_trigger = self.create_ig_story_general_trigger(
            priority=10, start_time="09:00", end_time="17:00", ig_story_ids=[story_id_configured]
        )
        
        aggregate = AutoReplyChannelSettingAggregate(
            bot_id=1, 
            organization_id=1, 
            timezone="Asia/Taipei", 
            trigger_settings=[ig_story_general_trigger]
        )
        
        tz = pytz.timezone("Asia/Taipei")
        event_time = tz.localize(datetime(2024, 1, 15, event_hour, 0))
        event = self.create_message_event("any message", event_time, ig_story_id=story_id_sent)
        
        result = aggregate.validate_trigger(event)
        
        if expected_result:
            assert result is not None, f"Test {test_case_id} failed: expected trigger to activate"
            assert result.auto_reply_id == ig_story_general_trigger.auto_reply_id
        else:
            assert result is None, f"Test {test_case_id} failed: expected trigger NOT to activate"

    def test_ig_story_priority_over_general(self):
        """Test B-P1-18-Test9: IG Story priority over general triggers."""
        ig_story_keyword_trigger = self.create_ig_story_keyword_trigger(
            priority=10, keywords=["hello"], ig_story_ids=["story123"]
        )
        general_keyword_trigger = self.create_general_keyword_trigger(
            priority=20, keywords=["hello"]
        )
        
        aggregate = AutoReplyChannelSettingAggregate(
            bot_id=1, 
            organization_id=1, 
            timezone="Asia/Taipei", 
            trigger_settings=[ig_story_keyword_trigger, general_keyword_trigger]
        )
        
        event = self.create_message_event("hello", ig_story_id="story123")
        result = aggregate.validate_trigger(event)
        assert result is not None
        assert result.auto_reply_id == ig_story_keyword_trigger.auto_reply_id

    def test_ig_story_keyword_priority_over_general_keyword(self):
        """Test IG-Story-Priority-Test1: IG Story keyword priority over general keyword."""
        ig_story_keyword_trigger = self.create_ig_story_keyword_trigger(
            priority=5, keywords=["hello"], ig_story_ids=["story123"]
        )
        general_keyword_trigger = self.create_general_keyword_trigger(
            priority=10, keywords=["hello"]
        )
        
        aggregate = AutoReplyChannelSettingAggregate(
            bot_id=1, 
            organization_id=1, 
            timezone="Asia/Taipei", 
            trigger_settings=[ig_story_keyword_trigger, general_keyword_trigger]
        )
        
        event = self.create_message_event("hello", ig_story_id="story123")
        result = aggregate.validate_trigger(event)
        assert result is not None
        assert result.auto_reply_id == ig_story_keyword_trigger.auto_reply_id

    def test_ig_story_general_priority_over_general_time(self):
        """Test IG-Story-Priority-Test2: IG Story general priority over general time-based."""
        ig_story_general_trigger = self.create_ig_story_general_trigger(
            priority=5, start_time="09:00", end_time="17:00", ig_story_ids=["story123"]
        )
        general_time_trigger = self.create_general_time_trigger(
            priority=10, start_time="09:00", end_time="17:00"
        )
        
        aggregate = AutoReplyChannelSettingAggregate(
            bot_id=1, 
            organization_id=1, 
            timezone="Asia/Taipei", 
            trigger_settings=[ig_story_general_trigger, general_time_trigger]
        )
        
        tz = pytz.timezone("Asia/Taipei")
        event_time = tz.localize(datetime(2024, 1, 15, 14, 0))
        event = self.create_message_event("any message", event_time, ig_story_id="story123")
        
        result = aggregate.validate_trigger(event)
        assert result is not None
        assert result.auto_reply_id == ig_story_general_trigger.auto_reply_id

    @pytest.mark.parametrize("test_case_id,keyword,story_id_sent,expected_result", [
        ("IG-Story-Multiple-Keywords-Test1", "hello", "story123", True),  # First keyword, correct story
        ("IG-Story-Multiple-Keywords-Test1", "hi", "story123", True),     # Second keyword, correct story
        ("IG-Story-Multiple-Keywords-Test2", "hello", "story456", False), # First keyword, wrong story
        ("IG-Story-Multiple-Keywords-Test2", "hi", "story456", False),    # Second keyword, wrong story
    ])
    def test_ig_story_multiple_keywords_scenarios(self, test_case_id, keyword, story_id_sent, expected_result):
        """Test IG Story multiple keywords scenarios using parametrized tests."""
        ig_story_trigger = self.create_ig_story_keyword_trigger(
            priority=10, keywords=["hello", "hi"], ig_story_ids=["story123"]
        )
        
        aggregate = AutoReplyChannelSettingAggregate(
            bot_id=1, 
            organization_id=1, 
            timezone="Asia/Taipei", 
            trigger_settings=[ig_story_trigger]
        )
        
        event = self.create_message_event(keyword, ig_story_id=story_id_sent)
        result = aggregate.validate_trigger(event)
        
        if expected_result:
            assert result is not None, f"Test {test_case_id} failed: expected trigger to activate for keyword '{keyword}'"
            assert result.auto_reply_id == ig_story_trigger.auto_reply_id
        else:
            assert result is None, f"Test {test_case_id} failed: expected trigger NOT to activate for keyword '{keyword}'"

    @pytest.mark.parametrize("test_case_id,message_content,ig_story_id,expected_trigger_id", [
        ("Complete-Priority-Test1", "hello", "story123", 101),  # IG Story Keyword (highest priority)
        ("Complete-Priority-Test2", "goodbye", "story123", 102),  # IG Story General (priority 2)
        ("Complete-Priority-Test3", "hello", None, 103),         # General Keyword (priority 3)
        ("Complete-Priority-Test4", "any message", None, 104),   # General Time (priority 4)
    ])
    def test_complete_priority_system(self, test_case_id, message_content, ig_story_id, expected_trigger_id):
        """Test complete priority system with all 4 trigger types using parametrized tests."""
        # Create all 4 types of triggers
        ig_story_keyword_trigger = self.create_ig_story_keyword_trigger(
            priority=1, keywords=["hello"], ig_story_ids=["story123"]
        )
        ig_story_general_trigger = self.create_ig_story_general_trigger(
            priority=2, start_time="09:00", end_time="17:00", ig_story_ids=["story123"]
        )
        general_keyword_trigger = self.create_general_keyword_trigger(
            priority=3, keywords=["hello"]
        )
        general_time_trigger = self.create_general_time_trigger(
            priority=4, start_time="09:00", end_time="17:00"
        )
        
        # For test cases 2-4, we need to exclude higher priority triggers to test specific scenarios
        if test_case_id == "Complete-Priority-Test2":
            # Test IG Story General - exclude IG Story Keyword
            triggers = [ig_story_general_trigger, general_keyword_trigger, general_time_trigger]
        elif test_case_id == "Complete-Priority-Test3":
            # Test General Keyword - exclude IG Story triggers
            triggers = [general_keyword_trigger, general_time_trigger]
        elif test_case_id == "Complete-Priority-Test4":
            # Test General Time - exclude all other triggers
            triggers = [general_time_trigger]
        else:
            # Complete-Priority-Test1: Include all triggers to test highest priority
            triggers = [ig_story_keyword_trigger, ig_story_general_trigger, general_keyword_trigger, general_time_trigger]
        
        aggregate = AutoReplyChannelSettingAggregate(
            bot_id=1, 
            organization_id=1, 
            timezone="Asia/Taipei", 
            trigger_settings=triggers
        )
        
        tz = pytz.timezone("Asia/Taipei")
        event_time = tz.localize(datetime(2024, 1, 15, 14, 0))  # Within schedule
        event = self.create_message_event(message_content, event_time, ig_story_id=ig_story_id)
        
        result = aggregate.validate_trigger(event)
        assert result is not None, f"Test {test_case_id} failed: expected trigger to activate"
        assert result.auto_reply_id == expected_trigger_id, f"Test {test_case_id} failed: expected trigger ID {expected_trigger_id}, got {result.auto_reply_id}"

    @pytest.mark.parametrize("test_case_id,has_ig_story_trigger,has_general_trigger,ig_story_id,expected_trigger_id", [
        ("IG-Story-Exclusion-Test1", True, False, None, None),      # IG Story only, no story ID -> no trigger
        ("IG-Story-Exclusion-Test2", False, True, None, 103),       # General only, no story ID -> general trigger
        ("IG-Story-Exclusion-Test3", True, True, None, 103),        # Both triggers, no story ID -> general trigger only
    ])
    def test_ig_story_exclusion_scenarios(self, test_case_id, has_ig_story_trigger, has_general_trigger, ig_story_id, expected_trigger_id):
        """Test IG Story exclusion logic using parametrized tests."""
        triggers = []
        
        if has_ig_story_trigger:
            ig_story_keyword_trigger = self.create_ig_story_keyword_trigger(
                priority=10, keywords=["hello"], ig_story_ids=["story123"]
            )
            triggers.append(ig_story_keyword_trigger)
        
        if has_general_trigger:
            general_keyword_trigger = self.create_general_keyword_trigger(
                priority=5, keywords=["hello"]
            )
            triggers.append(general_keyword_trigger)
        
        aggregate = AutoReplyChannelSettingAggregate(
            bot_id=1, 
            organization_id=1, 
            timezone="Asia/Taipei", 
            trigger_settings=triggers
        )
        
        event = self.create_message_event("hello", ig_story_id=ig_story_id)
        result = aggregate.validate_trigger(event)
        
        if expected_trigger_id is None:
            assert result is None, f"Test {test_case_id} failed: expected no trigger to activate"
        else:
            assert result is not None, f"Test {test_case_id} failed: expected trigger to activate"
            assert result.auto_reply_id == expected_trigger_id, f"Test {test_case_id} failed: expected trigger ID {expected_trigger_id}, got {result.auto_reply_id}"
