"""Tests for auto reply functions."""

import pytest
from datetime import datetime, time
from internal.domain.auto_reply.auto_reply import (
    keyword_auto_reply,
    general_auto_reply,
    validate_trigger,
    AutoReply,
    AutoReplyStatus,
    AutoReplyEventType,
    TriggerType,
    TriggerValidationResult,
)
from internal.domain.auto_reply.webhook_event import MessageEvent, ChannelType
from internal.domain.auto_reply.webhook_trigger import (
    WebhookTriggerScheduleType,
    WebhookTriggerScheduleSettings,
    DailySchedule,
    MonthlySchedule,
    BusinessHourSchedule,
    NonBusinessHourSchedule,
)


class TestKeywordAutoReply:
    """Test cases for keyword_auto_reply function."""

    def test_keyword_auto_reply_greeting_keywords(self):
        """Test greeting keyword matching."""
        # Test hello
        result = keyword_auto_reply("Hello there!")
        assert result is not None
        assert result["reply_type"] == "keyword"
        assert result["matched_keyword"] == "hello"
        assert result["confidence_score"] == 1.0
        assert "Hello! How can I help you today?" in result["reply_text"]

        # Test hi
        result = keyword_auto_reply("Hi, I need help")
        assert result is not None
        assert result["matched_keyword"] == "hi"

        # Test case insensitive
        result = keyword_auto_reply("HEY THERE")
        assert result is not None
        assert result["matched_keyword"] == "hey"

    def test_keyword_auto_reply_help_keywords(self):
        """Test help keyword matching."""
        result = keyword_auto_reply("I need help with something")
        assert result is not None
        assert result["reply_type"] == "keyword"
        assert result["matched_keyword"] == "help"
        assert result["confidence_score"] == 1.0

        result = keyword_auto_reply("Can you provide support?")
        assert result is not None
        assert result["matched_keyword"] == "support"

    def test_keyword_auto_reply_product_keywords(self):
        """Test product/service keyword matching."""
        result = keyword_auto_reply("What's the price?")
        assert result is not None
        assert result["matched_keyword"] == "price"

        result = keyword_auto_reply("Tell me about your pricing")
        assert result is not None
        assert result["matched_keyword"] == "pricing"

        result = keyword_auto_reply("What products do you offer?")
        assert result is not None
        assert result["matched_keyword"] == "product"

    def test_keyword_auto_reply_contact_keywords(self):
        """Test contact keyword matching."""
        result = keyword_auto_reply("How can I contact you?")
        assert result is not None
        assert result["matched_keyword"] == "contact"

        result = keyword_auto_reply("What's your phone number?")
        assert result is not None
        assert result["matched_keyword"] == "phone"

    def test_keyword_auto_reply_business_hours(self):
        """Test business hours keyword matching."""
        result = keyword_auto_reply("What are your hours?")
        assert result is not None
        assert result["matched_keyword"] == "hours"

        result = keyword_auto_reply("Are you open today?")
        assert result is not None
        assert result["matched_keyword"] == "open"

    def test_keyword_auto_reply_phrase_matching(self):
        """Test multi-word phrase matching."""
        result = keyword_auto_reply("Good morning! How are you?")
        assert result is not None
        assert result["matched_keyword"] == "good morning"

        result = keyword_auto_reply("Good afternoon, I have a question")
        assert result is not None
        assert result["matched_keyword"] == "good afternoon"

    def test_keyword_auto_reply_no_match(self):
        """Test cases where no keyword matches."""
        result = keyword_auto_reply("This is a random message with no keywords")
        assert result is None

        result = keyword_auto_reply("xyz123 random text")
        assert result is None

    def test_keyword_auto_reply_empty_input(self):
        """Test empty or None input."""
        result = keyword_auto_reply("")
        assert result is None

        result = keyword_auto_reply("   ")  # whitespace only
        assert result is None

        result = keyword_auto_reply(None)
        assert result is None

    def test_keyword_auto_reply_partial_matches(self):
        """Test partial word matching within sentences."""
        result = keyword_auto_reply("I would like some assistance please")
        assert result is not None
        assert result["matched_keyword"] == "assistance"

        result = keyword_auto_reply("Can you help me with customer service?")
        # Should match both "help" and "service" - test which one takes priority
        assert result is not None
        assert result["matched_keyword"] in ["help", "service"]


class TestGeneralAutoReply:
    """Test cases for general_auto_reply function."""

    def test_general_auto_reply_valid_message(self):
        """Test general reply for valid messages."""
        result = general_auto_reply("This is a random message")
        assert result is not None
        assert result["reply_type"] == "general"
        assert result["matched_keyword"] is None
        assert result["confidence_score"] == 0.8
        assert "Thank you for your message" in result["reply_text"]

    def test_general_auto_reply_empty_input(self):
        """Test empty or None input."""
        result = general_auto_reply("")
        assert result is None

        result = general_auto_reply("   ")  # whitespace only
        assert result is None

        result = general_auto_reply(None)
        assert result is None

    def test_general_auto_reply_consistency(self):
        """Test that general reply is consistent."""
        result1 = general_auto_reply("Message 1")
        result2 = general_auto_reply("Message 2")

        assert result1 is not None
        assert result2 is not None
        assert result1["reply_text"] == result2["reply_text"]  # Same reply for consistency
        assert result1["confidence_score"] == result2["confidence_score"]

    def test_general_auto_reply_various_inputs(self):
        """Test general reply with various input types."""
        test_messages = [
            "Random text",
            "1234567890",
            "Special characters: !@#$%^&*()",
            "Very long message that contains lots of text but no specific keywords that would trigger keyword-based replies",
            "Mixed 123 content with numbers and text",
        ]

        for message in test_messages:
            result = general_auto_reply(message)
            assert result is not None
            assert result["reply_type"] == "general"
            assert result["matched_keyword"] is None


