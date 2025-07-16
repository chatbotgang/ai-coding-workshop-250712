"""Comprehensive tests for auto-reply trigger validation logic.

Tests all use cases specified in the PRD including:
- Keyword Reply Logic (B-P0-7-Test2, B-P0-7-Test3, B-P0-7-Test4, B-P0-7-Test5)
- Multiple Keywords Support (Multiple-Keywords-Test1, Multiple-Keywords-Test2, Multiple-Keywords-Test3)
- General Time-based Logic (B-P0-6-Test3, B-P0-6-Test4, B-P0-6-Test5)
- Priority Logic (Priority-Test1, Priority-Test2, Priority-Test3)
- Message Content Handling (Message-Content-Test1, Message-Content-Test2, Message-Content-Test3)
"""

import pytest
import pytz
from datetime import datetime, time
from internal.domain.auto_reply.auto_reply import (
    AutoReplyTriggerSetting,
    AutoReplyChannelSettingAggregate,
    AutoReplyStatus,
    AutoReplyEventType,
)
from internal.domain.auto_reply.webhook_trigger import (
    WebhookTriggerEventType,
    WebhookTriggerScheduleType,
    MessageEvent,
    ChannelType,
    BusinessHour,
)


class TestKeywordReplyLogic:
    """Test keyword reply logic as specified in PRD Story 1."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.keyword_trigger = AutoReplyTriggerSetting(
            auto_reply_id=1,
            auto_reply_name="Hello Keyword",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.KEYWORD,
            auto_reply_priority=10,
            keywords=["hello"],
            webhook_trigger_id=1,
            bot_id=100,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
        )
        
        self.aggregate = AutoReplyChannelSettingAggregate(
            bot_id=100,
            trigger_settings=[self.keyword_trigger],
            business_hours=[],
            timezone="Asia/Taipei",
        )
    
    def test_keyword_exact_match_various_cases(self):
        """B-P0-7-Test2: Test triggering with exact keyword in various cases."""
        test_cases = [
            "hello",      # exact match
            "HELLO",      # uppercase
            "Hello",      # mixed case
            "hELLo",      # mixed case
        ]
        
        for content in test_cases:
            event = MessageEvent(
                event_id="test-1",
                channel_type=ChannelType.LINE,
                user_id="user1",
                timestamp=datetime.now(),
                content=content,
                message_id="msg1",
            )
            
            result = self.aggregate.validate_trigger(event)
            assert result is not None, f"Should match keyword '{content}'"
            assert result.auto_reply_id == 1
    
    def test_keyword_with_leading_trailing_spaces(self):
        """B-P0-7-Test3: Test triggering with keyword surrounded by spaces."""
        test_cases = [
            " hello",      # leading space
            "hello ",      # trailing space
            " hello ",     # both spaces
            "  hello  ",   # multiple spaces
        ]
        
        for content in test_cases:
            event = MessageEvent(
                event_id="test-2",
                channel_type=ChannelType.LINE,
                user_id="user1",
                timestamp=datetime.now(),
                content=content,
                message_id="msg2",
            )
            
            result = self.aggregate.validate_trigger(event)
            assert result is not None, f"Should match keyword with spaces '{content}'"
            assert result.auto_reply_id == 1
    
    def test_keyword_partial_match_not_triggered(self):
        """B-P0-7-Test4: Test that partial matches do not trigger."""
        test_cases = [
            "hello world",    # contains keyword but has extra text
            "say hello",      # keyword at end with prefix
            "hello there!",   # keyword at start with suffix
            "well hello there", # keyword in middle
        ]
        
        for content in test_cases:
            event = MessageEvent(
                event_id="test-3",
                channel_type=ChannelType.LINE,
                user_id="user1",
                timestamp=datetime.now(),
                content=content,
                message_id="msg3",
            )
            
            result = self.aggregate.validate_trigger(event)
            assert result is None, f"Should NOT match partial keyword '{content}'"
    
    def test_keyword_close_variation_not_triggered(self):
        """B-P0-7-Test5: Test that close variations do not trigger."""
        test_cases = [
            "helo",        # missing letter
            "helloo",      # extra letter
            "hellooo",     # extra letters
            "hell",        # partial word
            "hellow",      # wrong letter
        ]
        
        for content in test_cases:
            event = MessageEvent(
                event_id="test-4",
                channel_type=ChannelType.LINE,
                user_id="user1",
                timestamp=datetime.now(),
                content=content,
                message_id="msg4",
            )
            
            result = self.aggregate.validate_trigger(event)
            assert result is None, f"Should NOT match variation '{content}'"


class TestMultipleKeywordsSupport:
    """Test multiple keywords support as specified in PRD Story 2."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.multi_keyword_trigger = AutoReplyTriggerSetting(
            auto_reply_id=2,
            auto_reply_name="Multi Keyword",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.KEYWORD,
            auto_reply_priority=15,
            keywords=["hello", "hi", "hey"],
            webhook_trigger_id=2,
            bot_id=100,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
        )
        
        self.aggregate = AutoReplyChannelSettingAggregate(
            bot_id=100,
            trigger_settings=[self.multi_keyword_trigger],
            business_hours=[],
            timezone="Asia/Taipei",
        )
    
    def test_multiple_keywords_each_triggers(self):
        """Multiple-Keywords-Test1: Test each keyword triggers the same rule."""
        keywords = ["hello", "hi", "hey"]
        
        for keyword in keywords:
            event = MessageEvent(
                event_id=f"test-{keyword}",
                channel_type=ChannelType.LINE,
                user_id="user1",
                timestamp=datetime.now(),
                content=keyword,
                message_id=f"msg-{keyword}",
            )
            
            result = self.aggregate.validate_trigger(event)
            assert result is not None, f"Keyword '{keyword}' should trigger"
            assert result.auto_reply_id == 2
    
    def test_multiple_keywords_case_insensitive(self):
        """Multiple-Keywords-Test2: Test case insensitive matching for multiple keywords."""
        test_cases = [
            ("HELLO", "hello"),
            ("HI", "hi"), 
            ("Hey", "hey"),
            ("HEY", "hey"),
        ]
        
        for content, expected_keyword in test_cases:
            event = MessageEvent(
                event_id=f"test-{content}",
                channel_type=ChannelType.LINE,
                user_id="user1",
                timestamp=datetime.now(),
                content=content,
                message_id=f"msg-{content}",
            )
            
            result = self.aggregate.validate_trigger(event)
            assert result is not None, f"'{content}' should match '{expected_keyword}'"
            assert result.auto_reply_id == 2
    
    def test_multiple_keywords_no_match(self):
        """Multiple-Keywords-Test3: Test non-matching keywords."""
        non_matching_cases = [
            "goodbye",
            "thanks", 
            "help",
            "hello world",  # partial match
        ]
        
        for content in non_matching_cases:
            event = MessageEvent(
                event_id=f"test-{content}",
                channel_type=ChannelType.LINE,
                user_id="user1",
                timestamp=datetime.now(),
                content=content,
                message_id=f"msg-{content}",
            )
            
            result = self.aggregate.validate_trigger(event)
            assert result is None, f"'{content}' should not match any keyword"


