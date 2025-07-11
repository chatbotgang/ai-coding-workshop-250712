"""Tests for auto-reply trigger validation logic."""

from datetime import datetime

from internal.domain.auto_reply import (
    ChannelType,
    FollowEvent,
    MessageEvent,
    WebhookTriggerEventType,
    WebhookTriggerScheduleType,
    WebhookTriggerSetting,
    validate_trigger,
)


class MockBusinessHourChecker:
    """Mock business hour checker for testing with timezone support."""

    def __init__(self, in_business_hours: bool = True):
        self._in_business_hours = in_business_hours

    def is_in_business_hours(
        self,
        timestamp: datetime,
        organization_id: int,
        bot_timezone: str | None = None,
        organization_timezone: str | None = None,
    ) -> bool:
        """Mock business hour check with timezone support."""
        return self._in_business_hours


class TestKeywordReplyLogic:
    """Test keyword reply logic according to PRD B-P0-7."""

    def test_exact_keyword_match_various_cases(self):
        """[B-P0-7-Test2]: Test triggering with exact keyword in various cases."""
        # Create a keyword trigger
        trigger = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="test_keyword",
            event_type=WebhookTriggerEventType.MESSAGE,
            trigger_code="hello",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Test exact match
        event = MessageEvent(
            event_id="test-1",
            channel_type=ChannelType.LINE,
            user_id="user123",
            timestamp=datetime.now(),
            content="hello",
            message_id="msg-1",
        )

        result = validate_trigger([trigger], event)
        assert result.has_match
        assert result.matched_trigger == trigger
        assert result.match_type == "keyword"

        # Test case insensitive match
        event_upper = MessageEvent(
            event_id="test-2",
            channel_type=ChannelType.LINE,
            user_id="user123",
            timestamp=datetime.now(),
            content="HELLO",
            message_id="msg-2",
        )

        result = validate_trigger([trigger], event_upper)
        assert result.has_match
        assert result.matched_trigger == trigger
        assert result.match_type == "keyword"

        # Test mixed case
        event_mixed = MessageEvent(
            event_id="test-3",
            channel_type=ChannelType.LINE,
            user_id="user123",
            timestamp=datetime.now(),
            content="HeLLo",
            message_id="msg-3",
        )

        result = validate_trigger([trigger], event_mixed)
        assert result.has_match
        assert result.matched_trigger == trigger
        assert result.match_type == "keyword"

    def test_keyword_with_leading_trailing_spaces(self):
        """[B-P0-7-Test3]: Test triggering with keyword surrounded by leading/trailing spaces."""
        trigger = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="test_keyword",
            event_type=WebhookTriggerEventType.MESSAGE,
            trigger_code="hello",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Test leading spaces
        event_leading = MessageEvent(
            event_id="test-1",
            channel_type=ChannelType.LINE,
            user_id="user123",
            timestamp=datetime.now(),
            content="  hello",
            message_id="msg-1",
        )

        result = validate_trigger([trigger], event_leading)
        assert result.has_match
        assert result.matched_trigger == trigger

        # Test trailing spaces
        event_trailing = MessageEvent(
            event_id="test-2",
            channel_type=ChannelType.LINE,
            user_id="user123",
            timestamp=datetime.now(),
            content="hello  ",
            message_id="msg-2",
        )

        result = validate_trigger([trigger], event_trailing)
        assert result.has_match
        assert result.matched_trigger == trigger

        # Test both leading and trailing spaces
        event_both = MessageEvent(
            event_id="test-3",
            channel_type=ChannelType.LINE,
            user_id="user123",
            timestamp=datetime.now(),
            content="  hello  ",
            message_id="msg-3",
        )

        result = validate_trigger([trigger], event_both)
        assert result.has_match
        assert result.matched_trigger == trigger

    def test_partial_match_should_not_trigger(self):
        """[B-P0-7-Test4]: Test that partial matches do NOT trigger."""
        trigger = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="test_keyword",
            event_type=WebhookTriggerEventType.MESSAGE,
            trigger_code="hello",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Test keyword with additional text - should NOT match
        event_extra = MessageEvent(
            event_id="test-1",
            channel_type=ChannelType.LINE,
            user_id="user123",
            timestamp=datetime.now(),
            content="hello world",
            message_id="msg-1",
        )

        result = validate_trigger([trigger], event_extra)
        assert not result.has_match

        # Test keyword as part of larger word - should NOT match
        event_part = MessageEvent(
            event_id="test-2",
            channel_type=ChannelType.LINE,
            user_id="user123",
            timestamp=datetime.now(),
            content="hellothere",
            message_id="msg-2",
        )

        result = validate_trigger([trigger], event_part)
        assert not result.has_match

    def test_close_variation_should_not_trigger(self):
        """[B-P0-7-Test5]: Test that close variations do NOT trigger."""
        trigger = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="test_keyword",
            event_type=WebhookTriggerEventType.MESSAGE,
            trigger_code="hello",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Test typo - should NOT match
        event_typo = MessageEvent(
            event_id="test-1",
            channel_type=ChannelType.LINE,
            user_id="user123",
            timestamp=datetime.now(),
            content="helo",
            message_id="msg-1",
        )

        result = validate_trigger([trigger], event_typo)
        assert not result.has_match

        # Test similar word - should NOT match
        event_similar = MessageEvent(
            event_id="test-2",
            channel_type=ChannelType.LINE,
            user_id="user123",
            timestamp=datetime.now(),
            content="help",
            message_id="msg-2",
        )

        result = validate_trigger([trigger], event_similar)
        assert not result.has_match


