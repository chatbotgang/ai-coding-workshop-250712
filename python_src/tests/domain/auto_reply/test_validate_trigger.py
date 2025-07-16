"""Tests for validate_trigger function - PRD compliance tests.

This file tests the main validate_trigger function against all PRD test cases:

Story 1: Keyword Reply Logic
- [B-P0-7-Test2]: Exact keyword matching with various cases
- [B-P0-7-Test3]: Keyword with leading/trailing spaces
- [B-P0-7-Test4]: Message contains keyword but with other text (should not match)
- [B-P0-7-Test5]: Partial match or close variation (should not match)

Story 2: Multiple Keywords Support  
- [Multiple-Keywords-Test1]: Multiple keywords triggering
- [Multiple-Keywords-Test2]: Multiple keywords with different casing
- [Multiple-Keywords-Test3]: Message doesn't match any keywords

Story 3: General Time-based Logic
- [B-P0-6-Test3]: Daily schedule triggering
- [B-P0-6-Test4]: Monthly schedule triggering
- [B-P0-6-Test5]: Business hours triggering

Story 4: Priority Logic (Keyword over General)
- [Priority-Test1]: Keyword and General both match -> only Keyword triggered
- [Priority-Test2]: No keyword match, General matches -> only General triggered  
- [Priority-Test3]: Keyword matches outside General time -> only Keyword triggered

Story 5: Message Content Handling
- [Message-Content-Test1]: Keyword rule with matching message
- [Message-Content-Test2]: No keyword match with keyword rules
- [Message-Content-Test3]: General rule triggers regardless of message content
"""

from datetime import datetime
from zoneinfo import ZoneInfo
import pytest

from internal.domain.auto_reply.auto_reply import AutoReply, AutoReplyEventType, AutoReplyStatus
from internal.domain.auto_reply.webhook_trigger import (
    WebhookTriggerSetting, 
    WebhookTriggerEventType,
    DailySchedule,
    MonthlySchedule,
    WebhookTriggerScheduleSettings,
)
from internal.domain.auto_reply.validate_trigger import validate_trigger