class TestGeneralTimeBasedLogic:
    """Test general time-based logic as specified in PRD Story 3."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.daily_trigger = AutoReplyTriggerSetting(
            auto_reply_id=3,
            auto_reply_name="Daily Trigger",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.TIME,
            auto_reply_priority=5,
            keywords=None,
            webhook_trigger_id=3,
            bot_id=100,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
            trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
            trigger_schedule_settings={
                "schedules": [{"start_time": "09:00", "end_time": "17:00"}]
            },
        )
        
        self.monthly_trigger = AutoReplyTriggerSetting(
            auto_reply_id=4,
            auto_reply_name="Monthly Trigger",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.TIME,
            auto_reply_priority=8,
            keywords=None,
            webhook_trigger_id=4,
            bot_id=100,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
            trigger_schedule_type=WebhookTriggerScheduleType.MONTHLY,
            trigger_schedule_settings={
                "schedules": [{"day": 15, "start_time": "10:00", "end_time": "12:00"}]
            },
        )
        
        self.business_hour_trigger = AutoReplyTriggerSetting(
            auto_reply_id=5,
            auto_reply_name="Business Hour Trigger",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.TIME,
            auto_reply_priority=6,
            keywords=None,
            webhook_trigger_id=5,
            bot_id=100,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
            trigger_schedule_type=WebhookTriggerScheduleType.BUSINESS_HOUR,
            trigger_schedule_settings=None,
        )
        
        # Business hours: Monday-Friday 9:00-18:00
        business_hours = [
            BusinessHour(weekday=1, start_time="09:00", end_time="18:00"),  # Monday
            BusinessHour(weekday=2, start_time="09:00", end_time="18:00"),  # Tuesday
            BusinessHour(weekday=3, start_time="09:00", end_time="18:00"),  # Wednesday
            BusinessHour(weekday=4, start_time="09:00", end_time="18:00"),  # Thursday
            BusinessHour(weekday=5, start_time="09:00", end_time="18:00"),  # Friday
        ]
        
        self.aggregate = AutoReplyChannelSettingAggregate(
            bot_id=100,
            trigger_settings=[self.daily_trigger, self.monthly_trigger, self.business_hour_trigger],
            business_hours=business_hours,
            timezone="Asia/Taipei",
        )
    
    def test_daily_schedule_within_time_window(self):
        """B-P0-6-Test3: Test daily schedule triggering within time window."""
        # Create event during daily window (9:00-17:00)
        event_time = datetime(2023, 10, 15, 14, 30)  # 2:30 PM
        event = MessageEvent(
            event_id="daily-test",
            channel_type=ChannelType.LINE,
            user_id="user1",
            timestamp=event_time,
            content="any message",
            message_id="daily-msg",
        )
        
        result = self.aggregate.validate_trigger(event)
        assert result is not None, "Should trigger during daily time window"
        # Should get the daily trigger (priority 5)
        assert result.auto_reply_id == 3
    
    def test_monthly_schedule_on_correct_date(self):
        """B-P0-6-Test4: Test monthly schedule triggering on correct date and time."""
        # Create event on 15th of month during time window (10:00-12:00)
        event_time = datetime(2023, 10, 15, 11, 0)  # 11:00 AM on 15th
        event = MessageEvent(
            event_id="monthly-test",
            channel_type=ChannelType.LINE,
            user_id="user1",
            timestamp=event_time,
            content="any message",
            message_id="monthly-msg",
        )
        
        result = self.aggregate.validate_trigger(event)
        assert result is not None, "Should trigger on monthly schedule"
        # Should get monthly trigger (priority 8, higher than daily priority 5)
        assert result.auto_reply_id == 4
    
    def test_business_hours_schedule(self):
        """B-P0-6-Test5: Test business hours schedule."""
        # Test during business hours (Monday 10:00 AM)
        event_time = datetime(2023, 10, 16, 10, 0)  # Monday 10:00 AM
        event = MessageEvent(
            event_id="business-test",
            channel_type=ChannelType.LINE,
            user_id="user1",
            timestamp=event_time,
            content="any message",
            message_id="business-msg",
        )
        
        result = self.aggregate.validate_trigger(event)
        assert result is not None, "Should trigger during business hours"
        # Business hour has priority 6, daily has priority 5, so business hour should win
        assert result.auto_reply_id == 5
        
        # Test outside business hours (Saturday)
        weekend_time = datetime(2023, 10, 14, 10, 0)  # Saturday 10:00 AM
        weekend_event = MessageEvent(
            event_id="weekend-test",
            channel_type=ChannelType.LINE,
            user_id="user1",
            timestamp=weekend_time,
            content="any message",
            message_id="weekend-msg",
        )
        
        result = self.aggregate.validate_trigger(weekend_event)
        # Should still get daily trigger since it's within daily hours
        assert result is not None
        assert result.auto_reply_id == 3  # Daily trigger


class TestPriorityLogic:
    """Test priority logic as specified in PRD Story 4."""
    
    def setup_method(self):
        """Set up test fixtures with both keyword and general triggers."""
        self.keyword_trigger = AutoReplyTriggerSetting(
            auto_reply_id=10,
            auto_reply_name="Priority Keyword",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.KEYWORD,
            auto_reply_priority=20,
            keywords=["test"],
            webhook_trigger_id=10,
            bot_id=100,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
        )
        
        self.general_trigger = AutoReplyTriggerSetting(
            auto_reply_id=11,
            auto_reply_name="Priority General",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.TIME,
            auto_reply_priority=30,  # Higher priority than keyword, but should still lose
            keywords=None,
            webhook_trigger_id=11,
            bot_id=100,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
            trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
            trigger_schedule_settings={
                "schedules": [{"start_time": "00:00", "end_time": "23:59"}]
            },
        )
        
        self.aggregate = AutoReplyChannelSettingAggregate(
            bot_id=100,
            trigger_settings=[self.keyword_trigger, self.general_trigger],
            business_hours=[],
            timezone="Asia/Taipei",
        )
    
    def test_keyword_priority_over_general_when_matches(self):
        """Priority-Test1: Keyword reply has priority over general when keyword matches."""
        event = MessageEvent(
            event_id="priority-test-1",
            channel_type=ChannelType.LINE,
            user_id="user1",
            timestamp=datetime(2023, 10, 15, 12, 0),  # Within general trigger time
            content="test",  # Matches keyword
            message_id="priority-msg-1",
        )
        
        result = self.aggregate.validate_trigger(event)
        assert result is not None, "Should trigger some auto-reply"
        assert result.auto_reply_id == 10, "Should trigger keyword reply, not general"
    
    def test_general_triggers_when_no_keyword_match(self):
        """Priority-Test2: General reply triggers when no keyword match."""
        event = MessageEvent(
            event_id="priority-test-2",
            channel_type=ChannelType.LINE,
            user_id="user1",
            timestamp=datetime(2023, 10, 15, 12, 0),  # Within general trigger time
            content="hello",  # Does not match keyword "test"
            message_id="priority-msg-2",
        )
        
        result = self.aggregate.validate_trigger(event)
        assert result is not None, "Should trigger general reply"
        assert result.auto_reply_id == 11, "Should trigger general reply"
    
    def test_keyword_triggers_outside_general_time(self):
        """Priority-Test3: Keyword reply triggers even outside general time window."""
        # This is tricky since our general trigger is 00:00-23:59, so let's modify it
        limited_general = AutoReplyTriggerSetting(
            auto_reply_id=12,
            auto_reply_name="Limited General",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.TIME,
            auto_reply_priority=30,
            keywords=None,
            webhook_trigger_id=12,
            bot_id=100,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
            trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
            trigger_schedule_settings={
                "schedules": [{"start_time": "09:00", "end_time": "17:00"}]
            },
        )
        
        limited_aggregate = AutoReplyChannelSettingAggregate(
            bot_id=100,
            trigger_settings=[self.keyword_trigger, limited_general],
            business_hours=[],
            timezone="Asia/Taipei",
        )
        
        event = MessageEvent(
            event_id="priority-test-3",
            channel_type=ChannelType.LINE,
            user_id="user1",
            timestamp=datetime(2023, 10, 15, 20, 0),  # Outside general trigger time (9-17)
            content="test",  # Matches keyword
            message_id="priority-msg-3",
        )
        
        result = limited_aggregate.validate_trigger(event)
        assert result is not None, "Should trigger keyword reply"
        assert result.auto_reply_id == 10, "Should trigger keyword reply even outside general time"


class TestMessageContentHandling:
    """Test message content handling as specified in PRD Story 5."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.keyword_trigger = AutoReplyTriggerSetting(
            auto_reply_id=20,
            auto_reply_name="Content Keyword",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.KEYWORD,
            auto_reply_priority=10,
            keywords=["content"],
            webhook_trigger_id=20,
            bot_id=100,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
        )
        
        self.general_trigger = AutoReplyTriggerSetting(
            auto_reply_id=21,
            auto_reply_name="Content General",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.TIME,
            auto_reply_priority=5,
            keywords=None,
            webhook_trigger_id=21,
            bot_id=100,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
            trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
            trigger_schedule_settings={
                "schedules": [{"start_time": "00:00", "end_time": "23:59"}]
            },
        )
        
        self.aggregate = AutoReplyChannelSettingAggregate(
            bot_id=100,
            trigger_settings=[self.keyword_trigger, self.general_trigger],
            business_hours=[],
            timezone="Asia/Taipei",
        )
    
    def test_keyword_reply_with_matching_content(self):
        """Message-Content-Test1: Keyword reply triggers with matching content."""
        event = MessageEvent(
            event_id="content-test-1",
            channel_type=ChannelType.LINE,
            user_id="user1",
            timestamp=datetime.now(),
            content="content",  # Matches keyword
            message_id="content-msg-1",
        )
        
        result = self.aggregate.validate_trigger(event)
        assert result is not None, "Should trigger keyword reply"
        assert result.auto_reply_id == 20, "Should trigger keyword reply"
    
    def test_no_keyword_reply_without_matching_content(self):
        """Message-Content-Test2: No keyword reply when content doesn't match."""
        event = MessageEvent(
            event_id="content-test-2",
            channel_type=ChannelType.LINE,
            user_id="user1",
            timestamp=datetime.now(),
            content="different message",  # Does not match any keyword
            message_id="content-msg-2",
        )
        
        result = self.aggregate.validate_trigger(event)
        assert result is not None, "Should trigger general reply"
        assert result.auto_reply_id == 21, "Should trigger general reply, not keyword"
    
    def test_general_reply_regardless_of_content(self):
        """Message-Content-Test3: General reply triggers regardless of content."""
        test_contents = [
            "any message",
            "random text",
            "emojis 😀😃😄",
            "numbers 123 456",
            "",  # empty content
        ]
        
        for content in test_contents:
            event = MessageEvent(
                event_id=f"content-test-3-{hash(content)}",
                channel_type=ChannelType.LINE,
                user_id="user1",
                timestamp=datetime.now(),
                content=content,
                message_id=f"content-msg-3-{hash(content)}",
            )
            
            result = self.aggregate.validate_trigger(event)
            assert result is not None, f"Should trigger general reply for content: '{content}'"
            assert result.auto_reply_id == 21, f"Should trigger general reply for content: '{content}'"