class TestMultipleKeywordsSupport:
    """Test multiple keywords support according to PRD Multiple-Keywords."""

    def test_multiple_keywords_any_match(self):
        """[Multiple-Keywords-Test1]: Test triggering with any keyword from multiple keywords."""
        # Note: Current implementation uses trigger_code as single keyword
        # This test demonstrates the expected behavior when multiple keywords are supported

        trigger_hello = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="test_keyword",
            event_type=WebhookTriggerEventType.MESSAGE,
            trigger_code="hello",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        trigger_hi = WebhookTriggerSetting(
            id=2,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="test_keyword",
            event_type=WebhookTriggerEventType.MESSAGE,
            trigger_code="hi",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        trigger_hey = WebhookTriggerSetting(
            id=3,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="test_keyword",
            event_type=WebhookTriggerEventType.MESSAGE,
            trigger_code="hey",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        triggers = [trigger_hello, trigger_hi, trigger_hey]

        # Test first keyword
        event_hello = MessageEvent(
            event_id="test-1",
            channel_type=ChannelType.LINE,
            user_id="user123",
            timestamp=datetime.now(),
            content="hello",
            message_id="msg-1",
        )

        result = validate_trigger(triggers, event_hello)
        assert result.has_match
        assert result.matched_trigger == trigger_hello

        # Test second keyword
        event_hi = MessageEvent(
            event_id="test-2",
            channel_type=ChannelType.LINE,
            user_id="user123",
            timestamp=datetime.now(),
            content="hi",
            message_id="msg-2",
        )

        result = validate_trigger(triggers, event_hi)
        assert result.has_match
        assert result.matched_trigger == trigger_hi

        # Test third keyword
        event_hey = MessageEvent(
            event_id="test-3",
            channel_type=ChannelType.LINE,
            user_id="user123",
            timestamp=datetime.now(),
            content="hey",
            message_id="msg-3",
        )

        result = validate_trigger(triggers, event_hey)
        assert result.has_match
        assert result.matched_trigger == trigger_hey

    def test_multiple_keywords_case_insensitive(self):
        """[Multiple-Keywords-Test2]: Test case insensitive matching with multiple keywords."""
        trigger = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="test_keyword",
            event_type=WebhookTriggerEventType.MESSAGE,
            trigger_code="hello",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        event = MessageEvent(
            event_id="test-1",
            channel_type=ChannelType.LINE,
            user_id="user123",
            timestamp=datetime.now(),
            content="HELLO",
            message_id="msg-1",
        )

        result = validate_trigger([trigger], event)
        assert result.has_match
        assert result.matched_trigger == trigger

    def test_no_keyword_match(self):
        """[Multiple-Keywords-Test3]: Test no match when message doesn't match any keyword."""
        trigger = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="test_keyword",
            event_type=WebhookTriggerEventType.MESSAGE,
            trigger_code="hello",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        event = MessageEvent(
            event_id="test-1",
            channel_type=ChannelType.LINE,
            user_id="user123",
            timestamp=datetime.now(),
            content="goodbye",
            message_id="msg-1",
        )

        result = validate_trigger([trigger], event)
        assert not result.has_match


class TestGeneralTimeBasedLogic:
    """Test general time-based logic according to PRD B-P0-6."""

    def test_daily_schedule_within_time_window(self):
        """[B-P0-6-Test3]: Test daily schedule triggering within time window."""
        trigger = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="daily_trigger",
            event_type=WebhookTriggerEventType.TIME,
            trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
            trigger_schedule_settings={"start_time": "10:00", "end_time": "12:00"},
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Test within time window
        event_within = MessageEvent(
            event_id="test-1",
            channel_type=ChannelType.LINE,
            user_id="user123",
            timestamp=datetime(2025, 1, 15, 11, 0),  # 11:00 AM
            content="any message",
            message_id="msg-1",
        )

        result = validate_trigger([trigger], event_within)
        assert result.has_match
        assert result.matched_trigger == trigger
        assert result.match_type == "general"

        # Test outside time window
        event_outside = MessageEvent(
            event_id="test-2",
            channel_type=ChannelType.LINE,
            user_id="user123",
            timestamp=datetime(2025, 1, 15, 13, 0),  # 1:00 PM
            content="any message",
            message_id="msg-2",
        )

        result = validate_trigger([trigger], event_outside)
        assert not result.has_match

    def test_monthly_schedule_on_specific_date(self):
        """[B-P0-6-Test4]: Test monthly schedule triggering on specific date."""
        trigger = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="monthly_trigger",
            event_type=WebhookTriggerEventType.TIME,
            trigger_schedule_type=WebhookTriggerScheduleType.MONTHLY,
            trigger_schedule_settings={"day": 15, "start_time": "14:00", "end_time": "16:00"},
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Test on correct day and time
        event_correct = MessageEvent(
            event_id="test-1",
            channel_type=ChannelType.LINE,
            user_id="user123",
            timestamp=datetime(2025, 1, 15, 15, 0),  # Jan 15, 3:00 PM
            content="any message",
            message_id="msg-1",
        )

        result = validate_trigger([trigger], event_correct)
        assert result.has_match
        assert result.matched_trigger == trigger
        assert result.match_type == "general"

        # Test on wrong day
        event_wrong_day = MessageEvent(
            event_id="test-2",
            channel_type=ChannelType.LINE,
            user_id="user123",
            timestamp=datetime(2025, 1, 16, 15, 0),  # Jan 16, 3:00 PM
            content="any message",
            message_id="msg-2",
        )

        result = validate_trigger([trigger], event_wrong_day)
        assert not result.has_match

        # Test on correct day but wrong time
        event_wrong_time = MessageEvent(
            event_id="test-3",
            channel_type=ChannelType.LINE,
            user_id="user123",
            timestamp=datetime(2025, 1, 15, 17, 0),  # Jan 15, 5:00 PM
            content="any message",
            message_id="msg-3",
        )

        result = validate_trigger([trigger], event_wrong_time)
        assert not result.has_match

    def test_business_hours_trigger(self):
        """[B-P0-6-Test5]: Test business hours triggering."""
        trigger = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="business_hours_trigger",
            event_type=WebhookTriggerEventType.TIME,
            trigger_schedule_type=WebhookTriggerScheduleType.BUSINESS_HOUR,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        event = MessageEvent(
            event_id="test-1",
            channel_type=ChannelType.LINE,
            user_id="user123",
            timestamp=datetime.now(),
            content="any message",
            message_id="msg-1",
        )

        # Test during business hours
        business_hour_checker = MockBusinessHourChecker(in_business_hours=True)
        result = validate_trigger([trigger], event, business_hour_checker, 1)
        assert result.has_match
        assert result.matched_trigger == trigger
        assert result.match_type == "general"

        # Test outside business hours
        business_hour_checker = MockBusinessHourChecker(in_business_hours=False)
        result = validate_trigger([trigger], event, business_hour_checker, 1)
        assert not result.has_match


class TestPriorityLogic:
    """Test priority logic according to PRD Priority-Logic."""

    def test_keyword_priority_over_general(self):
        """[Priority-Test1]: Test keyword triggers have priority over general triggers."""
        keyword_trigger = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="keyword_trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            trigger_code="hello",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        general_trigger = WebhookTriggerSetting(
            id=2,
            auto_reply_id=2,
            bot_id=1,
            enable=True,
            name="general_trigger",
            event_type=WebhookTriggerEventType.TIME,
            trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
            trigger_schedule_settings={"start_time": "00:00", "end_time": "23:59"},
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Message that matches keyword during general time window
        event = MessageEvent(
            event_id="test-1",
            channel_type=ChannelType.LINE,
            user_id="user123",
            timestamp=datetime(2025, 1, 15, 12, 0),
            content="hello",
            message_id="msg-1",
        )

        result = validate_trigger([keyword_trigger, general_trigger], event)
        assert result.has_match
        assert result.matched_trigger == keyword_trigger
        assert result.match_type == "keyword"

    def test_general_trigger_when_no_keyword_match(self):
        """[Priority-Test2]: Test general trigger activates when no keyword matches."""
        keyword_trigger = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="keyword_trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            trigger_code="hello",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        general_trigger = WebhookTriggerSetting(
            id=2,
            auto_reply_id=2,
            bot_id=1,
            enable=True,
            name="general_trigger",
            event_type=WebhookTriggerEventType.TIME,
            trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
            trigger_schedule_settings={"start_time": "00:00", "end_time": "23:59"},
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Message that doesn't match keyword but is in general time window
        event = MessageEvent(
            event_id="test-1",
            channel_type=ChannelType.LINE,
            user_id="user123",
            timestamp=datetime(2025, 1, 15, 12, 0),
            content="goodbye",
            message_id="msg-1",
        )

        result = validate_trigger([keyword_trigger, general_trigger], event)
        assert result.has_match
        assert result.matched_trigger == general_trigger
        assert result.match_type == "general"

    def test_keyword_priority_outside_general_time(self):
        """[Priority-Test3]: Test keyword trigger activates outside general time window."""
        keyword_trigger = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="keyword_trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            trigger_code="hello",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        general_trigger = WebhookTriggerSetting(
            id=2,
            auto_reply_id=2,
            bot_id=1,
            enable=True,
            name="general_trigger",
            event_type=WebhookTriggerEventType.TIME,
            trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
            trigger_schedule_settings={"start_time": "09:00", "end_time": "17:00"},
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Message that matches keyword outside general time window
        event = MessageEvent(
            event_id="test-1",
            channel_type=ChannelType.LINE,
            user_id="user123",
            timestamp=datetime(2025, 1, 15, 20, 0),  # 8:00 PM - outside business hours
            content="hello",
            message_id="msg-1",
        )

        result = validate_trigger([keyword_trigger, general_trigger], event)
        assert result.has_match
        assert result.matched_trigger == keyword_trigger
        assert result.match_type == "keyword"


class TestWelcomeTrigger:
    """Test welcome trigger functionality."""

    def test_follow_event_triggers_welcome(self):
        """Test that FOLLOW events trigger welcome triggers."""
        welcome_trigger = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="welcome_trigger",
            event_type=WebhookTriggerEventType.FOLLOW,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        follow_event = FollowEvent(
            event_id="test-1", channel_type=ChannelType.LINE, user_id="user123", timestamp=datetime.now()
        )

        result = validate_trigger([welcome_trigger], follow_event)
        assert result.has_match
        assert result.matched_trigger == welcome_trigger
        assert result.match_type == "welcome"

    def test_message_event_does_not_trigger_welcome(self):
        """Test that MESSAGE events do not trigger welcome triggers."""
        welcome_trigger = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="welcome_trigger",
            event_type=WebhookTriggerEventType.FOLLOW,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        message_event = MessageEvent(
            event_id="test-1",
            channel_type=ChannelType.LINE,
            user_id="user123",
            timestamp=datetime.now(),
            content="hello",
            message_id="msg-1",
        )

        result = validate_trigger([welcome_trigger], message_event)
        assert not result.has_match


class TestInactiveTriggers:
    """Test that inactive triggers are not processed."""

    def test_disabled_trigger_not_processed(self):
        """Test that disabled triggers are not processed."""
        disabled_trigger = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=False,  # Disabled
            name="disabled_trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            trigger_code="hello",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        event = MessageEvent(
            event_id="test-1",
            channel_type=ChannelType.LINE,
            user_id="user123",
            timestamp=datetime.now(),
            content="hello",
            message_id="msg-1",
        )

        result = validate_trigger([disabled_trigger], event)
        assert not result.has_match

    def test_archived_trigger_not_processed(self):
        """Test that archived triggers are not processed."""
        archived_trigger = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="archived_trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            trigger_code="hello",
            archived=True,  # Archived
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        event = MessageEvent(
            event_id="test-1",
            channel_type=ChannelType.LINE,
            user_id="user123",
            timestamp=datetime.now(),
            content="hello",
            message_id="msg-1",
        )

        result = validate_trigger([archived_trigger], event)
        assert not result.has_match


class TestIGStoryKeywordLogic:
    """Test IG Story keyword trigger logic according to PRD Feature 2."""

    def test_ig_story_keyword_trigger_with_matching_story_and_keyword(self):
        """[IG-Story-Keyword-Test1]: IG story keyword trigger with matching story ID and keyword."""
        # Create IG Story keyword trigger
        ig_story_trigger = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="ig_story_keyword_trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            extra={"ig_story_ids": ["story123"], "keywords": ["hello"]},
        )

        # Create message event with matching story ID and keyword
        event = MessageEvent(
            event_id="test-1",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user123",
            timestamp=datetime.now(),
            content="hello",
            message_id="msg-1",
            extra={"ig_story_id": "story123"},
        )

        result = validate_trigger([ig_story_trigger], event)
        assert result.has_match
        assert result.matched_trigger == ig_story_trigger
        assert result.match_type == "ig_story_keyword"

    def test_ig_story_keyword_trigger_wrong_story_id(self):
        """[IG-Story-Keyword-Test2]: IG story keyword trigger with wrong story ID."""
        ig_story_trigger = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="ig_story_keyword_trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            extra={"ig_story_ids": ["story123"], "keywords": ["hello"]},
        )

        # Create message event with wrong story ID
        event = MessageEvent(
            event_id="test-1",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user123",
            timestamp=datetime.now(),
            content="hello",
            message_id="msg-1",
            extra={"ig_story_id": "story456"},  # Wrong story ID
        )

        result = validate_trigger([ig_story_trigger], event)
        assert not result.has_match

    def test_ig_story_keyword_trigger_no_story_context(self):
        """[IG-Story-Keyword-Test3]: IG story keyword trigger with no story context."""
        ig_story_trigger = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="ig_story_keyword_trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            extra={"ig_story_ids": ["story123"], "keywords": ["hello"]},
        )

        # Create message event without story context
        event = MessageEvent(
            event_id="test-1",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user123",
            timestamp=datetime.now(),
            content="hello",
            message_id="msg-1",
            # No extra field with ig_story_id
        )

        result = validate_trigger([ig_story_trigger], event)
        assert not result.has_match

    def test_ig_story_keyword_case_insensitive_matching(self):
        """[B-P1-18-Test8a]: IG story keyword trigger with case insensitive matching."""
        ig_story_trigger = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="ig_story_keyword_trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            extra={"ig_story_ids": ["story123"], "keywords": ["hello"]},
        )

        # Test various case combinations
        test_cases = ["HELLO", "Hello", "HeLLo", "  hello  "]

        for content in test_cases:
            event = MessageEvent(
                event_id=f"test-{content}",
                channel_type=ChannelType.INSTAGRAM,
                user_id="user123",
                timestamp=datetime.now(),
                content=content,
                message_id=f"msg-{content}",
                extra={"ig_story_id": "story123"},
            )

            result = validate_trigger([ig_story_trigger], event)
            assert result.has_match, f"Failed for content: '{content}'"
            assert result.match_type == "ig_story_keyword"