class TestValidateTrigger:
    """Test cases for validate_trigger function."""
    
    def test_validate_trigger_basic_functionality(self):
        """Test basic validate_trigger functionality."""
        from internal.domain.auto_reply.validate_trigger import validate_trigger
        
        # Create AutoReply for keyword trigger
        keyword_auto_reply = AutoReply(
            id=1,
            organization_id=1,
            name="Test Keyword Reply",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD,
            priority=1,
            keywords=["hello", "hi"],
            trigger_schedule_type=None,
            trigger_schedule_settings=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Create WebhookTriggerSetting
        keyword_trigger_setting = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="Test Keyword Trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Test matching keyword
        result = validate_trigger(
            trigger_settings=[keyword_trigger_setting],
            auto_replies={1: keyword_auto_reply},
            message_content="hello",
            event_time=datetime.now(tz=ZoneInfo("Asia/Taipei")),
            organization_timezone="Asia/Taipei"
        )
        
        assert result is not None
        assert result.auto_reply_id == 1
        
        # Test non-matching keyword
        result = validate_trigger(
            trigger_settings=[keyword_trigger_setting],
            auto_replies={1: keyword_auto_reply},
            message_content="goodbye",
            event_time=datetime.now(tz=ZoneInfo("Asia/Taipei")),
            organization_timezone="Asia/Taipei"
        )
        
        assert result is None


# PRD Test Case Templates - Will be implemented when validate_trigger is ready

class TestKeywordReplyLogic:
    """PRD Story 1: Keyword Reply Logic tests."""
    
    def test_prd_b_p0_7_test2_exact_keyword_various_cases(self):
        """[PRD B-P0-7-Test2] Create a Keyword Reply with specific keyword and test various cases.
        
        Expected Result: Auto-reply is triggered when message exactly matches keyword, regardless of case.
        """
        # Create keyword auto-reply
        auto_reply = AutoReply(
            id=1, organization_id=1, name="Keyword Reply", status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD, priority=1, keywords=["hello"],
            trigger_schedule_type=None, trigger_schedule_settings=None,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        trigger_setting = WebhookTriggerSetting(
            id=1, auto_reply_id=1, bot_id=1, enable=True, name="Keyword Trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        # Test various cases
        test_cases = ["hello", "HELLO", "Hello", "HeLLo"]
        for message in test_cases:
            result = validate_trigger([trigger_setting], {1: auto_reply}, message, datetime.now(tz=ZoneInfo("Asia/Taipei")), "Asia/Taipei")
            assert result is not None, f"Should match keyword: '{message}'"
            assert result.auto_reply_id == 1
    
    def test_prd_b_p0_7_test3_keyword_with_leading_trailing_spaces(self):
        """[PRD B-P0-7-Test3] Test triggering with keyword surrounded by spaces.
        
        Expected Result: Leading and trailing spaces are trimmed, auto-reply triggered if core keyword matches.
        """
        auto_reply = AutoReply(
            id=1, organization_id=1, name="Keyword Reply", status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD, priority=1, keywords=["hello"],
            trigger_schedule_type=None, trigger_schedule_settings=None,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        trigger_setting = WebhookTriggerSetting(
            id=1, auto_reply_id=1, bot_id=1, enable=True, name="Keyword Trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        # Test spaces around keyword
        test_cases = [" hello ", "  hello  ", "\thello\t", "\nhello\n", " HELLO "]
        for message in test_cases:
            result = validate_trigger([trigger_setting], {1: auto_reply}, message, datetime.now(tz=ZoneInfo("Asia/Taipei")), "Asia/Taipei")
            assert result is not None, f"Should match keyword with spaces: '{message}'"
            assert result.auto_reply_id == 1
    
    def test_prd_b_p0_7_test4_message_contains_keyword_plus_other_text(self):
        """[PRD B-P0-7-Test4] Test with message containing keyword plus other text.
        
        Expected Result: Auto-reply is NOT triggered as match must be exact.
        """
        auto_reply = AutoReply(
            id=1, organization_id=1, name="Keyword Reply", status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD, priority=1, keywords=["hello"],
            trigger_schedule_type=None, trigger_schedule_settings=None,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        trigger_setting = WebhookTriggerSetting(
            id=1, auto_reply_id=1, bot_id=1, enable=True, name="Keyword Trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        # Test messages that contain keyword but have other text
        test_cases = ["hello world", "say hello", "hello there friend", "well hello", "hello!", "hello."]
        for message in test_cases:
            result = validate_trigger([trigger_setting], {1: auto_reply}, message, datetime.now(tz=ZoneInfo("Asia/Taipei")), "Asia/Taipei")
            assert result is None, f"Should NOT match: '{message}'"
    
    def test_prd_b_p0_7_test5_partial_match_or_close_variation(self):
        """[PRD B-P0-7-Test5] Test with partial match or close variation of keyword.
        
        Expected Result: Auto-reply is NOT triggered.
        """
        auto_reply = AutoReply(
            id=1, organization_id=1, name="Keyword Reply", status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD, priority=1, keywords=["hello"],
            trigger_schedule_type=None, trigger_schedule_settings=None,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        trigger_setting = WebhookTriggerSetting(
            id=1, auto_reply_id=1, bot_id=1, enable=True, name="Keyword Trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        # Test partial matches and variations
        test_cases = ["hell", "hel", "ello", "helo", "helllo", "heello", "hellp"]
        for message in test_cases:
            result = validate_trigger([trigger_setting], {1: auto_reply}, message, datetime.now(tz=ZoneInfo("Asia/Taipei")), "Asia/Taipei")
            assert result is None, f"Should NOT match partial/variation: '{message}'"


class TestMultipleKeywordsSupport:
    """PRD Story 2: Multiple Keywords Support tests."""
    
    def test_prd_multiple_keywords_test1_multiple_keywords_triggering(self):
        """[PRD Multiple-Keywords-Test1] Create rule with multiple keywords and test each.
        
        Expected Result: Auto-reply triggered when any configured keyword matches exactly.
        """
        auto_reply = AutoReply(
            id=1, organization_id=1, name="Multiple Keywords Reply", status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD, priority=1, keywords=["hello", "hi", "hey"],
            trigger_schedule_type=None, trigger_schedule_settings=None,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        trigger_setting = WebhookTriggerSetting(
            id=1, auto_reply_id=1, bot_id=1, enable=True, name="Multiple Keywords Trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        # Test each keyword matches
        for keyword in ["hello", "hi", "hey"]:
            result = validate_trigger([trigger_setting], {1: auto_reply}, keyword, datetime.now(tz=ZoneInfo("Asia/Taipei")), "Asia/Taipei")
            assert result is not None, f"Should match keyword: '{keyword}'"
            assert result.auto_reply_id == 1
    
    def test_prd_multiple_keywords_test2_different_casing(self):
        """[PRD Multiple-Keywords-Test2] Test keyword matching one of multiple with different casing.
        
        Expected Result: Auto-reply triggered due to case-insensitive matching.
        """
        auto_reply = AutoReply(
            id=1, organization_id=1, name="Multiple Keywords Reply", status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD, priority=1, keywords=["hello", "hi", "hey"],
            trigger_schedule_type=None, trigger_schedule_settings=None,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        trigger_setting = WebhookTriggerSetting(
            id=1, auto_reply_id=1, bot_id=1, enable=True, name="Multiple Keywords Trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        # Test case insensitive matching for multiple keywords
        test_cases = ["HELLO", "HI", "HEY", "Hello", "Hi", "Hey"]
        for message in test_cases:
            result = validate_trigger([trigger_setting], {1: auto_reply}, message, datetime.now(tz=ZoneInfo("Asia/Taipei")), "Asia/Taipei")
            assert result is not None, f"Should match case insensitive: '{message}'"
            assert result.auto_reply_id == 1
    
    def test_prd_multiple_keywords_test3_no_match_any_keywords(self):
        """[PRD Multiple-Keywords-Test3] Test message that doesn't match any keywords.
        
        Expected Result: Auto-reply is NOT triggered.
        """
        auto_reply = AutoReply(
            id=1, organization_id=1, name="Multiple Keywords Reply", status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD, priority=1, keywords=["hello", "hi", "hey"],
            trigger_schedule_type=None, trigger_schedule_settings=None,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        trigger_setting = WebhookTriggerSetting(
            id=1, auto_reply_id=1, bot_id=1, enable=True, name="Multiple Keywords Trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        # Test messages that don't match any keywords
        test_cases = ["goodbye", "welcome", "greetings", "yo", "sup", "hello world", "hi there", "hey buddy"]
        for message in test_cases:
            result = validate_trigger([trigger_setting], {1: auto_reply}, message, datetime.now(tz=ZoneInfo("Asia/Taipei")), "Asia/Taipei")
            assert result is None, f"Should NOT match: '{message}'"


class TestGeneralTimeBasedLogic:
    """PRD Story 3: General Time-based Logic tests."""
    
    def test_prd_b_p0_6_test3_daily_schedule_within_time_window(self):
        """[PRD B-P0-6-Test3] Create General Reply with Daily schedule, test during time window.
        
        Expected Result: Auto-reply sent when message received within scheduled daily time.
        """
        # Create daily schedule: 09:00-17:00
        daily_schedule = DailySchedule(
            start_time="09:00",
            end_time="17:00"
        )
        
        schedule_settings = WebhookTriggerScheduleSettings(
            schedules=[daily_schedule]
        )
        
        time_auto_reply = AutoReply(
            id=1, organization_id=1, name="Daily Time Reply", status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.TIME, priority=1, keywords=None,
            trigger_schedule_type="daily", trigger_schedule_settings=schedule_settings,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        trigger_setting = WebhookTriggerSetting(
            id=1, auto_reply_id=1, bot_id=1, enable=True, name="Daily Time Trigger",
            event_type=WebhookTriggerEventType.TIME,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        # Test within time window (13:30 Taipei time)
        within_time = datetime(2024, 1, 15, 13, 30, 0, tzinfo=ZoneInfo("Asia/Taipei"))  # Monday 1:30 PM Taipei
        result = validate_trigger([trigger_setting], {1: time_auto_reply}, "any message", within_time, "Asia/Taipei")
        assert result is not None, "Should trigger during daily time window"
        assert result.auto_reply_id == 1
        
        # Test outside time window (early morning)
        outside_time_early = datetime(2024, 1, 15, 7, 0, 0, tzinfo=ZoneInfo("Asia/Taipei"))  # Monday 7:00 AM Taipei
        result = validate_trigger([trigger_setting], {1: time_auto_reply}, "any message", outside_time_early, "Asia/Taipei")
        assert result is None, "Should NOT trigger outside daily time window (early)"
        
        # Test outside time window (late evening)
        outside_time_late = datetime(2024, 1, 15, 20, 0, 0, tzinfo=ZoneInfo("Asia/Taipei"))  # Monday 8:00 PM Taipei
        result = validate_trigger([trigger_setting], {1: time_auto_reply}, "any message", outside_time_late, "Asia/Taipei")
        assert result is None, "Should NOT trigger outside daily time window (late)"
    
    def test_prd_b_p0_6_test4_monthly_schedule_on_scheduled_date_time(self):
        """[PRD B-P0-6-Test4] Create General Reply with Monthly schedule, test on scheduled date/time.
        
        Expected Result: Auto-reply sent when message received on scheduled monthly date and time.
        """
        # Create monthly schedule: 15th of every month at 14:00
        monthly_schedule = MonthlySchedule(
            day=15,
            start_time="14:00",
            end_time="14:30"
        )
        
        schedule_settings = WebhookTriggerScheduleSettings(
            schedules=[monthly_schedule]
        )
        
        time_auto_reply = AutoReply(
            id=1, organization_id=1, name="Monthly Time Reply", status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.TIME, priority=1, keywords=None,
            trigger_schedule_type="monthly", trigger_schedule_settings=schedule_settings,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        trigger_setting = WebhookTriggerSetting(
            id=1, auto_reply_id=1, bot_id=1, enable=True, name="Monthly Time Trigger",
            event_type=WebhookTriggerEventType.TIME,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        # Test on scheduled date and time (15th at 14:15 Taipei time)
        scheduled_time = datetime(2024, 3, 15, 14, 15, 0, tzinfo=ZoneInfo("Asia/Taipei"))  # March 15th, 2:15 PM Taipei
        result = validate_trigger([trigger_setting], {1: time_auto_reply}, "any message", scheduled_time, "Asia/Taipei")
        assert result is not None, "Should trigger on scheduled monthly date and time"
        assert result.auto_reply_id == 1
        
        # Test on wrong date (14th at correct time)
        wrong_date = datetime(2024, 3, 14, 14, 15, 0, tzinfo=ZoneInfo("Asia/Taipei"))  # March 14th, 2:15 PM Taipei
        result = validate_trigger([trigger_setting], {1: time_auto_reply}, "any message", wrong_date, "Asia/Taipei")
        assert result is None, "Should NOT trigger on wrong date"
        
        # Test on correct date but wrong time
        wrong_time = datetime(2024, 3, 15, 16, 0, 0, tzinfo=ZoneInfo("Asia/Taipei"))  # March 15th, 4:00 PM Taipei
        result = validate_trigger([trigger_setting], {1: time_auto_reply}, "any message", wrong_time, "Asia/Taipei")
        assert result is None, "Should NOT trigger on correct date but wrong time"
    
    def test_prd_b_p0_6_test5_business_hours_during_outside_hours(self):
        """[PRD B-P0-6-Test5] Create General Reply based on Business hours, test during/outside hours.
        
        Expected Result: Auto-reply sent based on whether message received during/outside reply hours.
        """
        # Note: Business hours implementation is placeholder - will be implemented when organization integration is ready
        # For now, we'll test with daily schedule to demonstrate the logic
        business_hours_schedule = DailySchedule(
            start_time="09:00",
            end_time="18:00"
        )
        
        schedule_settings = WebhookTriggerScheduleSettings(
            schedules=[business_hours_schedule]
        )
        
        business_auto_reply = AutoReply(
            id=1, organization_id=1, name="Business Hours Reply", status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.TIME, priority=1, keywords=None,
            trigger_schedule_type="business_hour", trigger_schedule_settings=schedule_settings,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        trigger_setting = WebhookTriggerSetting(
            id=1, auto_reply_id=1, bot_id=1, enable=True, name="Business Hours Trigger",
            event_type=WebhookTriggerEventType.TIME,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        # Test during business hours
        during_hours = datetime(2024, 1, 15, 12, 0, 0, tzinfo=ZoneInfo("Asia/Taipei"))  # Monday noon Taipei
        result = validate_trigger([trigger_setting], {1: business_auto_reply}, "any message", during_hours, "Asia/Taipei")
        assert result is not None, "Should trigger during business hours"
        assert result.auto_reply_id == 1
        
        # Test outside business hours (evening)
        outside_hours = datetime(2024, 1, 15, 22, 0, 0, tzinfo=ZoneInfo("Asia/Taipei"))  # Monday 10 PM Taipei
        result = validate_trigger([trigger_setting], {1: business_auto_reply}, "any message", outside_hours, "Asia/Taipei")
        assert result is None, "Should NOT trigger outside business hours"


class TestPriorityLogic:
    """PRD Story 4: Priority Logic (Keyword over General) tests."""
    
    def test_prd_priority_test1_keyword_and_general_both_match(self):
        """[PRD Priority-Test1] Both Keyword and General rules for same channel, message matches keyword during general time.
        
        Expected Result: Only the Keyword Reply is triggered, not the General Reply.
        """
        # 建立關鍵字自動回覆
        keyword_auto_reply = AutoReply(
            id=1, organization_id=1, name="Keyword Reply", status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD, priority=5, keywords=["hello"],
            trigger_schedule_type=None, trigger_schedule_settings=None,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        # 建立一般時間自動回覆（低優先級）
        daily_schedule = DailySchedule(start_time="09:00", end_time="18:00")
        schedule_settings = WebhookTriggerScheduleSettings(schedules=[daily_schedule])
        
        general_auto_reply = AutoReply(
            id=2, organization_id=1, name="General Reply", status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.TIME, priority=1, keywords=None,
            trigger_schedule_type="daily", trigger_schedule_settings=schedule_settings,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        # 建立觸發設定
        keyword_trigger = WebhookTriggerSetting(
            id=1, auto_reply_id=1, bot_id=1, enable=True, name="Keyword Trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        general_trigger = WebhookTriggerSetting(
            id=2, auto_reply_id=2, bot_id=1, enable=True, name="General Trigger",
            event_type=WebhookTriggerEventType.TIME,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        # 測試：在一般時間內發送匹配關鍵字的訊息
        event_time = datetime(2024, 1, 15, 12, 0, 0, tzinfo=ZoneInfo("Asia/Taipei"))  # 週一中午，在一般時間內
        result = validate_trigger(
            [keyword_trigger, general_trigger], 
            {1: keyword_auto_reply, 2: general_auto_reply}, 
            "hello", 
            event_time,
            "Asia/Taipei"
        )
        
        # 應該只觸發關鍵字回覆（較高優先級）
        assert result is not None, "應該觸發關鍵字回覆"
        assert result.auto_reply_id == 1, "應該是關鍵字回覆，不是一般回覆"
    
    def test_prd_priority_test2_no_keyword_general_matches(self):
        """[PRD Priority-Test2] Both rules for same channel, message doesn't match keyword during general time.
        
        Expected Result: Only the General Reply is triggered.
        """
        # 建立關鍵字自動回覆
        keyword_auto_reply = AutoReply(
            id=1, organization_id=1, name="Keyword Reply", status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD, priority=5, keywords=["hello"],
            trigger_schedule_type=None, trigger_schedule_settings=None,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        # 建立一般時間自動回覆
        daily_schedule = DailySchedule(start_time="09:00", end_time="18:00")
        schedule_settings = WebhookTriggerScheduleSettings(schedules=[daily_schedule])
        
        general_auto_reply = AutoReply(
            id=2, organization_id=1, name="General Reply", status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.TIME, priority=1, keywords=None,
            trigger_schedule_type="daily", trigger_schedule_settings=schedule_settings,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        # 建立觸發設定
        keyword_trigger = WebhookTriggerSetting(
            id=1, auto_reply_id=1, bot_id=1, enable=True, name="Keyword Trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        general_trigger = WebhookTriggerSetting(
            id=2, auto_reply_id=2, bot_id=1, enable=True, name="General Trigger",
            event_type=WebhookTriggerEventType.TIME,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        # 測試：在一般時間內發送不匹配關鍵字的訊息
        event_time = datetime(2024, 1, 15, 12, 0, 0, tzinfo=ZoneInfo("Asia/Taipei"))  # 週一中午，在一般時間內
        result = validate_trigger(
            [keyword_trigger, general_trigger], 
            {1: keyword_auto_reply, 2: general_auto_reply}, 
            "goodbye",  # 不匹配關鍵字
            event_time,
            "Asia/Taipei"
        )
        
        # 應該只觸發一般回覆
        assert result is not None, "應該觸發一般回覆"
        assert result.auto_reply_id == 2, "應該是一般回覆"
    
    def test_prd_priority_test3_keyword_outside_general_time(self):
        """[PRD Priority-Test3] Both rules for same channel, message matches keyword outside general time.
        
        Expected Result: Only the Keyword Reply is triggered.
        """
        # 建立關鍵字自動回覆
        keyword_auto_reply = AutoReply(
            id=1, organization_id=1, name="Keyword Reply", status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD, priority=5, keywords=["hello"],
            trigger_schedule_type=None, trigger_schedule_settings=None,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        # 建立一般時間自動回覆（工作時間）
        daily_schedule = DailySchedule(start_time="09:00", end_time="17:00")
        schedule_settings = WebhookTriggerScheduleSettings(schedules=[daily_schedule])
        
        general_auto_reply = AutoReply(
            id=2, organization_id=1, name="General Reply", status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.TIME, priority=1, keywords=None,
            trigger_schedule_type="daily", trigger_schedule_settings=schedule_settings,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        # 建立觸發設定
        keyword_trigger = WebhookTriggerSetting(
            id=1, auto_reply_id=1, bot_id=1, enable=True, name="Keyword Trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        general_trigger = WebhookTriggerSetting(
            id=2, auto_reply_id=2, bot_id=1, enable=True, name="General Trigger",
            event_type=WebhookTriggerEventType.TIME,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        # 測試：在一般時間外發送匹配關鍵字的訊息
        event_time = datetime(2024, 1, 15, 22, 0, 0, tzinfo=ZoneInfo("Asia/Taipei"))  # 週一晚上10點，在一般時間外
        result = validate_trigger(
            [keyword_trigger, general_trigger], 
            {1: keyword_auto_reply, 2: general_auto_reply}, 
            "hello",  # 匹配關鍵字
            event_time,
            "Asia/Taipei"
        )
        
        # 應該只觸發關鍵字回覆
        assert result is not None, "應該觸發關鍵字回覆"
        assert result.auto_reply_id == 1, "應該是關鍵字回覆，即使在一般時間外"


class TestMessageContentHandling:
    """PRD Story 5: Message Content Handling tests."""
    
    def test_prd_message_content_test1_keyword_rule_with_matching_message(self):
        """[PRD Message-Content-Test1] Create Keyword Reply rule, test with message containing keyword.
        
        Expected Result: Keyword reply triggered when message contains exact keyword.
        """
        # 建立關鍵字自動回覆
        keyword_auto_reply = AutoReply(
            id=1, organization_id=1, name="Keyword Reply", status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD, priority=1, keywords=["support", "help"],
            trigger_schedule_type=None, trigger_schedule_settings=None,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        trigger_setting = WebhookTriggerSetting(
            id=1, auto_reply_id=1, bot_id=1, enable=True, name="Keyword Trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        # 測試匹配關鍵字的訊息
        test_cases = ["support", "SUPPORT", "Support", "help", "HELP", " support ", "  help  "]
        for message in test_cases:
            result = validate_trigger([trigger_setting], {1: keyword_auto_reply}, message, datetime.now(tz=ZoneInfo("Asia/Taipei")), "Asia/Taipei")
            assert result is not None, f"應該觸發關鍵字回覆: '{message}'"
            assert result.auto_reply_id == 1
    
    def test_prd_message_content_test2_no_keyword_match_with_keyword_rules(self):
        """[PRD Message-Content-Test2] Send message without keyword to channel with keyword rules.
        
        Expected Result: No keyword reply triggered when message has no matching keyword.
        """
        # 建立關鍵字自動回覆
        keyword_auto_reply = AutoReply(
            id=1, organization_id=1, name="Keyword Reply", status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD, priority=1, keywords=["support", "help"],
            trigger_schedule_type=None, trigger_schedule_settings=None,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        trigger_setting = WebhookTriggerSetting(
            id=1, auto_reply_id=1, bot_id=1, enable=True, name="Keyword Trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        # 測試不匹配關鍵字的訊息
        non_matching_messages = [
            "hello", "goodbye", "information", "assist", 
            "support me", "need help", "help please",  # 包含但不完全匹配
            "supports", "helpful", "supporting"         # 相似但不完全匹配
        ]
        
        for message in non_matching_messages:
            result = validate_trigger([trigger_setting], {1: keyword_auto_reply}, message, datetime.now(tz=ZoneInfo("Asia/Taipei")), "Asia/Taipei")
            assert result is None, f"不應該觸發關鍵字回覆: '{message}'"
    
    def test_prd_message_content_test3_general_rule_any_content(self):
        """[PRD Message-Content-Test3] Create General Reply rule, test with any message content during scheduled time.
        
        Expected Result: General reply triggered regardless of message content when schedule matches.
        """
        # 建立一般時間自動回覆
        daily_schedule = DailySchedule(start_time="09:00", end_time="18:00")
        schedule_settings = WebhookTriggerScheduleSettings(schedules=[daily_schedule])
        
        general_auto_reply = AutoReply(
            id=1, organization_id=1, name="General Reply", status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.TIME, priority=1, keywords=None,
            trigger_schedule_type="daily", trigger_schedule_settings=schedule_settings,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        trigger_setting = WebhookTriggerSetting(
            id=1, auto_reply_id=1, bot_id=1, enable=True, name="General Trigger",
            event_type=WebhookTriggerEventType.TIME,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        # 在排程時間內測試各種訊息內容
        scheduled_time = datetime(2024, 1, 15, 12, 0, 0, tzinfo=ZoneInfo("Asia/Taipei"))  # 週一中午，在排程時間內
        
        # 測試各種不同的訊息內容
        various_messages = [
            "hello", "support", "help", "goodbye", "information",
            "任何中文訊息", "🎉", "123", "!@#$%",
            "", "   ", "very long message with lots of content that doesn't match any specific pattern",
            "multi\nline\nmessage"
        ]
        
        for message in various_messages:
            result = validate_trigger([trigger_setting], {1: general_auto_reply}, message, scheduled_time, "Asia/Taipei")
            assert result is not None, f"一般回覆應該被觸發，無論訊息內容為何: '{message}'"
            assert result.auto_reply_id == 1
        
        # 在排程時間外測試 - 不應該觸發
        outside_schedule_time = datetime(2024, 1, 15, 22, 0, 0, tzinfo=ZoneInfo("Asia/Taipei"))  # 週一晚上10點
        for message in ["hello", "any message"]:
            result = validate_trigger([trigger_setting], {1: general_auto_reply}, message, outside_schedule_time, "Asia/Taipei")
            assert result is None, f"在排程時間外不應該觸發一般回覆: '{message}'"