class TestAutoReplyIntegration:
    """Integration tests for the auto-reply flow."""

    def test_keyword_priority_over_general(self):
        """Test that keyword replies take priority over general replies."""
        message = "Hello, I need help"

        # Try keyword first
        keyword_result = keyword_auto_reply(message)
        assert keyword_result is not None
        assert keyword_result["reply_type"] == "keyword"

        # General reply should also work but shouldn't be used when keyword matches
        general_result = general_auto_reply(message)
        assert general_result is not None
        assert general_result["reply_type"] == "general"

    def test_full_auto_reply_flow(self):
        """Test the complete auto-reply flow simulation."""
        test_cases = [
            {"message": "Hello there!", "expected_type": "keyword", "expected_keyword": "hello"},
            {"message": "Random message with no keywords", "expected_type": "general", "expected_keyword": None},
            {
                "message": "I need support with pricing",
                "expected_type": "keyword",
                "expected_keyword": "support",  # First match wins
            },
        ]

        for case in test_cases:
            # Simulate the flow: try keyword first, then general
            result = keyword_auto_reply(case["message"])
            if result is None:
                result = general_auto_reply(case["message"])

            assert result is not None
            assert result["reply_type"] == case["expected_type"]
            assert result["matched_keyword"] == case["expected_keyword"]

    def test_response_structure_validation(self):
        """Test that response structures are valid."""
        # Test keyword response structure
        keyword_result = keyword_auto_reply("hello")
        assert isinstance(keyword_result, dict)
        assert "reply_text" in keyword_result
        assert "reply_type" in keyword_result
        assert "confidence_score" in keyword_result
        assert "matched_keyword" in keyword_result
        assert isinstance(keyword_result["confidence_score"], float)
        assert 0.0 <= keyword_result["confidence_score"] <= 1.0

        # Test general response structure
        general_result = general_auto_reply("random message")
        assert isinstance(general_result, dict)
        assert "reply_text" in general_result
        assert "reply_type" in general_result
        assert "confidence_score" in general_result
        assert "matched_keyword" in general_result
        assert isinstance(general_result["confidence_score"], float)
        assert 0.0 <= general_result["confidence_score"] <= 1.0
        assert general_result["matched_keyword"] is None