class TestIGStoryGeneralLogic:
    """Test IG Story general (time-based) trigger logic according to PRD Feature 2."""

    def test_ig_story_general_trigger_within_schedule(self):
        """[IG-Story-General-Test1]: IG story general trigger within scheduled time."""
        ig_story_general_trigger = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="ig_story_general_trigger",
            event_type=WebhookTriggerEventType.TIME,
            trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
            trigger_schedule_settings={"start_time": "09:00", "end_time": "17:00"},
            created_at=datetime.now(),
            updated_at=datetime.now(),
            extra={
                "ig_story_ids": ["story123"]
                # No keywords = general trigger
            },
        )

        # Create message event within schedule and matching story
        event = MessageEvent(
            event_id="test-1",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user123",
            timestamp=datetime(2025, 1, 15, 14, 0),  # 2:00 PM - within schedule
            content="any message",
            message_id="msg-1",
            extra={"ig_story_id": "story123"},
        )

        result = validate_trigger([ig_story_general_trigger], event)
        assert result.has_match
        assert result.matched_trigger == ig_story_general_trigger
        assert result.match_type == "ig_story_general"

    def test_ig_story_general_trigger_outside_schedule(self):
        """[IG-Story-General-Test2]: IG story general trigger outside scheduled time."""
        ig_story_general_trigger = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="ig_story_general_trigger",
            event_type=WebhookTriggerEventType.TIME,
            trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
            trigger_schedule_settings={"start_time": "09:00", "end_time": "17:00"},
            created_at=datetime.now(),
            updated_at=datetime.now(),
            extra={"ig_story_ids": ["story123"]},
        )

        # Create message event outside schedule
        event = MessageEvent(
            event_id="test-1",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user123",
            timestamp=datetime(2025, 1, 15, 20, 0),  # 8:00 PM - outside schedule
            content="any message",
            message_id="msg-1",
            extra={"ig_story_id": "story123"},
        )

        result = validate_trigger([ig_story_general_trigger], event)
        assert not result.has_match

    def test_ig_story_general_trigger_wrong_story_id(self):
        """[IG-Story-General-Test3]: IG story general trigger with wrong story ID."""
        ig_story_general_trigger = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="ig_story_general_trigger",
            event_type=WebhookTriggerEventType.TIME,
            trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
            trigger_schedule_settings={"start_time": "09:00", "end_time": "17:00"},
            created_at=datetime.now(),
            updated_at=datetime.now(),
            extra={"ig_story_ids": ["story123"]},
        )

        # Create message event with wrong story ID
        event = MessageEvent(
            event_id="test-1",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user123",
            timestamp=datetime(2025, 1, 15, 14, 0),  # Within schedule
            content="any message",
            message_id="msg-1",
            extra={"ig_story_id": "story456"},  # Wrong story ID
        )

        result = validate_trigger([ig_story_general_trigger], event)
        assert not result.has_match