class TestMidnightCrossingAndTimezones:
    """Test midnight crossing and timezone handling edge cases."""
    
    def test_daily_trigger_midnight_crossing(self):
        """Test daily trigger that crosses midnight (22:00 to 06:00)."""
        midnight_crossing_trigger = AutoReplyTriggerSetting(
            auto_reply_id=60,
            auto_reply_name="Night Shift Trigger",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.TIME,
            auto_reply_priority=10,
            keywords=None,
            webhook_trigger_id=60,
            bot_id=100,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
            trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
            trigger_schedule_settings={
                "schedules": [{"start_time": "22:00", "end_time": "06:00"}]
            },
        )
        
        aggregate = AutoReplyChannelSettingAggregate(
            bot_id=100,
            trigger_settings=[midnight_crossing_trigger],
            business_hours=[],
            timezone="Asia/Taipei",
        )
        
        # Test at 23:00 (should match)
        night_event = MessageEvent(
            event_id="night-test",
            channel_type=ChannelType.LINE,
            user_id="user1",
            timestamp=datetime(2023, 10, 15, 23, 0),  # 11:00 PM
            content="night shift message",
            message_id="night-msg",
        )
        
        result = aggregate.validate_trigger(night_event)
        assert result is not None, "Should trigger at 23:00 (midnight crossing range)"
        assert result.auto_reply_id == 60
        
        # Test at 05:00 next day (should match)
        early_morning_event = MessageEvent(
            event_id="early-morning-test",
            channel_type=ChannelType.LINE,
            user_id="user1",
            timestamp=datetime(2023, 10, 16, 5, 0),  # 5:00 AM next day
            content="early morning message",
            message_id="early-morning-msg",
        )
        
        result = aggregate.validate_trigger(early_morning_event)
        assert result is not None, "Should trigger at 05:00 (midnight crossing range)"
        assert result.auto_reply_id == 60
        
        # Test at 12:00 noon (should NOT match)
        noon_event = MessageEvent(
            event_id="noon-test",
            channel_type=ChannelType.LINE,
            user_id="user1",
            timestamp=datetime(2023, 10, 15, 12, 0),  # 12:00 PM
            content="noon message",
            message_id="noon-msg",
        )
        
        result = aggregate.validate_trigger(noon_event)
        assert result is None, "Should NOT trigger at 12:00 (outside midnight crossing range)"
        
        # Test at 07:00 (should NOT match - after end time)
        morning_event = MessageEvent(
            event_id="morning-test",
            channel_type=ChannelType.LINE,
            user_id="user1",
            timestamp=datetime(2023, 10, 15, 7, 0),  # 7:00 AM
            content="morning message",
            message_id="morning-msg",
        )
        
        result = aggregate.validate_trigger(morning_event)
        assert result is None, "Should NOT trigger at 07:00 (after midnight crossing end time)"
    
    def test_monthly_trigger_midnight_crossing(self):
        """Test monthly trigger that crosses midnight."""
        monthly_midnight_trigger = AutoReplyTriggerSetting(
            auto_reply_id=61,
            auto_reply_name="Monthly Night Trigger",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.TIME,
            auto_reply_priority=15,
            keywords=None,
            webhook_trigger_id=61,
            bot_id=100,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
            trigger_schedule_type=WebhookTriggerScheduleType.MONTHLY,
            trigger_schedule_settings={
                "schedules": [{"day": 15, "start_time": "23:30", "end_time": "01:30"}]
            },
        )
        
        aggregate = AutoReplyChannelSettingAggregate(
            bot_id=100,
            trigger_settings=[monthly_midnight_trigger],
            business_hours=[],
            timezone="Asia/Taipei",
        )
        
        # Test on 15th at 23:45 (should match)
        late_night_event = MessageEvent(
            event_id="late-night-test",
            channel_type=ChannelType.LINE,
            user_id="user1",
            timestamp=datetime(2023, 10, 15, 23, 45),  # 11:45 PM on 15th
            content="late night message",
            message_id="late-night-msg",
        )
        
        result = aggregate.validate_trigger(late_night_event)
        assert result is not None, "Should trigger on 15th at 23:45 (monthly midnight crossing)"
        assert result.auto_reply_id == 61
        
        # Test on 15th at 01:00 next day (should match - still 15th schedule)
        early_next_day_event = MessageEvent(
            event_id="early-next-day-test",
            channel_type=ChannelType.LINE,
            user_id="user1",
            timestamp=datetime(2023, 10, 15, 1, 0),  # 1:00 AM on 15th
            content="early next day message",
            message_id="early-next-day-msg",
        )
        
        result = aggregate.validate_trigger(early_next_day_event)
        assert result is not None, "Should trigger on 15th at 01:00 (monthly midnight crossing)"
        assert result.auto_reply_id == 61
        
        # Test on 16th at 01:00 (should NOT match - different day)
        different_day_event = MessageEvent(
            event_id="different-day-test",
            channel_type=ChannelType.LINE,
            user_id="user1",
            timestamp=datetime(2023, 10, 16, 1, 0),  # 1:00 AM on 16th
            content="different day message",
            message_id="different-day-msg",
        )
        
        result = aggregate.validate_trigger(different_day_event)
        assert result is None, "Should NOT trigger on 16th at 01:00 (different day)"
    
    def test_business_hours_different_timezones(self):
        """Test business hours when bot timezone differs from organization timezone."""
        business_hour_trigger = AutoReplyTriggerSetting(
            auto_reply_id=62,
            auto_reply_name="Business Hour Different TZ",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.TIME,
            auto_reply_priority=10,
            keywords=None,
            webhook_trigger_id=62,
            bot_id=100,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
            trigger_schedule_type=WebhookTriggerScheduleType.BUSINESS_HOUR,
            trigger_schedule_settings=None,
        )
        
        # Organization business hours in UTC+0 (9:00-17:00)
        business_hours_utc = [
            BusinessHour(weekday=1, start_time="09:00", end_time="17:00"),  # Monday
            BusinessHour(weekday=2, start_time="09:00", end_time="17:00"),  # Tuesday
            BusinessHour(weekday=3, start_time="09:00", end_time="17:00"),  # Wednesday
            BusinessHour(weekday=4, start_time="09:00", end_time="17:00"),  # Thursday
            BusinessHour(weekday=5, start_time="09:00", end_time="17:00"),  # Friday
        ]
        
        # Bot timezone is Asia/Tokyo (UTC+9), organization timezone is UTC
        aggregate_tokyo = AutoReplyChannelSettingAggregate(
            bot_id=100,
            trigger_settings=[business_hour_trigger],
            business_hours=business_hours_utc,  # Organization business hours in UTC
            timezone="Asia/Tokyo",  # Bot timezone
            organization_timezone="UTC",  # Organization timezone
        )
        
        # Event at 10:00 Tokyo time on Monday
        # This would be 01:00 UTC, which is outside 09:00-17:00 UTC business hours
        # Create Tokyo timezone aware timestamp
        tokyo_tz = pytz.timezone("Asia/Tokyo")
        tokyo_event = MessageEvent(
            event_id="tokyo-test",
            channel_type=ChannelType.LINE,
            user_id="user1",
            timestamp=tokyo_tz.localize(datetime(2023, 10, 16, 10, 0)),  # Monday 10:00 AM in Tokyo
            content="tokyo message",
            message_id="tokyo-msg",
        )
        
        # This should NOT match because business hours are in organization timezone (UTC)
        # and 10:00 Tokyo = 01:00 UTC which is outside 09:00-17:00 UTC
        result = aggregate_tokyo.validate_trigger(tokyo_event)
        assert result is None, "Should NOT match: 10:00 Tokyo = 01:00 UTC (outside 09:00-17:00 UTC business hours)"
        
        # Test with aligned timezones
        aggregate_aligned = AutoReplyChannelSettingAggregate(
            bot_id=100,
            trigger_settings=[business_hour_trigger],
            business_hours=business_hours_utc,
            timezone="UTC",  # Same timezone as business hours
        )
        
        utc_event = MessageEvent(
            event_id="utc-test",
            channel_type=ChannelType.LINE,
            user_id="user1",
            timestamp=datetime(2023, 10, 16, 10, 0, tzinfo=pytz.UTC),  # Monday 10:00 AM UTC with timezone
            content="utc message",
            message_id="utc-msg",
        )
        
        result = aggregate_aligned.validate_trigger(utc_event)
        assert result is not None, "Should match when timezones are aligned (10:00 UTC in 09:00-17:00 UTC business hours)"
        assert result.auto_reply_id == 62
    
    def test_timezone_conversion_accuracy(self):
        """Test that timezone conversions are handled accurately."""
        daily_trigger = AutoReplyTriggerSetting(
            auto_reply_id=63,
            auto_reply_name="Timezone Test Trigger",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.TIME,
            auto_reply_priority=10,
            keywords=None,
            webhook_trigger_id=63,
            bot_id=100,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
            trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
            trigger_schedule_settings={
                "schedules": [{"start_time": "14:00", "end_time": "15:00"}]  # 2:00-3:00 PM
            },
        )
        
        # Bot in New York timezone (UTC-5 in winter, UTC-4 in summer)
        aggregate_ny = AutoReplyChannelSettingAggregate(
            bot_id=100,
            trigger_settings=[daily_trigger],
            business_hours=[],
            timezone="America/New_York",
        )
        
        # Event timestamped as UTC, but should be converted to NY time for matching
        # 19:30 UTC = 14:30 EST (winter) or 15:30 EDT (summer)
        
        # Winter time test (EST = UTC-5)
        winter_event = MessageEvent(
            event_id="winter-test",
            channel_type=ChannelType.LINE,
            user_id="user1",
            timestamp=datetime(2023, 1, 15, 19, 30).replace(tzinfo=pytz.UTC),  # 19:30 UTC in winter
            content="winter message",
            message_id="winter-msg",
        )
        
        result = aggregate_ny.validate_trigger(winter_event)
        assert result is not None, "Should match in winter: 19:30 UTC = 14:30 EST (within 14:00-15:00)"
        
        # Summer time test (EDT = UTC-4)  
        summer_event = MessageEvent(
            event_id="summer-test",
            channel_type=ChannelType.LINE,
            user_id="user1",
            timestamp=datetime(2023, 7, 15, 18, 30).replace(tzinfo=pytz.UTC),  # 18:30 UTC in summer
            content="summer message",
            message_id="summer-msg",
        )
        
        result = aggregate_ny.validate_trigger(summer_event)
        assert result is not None, "Should match in summer: 18:30 UTC = 14:30 EDT (within 14:00-15:00)"
        
        # Test outside range
        outside_range_event = MessageEvent(
            event_id="outside-range-test",
            channel_type=ChannelType.LINE,
            user_id="user1",
            timestamp=datetime(2023, 1, 15, 22, 30).replace(tzinfo=pytz.UTC),  # 22:30 UTC = 17:30 EST
            content="outside range message",
            message_id="outside-range-msg",
        )
        
        result = aggregate_ny.validate_trigger(outside_range_event)
        assert result is None, "Should NOT match: 22:30 UTC = 17:30 EST (outside 14:00-15:00)"