class TestValidateTrigger:
    """Test cases for validate_trigger function based on PRD requirements."""

    def setup_method(self):
        """Set up test data for each test method."""
        self.test_time = datetime(2025, 7, 16, 14, 30, 0)  # Wednesday 2:30 PM

        # Create test auto-reply rules
        self.keyword_rule_hello = AutoReply(
            id=1,
            organization_id=100,
            name="Greeting Rule",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD,
            priority=1,
            keywords=["hello", "hi", "hey"],
            created_at=self.test_time,
            updated_at=self.test_time,
        )

        self.keyword_rule_help = AutoReply(
            id=2,
            organization_id=100,
            name="Help Rule",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD,
            priority=1,
            keywords=["help", "support"],
            created_at=self.test_time,
            updated_at=self.test_time,
        )

        # Daily schedule rule (9 AM to 5 PM)
        daily_schedule = WebhookTriggerScheduleSettings(schedules=[DailySchedule(start_time="09:00", end_time="17:00")])

        self.time_rule_daily = AutoReply(
            id=3,
            organization_id=100,
            name="Daily Time Rule",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.TIME,
            priority=2,
            trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
            trigger_schedule_settings=daily_schedule,
            created_at=self.test_time,
            updated_at=self.test_time,
        )

        # Business hour rule
        business_schedule = WebhookTriggerScheduleSettings(schedules=[BusinessHourSchedule()])

        self.time_rule_business = AutoReply(
            id=4,
            organization_id=100,
            name="Business Hour Rule",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.TIME,
            priority=2,
            trigger_schedule_type=WebhookTriggerScheduleType.BUSINESS_HOUR,
            trigger_schedule_settings=business_schedule,
            created_at=self.test_time,
            updated_at=self.test_time,
        )

        # Inactive rule (should not trigger)
        self.inactive_rule = AutoReply(
            id=5,
            organization_id=100,
            name="Inactive Rule",
            status=AutoReplyStatus.INACTIVE,
            event_type=AutoReplyEventType.KEYWORD,
            priority=1,
            keywords=["inactive"],
            created_at=self.test_time,
            updated_at=self.test_time,
        )

    # PRD Test Cases: Story 1 - Keyword Reply Logic

    def test_b_p0_7_test2_exact_keyword_match_various_cases(self):
        """[B-P0-7-Test2]: Create a Keyword Reply for a LINE/FB/IG channel
        with a specific keyword and test triggering it with the exact keyword
        (various cases)."""

        test_cases = [
            ("hello", "hello"),  # exact match
            ("HELLO", "hello"),  # uppercase
            ("Hello", "hello"),  # mixed case
            ("hi", "hi"),  # different keyword
            ("HEY", "hey"),  # uppercase different keyword
        ]

        for input_text, expected_keyword in test_cases:
            event = MessageEvent(
                event_id="test_msg_1",
                channel_type=ChannelType.LINE,
                user_id="user_123",
                timestamp=self.test_time,
                content=input_text,
                message_id="msg_123",
            )

            result = validate_trigger(event, [self.keyword_rule_hello], self.test_time)

            assert result is not None
            assert result.trigger_type == TriggerType.KEYWORD
            assert result.matched_keyword == expected_keyword
            assert result.confidence_score == 1.0
            assert result.should_send_reply is True

    def test_b_p0_7_test3_keyword_with_leading_trailing_spaces(self):
        """[B-P0-7-Test3]: Test triggering with the keyword surrounded by
        leading/trailing spaces."""

        test_cases = ["  hello  ", "\thello\t", "\n hello \n", "   hi   ", " hey "]

        for input_text in test_cases:
            event = MessageEvent(
                event_id="test_msg_2",
                channel_type=ChannelType.FACEBOOK,
                user_id="user_456",
                timestamp=self.test_time,
                content=input_text,
                message_id="fb_msg_456",
            )

            result = validate_trigger(event, [self.keyword_rule_hello], self.test_time)

            assert result is not None
            assert result.trigger_type == TriggerType.KEYWORD
            assert result.matched_keyword in ["hello", "hi", "hey"]
            assert result.confidence_score == 1.0

    def test_b_p0_7_test4_keyword_with_other_text_no_match(self):
        """[B-P0-7-Test4]: Test triggering with a message that contains the
        keyword but also includes other text. Expected: NOT triggered."""

        test_cases = [
            "hello world",
            "say hello to everyone",
            "hi there how are you",
            "I need help with this",
            "please help me",
            "hey there friend",
        ]

        for input_text in test_cases:
            event = MessageEvent(
                event_id="test_msg_3",
                channel_type=ChannelType.INSTAGRAM,
                user_id="user_789",
                timestamp=self.test_time,
                content=input_text,
                message_id="ig_msg_789",
            )

            result = validate_trigger(event, [self.keyword_rule_hello], self.test_time)

            # Should not match due to exact match requirement
            assert result is None

    def test_b_p0_7_test5_partial_match_no_trigger(self):
        """[B-P0-7-Test5]: Test triggering with a message that is a partial
        match or close variation of the keyword. Expected: NOT triggered."""

        test_cases = [
            "hel",  # partial
            "hell",  # partial
            "helloo",  # variation
            "helo",  # typo
            "h",  # single char
            "helping",  # contains but not exact
            "helper",  # contains but not exact
        ]

        for input_text in test_cases:
            event = MessageEvent(
                event_id="test_msg_4",
                channel_type=ChannelType.LINE,
                user_id="user_000",
                timestamp=self.test_time,
                content=input_text,
                message_id="line_msg_000",
            )

            result = validate_trigger(event, [self.keyword_rule_hello], self.test_time)

            assert result is None

    # PRD Test Cases: Story 2 - Multiple Keywords Support

    def test_multiple_keywords_test1_multiple_keywords_trigger(self):
        """[Multiple-Keywords-Test1]: Create a Keyword Reply rule with
        multiple keywords and test triggering with each keyword."""

        keywords_to_test = ["hello", "hi", "hey"]

        for keyword in keywords_to_test:
            event = MessageEvent(
                event_id=f"test_msg_{keyword}",
                channel_type=ChannelType.LINE,
                user_id="user_multi",
                timestamp=self.test_time,
                content=keyword,
                message_id=f"msg_{keyword}",
            )

            result = validate_trigger(event, [self.keyword_rule_hello], self.test_time)

            assert result is not None
            assert result.trigger_type == TriggerType.KEYWORD
            assert result.matched_keyword == keyword
            assert result.confidence_score == 1.0

    def test_multiple_keywords_test2_case_insensitive_multiple(self):
        """[Multiple-Keywords-Test2]: Test triggering with a keyword that
        matches one of multiple keywords but with different casing."""

        test_cases = [("HELLO", "hello"), ("HI", "hi"), ("Hey", "hey"), ("hELLo", "hello")]

        for input_text, expected_keyword in test_cases:
            event = MessageEvent(
                event_id=f"test_case_{input_text}",
                channel_type=ChannelType.FACEBOOK,
                user_id="user_case",
                timestamp=self.test_time,
                content=input_text,
                message_id=f"fb_case_{input_text}",
            )

            result = validate_trigger(event, [self.keyword_rule_hello], self.test_time)

            assert result is not None
            assert result.matched_keyword == expected_keyword

    def test_multiple_keywords_test3_no_match_multiple(self):
        """[Multiple-Keywords-Test3]: Test triggering with a message that
        doesn't match any of the multiple keywords."""

        test_cases = ["goodbye", "farewell", "see you", "random text", "xyz123"]

        for input_text in test_cases:
            event = MessageEvent(
                event_id=f"test_no_match_{input_text}",
                channel_type=ChannelType.INSTAGRAM,
                user_id="user_no_match",
                timestamp=self.test_time,
                content=input_text,
                message_id=f"ig_no_match",
            )

            result = validate_trigger(event, [self.keyword_rule_hello], self.test_time)

            assert result is None

    # PRD Test Cases: Story 3 - General Time-based Logic

    def test_b_p0_6_test3_daily_schedule_within_time(self):
        """[B-P0-6-Test3]: Create a General Reply for a LINE/FB/IG channel
        with a Daily schedule and test triggering it during the defined time window."""

        # Test during business hours (rule is 9 AM to 5 PM)
        test_time_during = datetime(2025, 7, 16, 14, 30, 0)  # 2:30 PM

        event = MessageEvent(
            event_id="daily_test_1",
            channel_type=ChannelType.LINE,
            user_id="user_daily",
            timestamp=test_time_during,
            content="any message",
            message_id="daily_msg_1",
        )

        result = validate_trigger(event, [self.time_rule_daily], test_time_during)

        assert result is not None
        assert result.trigger_type == TriggerType.GENERAL_TIME
        assert result.matched_keyword is None
        assert result.confidence_score == 0.8

    def test_b_p0_6_test3_daily_schedule_outside_time(self):
        """Test Daily schedule outside the defined time window."""

        # Test outside business hours
        test_time_outside = datetime(2025, 7, 16, 20, 30, 0)  # 8:30 PM

        event = MessageEvent(
            event_id="daily_test_2",
            channel_type=ChannelType.FACEBOOK,
            user_id="user_daily_out",
            timestamp=test_time_outside,
            content="any message",
            message_id="daily_msg_2",
        )

        result = validate_trigger(event, [self.time_rule_daily], test_time_outside)

        assert result is None

    def test_b_p0_6_test5_business_hours_schedule(self):
        """[B-P0-6-Test5]: Create a General Reply for a LINE/FB/IG channel
        based on Business hours and test triggering it during/outside
        configured reply hours."""

        # Test during business hours (Mon-Fri, 9 AM-5 PM)
        business_time = datetime(2025, 7, 16, 11, 0, 0)  # Wednesday 11 AM

        event_during = MessageEvent(
            event_id="business_test_1",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user_business",
            timestamp=business_time,
            content="business hours message",
            message_id="business_msg_1",
        )

        result = validate_trigger(event_during, [self.time_rule_business], business_time)

        assert result is not None
        assert result.trigger_type == TriggerType.GENERAL_TIME

        # Test outside business hours (weekend)
        weekend_time = datetime(2025, 7, 19, 11, 0, 0)  # Saturday 11 AM

        event_outside = MessageEvent(
            event_id="business_test_2",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user_business_out",
            timestamp=weekend_time,
            content="weekend message",
            message_id="business_msg_2",
        )

        result = validate_trigger(event_outside, [self.time_rule_business], weekend_time)

        assert result is None

    # PRD Test Cases: Story 4 - Priority Logic

    def test_priority_test1_keyword_over_general_same_time(self):
        """[Priority-Test1]: Create both a Keyword Reply rule and a General
        Reply rule for the same channel. Send a message that matches the
        keyword during the general reply time window.
        Expected: Only the Keyword Reply is triggered."""

        # Time during both keyword and general time window
        test_time = datetime(2025, 7, 16, 14, 30, 0)  # Wednesday 2:30 PM

        event = MessageEvent(
            event_id="priority_test_1",
            channel_type=ChannelType.LINE,
            user_id="user_priority",
            timestamp=test_time,
            content="hello",  # Matches keyword
            message_id="priority_msg_1",
        )

        # Both rules should match individually, but keyword has priority
        result = validate_trigger(event, [self.keyword_rule_hello, self.time_rule_daily], test_time)

        assert result is not None
        assert result.trigger_type == TriggerType.KEYWORD
        assert result.matched_keyword == "hello"

    def test_priority_test2_general_only_no_keyword_match(self):
        """[Priority-Test2]: Create both a Keyword Reply rule and a General
        Reply rule for the same channel. Send a message that doesn't match
        the keyword during the general reply time window.
        Expected: Only the General Reply is triggered."""

        test_time = datetime(2025, 7, 16, 14, 30, 0)  # Wednesday 2:30 PM

        event = MessageEvent(
            event_id="priority_test_2",
            channel_type=ChannelType.FACEBOOK,
            user_id="user_priority_2",
            timestamp=test_time,
            content="random message",  # No keyword match
            message_id="priority_msg_2",
        )

        result = validate_trigger(event, [self.keyword_rule_hello, self.time_rule_daily], test_time)

        assert result is not None
        assert result.trigger_type == TriggerType.GENERAL_TIME
        assert result.matched_keyword is None

    def test_priority_test3_keyword_outside_general_time(self):
        """[Priority-Test3]: Create both a Keyword Reply rule and a General
        Reply rule for the same channel. Send a message that matches the
        keyword outside the general reply time window.
        Expected: Only the Keyword Reply is triggered."""

        # Outside general time window (after 5 PM)
        test_time = datetime(2025, 7, 16, 20, 30, 0)  # Wednesday 8:30 PM

        event = MessageEvent(
            event_id="priority_test_3",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user_priority_3",
            timestamp=test_time,
            content="hello",  # Matches keyword
            message_id="priority_msg_3",
        )

        result = validate_trigger(event, [self.keyword_rule_hello, self.time_rule_daily], test_time)

        assert result is not None
        assert result.trigger_type == TriggerType.KEYWORD
        assert result.matched_keyword == "hello"

    # PRD Test Cases: Story 5 - Message Content Handling

    def test_message_content_test1_keyword_match(self):
        """[Message-Content-Test1]: Create a Keyword Reply rule and test
        triggering with a message containing the keyword."""

        event = MessageEvent(
            event_id="content_test_1",
            channel_type=ChannelType.LINE,
            user_id="user_content",
            timestamp=self.test_time,
            content="help",  # Exact keyword match
            message_id="content_msg_1",
        )

        result = validate_trigger(event, [self.keyword_rule_help], self.test_time)

        assert result is not None
        assert result.trigger_type == TriggerType.KEYWORD
        assert result.matched_keyword == "help"

    def test_message_content_test2_no_keyword_match(self):
        """[Message-Content-Test2]: Test sending a message without any
        keyword to a channel with keyword rules.
        Expected: No keyword reply is triggered."""

        event = MessageEvent(
            event_id="content_test_2",
            channel_type=ChannelType.FACEBOOK,
            user_id="user_content_2",
            timestamp=self.test_time,
            content="random message with no keywords",
            message_id="content_msg_2",
        )

        result = validate_trigger(event, [self.keyword_rule_help], self.test_time)

        assert result is None

    def test_message_content_test3_general_any_content(self):
        """[Message-Content-Test3]: Create a General Reply rule and test
        triggering with any message content during scheduled time.
        Expected: The general reply is triggered regardless of message content."""

        test_messages = ["any random text", "1234567890", "special chars: !@#$%^&*()", "mixed content 123 abc"]

        # Time during business hours
        test_time = datetime(2025, 7, 16, 14, 30, 0)  # Wednesday 2:30 PM

        for i, content in enumerate(test_messages):
            event = MessageEvent(
                event_id=f"content_test_3_{i}",
                channel_type=ChannelType.INSTAGRAM,
                user_id=f"user_content_3_{i}",
                timestamp=test_time,
                content=content,
                message_id=f"content_msg_3_{i}",
            )

            result = validate_trigger(event, [self.time_rule_daily], test_time)

            assert result is not None
            assert result.trigger_type == TriggerType.GENERAL_TIME
            assert result.matched_keyword is None

    # Additional edge case tests

    def test_inactive_rule_not_triggered(self):
        """Test that inactive rules are not triggered."""

        event = MessageEvent(
            event_id="inactive_test",
            channel_type=ChannelType.LINE,
            user_id="user_inactive",
            timestamp=self.test_time,
            content="inactive",  # Would match if rule was active
            message_id="inactive_msg",
        )

        result = validate_trigger(event, [self.inactive_rule], self.test_time)

        assert result is None

    def test_empty_rules_list(self):
        """Test with empty rules list."""

        event = MessageEvent(
            event_id="empty_test",
            channel_type=ChannelType.LINE,
            user_id="user_empty",
            timestamp=self.test_time,
            content="any message",
            message_id="empty_msg",
        )

        result = validate_trigger(event, [], self.test_time)
        assert result is None

    def test_unsupported_event_type(self):
        """Test with unsupported event type."""

        # This would be a future event type like PostbackEvent
        class UnsupportedEvent:
            def __init__(self):
                self.event_id = "unsupported"
                self.channel_type = ChannelType.LINE
                self.user_id = "user_unsupported"
                self.timestamp = datetime.now()

        with pytest.raises(ValueError, match="Unsupported event type"):
            validate_trigger(UnsupportedEvent(), [self.keyword_rule_hello], self.test_time)

    def test_multiple_platform_support(self):
        """Test that all platforms (LINE/FB/IG) are supported."""

        platforms = [ChannelType.LINE, ChannelType.FACEBOOK, ChannelType.INSTAGRAM]

        for platform in platforms:
            event = MessageEvent(
                event_id=f"platform_test_{platform}",
                channel_type=platform,
                user_id=f"user_{platform}",
                timestamp=self.test_time,
                content="hello",
                message_id=f"msg_{platform}",
            )

            result = validate_trigger(event, [self.keyword_rule_hello], self.test_time)

            assert result is not None
            assert result.trigger_type == TriggerType.KEYWORD
            assert result.matched_keyword == "hello"