class TestIGStoryPrioritySystem:
    """Test IG Story priority over general triggers according to PRD."""

    def test_ig_story_keyword_priority_over_general_keyword(self):
        """[IG-Story-Priority-Test1]: IG story keyword priority over general keyword."""
        # IG Story keyword trigger
        ig_story_keyword_trigger = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="ig_story_keyword_trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            extra={"ig_story_ids": ["story123"], "keywords": ["hello"]},
        )

        # General keyword trigger
        general_keyword_trigger = WebhookTriggerSetting(
            id=2,
            auto_reply_id=2,
            bot_id=1,
            enable=True,
            name="general_keyword_trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            trigger_code="hello",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Message that matches both triggers
        event = MessageEvent(
            event_id="test-1",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user123",
            timestamp=datetime.now(),
            content="hello",
            message_id="msg-1",
            extra={"ig_story_id": "story123"},
        )

        result = validate_trigger([ig_story_keyword_trigger, general_keyword_trigger], event)
        assert result.has_match
        assert result.matched_trigger == ig_story_keyword_trigger
        assert result.match_type == "ig_story_keyword"

    def test_ig_story_general_priority_over_general_time(self):
        """[IG-Story-Priority-Test2]: IG story general priority over general time-based."""
        # IG Story general trigger
        ig_story_general_trigger = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="ig_story_general_trigger",
            event_type=WebhookTriggerEventType.TIME,
            trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
            trigger_schedule_settings={"start_time": "09:00", "end_time": "17:00"},
            created_at=datetime.now(),
            updated_at=datetime.now(),
            extra={"ig_story_ids": ["story123"]},
        )

        # General time-based trigger
        general_time_trigger = WebhookTriggerSetting(
            id=2,
            auto_reply_id=2,
            bot_id=1,
            enable=True,
            name="general_time_trigger",
            event_type=WebhookTriggerEventType.TIME,
            trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
            trigger_schedule_settings={"start_time": "09:00", "end_time": "17:00"},
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Message during scheduled time with story ID
        event = MessageEvent(
            event_id="test-1",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user123",
            timestamp=datetime(2025, 1, 15, 14, 0),  # 2:00 PM - within schedule
            content="any message",
            message_id="msg-1",
            extra={"ig_story_id": "story123"},
        )

        result = validate_trigger([ig_story_general_trigger, general_time_trigger], event)
        assert result.has_match
        assert result.matched_trigger == ig_story_general_trigger
        assert result.match_type == "ig_story_general"

    def test_story_specific_trigger_excludes_general_processing(self):
        """[B-P1-18-Test9]: Story-specific trigger takes precedence when both conditions met."""
        # Story-specific keyword trigger
        story_keyword_trigger = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="story_keyword_trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            extra={"ig_story_ids": ["story123"], "keywords": ["hello"]},
        )

        # General keyword trigger for same keyword
        general_keyword_trigger = WebhookTriggerSetting(
            id=2,
            auto_reply_id=2,
            bot_id=1,
            enable=True,
            name="general_keyword_trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            trigger_code="hello",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Message that matches both (story reply + keyword)
        event = MessageEvent(
            event_id="test-1",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user123",
            timestamp=datetime.now(),
            content="hello",
            message_id="msg-1",
            extra={"ig_story_id": "story123"},
        )

        result = validate_trigger([story_keyword_trigger, general_keyword_trigger], event)
        assert result.has_match
        assert result.matched_trigger == story_keyword_trigger
        assert result.match_type == "ig_story_keyword"


class TestIGStoryMultipleKeywords:
    """Test IG Story multiple keywords support according to PRD."""

    def test_ig_story_multiple_keywords_any_match(self):
        """[IG-Story-Multiple-Keywords-Test1]: Multiple keywords, any keyword should trigger."""
        ig_story_trigger = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="ig_story_multiple_keywords",
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            extra={"ig_story_ids": ["story123"], "keywords": ["hello", "hi", "help"]},
        )

        # Test each keyword individually
        test_keywords = ["hello", "hi", "help"]
        for keyword in test_keywords:
            event = MessageEvent(
                event_id=f"test-{keyword}",
                channel_type=ChannelType.INSTAGRAM,
                user_id="user123",
                timestamp=datetime.now(),
                content=keyword,
                message_id=f"msg-{keyword}",
                extra={"ig_story_id": "story123"},
            )

            result = validate_trigger([ig_story_trigger], event)
            assert result.has_match, f"Failed for keyword: {keyword}"
            assert result.matched_trigger == ig_story_trigger
            assert result.match_type == "ig_story_keyword"

    def test_ig_story_multiple_keywords_wrong_story_id(self):
        """[IG-Story-Multiple-Keywords-Test2]: Multiple keywords with wrong story ID."""
        ig_story_trigger = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="ig_story_multiple_keywords",
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            extra={"ig_story_ids": ["story123"], "keywords": ["hello", "hi", "help"]},
        )

        # Test with matching keyword but wrong story ID
        event = MessageEvent(
            event_id="test-1",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user123",
            timestamp=datetime.now(),
            content="hello",
            message_id="msg-1",
            extra={"ig_story_id": "story456"},  # Wrong story ID
        )

        result = validate_trigger([ig_story_trigger], event)
        assert not result.has_match