class TestIGStoryKeywordLogic:
    """Test IG Story keyword logic as specified in PRD Story 6."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.ig_story_keyword_trigger = AutoReplyTriggerSetting(
            auto_reply_id=70,
            auto_reply_name="IG Story Keyword Trigger",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.KEYWORD,
            auto_reply_priority=20,
            keywords=["hello"],
            ig_story_ids=["story123"],
            webhook_trigger_id=70,
            bot_id=100,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
        )
        
        self.aggregate = AutoReplyChannelSettingAggregate(
            bot_id=100,
            trigger_settings=[self.ig_story_keyword_trigger],
            business_hours=[],
            timezone="Asia/Taipei",
        )
    
    def test_ig_story_keyword_no_story_id(self):
        """B-P1-18-Test7: Message matches keyword but is NOT a reply to selected story."""
        event = MessageEvent(
            event_id="test-ig-story-1",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user1",
            timestamp=datetime.now(),
            content="hello",
            message_id="msg1",
            ig_story_id=None,  # No story ID
        )
        
        result = self.aggregate.validate_trigger(event)
        assert result is None, "Should NOT trigger without story ID"
    
    def test_ig_story_keyword_with_matching_story(self):
        """B-P1-18-Test8a: Message is reply to selected story and matches keyword."""
        event = MessageEvent(
            event_id="test-ig-story-2",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user1",
            timestamp=datetime.now(),
            content="hello",
            message_id="msg2",
            ig_story_id="story123",  # Matching story ID
        )
        
        result = self.aggregate.validate_trigger(event)
        assert result is not None, "Should trigger with matching story ID and keyword"
        assert result.auto_reply_id == 70
    
    def test_ig_story_keyword_with_matching_keyword_and_story(self):
        """IG-Story-Keyword-Test1: Keyword and story ID both match."""
        event = MessageEvent(
            event_id="test-ig-story-3",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user1",
            timestamp=datetime.now(),
            content="hello",
            message_id="msg3",
            ig_story_id="story123",
        )
        
        result = self.aggregate.validate_trigger(event)
        assert result is not None, "Should trigger with matching keyword and story ID"
        assert result.auto_reply_id == 70
    
    def test_ig_story_keyword_wrong_story_id(self):
        """IG-Story-Keyword-Test2: Keyword matches but wrong story ID."""
        event = MessageEvent(
            event_id="test-ig-story-4",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user1",
            timestamp=datetime.now(),
            content="hello",
            message_id="msg4",
            ig_story_id="story456",  # Wrong story ID
        )
        
        result = self.aggregate.validate_trigger(event)
        assert result is None, "Should NOT trigger with wrong story ID"
    
    def test_ig_story_keyword_no_story_context(self):
        """IG-Story-Keyword-Test3: Keyword matches but no story context."""
        event = MessageEvent(
            event_id="test-ig-story-5",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user1",
            timestamp=datetime.now(),
            content="hello",
            message_id="msg5",
            ig_story_id=None,  # No story context
        )
        
        result = self.aggregate.validate_trigger(event)
        assert result is None, "Should NOT trigger without story context"


class TestIGStoryGeneralLogic:
    """Test IG Story general logic as specified in PRD Story 7."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.ig_story_general_trigger = AutoReplyTriggerSetting(
            auto_reply_id=71,
            auto_reply_name="IG Story General Trigger",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.TIME,
            auto_reply_priority=15,
            keywords=None,
            ig_story_ids=["story123"],
            webhook_trigger_id=71,
            bot_id=100,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
            trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
            trigger_schedule_settings={
                "schedules": [{"start_time": "09:00", "end_time": "17:00"}]
            },
        )
        
        self.aggregate = AutoReplyChannelSettingAggregate(
            bot_id=100,
            trigger_settings=[self.ig_story_general_trigger],
            business_hours=[],
            timezone="Asia/Taipei",
        )
    
    def test_ig_story_general_with_matching_story_and_schedule(self):
        """B-P1-18-Test8b: Message is reply to selected story and within schedule."""
        event = MessageEvent(
            event_id="test-ig-story-general-1",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user1",
            timestamp=datetime(2023, 10, 16, 14, 0),  # Within 9-17 schedule
            content="any message",
            message_id="msg1",
            ig_story_id="story123",
        )
        
        result = self.aggregate.validate_trigger(event)
        assert result is not None, "Should trigger with matching story and schedule"
        assert result.auto_reply_id == 71
    
    def test_ig_story_general_within_schedule_matching_story(self):
        """IG-Story-General-Test1: Within schedule and matching story."""
        event = MessageEvent(
            event_id="test-ig-story-general-2",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user1",
            timestamp=datetime(2023, 10, 16, 14, 0),  # 14:00 within 9-17
            content="any message",
            message_id="msg2",
            ig_story_id="story123",
        )
        
        result = self.aggregate.validate_trigger(event)
        assert result is not None, "Should trigger at 14:00 with matching story"
        assert result.auto_reply_id == 71
    
    def test_ig_story_general_outside_schedule(self):
        """IG-Story-General-Test2: Outside schedule even with matching story."""
        event = MessageEvent(
            event_id="test-ig-story-general-3",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user1",
            timestamp=datetime(2023, 10, 16, 20, 0),  # 20:00 outside 9-17
            content="any message",
            message_id="msg3",
            ig_story_id="story123",
        )
        
        result = self.aggregate.validate_trigger(event)
        assert result is None, "Should NOT trigger outside schedule"
    
    def test_ig_story_general_wrong_story_id(self):
        """IG-Story-General-Test3: Within schedule but wrong story ID."""
        event = MessageEvent(
            event_id="test-ig-story-general-4",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user1",
            timestamp=datetime(2023, 10, 16, 14, 0),  # Within schedule
            content="any message",
            message_id="msg4",
            ig_story_id="story456",  # Wrong story ID
        )
        
        result = self.aggregate.validate_trigger(event)
        assert result is None, "Should NOT trigger with wrong story ID"