class TestIGStoryAutoReply:
    """Test cases for Feature 2: IG Story-Specific Auto-Reply based on PRD Part 2."""

    def setup_method(self):
        """Set up test data for each test method."""
        self.test_time = datetime(2025, 7, 16, 14, 30, 0)  # Wednesday 2:30 PM

        # IG Story Keyword Rule for story123
        self.ig_story_keyword_rule = AutoReply(
            id=10,
            organization_id=100,
            name="IG Story Greeting Rule",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.IG_STORY_KEYWORD,
            priority=1,
            keywords=["hello", "hi", "hey"],
            ig_story_ids=["story123"],
            created_at=self.test_time,
            updated_at=self.test_time,
        )

        # IG Story General Rule for story123 (9 AM to 5 PM)
        daily_schedule = WebhookTriggerScheduleSettings(schedules=[DailySchedule(start_time="09:00", end_time="17:00")])

        self.ig_story_general_rule = AutoReply(
            id=11,
            organization_id=100,
            name="IG Story Daily Time Rule",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.IG_STORY_TIME,
            priority=2,
            trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
            trigger_schedule_settings=daily_schedule,
            ig_story_ids=["story123"],
            created_at=self.test_time,
            updated_at=self.test_time,
        )

        # General Keyword Rule (for comparison)
        self.general_keyword_rule = AutoReply(
            id=12,
            organization_id=100,
            name="General Greeting Rule",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD,
            priority=3,
            keywords=["hello", "hi"],
            created_at=self.test_time,
            updated_at=self.test_time,
        )

        # General Time Rule (for comparison)
        self.general_time_rule = AutoReply(
            id=13,
            organization_id=100,
            name="General Daily Time Rule",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.TIME,
            priority=4,
            trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
            trigger_schedule_settings=daily_schedule,
            created_at=self.test_time,
            updated_at=self.test_time,
        )

    # PRD Test Cases: Story 6 - IG Story Keyword Logic

    def test_b_p1_18_test7_ig_story_keyword_wrong_story_no_match(self):
        """[B-P1-18-Test7]: Create a specific IG Story Keyword Reply rule.
        Test sending a message that matches the keyword but is NOT a reply to
        one of the selected stories."""

        event = MessageEvent(
            event_id="ig_story_test_1",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user_ig_story",
            timestamp=self.test_time,
            content="hello",  # Matches keyword
            message_id="ig_msg_1",
            ig_story_id="story456",  # Wrong story ID
        )

        result = validate_trigger(
            event,
            [self.ig_story_keyword_rule],
            self.test_time,
        )

        # Should NOT match because story ID doesn't match
        assert result is None

    def test_b_p1_18_test8a_ig_story_keyword_correct_story_match(self):
        """[B-P1-18-Test8a]: Create a specific IG Story Keyword Reply rule.
        Test sending a message that is a reply to one of the selected stories
        and matches the keyword."""

        event = MessageEvent(
            event_id="ig_story_test_2",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user_ig_story",
            timestamp=self.test_time,
            content="hello",  # Matches keyword
            message_id="ig_msg_2",
            ig_story_id="story123",  # Correct story ID
        )

        result = validate_trigger(
            event,
            [self.ig_story_keyword_rule],
            self.test_time,
        )

        # Should match IG Story keyword trigger
        assert result is not None
        assert result.trigger_type == TriggerType.IG_STORY_KEYWORD
        assert result.matched_keyword == "hello"
        assert result.confidence_score == 1.0
        assert "Thanks for replying to our story" in result.reply_content

    def test_ig_story_keyword_test1_correct_story_and_keyword(self):
        """[IG-Story-Keyword-Test1]: Create an IG Story Keyword Reply rule for
        story "story123" with keyword "hello". Send a message with keyword "hello"
        and ig_story_id "story123"."""

        event = MessageEvent(
            event_id="ig_story_keyword_1",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user_ig_keyword",
            timestamp=self.test_time,
            content="hello",
            message_id="ig_keyword_msg_1",
            ig_story_id="story123",
        )

        result = validate_trigger(
            event,
            [self.ig_story_keyword_rule],
            self.test_time,
        )

        assert result is not None
        assert result.trigger_type == TriggerType.IG_STORY_KEYWORD
        assert result.matched_keyword == "hello"

    def test_ig_story_keyword_test2_wrong_story_id(self):
        """[IG-Story-Keyword-Test2]: Create an IG Story Keyword Reply rule for
        story "story123" with keyword "hello". Send a message with keyword "hello"
        and ig_story_id "story456"."""

        event = MessageEvent(
            event_id="ig_story_keyword_2",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user_ig_keyword",
            timestamp=self.test_time,
            content="hello",
            message_id="ig_keyword_msg_2",
            ig_story_id="story456",  # Wrong story
        )

        result = validate_trigger(
            event,
            [self.ig_story_keyword_rule],
            self.test_time,
        )

        assert result is None

    def test_ig_story_keyword_test3_no_story_id(self):
        """[IG-Story-Keyword-Test3]: Create an IG Story Keyword Reply rule for
        story "story123" with keyword "hello". Send a message with keyword "hello"
        but no ig_story_id."""

        event = MessageEvent(
            event_id="ig_story_keyword_3",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user_ig_keyword",
            timestamp=self.test_time,
            content="hello",
            message_id="ig_keyword_msg_3",
            ig_story_id=None,  # No story context
        )

        result = validate_trigger(
            event,
            [self.ig_story_keyword_rule],
            self.test_time,
        )

        assert result is None

    # PRD Test Cases: Story 7 - IG Story General Logic

    def test_b_p1_18_test8b_ig_story_general_within_schedule(self):
        """[B-P1-18-Test8b]: Create a specific IG Story General Reply rule.
        Test sending a message that is a reply to one of the selected stories
        and is within the schedule."""

        event = MessageEvent(
            event_id="ig_story_general_1",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user_ig_general",
            timestamp=self.test_time,  # 2:30 PM, within 9-17 schedule
            content="any message",
            message_id="ig_general_msg_1",
            ig_story_id="story123",  # Correct story
        )

        result = validate_trigger(
            event,
            [self.ig_story_general_rule],
            self.test_time,
        )

        assert result is not None
        assert result.trigger_type == TriggerType.IG_STORY_GENERAL
        assert result.matched_keyword is None
        assert result.confidence_score == 0.8
        assert "Thanks for engaging with our story" in result.reply_content

    def test_ig_story_general_test1_correct_story_and_time(self):
        """[IG-Story-General-Test1]: Create an IG Story General Reply rule for
        story "story123" with daily 9-17 schedule. Send a message at 14:00
        with ig_story_id "story123"."""

        test_time_14 = datetime(2025, 7, 16, 14, 0, 0)  # 2:00 PM

        event = MessageEvent(
            event_id="ig_story_general_test_1",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user_general_test",
            timestamp=test_time_14,
            content="any message",
            message_id="ig_general_test_msg_1",
            ig_story_id="story123",
        )

        result = validate_trigger(
            event,
            [self.ig_story_general_rule],
            test_time_14,
        )

        assert result is not None
        assert result.trigger_type == TriggerType.IG_STORY_GENERAL

    def test_ig_story_general_test2_outside_schedule(self):
        """[IG-Story-General-Test2]: Create an IG Story General Reply rule for
        story "story123" with daily 9-17 schedule. Send a message at 20:00
        with ig_story_id "story123"."""

        test_time_20 = datetime(2025, 7, 16, 20, 0, 0)  # 8:00 PM, outside schedule

        event = MessageEvent(
            event_id="ig_story_general_test_2",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user_general_test",
            timestamp=test_time_20,
            content="any message",
            message_id="ig_general_test_msg_2",
            ig_story_id="story123",
        )

        result = validate_trigger(
            event,
            [self.ig_story_general_rule],
            test_time_20,
        )

        assert result is None

    def test_ig_story_general_test3_wrong_story_id(self):
        """[IG-Story-General-Test3]: Create an IG Story General Reply rule for
        story "story123" with daily 9-17 schedule. Send a message at 14:00
        with ig_story_id "story456"."""

        test_time_14 = datetime(2025, 7, 16, 14, 0, 0)  # 2:00 PM

        event = MessageEvent(
            event_id="ig_story_general_test_3",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user_general_test",
            timestamp=test_time_14,
            content="any message",
            message_id="ig_general_test_msg_3",
            ig_story_id="story456",  # Wrong story
        )

        result = validate_trigger(
            event,
            [self.ig_story_general_rule],
            test_time_14,
        )

        assert result is None

    # PRD Test Cases: Story 8 - IG Story Priority over General

    def test_b_p1_18_test9_story_keyword_over_general_keyword(self):
        """[B-P1-18-Test9]: Create both a story-specific keyword rule and a
        general keyword rule. Test sending a message that matches both rules
        (story reply + keyword)."""

        event = MessageEvent(
            event_id="priority_test_story_keyword",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user_priority",
            timestamp=self.test_time,
            content="hello",  # Matches both rules
            message_id="priority_msg_1",
            ig_story_id="story123",  # Matches IG story rule
        )

        result = validate_trigger(
            event,
            [self.ig_story_keyword_rule, self.general_keyword_rule],
            self.test_time,
        )

        # Should only trigger IG Story keyword (priority 1), not general keyword (priority 3)
        assert result is not None
        assert result.trigger_type == TriggerType.IG_STORY_KEYWORD
        assert result.matched_keyword == "hello"
        assert "Thanks for replying to our story" in result.reply_content

    def test_ig_story_priority_test1_ig_story_keyword_over_general_keyword(self):
        """[IG-Story-Priority-Test1]: Create both an IG story keyword rule and
        a general keyword rule for the same keyword. Send a message with the
        keyword and matching story ID."""

        event = MessageEvent(
            event_id="ig_priority_1",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user_priority_1",
            timestamp=self.test_time,
            content="hello",
            message_id="ig_priority_msg_1",
            ig_story_id="story123",
        )

        result = validate_trigger(
            event,
            [self.ig_story_keyword_rule, self.general_keyword_rule],
            self.test_time,
        )

        assert result is not None
        assert result.trigger_type == TriggerType.IG_STORY_KEYWORD
        assert result.matched_keyword == "hello"

    def test_ig_story_priority_test2_ig_story_general_over_general_time(self):
        """[IG-Story-Priority-Test2]: Create both an IG story general rule and
        a general time-based rule for the same schedule. Send a message during
        scheduled time with matching story ID."""

        event = MessageEvent(
            event_id="ig_priority_2",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user_priority_2",
            timestamp=self.test_time,  # Within schedule
            content="any message",
            message_id="ig_priority_msg_2",
            ig_story_id="story123",  # Matches IG story rule
        )

        result = validate_trigger(
            event,
            [self.ig_story_general_rule, self.general_time_rule],
            self.test_time,
        )

        # Should only trigger IG Story general (priority 2), not general time (priority 4)
        assert result is not None
        assert result.trigger_type == TriggerType.IG_STORY_GENERAL
        assert result.matched_keyword is None

    # PRD Test Cases: Story 9 - IG Story Multiple Keywords

    def test_ig_story_multiple_keywords_test1_all_keywords_trigger(self):
        """[IG-Story-Multiple-Keywords-Test1]: Create an IG Story Keyword Reply rule
        with multiple keywords (e.g., ["hello", "hi"]) for story "story123".
        Test triggering with each keyword and the correct story ID."""

        keywords_to_test = ["hello", "hi", "hey"]

        for keyword in keywords_to_test:
            event = MessageEvent(
                event_id=f"ig_multi_keyword_{keyword}",
                channel_type=ChannelType.INSTAGRAM,
                user_id="user_multi_keyword",
                timestamp=self.test_time,
                content=keyword,
                message_id=f"ig_multi_msg_{keyword}",
                ig_story_id="story123",
            )

            result = validate_trigger(
                event,
                [self.ig_story_keyword_rule],
                self.test_time,
            )

            assert result is not None
            assert result.trigger_type == TriggerType.IG_STORY_KEYWORD
            assert result.matched_keyword == keyword

    def test_ig_story_multiple_keywords_test2_wrong_story_no_trigger(self):
        """[IG-Story-Multiple-Keywords-Test2]: Create an IG Story Keyword Reply rule
        with multiple keywords for story "story123". Test triggering with one of
        the keywords but wrong story ID."""

        event = MessageEvent(
            event_id="ig_multi_keyword_wrong_story",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user_multi_keyword",
            timestamp=self.test_time,
            content="hello",  # Valid keyword
            message_id="ig_multi_msg_wrong",
            ig_story_id="story456",  # Wrong story
        )

        result = validate_trigger(
            event,
            [self.ig_story_keyword_rule],
            self.test_time,
        )

        assert result is None

    # PRD Test Cases: Story 10 - Complete Priority System

    def test_complete_priority_test1_all_rules_ig_story_keyword_wins(self):
        """[Complete-Priority-Test1]: Create all 4 types of rules (IG story keyword,
        IG story general, general keyword, general time-based). Send a message that
        could match all rules."""

        event = MessageEvent(
            event_id="complete_priority_1",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user_complete_1",
            timestamp=self.test_time,  # Within schedule for time rules
            content="hello",  # Matches keyword rules
            message_id="complete_msg_1",
            ig_story_id="story123",  # Matches IG story rules
        )

        all_rules = [
            self.ig_story_keyword_rule,  # Priority 1
            self.ig_story_general_rule,  # Priority 2
            self.general_keyword_rule,  # Priority 3
            self.general_time_rule,  # Priority 4
        ]

        result = validate_trigger(event, all_rules, self.test_time)

        # Should only trigger IG Story keyword (highest priority)
        assert result is not None
        assert result.trigger_type == TriggerType.IG_STORY_KEYWORD
        assert result.matched_keyword == "hello"

    def test_complete_priority_test2_ig_story_general_wins(self):
        """[Complete-Priority-Test2]: Create IG story general, general keyword,
        and general time-based rules. Send a message during scheduled time with
        story ID but non-matching keyword."""

        event = MessageEvent(
            event_id="complete_priority_2",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user_complete_2",
            timestamp=self.test_time,  # Within schedule
            content="random message",  # Non-matching keyword
            message_id="complete_msg_2",
            ig_story_id="story123",  # Matches IG story rule
        )

        rules = [
            self.ig_story_general_rule,  # Priority 2
            self.general_keyword_rule,  # Priority 3
            self.general_time_rule,  # Priority 4
        ]

        result = validate_trigger(event, rules, self.test_time)

        # Should only trigger IG Story general (priority 2)
        assert result is not None
        assert result.trigger_type == TriggerType.IG_STORY_GENERAL
        assert result.matched_keyword is None

    def test_complete_priority_test3_general_keyword_wins(self):
        """[Complete-Priority-Test3]: Create general keyword and general time-based
        rules. Send a message with matching keyword during scheduled time but no story ID."""

        event = MessageEvent(
            event_id="complete_priority_3",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user_complete_3",
            timestamp=self.test_time,  # Within schedule
            content="hello",  # Matching keyword
            message_id="complete_msg_3",
            ig_story_id=None,  # No story context
        )

        rules = [self.general_keyword_rule, self.general_time_rule]  # Priority 3  # Priority 4

        result = validate_trigger(event, rules, self.test_time)

        # Should only trigger general keyword (priority 3)
        assert result is not None
        assert result.trigger_type == TriggerType.KEYWORD
        assert result.matched_keyword == "hello"

    def test_complete_priority_test4_general_time_wins(self):
        """[Complete-Priority-Test4]: Create only general time-based rule.
        Send a message during scheduled time with no keyword and no story ID."""

        event = MessageEvent(
            event_id="complete_priority_4",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user_complete_4",
            timestamp=self.test_time,  # Within schedule
            content="random message",  # No matching keyword
            message_id="complete_msg_4",
            ig_story_id=None,  # No story context
        )

        result = validate_trigger(
            event,
            [self.general_time_rule],  # Priority 4
            self.test_time,
        )

        # Should only trigger general time-based (priority 4)
        assert result is not None
        assert result.trigger_type == TriggerType.GENERAL_TIME
        assert result.matched_keyword is None

    # PRD Test Cases: Story 11 - IG Story Exclusion Logic

    def test_ig_story_exclusion_test1_ig_story_rule_no_trigger_without_story(self):
        """[IG-Story-Exclusion-Test1]: Create an IG story-specific keyword setting
        with keyword "hello". Send a normal message with keyword "hello" (no IG story ID)."""

        event = MessageEvent(
            event_id="ig_exclusion_1",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user_exclusion_1",
            timestamp=self.test_time,
            content="hello",  # Matches keyword
            message_id="ig_exclusion_msg_1",
            ig_story_id=None,  # No story context
        )

        result = validate_trigger(
            event,
            [self.ig_story_keyword_rule],  # IG Story-specific rule
            self.test_time,
        )

        # Should NOT trigger because rule is IG story-specific but no story ID provided
        assert result is None

    def test_ig_story_exclusion_test2_general_rule_triggers_without_story(self):
        """[IG-Story-Exclusion-Test2]: Create a normal keyword setting without
        IG story configuration. Send a normal message with matching keyword."""

        event = MessageEvent(
            event_id="ig_exclusion_2",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user_exclusion_2",
            timestamp=self.test_time,
            content="hello",
            message_id="ig_exclusion_msg_2",
            ig_story_id=None,  # No story context
        )

        result = validate_trigger(
            event,
            [self.general_keyword_rule],  # General rule (not IG story-specific)
            self.test_time,
        )

        # Should trigger because rule is general (not IG story-specific)
        assert result is not None
        assert result.trigger_type == TriggerType.KEYWORD
        assert result.matched_keyword == "hello"

    def test_ig_story_exclusion_test3_general_rule_wins_without_story(self):
        """[IG-Story-Exclusion-Test3]: Create both IG story-specific and general
        keyword settings for the same keyword. Send a message with keyword but no story ID."""

        event = MessageEvent(
            event_id="ig_exclusion_3",
            channel_type=ChannelType.INSTAGRAM,
            user_id="user_exclusion_3",
            timestamp=self.test_time,
            content="hello",
            message_id="ig_exclusion_msg_3",
            ig_story_id=None,  # No story context
        )

        result = validate_trigger(
            event,
            [self.ig_story_keyword_rule, self.general_keyword_rule],
            self.test_time,
        )

        # Should only trigger general keyword rule, not IG story-specific one
        assert result is not None
        assert result.trigger_type == TriggerType.KEYWORD
        assert result.matched_keyword == "hello"
        # Should use general response, not IG story response
        assert "Thanks for replying to our story" not in result.reply_content

    # Additional helper tests

    def test_ig_story_specific_method(self):
        """Test the is_ig_story_specific() method works correctly."""

        # IG Story rule should be story-specific
        assert self.ig_story_keyword_rule.is_ig_story_specific() is True
        assert self.ig_story_general_rule.is_ig_story_specific() is True

        # General rules should not be story-specific
        assert self.general_keyword_rule.is_ig_story_specific() is False
        assert self.general_time_rule.is_ig_story_specific() is False

    def test_multiple_story_ids_support(self):
        """Test that a rule can support multiple story IDs."""

        # Create rule with multiple story IDs
        multi_story_rule = AutoReply(
            id=20,
            organization_id=100,
            name="Multi Story Rule",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.IG_STORY_KEYWORD,
            priority=1,
            keywords=["hello"],
            ig_story_ids=["story123", "story456", "story789"],
            created_at=self.test_time,
            updated_at=self.test_time,
        )

        # Test with each story ID
        for story_id in ["story123", "story456", "story789"]:
            event = MessageEvent(
                event_id=f"multi_story_{story_id}",
                channel_type=ChannelType.INSTAGRAM,
                user_id="user_multi_story",
                timestamp=self.test_time,
                content="hello",
                message_id=f"multi_msg_{story_id}",
                ig_story_id=story_id,
            )

            result = validate_trigger(event, [multi_story_rule], self.test_time)

            assert result is not None
            assert result.trigger_type == TriggerType.IG_STORY_KEYWORD
            assert result.matched_keyword == "hello"