class TestCompletePrioritySystem:
    """Test complete 5-level priority system according to PRD."""

    def test_complete_priority_order_all_triggers(self):
        """[Complete-Priority-Test1]: All 4 types of rules, highest priority wins."""
        # Priority 0: IG Story keyword
        ig_story_keyword_trigger = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="ig_story_keyword",
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            extra={"ig_story_ids": ["story123"], "keywords": ["hello"]},
        )

        # Priority 0.5: IG Story general
        ig_story_general_trigger = WebhookTriggerSetting(
            id=2,
            auto_reply_id=2,
            bot_id=1,
            enable=True,
            name="ig_story_general",
            event_type=WebhookTriggerEventType.TIME,
            trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
            trigger_schedule_settings={"start_time": "00:00", "end_time": "23:59"},
            created_at=datetime.now(),
            updated_at=datetime.now(),
            extra={"ig_story_ids": ["story123"]},
        )

        # Priority 1: General keyword
        general_keyword_trigger = WebhookTriggerSetting(
            id=3,
            auto_reply_id=3,
            bot_id=1,
            enable=True,
            name="general_keyword",
            event_type=WebhookTriggerEventType.MESSAGE,
            trigger_code="hello",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Priority 3: General time-based
        general_time_trigger = WebhookTriggerSetting(
            id=4,
            auto_reply_id=4,
            bot_id=1,
            enable=True,
            name="general_time",
            event_type=WebhookTriggerEventType.TIME,
            trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
            trigger_schedule_settings={"start_time": "00:00", "end_time": "23:59"},
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Message that could match all rules
        event = MessageEvent(
            event_id="test-1",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user123",
            timestamp=datetime(2025, 1, 15, 14, 0),
            content="hello",
            message_id="msg-1",
            extra={"ig_story_id": "story123"},
        )

        all_triggers = [
            ig_story_keyword_trigger,
            ig_story_general_trigger,
            general_keyword_trigger,
            general_time_trigger,
        ]
        result = validate_trigger(all_triggers, event)

        assert result.has_match
        assert result.matched_trigger == ig_story_keyword_trigger
        assert result.match_type == "ig_story_keyword"

    def test_priority_2_ig_story_general_wins(self):
        """[Complete-Priority-Test2]: IG story general beats general keyword and time."""
        # Priority 0.5: IG Story general
        ig_story_general_trigger = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="ig_story_general",
            event_type=WebhookTriggerEventType.TIME,
            trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
            trigger_schedule_settings={"start_time": "00:00", "end_time": "23:59"},
            created_at=datetime.now(),
            updated_at=datetime.now(),
            extra={"ig_story_ids": ["story123"]},
        )

        # Priority 1: General keyword
        general_keyword_trigger = WebhookTriggerSetting(
            id=2,
            auto_reply_id=2,
            bot_id=1,
            enable=True,
            name="general_keyword",
            event_type=WebhookTriggerEventType.MESSAGE,
            trigger_code="help",  # Different keyword so IG story keyword doesn't match
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Priority 3: General time-based
        general_time_trigger = WebhookTriggerSetting(
            id=3,
            auto_reply_id=3,
            bot_id=1,
            enable=True,
            name="general_time",
            event_type=WebhookTriggerEventType.TIME,
            trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
            trigger_schedule_settings={"start_time": "00:00", "end_time": "23:59"},
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Message during scheduled time with story ID but non-matching keyword
        event = MessageEvent(
            event_id="test-1",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user123",
            timestamp=datetime(2025, 1, 15, 14, 0),
            content="random message",  # Doesn't match "help" keyword
            message_id="msg-1",
            extra={"ig_story_id": "story123"},
        )

        result = validate_trigger([ig_story_general_trigger, general_keyword_trigger, general_time_trigger], event)
        assert result.has_match
        assert result.matched_trigger == ig_story_general_trigger
        assert result.match_type == "ig_story_general"

    def test_priority_3_general_keyword_wins(self):
        """[Complete-Priority-Test3]: General keyword beats general time when no IG story."""
        # Priority 1: General keyword
        general_keyword_trigger = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="general_keyword",
            event_type=WebhookTriggerEventType.MESSAGE,
            trigger_code="hello",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Priority 3: General time-based
        general_time_trigger = WebhookTriggerSetting(
            id=2,
            auto_reply_id=2,
            bot_id=1,
            enable=True,
            name="general_time",
            event_type=WebhookTriggerEventType.TIME,
            trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
            trigger_schedule_settings={"start_time": "00:00", "end_time": "23:59"},
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Message with matching keyword during scheduled time but no story ID
        event = MessageEvent(
            event_id="test-1",
            channel_type=ChannelType.LINE,  # Not Instagram
            user_id="user123",
            timestamp=datetime(2025, 1, 15, 14, 0),
            content="hello",
            message_id="msg-1",
            # No IG story context
        )

        result = validate_trigger([general_keyword_trigger, general_time_trigger], event)
        assert result.has_match
        assert result.matched_trigger == general_keyword_trigger
        assert result.match_type == "keyword"

    def test_priority_4_general_time_wins_when_alone(self):
        """[Complete-Priority-Test4]: General time-based wins when only option."""
        # Priority 3: General time-based only
        general_time_trigger = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="general_time",
            event_type=WebhookTriggerEventType.TIME,
            trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
            trigger_schedule_settings={"start_time": "00:00", "end_time": "23:59"},
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Message during scheduled time with no keyword and no story ID
        event = MessageEvent(
            event_id="test-1",
            channel_type=ChannelType.LINE,
            user_id="user123",
            timestamp=datetime(2025, 1, 15, 14, 0),
            content="random message",
            message_id="msg-1",
        )

        result = validate_trigger([general_time_trigger], event)
        assert result.has_match
        assert result.matched_trigger == general_time_trigger
        assert result.match_type == "general"


class TestIGStoryExclusionLogic:
    """Test IG Story exclusion from general trigger processing according to PRD."""

    def test_ig_story_specific_excluded_from_general_processing(self):
        """[IG-Story-Exclusion-Test1]: IG story-specific settings excluded from general processing."""
        # IG story-specific keyword trigger
        ig_story_keyword_trigger = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="ig_story_keyword",
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            extra={"ig_story_ids": ["story123"], "keywords": ["hello"]},
        )

        # Normal message with keyword but no IG story ID
        event = MessageEvent(
            event_id="test-1",
            channel_type=ChannelType.LINE,
            user_id="user123",
            timestamp=datetime.now(),
            content="hello",
            message_id="msg-1",
            # No IG story context
        )

        result = validate_trigger([ig_story_keyword_trigger], event)
        assert not result.has_match

    def test_general_keyword_setting_triggers_without_story(self):
        """[IG-Story-Exclusion-Test2]: General keyword settings work without IG story."""
        # Normal keyword trigger (not IG story-specific)
        general_keyword_trigger = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="general_keyword",
            event_type=WebhookTriggerEventType.MESSAGE,
            trigger_code="hello",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Normal message with matching keyword
        event = MessageEvent(
            event_id="test-1",
            channel_type=ChannelType.LINE,
            user_id="user123",
            timestamp=datetime.now(),
            content="hello",
            message_id="msg-1",
        )

        result = validate_trigger([general_keyword_trigger], event)
        assert result.has_match
        assert result.matched_trigger == general_keyword_trigger
        assert result.match_type == "keyword"

    def test_mixed_triggers_correct_separation(self):
        """[IG-Story-Exclusion-Test3]: Mixed IG story and general triggers work independently."""
        # IG story-specific keyword trigger
        ig_story_keyword_trigger = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="ig_story_keyword",
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            extra={"ig_story_ids": ["story123"], "keywords": ["hello"]},
        )

        # General keyword trigger for same keyword
        general_keyword_trigger = WebhookTriggerSetting(
            id=2,
            auto_reply_id=2,
            bot_id=1,
            enable=True,
            name="general_keyword",
            event_type=WebhookTriggerEventType.MESSAGE,
            trigger_code="hello",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Message with keyword but no story ID - should only trigger general
        event = MessageEvent(
            event_id="test-1",
            channel_type=ChannelType.LINE,
            user_id="user123",
            timestamp=datetime.now(),
            content="hello",
            message_id="msg-1",
        )

        result = validate_trigger([ig_story_keyword_trigger, general_keyword_trigger], event)
        assert result.has_match
        assert result.matched_trigger == general_keyword_trigger
        assert result.match_type == "keyword"