class TestIGStoryPriority:
    """Test IG Story priority over general as specified in PRD Story 8."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.ig_story_keyword_trigger = AutoReplyTriggerSetting(
            auto_reply_id=72,
            auto_reply_name="IG Story Keyword Priority",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.KEYWORD,
            auto_reply_priority=20,
            keywords=["hello"],
            ig_story_ids=["story123"],
            webhook_trigger_id=72,
            bot_id=100,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
        )
        
        self.general_keyword_trigger = AutoReplyTriggerSetting(
            auto_reply_id=73,
            auto_reply_name="General Keyword Priority",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.KEYWORD,
            auto_reply_priority=25,  # Higher priority number but lower in hierarchy
            keywords=["hello"],
            ig_story_ids=None,  # General trigger
            webhook_trigger_id=73,
            bot_id=100,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
        )
        
        self.ig_story_general_trigger = AutoReplyTriggerSetting(
            auto_reply_id=74,
            auto_reply_name="IG Story General Priority",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.TIME,
            auto_reply_priority=10,
            keywords=None,
            ig_story_ids=["story123"],
            webhook_trigger_id=74,
            bot_id=100,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
            trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
            trigger_schedule_settings={
                "schedules": [{"start_time": "00:00", "end_time": "23:59"}]
            },
        )
        
        self.general_time_trigger = AutoReplyTriggerSetting(
            auto_reply_id=75,
            auto_reply_name="General Time Priority",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.TIME,
            auto_reply_priority=30,  # Higher priority number but lower in hierarchy
            keywords=None,
            ig_story_ids=None,  # General trigger
            webhook_trigger_id=75,
            bot_id=100,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
            trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
            trigger_schedule_settings={
                "schedules": [{"start_time": "00:00", "end_time": "23:59"}]
            },
        )
        
        self.aggregate = AutoReplyChannelSettingAggregate(
            bot_id=100,
            trigger_settings=[
                self.ig_story_keyword_trigger,
                self.general_keyword_trigger,
                self.ig_story_general_trigger,
                self.general_time_trigger,
            ],
            business_hours=[],
            timezone="Asia/Taipei",
        )
    
    def test_ig_story_keyword_over_general_keyword(self):
        """B-P1-18-Test9: Story-specific keyword has priority over general keyword."""
        event = MessageEvent(
            event_id="test-priority-1",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user1",
            timestamp=datetime.now(),
            content="hello",
            message_id="msg1",
            ig_story_id="story123",
        )
        
        result = self.aggregate.validate_trigger(event)
        assert result is not None, "Should trigger some rule"
        assert result.auto_reply_id == 72, "Should trigger IG story keyword (highest priority)"
    
    def test_ig_story_keyword_priority_over_general(self):
        """IG-Story-Priority-Test1: IG story keyword over general keyword."""
        event = MessageEvent(
            event_id="test-priority-2",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user1",
            timestamp=datetime.now(),
            content="hello",
            message_id="msg2",
            ig_story_id="story123",
        )
        
        result = self.aggregate.validate_trigger(event)
        assert result is not None, "Should trigger some rule"
        assert result.auto_reply_id == 72, "Should trigger IG story keyword, not general keyword"
    
    def test_ig_story_general_over_general_time(self):
        """IG-Story-Priority-Test2: IG story general over general time-based."""
        event = MessageEvent(
            event_id="test-priority-3",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user1",
            timestamp=datetime.now(),
            content="non-matching-keyword",  # No keyword match
            message_id="msg3",
            ig_story_id="story123",
        )
        
        result = self.aggregate.validate_trigger(event)
        assert result is not None, "Should trigger some rule"
        assert result.auto_reply_id == 74, "Should trigger IG story general, not general time"


class TestIGStoryMultipleKeywords:
    """Test IG Story multiple keywords as specified in PRD Story 9."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.ig_story_multi_keyword_trigger = AutoReplyTriggerSetting(
            auto_reply_id=76,
            auto_reply_name="IG Story Multi Keyword",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.KEYWORD,
            auto_reply_priority=20,
            keywords=["hello", "hi"],
            ig_story_ids=["story123"],
            webhook_trigger_id=76,
            bot_id=100,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
        )
        
        self.aggregate = AutoReplyChannelSettingAggregate(
            bot_id=100,
            trigger_settings=[self.ig_story_multi_keyword_trigger],
            business_hours=[],
            timezone="Asia/Taipei",
        )
    
    def test_ig_story_multiple_keywords_each_triggers(self):
        """IG-Story-Multiple-Keywords-Test1: Each keyword triggers with correct story ID."""
        keywords = ["hello", "hi"]
        
        for keyword in keywords:
            event = MessageEvent(
                event_id=f"test-multi-keyword-{keyword}",
                channel_type=ChannelType.INSTAGRAM,
                user_id="user1",
                timestamp=datetime.now(),
                content=keyword,
                message_id=f"msg-{keyword}",
                ig_story_id="story123",
            )
            
            result = self.aggregate.validate_trigger(event)
            assert result is not None, f"Should trigger with keyword '{keyword}'"
            assert result.auto_reply_id == 76
    
    def test_ig_story_multiple_keywords_wrong_story(self):
        """IG-Story-Multiple-Keywords-Test2: Keywords match but wrong story ID."""
        event = MessageEvent(
            event_id="test-multi-keyword-wrong-story",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user1",
            timestamp=datetime.now(),
            content="hello",
            message_id="msg-wrong-story",
            ig_story_id="story456",  # Wrong story ID
        )
        
        result = self.aggregate.validate_trigger(event)
        assert result is None, "Should NOT trigger with wrong story ID"


class TestCompletePrioritySystem:
    """Test complete priority system as specified in PRD Story 10."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.ig_story_keyword_trigger = AutoReplyTriggerSetting(
            auto_reply_id=80,
            auto_reply_name="Priority 1: IG Story Keyword",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.KEYWORD,
            auto_reply_priority=10,
            keywords=["hello"],
            ig_story_ids=["story123"],
            webhook_trigger_id=80,
            bot_id=100,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
        )
        
        self.ig_story_general_trigger = AutoReplyTriggerSetting(
            auto_reply_id=81,
            auto_reply_name="Priority 2: IG Story General",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.TIME,
            auto_reply_priority=10,
            keywords=None,
            ig_story_ids=["story123"],
            webhook_trigger_id=81,
            bot_id=100,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
            trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
            trigger_schedule_settings={
                "schedules": [{"start_time": "00:00", "end_time": "23:59"}]
            },
        )
        
        self.general_keyword_trigger = AutoReplyTriggerSetting(
            auto_reply_id=82,
            auto_reply_name="Priority 3: General Keyword",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.KEYWORD,
            auto_reply_priority=10,
            keywords=["hello"],
            ig_story_ids=None,  # General trigger
            webhook_trigger_id=82,
            bot_id=100,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
        )
        
        self.general_time_trigger = AutoReplyTriggerSetting(
            auto_reply_id=83,
            auto_reply_name="Priority 4: General Time",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.TIME,
            auto_reply_priority=10,
            keywords=None,
            ig_story_ids=None,  # General trigger
            webhook_trigger_id=83,
            bot_id=100,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
            trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
            trigger_schedule_settings={
                "schedules": [{"start_time": "00:00", "end_time": "23:59"}]
            },
        )
        
        self.aggregate = AutoReplyChannelSettingAggregate(
            bot_id=100,
            trigger_settings=[
                self.ig_story_keyword_trigger,
                self.ig_story_general_trigger,
                self.general_keyword_trigger,
                self.general_time_trigger,
            ],
            business_hours=[],
            timezone="Asia/Taipei",
        )
    
    def test_all_rules_priority_1_wins(self):
        """Complete-Priority-Test1: IG story keyword wins over all others."""
        event = MessageEvent(
            event_id="test-complete-priority-1",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user1",
            timestamp=datetime.now(),
            content="hello",
            message_id="msg1",
            ig_story_id="story123",
        )
        
        result = self.aggregate.validate_trigger(event)
        assert result is not None, "Should trigger some rule"
        assert result.auto_reply_id == 80, "Should trigger IG story keyword (priority 1)"
    
    def test_priority_2_wins_without_keyword_match(self):
        """Complete-Priority-Test2: IG story general wins when no keyword match."""
        event = MessageEvent(
            event_id="test-complete-priority-2",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user1",
            timestamp=datetime.now(),
            content="non-matching-keyword",
            message_id="msg2",
            ig_story_id="story123",
        )
        
        result = self.aggregate.validate_trigger(event)
        assert result is not None, "Should trigger some rule"
        assert result.auto_reply_id == 81, "Should trigger IG story general (priority 2)"
    
    def test_priority_3_wins_without_story_id(self):
        """Complete-Priority-Test3: General keyword wins without story ID."""
        event = MessageEvent(
            event_id="test-complete-priority-3",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user1",
            timestamp=datetime.now(),
            content="hello",
            message_id="msg3",
            ig_story_id=None,  # No story ID
        )
        
        result = self.aggregate.validate_trigger(event)
        assert result is not None, "Should trigger some rule"
        assert result.auto_reply_id == 82, "Should trigger general keyword (priority 3)"
    
    def test_priority_4_wins_time_only(self):
        """Complete-Priority-Test4: General time wins when only time-based rule applies."""
        event = MessageEvent(
            event_id="test-complete-priority-4",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user1",
            timestamp=datetime.now(),
            content="non-matching-keyword",
            message_id="msg4",
            ig_story_id=None,  # No story ID
        )
        
        # Create aggregate with only general time trigger
        time_only_aggregate = AutoReplyChannelSettingAggregate(
            bot_id=100,
            trigger_settings=[self.general_time_trigger],
            business_hours=[],
            timezone="Asia/Taipei",
        )
        
        result = time_only_aggregate.validate_trigger(event)
        assert result is not None, "Should trigger some rule"
        assert result.auto_reply_id == 83, "Should trigger general time (priority 4)"


class TestIGStoryExclusionLogic:
    """Test IG Story exclusion logic as specified in PRD Story 11."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.ig_story_only_trigger = AutoReplyTriggerSetting(
            auto_reply_id=90,
            auto_reply_name="IG Story Only Trigger",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.KEYWORD,
            auto_reply_priority=10,
            keywords=["hello"],
            ig_story_ids=["story123"],  # IG story specific
            webhook_trigger_id=90,
            bot_id=100,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
        )
        
        self.general_only_trigger = AutoReplyTriggerSetting(
            auto_reply_id=91,
            auto_reply_name="General Only Trigger",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.KEYWORD,
            auto_reply_priority=10,
            keywords=["hello"],
            ig_story_ids=None,  # General trigger
            webhook_trigger_id=91,
            bot_id=100,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
        )
        
        self.mixed_aggregate = AutoReplyChannelSettingAggregate(
            bot_id=100,
            trigger_settings=[self.ig_story_only_trigger, self.general_only_trigger],
            business_hours=[],
            timezone="Asia/Taipei",
        )
        
        self.ig_story_only_aggregate = AutoReplyChannelSettingAggregate(
            bot_id=100,
            trigger_settings=[self.ig_story_only_trigger],
            business_hours=[],
            timezone="Asia/Taipei",
        )
        
        self.general_only_aggregate = AutoReplyChannelSettingAggregate(
            bot_id=100,
            trigger_settings=[self.general_only_trigger],
            business_hours=[],
            timezone="Asia/Taipei",
        )
    
    def test_ig_story_specific_excluded_from_general(self):
        """IG-Story-Exclusion-Test1: IG story-specific setting excluded from general messages."""
        event = MessageEvent(
            event_id="test-exclusion-1",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user1",
            timestamp=datetime.now(),
            content="hello",
            message_id="msg1",
            ig_story_id=None,  # No story ID
        )
        
        result = self.ig_story_only_aggregate.validate_trigger(event)
        assert result is None, "Should NOT trigger IG story-specific setting for general message"
    
    def test_general_setting_triggers_for_general_message(self):
        """IG-Story-Exclusion-Test2: General setting triggers for general message."""
        event = MessageEvent(
            event_id="test-exclusion-2",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user1",
            timestamp=datetime.now(),
            content="hello",
            message_id="msg2",
            ig_story_id=None,  # No story ID
        )
        
        result = self.general_only_aggregate.validate_trigger(event)
        assert result is not None, "Should trigger general setting for general message"
        assert result.auto_reply_id == 91
    
    def test_mixed_settings_only_general_triggers(self):
        """IG-Story-Exclusion-Test3: Only general setting triggers for general message."""
        event = MessageEvent(
            event_id="test-exclusion-3",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user1",
            timestamp=datetime.now(),
            content="hello",
            message_id="msg3",
            ig_story_id=None,  # No story ID
        )
        
        result = self.mixed_aggregate.validate_trigger(event)
        assert result is not None, "Should trigger some rule"
        assert result.auto_reply_id == 91, "Should trigger general setting, not IG story-specific"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_inactive_triggers_not_matched(self):
        """Test that inactive triggers are not matched."""
        inactive_trigger = AutoReplyTriggerSetting(
            auto_reply_id=30,
            auto_reply_name="Inactive Trigger",
            auto_reply_status=AutoReplyStatus.INACTIVE,  # Inactive
            auto_reply_event_type=AutoReplyEventType.KEYWORD,
            auto_reply_priority=100,
            keywords=["inactive"],
            webhook_trigger_id=30,
            bot_id=100,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
        )
        
        aggregate = AutoReplyChannelSettingAggregate(
            bot_id=100,
            trigger_settings=[inactive_trigger],
            business_hours=[],
            timezone="Asia/Taipei",
        )
        
        event = MessageEvent(
            event_id="inactive-test",
            channel_type=ChannelType.LINE,
            user_id="user1",
            timestamp=datetime.now(),
            content="inactive",
            message_id="inactive-msg",
        )
        
        result = aggregate.validate_trigger(event)
        assert result is None, "Inactive trigger should not match"
    
    def test_disabled_triggers_not_matched(self):
        """Test that disabled triggers are not matched."""
        disabled_trigger = AutoReplyTriggerSetting(
            auto_reply_id=31,
            auto_reply_name="Disabled Trigger",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.KEYWORD,
            auto_reply_priority=100,
            keywords=["disabled"],
            webhook_trigger_id=31,
            bot_id=100,
            enable=False,  # Disabled
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
        )
        
        aggregate = AutoReplyChannelSettingAggregate(
            bot_id=100,
            trigger_settings=[disabled_trigger],
            business_hours=[],
            timezone="Asia/Taipei",
        )
        
        event = MessageEvent(
            event_id="disabled-test",
            channel_type=ChannelType.LINE,
            user_id="user1",
            timestamp=datetime.now(),
            content="disabled",
            message_id="disabled-msg",
        )
        
        result = aggregate.validate_trigger(event)
        assert result is None, "Disabled trigger should not match"
    
    def test_archived_triggers_not_matched(self):
        """Test that archived triggers are not matched."""
        archived_trigger = AutoReplyTriggerSetting(
            auto_reply_id=32,
            auto_reply_name="Archived Trigger",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.KEYWORD,
            auto_reply_priority=100,
            keywords=["archived"],
            webhook_trigger_id=32,
            bot_id=100,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
            archived=True,  # Archived
        )
        
        aggregate = AutoReplyChannelSettingAggregate(
            bot_id=100,
            trigger_settings=[archived_trigger],
            business_hours=[],
            timezone="Asia/Taipei",
        )
        
        event = MessageEvent(
            event_id="archived-test",
            channel_type=ChannelType.LINE,
            user_id="user1",
            timestamp=datetime.now(),
            content="archived",
            message_id="archived-msg",
        )
        
        result = aggregate.validate_trigger(event)
        assert result is None, "Archived trigger should not match"
    
    def test_empty_keywords_not_matched(self):
        """Test that triggers with empty keywords are not matched."""
        empty_keywords_trigger = AutoReplyTriggerSetting(
            auto_reply_id=33,
            auto_reply_name="Empty Keywords",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.KEYWORD,
            auto_reply_priority=100,
            keywords=[],  # Empty keywords
            webhook_trigger_id=33,
            bot_id=100,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
        )
        
        aggregate = AutoReplyChannelSettingAggregate(
            bot_id=100,
            trigger_settings=[empty_keywords_trigger],
            business_hours=[],
            timezone="Asia/Taipei",
        )
        
        event = MessageEvent(
            event_id="empty-keywords-test",
            channel_type=ChannelType.LINE,
            user_id="user1",
            timestamp=datetime.now(),
            content="anything",
            message_id="empty-keywords-msg",
        )
        
        result = aggregate.validate_trigger(event)
        assert result is None, "Trigger with empty keywords should not match"
    
    def test_keyword_priority_ordering(self):
        """Test that keyword triggers are ordered by priority correctly."""
        low_priority_trigger = AutoReplyTriggerSetting(
            auto_reply_id=40,
            auto_reply_name="Low Priority",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.KEYWORD,
            auto_reply_priority=5,  # Lower priority
            keywords=["priority"],
            webhook_trigger_id=40,
            bot_id=100,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
        )
        
        high_priority_trigger = AutoReplyTriggerSetting(
            auto_reply_id=41,
            auto_reply_name="High Priority",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.KEYWORD,
            auto_reply_priority=100,  # Higher priority
            keywords=["priority"],
            webhook_trigger_id=41,
            bot_id=100,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
        )
        
        aggregate = AutoReplyChannelSettingAggregate(
            bot_id=100,
            trigger_settings=[low_priority_trigger, high_priority_trigger],
            business_hours=[],
            timezone="Asia/Taipei",
        )
        
        event = MessageEvent(
            event_id="priority-order-test",
            channel_type=ChannelType.LINE,
            user_id="user1",
            timestamp=datetime.now(),
            content="priority",
            message_id="priority-order-msg",
        )
        
        result = aggregate.validate_trigger(event)
        assert result is not None, "Should match a priority trigger"
        assert result.auto_reply_id == 41, "Should match the higher priority trigger"
    
    def test_time_trigger_schedule_priority_ordering(self):
        """Test that time triggers are ordered by schedule type priority correctly."""
        daily_trigger = AutoReplyTriggerSetting(
            auto_reply_id=50,
            auto_reply_name="Daily Trigger",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.TIME,
            auto_reply_priority=100,  # High priority number
            keywords=None,
            webhook_trigger_id=50,
            bot_id=100,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
            trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
            trigger_schedule_settings={
                "schedules": [{"start_time": "00:00", "end_time": "23:59"}]
            },
        )
        
        monthly_trigger = AutoReplyTriggerSetting(
            auto_reply_id=51,
            auto_reply_name="Monthly Trigger",
            auto_reply_status=AutoReplyStatus.ACTIVE,
            auto_reply_event_type=AutoReplyEventType.TIME,
            auto_reply_priority=5,  # Lower priority number
            keywords=None,
            webhook_trigger_id=51,
            bot_id=100,
            enable=True,
            webhook_event_type=WebhookTriggerEventType.MESSAGE,
            trigger_schedule_type=WebhookTriggerScheduleType.MONTHLY,
            trigger_schedule_settings={
                "schedules": [{"day": 15, "start_time": "00:00", "end_time": "23:59"}]
            },
        )
        
        aggregate = AutoReplyChannelSettingAggregate(
            bot_id=100,
            trigger_settings=[daily_trigger, monthly_trigger],
            business_hours=[],
            timezone="Asia/Taipei",
        )
        
        # Test on 15th of month (both triggers should match)
        event = MessageEvent(
            event_id="schedule-priority-test",
            channel_type=ChannelType.LINE,
            user_id="user1",
            timestamp=datetime(2023, 10, 15, 12, 0),  # 15th of month
            content="test message",
            message_id="schedule-priority-msg",
        )
        
        result = aggregate.validate_trigger(event)
        assert result is not None, "Should match a time trigger"
        # Monthly should have higher schedule type priority than daily
        assert result.auto_reply_id == 51, "Should match monthly trigger (higher schedule type priority)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])