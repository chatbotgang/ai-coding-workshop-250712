"""Test IG Story specific auto-reply features per PRD Part 2."""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from internal.domain.auto_reply.auto_reply import AutoReply, AutoReplyEventType, AutoReplyStatus
from internal.domain.auto_reply.validate_trigger import validate_trigger
from internal.domain.auto_reply.webhook_trigger import (
    DailySchedule,
    WebhookTriggerEventType,
    WebhookTriggerScheduleSettings,
    WebhookTriggerSetting,
)


class TestIGStoryKeywordLogic:
    """Test cases for Story 6: IG Story Keyword Logic."""

    def test_ig_story_keyword_trigger_with_matching_story_and_keyword(self):
        """[IG-Story-Keyword-Test1]: Create an IG Story Keyword Reply rule for story "story123" with keyword "hello".
        Send a message with keyword "hello" and ig_story_id "story123".
        Expected Result: The IG story keyword reply is triggered.
        """
        # Arrange: Create IG Story keyword trigger
        auto_reply = AutoReply(
            id=1,
            organization_id=1,
            name="IG Story Keyword Reply",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD,
            priority=1,
            keywords=["hello"],
            ig_story_ids=["story123"],
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        trigger_setting = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="IG Story Keyword Trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        # Act: Send message with matching keyword and story ID
        result = validate_trigger(
            trigger_settings=[trigger_setting],
            auto_replies={1: auto_reply},
            message_content="hello",
            event_time=datetime.now(ZoneInfo("UTC")),
            ig_story_id="story123",
        )

        # Assert: IG story keyword reply is triggered
        assert result is not None
        assert result.auto_reply_id == 1

    def test_ig_story_keyword_trigger_with_wrong_story_id(self):
        """[IG-Story-Keyword-Test2]: Create an IG Story Keyword Reply rule for story "story123" with keyword "hello".
        Send a message with keyword "hello" and ig_story_id "story456".
        Expected Result: The IG story keyword reply is NOT triggered (wrong story).
        """
        # Arrange: Create IG Story keyword trigger for story123
        auto_reply = AutoReply(
            id=1,
            organization_id=1,
            name="IG Story Keyword Reply",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD,
            priority=1,
            keywords=["hello"],
            ig_story_ids=["story123"],
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        trigger_setting = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="IG Story Keyword Trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        # Act: Send message with matching keyword but wrong story ID
        result = validate_trigger(
            trigger_settings=[trigger_setting],
            auto_replies={1: auto_reply},
            message_content="hello",
            event_time=datetime.now(ZoneInfo("UTC")),
            ig_story_id="story456",  # Wrong story ID
        )

        # Assert: IG story keyword reply is NOT triggered
        assert result is None

    def test_ig_story_keyword_trigger_without_story_context(self):
        """[IG-Story-Keyword-Test3]: Create an IG Story Keyword Reply rule for story "story123" with keyword "hello".
        Send a message with keyword "hello" but no ig_story_id.
        Expected Result: The IG story keyword reply is NOT triggered (no story context).
        """
        # Arrange: Create IG Story keyword trigger
        auto_reply = AutoReply(
            id=1,
            organization_id=1,
            name="IG Story Keyword Reply",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD,
            priority=1,
            keywords=["hello"],
            ig_story_ids=["story123"],
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        trigger_setting = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="IG Story Keyword Trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        # Act: Send message with matching keyword but no story context
        result = validate_trigger(
            trigger_settings=[trigger_setting],
            auto_replies={1: auto_reply},
            message_content="hello",
            event_time=datetime.now(ZoneInfo("UTC")),
            ig_story_id=None,  # No story context
        )

        # Assert: IG story keyword reply is NOT triggered
        assert result is None

    def test_b_p1_18_test7_keyword_message_not_story_reply(self):
        """[B-P1-18-Test7]: Create a specific IG Story Keyword Reply rule.
        Test sending a message that matches the keyword but is NOT a reply to one of the selected stories.
        Expected Result: The auto-reply is NOT triggered.
        """
        # Arrange: Create IG Story keyword trigger for specific story
        auto_reply = AutoReply(
            id=1,
            organization_id=1,
            name="IG Story Keyword Reply",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD,
            priority=1,
            keywords=["offer"],
            ig_story_ids=["story_offer_123"],
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        trigger_setting = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="IG Story Keyword Trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        # Act: Send message with matching keyword but wrong story
        result = validate_trigger(
            trigger_settings=[trigger_setting],
            auto_replies={1: auto_reply},
            message_content="offer",
            event_time=datetime.now(ZoneInfo("UTC")),
            ig_story_id="different_story_456",  # Not the selected story
        )

        # Assert: Auto-reply is NOT triggered
        assert result is None

    def test_b_p1_18_test8a_keyword_message_is_story_reply(self):
        """[B-P1-18-Test8a]: Create a specific IG Story Keyword Reply rule.
        Test sending a message that is a reply to one of the selected stories and matches the keyword.
        Expected Result: The auto-reply IS triggered.
        """
        # Arrange: Create IG Story keyword trigger
        auto_reply = AutoReply(
            id=1,
            organization_id=1,
            name="IG Story Keyword Reply",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD,
            priority=1,
            keywords=["discount"],
            ig_story_ids=["story_discount_789"],
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        trigger_setting = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="IG Story Keyword Trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        # Act: Send message that is reply to selected story with matching keyword
        result = validate_trigger(
            trigger_settings=[trigger_setting],
            auto_replies={1: auto_reply},
            message_content="discount",
            event_time=datetime.now(ZoneInfo("UTC")),
            ig_story_id="story_discount_789",  # Selected story
        )

        # Assert: Auto-reply IS triggered
        assert result is not None
        assert result.auto_reply_id == 1


class TestIGStoryGeneralLogic:
    """Test cases for Story 7: IG Story General Logic."""

    def test_ig_story_general_trigger_with_matching_story_and_schedule(self):
        """[IG-Story-General-Test1]: Create an IG Story General Reply rule for story "story123" with daily 9-17 schedule.
        Send a message at 14:00 with ig_story_id "story123".
        Expected Result: The IG story general reply is triggered.
        """
        # Arrange: Create IG Story general trigger with schedule
        schedule_settings = WebhookTriggerScheduleSettings(
            schedules=[DailySchedule(start_time="09:00", end_time="17:00")]
        )

        auto_reply = AutoReply(
            id=1,
            organization_id=1,
            name="IG Story General Reply",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.TIME,
            priority=1,
            trigger_schedule_settings=schedule_settings,
            ig_story_ids=["story123"],
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        trigger_setting = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="IG Story General Trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        # Act: Send message at 14:00 with matching story ID
        event_time = datetime(2024, 1, 15, 14, 0, 0, tzinfo=ZoneInfo("Asia/Taipei"))
        result = validate_trigger(
            trigger_settings=[trigger_setting],
            auto_replies={1: auto_reply},
            message_content="any message",
            event_time=event_time,
            organization_timezone="Asia/Taipei",
            ig_story_id="story123",
        )

        # Assert: IG story general reply is triggered
        assert result is not None
        assert result.auto_reply_id == 1

    def test_ig_story_general_trigger_outside_schedule(self):
        """[IG-Story-General-Test2]: Create an IG Story General Reply rule for story "story123" with daily 9-17 schedule.
        Send a message at 20:00 with ig_story_id "story123".
        Expected Result: The IG story general reply is NOT triggered (outside schedule).
        """
        # Arrange: Create IG Story general trigger with schedule
        schedule_settings = WebhookTriggerScheduleSettings(
            schedules=[DailySchedule(start_time="09:00", end_time="17:00")]
        )

        auto_reply = AutoReply(
            id=1,
            organization_id=1,
            name="IG Story General Reply",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.TIME,
            priority=1,
            trigger_schedule_settings=schedule_settings,
            ig_story_ids=["story123"],
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        trigger_setting = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="IG Story General Trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        # Act: Send message at 20:00 (outside schedule) with matching story ID
        event_time = datetime(2024, 1, 15, 20, 0, 0, tzinfo=ZoneInfo("Asia/Taipei"))
        result = validate_trigger(
            trigger_settings=[trigger_setting],
            auto_replies={1: auto_reply},
            message_content="any message",
            event_time=event_time,
            organization_timezone="Asia/Taipei",
            ig_story_id="story123",
        )

        # Assert: IG story general reply is NOT triggered
        assert result is None

    def test_ig_story_general_trigger_with_wrong_story_id(self):
        """[IG-Story-General-Test3]: Create an IG Story General Reply rule for story "story123" with daily 9-17 schedule.
        Send a message at 14:00 with ig_story_id "story456".
        Expected Result: The IG story general reply is NOT triggered (wrong story).
        """
        # Arrange: Create IG Story general trigger
        schedule_settings = WebhookTriggerScheduleSettings(
            schedules=[DailySchedule(start_time="09:00", end_time="17:00")]
        )

        auto_reply = AutoReply(
            id=1,
            organization_id=1,
            name="IG Story General Reply",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.TIME,
            priority=1,
            trigger_schedule_settings=schedule_settings,
            ig_story_ids=["story123"],
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        trigger_setting = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="IG Story General Trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        # Act: Send message at 14:00 with wrong story ID
        event_time = datetime(2024, 1, 15, 14, 0, 0, tzinfo=ZoneInfo("Asia/Taipei"))
        result = validate_trigger(
            trigger_settings=[trigger_setting],
            auto_replies={1: auto_reply},
            message_content="any message",
            event_time=event_time,
            organization_timezone="Asia/Taipei",
            ig_story_id="story456",  # Wrong story ID
        )

        # Assert: IG story general reply is NOT triggered
        assert result is None

    def test_b_p1_18_test8b_general_message_is_story_reply_in_schedule(self):
        """[B-P1-18-Test8b]: Create a specific IG Story General Reply rule.
        Test sending a message that is a reply to one of the selected stories and is within the schedule.
        Expected Result: The auto-reply IS triggered.
        """
        # Arrange: Create IG Story general trigger
        schedule_settings = WebhookTriggerScheduleSettings(
            schedules=[DailySchedule(start_time="08:00", end_time="18:00")]
        )

        auto_reply = AutoReply(
            id=1,
            organization_id=1,
            name="IG Story General Reply",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.TIME,
            priority=1,
            trigger_schedule_settings=schedule_settings,
            ig_story_ids=["story_promo_123"],
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        trigger_setting = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="IG Story General Trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        # Act: Send message that is reply to selected story within schedule
        event_time = datetime(2024, 1, 15, 12, 30, 0, tzinfo=ZoneInfo("Asia/Taipei"))
        result = validate_trigger(
            trigger_settings=[trigger_setting],
            auto_replies={1: auto_reply},
            message_content="interested",
            event_time=event_time,
            organization_timezone="Asia/Taipei",
            ig_story_id="story_promo_123",  # Selected story
        )

        # Assert: Auto-reply IS triggered
        assert result is not None
        assert result.auto_reply_id == 1


class TestIGStoryPriorityOverGeneral:
    """Test cases for Story 8: IG Story Priority over General."""

    def test_ig_story_keyword_priority_over_general_keyword(self):
        """[IG-Story-Priority-Test1]: Create both an IG story keyword rule and a general keyword rule for the same keyword.
        Send a message with the keyword and matching story ID.
        Expected Result: Only the IG story keyword reply is triggered, not the general keyword reply.
        """
        # Arrange: Create both IG story and general keyword triggers
        ig_story_auto_reply = AutoReply(
            id=1,
            organization_id=1,
            name="IG Story Keyword Reply",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD,
            priority=1,
            keywords=["help"],
            ig_story_ids=["story123"],
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        general_auto_reply = AutoReply(
            id=2,
            organization_id=1,
            name="General Keyword Reply",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD,
            priority=1,
            keywords=["help"],
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        ig_story_trigger = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="IG Story Keyword Trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        general_trigger = WebhookTriggerSetting(
            id=2,
            auto_reply_id=2,
            bot_id=1,
            enable=True,
            name="General Keyword Trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        # Act: Send message with keyword and story ID
        result = validate_trigger(
            trigger_settings=[ig_story_trigger, general_trigger],
            auto_replies={1: ig_story_auto_reply, 2: general_auto_reply},
            message_content="help",
            event_time=datetime.now(ZoneInfo("UTC")),
            ig_story_id="story123",
        )

        # Assert: Only IG story keyword reply is triggered
        assert result is not None
        assert result.auto_reply_id == 1  # IG story trigger, not general

    def test_ig_story_general_priority_over_general_time_based(self):
        """[IG-Story-Priority-Test2]: Create both an IG story general rule and a general time-based rule for the same schedule.
        Send a message during scheduled time with matching story ID.
        Expected Result: Only the IG story general reply is triggered, not the general time-based reply.
        """
        # Arrange: Create both IG story general and general time-based triggers
        schedule_settings = WebhookTriggerScheduleSettings(
            schedules=[DailySchedule(start_time="09:00", end_time="17:00")]
        )

        ig_story_auto_reply = AutoReply(
            id=1,
            organization_id=1,
            name="IG Story General Reply",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.TIME,
            priority=1,
            trigger_schedule_settings=schedule_settings,
            ig_story_ids=["story123"],
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        general_auto_reply = AutoReply(
            id=2,
            organization_id=1,
            name="General Time-based Reply",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.TIME,
            priority=1,
            trigger_schedule_settings=schedule_settings,
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        ig_story_trigger = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="IG Story General Trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        general_trigger = WebhookTriggerSetting(
            id=2,
            auto_reply_id=2,
            bot_id=1,
            enable=True,
            name="General Time-based Trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        # Act: Send message during scheduled time with story ID
        event_time = datetime(2024, 1, 15, 14, 0, 0, tzinfo=ZoneInfo("Asia/Taipei"))
        result = validate_trigger(
            trigger_settings=[ig_story_trigger, general_trigger],
            auto_replies={1: ig_story_auto_reply, 2: general_auto_reply},
            message_content="any message",
            event_time=event_time,
            organization_timezone="Asia/Taipei",
            ig_story_id="story123",
        )

        # Assert: Only IG story general reply is triggered
        assert result is not None
        assert result.auto_reply_id == 1  # IG story trigger, not general

    def test_b_p1_18_test9_story_specific_over_general_keyword(self):
        """[B-P1-18-Test9]: Create both a story-specific keyword rule and a general keyword rule.
        Test sending a message that matches both rules (story reply + keyword).
        Expected Result: Only the story-specific auto-reply is triggered.
        """
        # Arrange: Create both story-specific and general keyword triggers
        story_specific_auto_reply = AutoReply(
            id=1,
            organization_id=1,
            name="Story Specific Keyword Reply",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD,
            priority=1,
            keywords=["info"],
            ig_story_ids=["story_campaign_456"],
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        general_auto_reply = AutoReply(
            id=2,
            organization_id=1,
            name="General Keyword Reply",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD,
            priority=1,
            keywords=["info"],
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        story_trigger = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="Story Specific Keyword Trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        general_trigger = WebhookTriggerSetting(
            id=2,
            auto_reply_id=2,
            bot_id=1,
            enable=True,
            name="General Keyword Trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        # Act: Send message that matches both rules (story reply + keyword)
        result = validate_trigger(
            trigger_settings=[story_trigger, general_trigger],
            auto_replies={1: story_specific_auto_reply, 2: general_auto_reply},
            message_content="info",
            event_time=datetime.now(ZoneInfo("UTC")),
            ig_story_id="story_campaign_456",
        )

        # Assert: Only story-specific auto-reply is triggered
        assert result is not None
        assert result.auto_reply_id == 1  # Story specific trigger, not general


class TestIGStoryMultipleKeywords:
    """Test cases for Story 9: IG Story Multiple Keywords."""

    def test_ig_story_multiple_keywords_trigger_each_keyword(self):
        """[IG-Story-Multiple-Keywords-Test1]: Create an IG Story Keyword Reply rule with multiple keywords (e.g., ["hello", "hi"]) for story "story123".
        Test triggering with each keyword and the correct story ID.
        Expected Result: The IG story auto-reply is triggered for any of the configured keywords when sent as a reply to the specified story.
        """
        # Arrange: Create IG Story keyword trigger with multiple keywords
        auto_reply = AutoReply(
            id=1,
            organization_id=1,
            name="IG Story Multiple Keywords Reply",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD,
            priority=1,
            keywords=["hello", "hi"],
            ig_story_ids=["story123"],
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        trigger_setting = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="IG Story Multiple Keywords Trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        # Act & Assert: Test each keyword triggers the reply
        for keyword in ["hello", "hi"]:
            result = validate_trigger(
                trigger_settings=[trigger_setting],
                auto_replies={1: auto_reply},
                message_content=keyword,
                event_time=datetime.now(ZoneInfo("UTC")),
                ig_story_id="story123",
            )

            assert result is not None, f"Keyword '{keyword}' should trigger the reply"
            assert result.auto_reply_id == 1

    def test_ig_story_multiple_keywords_wrong_story_id(self):
        """[IG-Story-Multiple-Keywords-Test2]: Create an IG Story Keyword Reply rule with multiple keywords for story "story123".
        Test triggering with one of the keywords but wrong story ID.
        Expected Result: The IG story auto-reply is NOT triggered.
        """
        # Arrange: Create IG Story keyword trigger with multiple keywords
        auto_reply = AutoReply(
            id=1,
            organization_id=1,
            name="IG Story Multiple Keywords Reply",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD,
            priority=1,
            keywords=["hello", "hi"],
            ig_story_ids=["story123"],
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        trigger_setting = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="IG Story Multiple Keywords Trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        # Act: Test with valid keyword but wrong story ID
        result = validate_trigger(
            trigger_settings=[trigger_setting],
            auto_replies={1: auto_reply},
            message_content="hello",
            event_time=datetime.now(ZoneInfo("UTC")),
            ig_story_id="wrong_story_456",  # Wrong story ID
        )

        # Assert: IG story auto-reply is NOT triggered
        assert result is None


class TestCompletePrioritySystem:
    """Test cases for Story 10: Complete Priority System."""

    def test_complete_priority_test1_all_four_rules_ig_story_keyword_wins(self):
        """[Complete-Priority-Test1]: Create all 4 types of rules (IG story keyword, IG story general, general keyword, general time-based).
        Send a message that could match all rules.
        Expected Result: Only the IG story keyword reply is triggered (highest priority).
        """
        # Arrange: Create all 4 types of rules
        schedule_settings = WebhookTriggerScheduleSettings(
            schedules=[DailySchedule(start_time="09:00", end_time="17:00")]
        )

        # 1. IG Story Keyword (Priority 1 - highest)
        ig_story_keyword_auto_reply = AutoReply(
            id=1,
            organization_id=1,
            name="IG Story Keyword Reply",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD,
            priority=1,
            keywords=["sale"],
            ig_story_ids=["story123"],
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        # 2. IG Story General (Priority 2)
        ig_story_general_auto_reply = AutoReply(
            id=2,
            organization_id=1,
            name="IG Story General Reply",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.TIME,
            priority=1,
            trigger_schedule_settings=schedule_settings,
            ig_story_ids=["story123"],
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        # 3. General Keyword (Priority 3)
        general_keyword_auto_reply = AutoReply(
            id=3,
            organization_id=1,
            name="General Keyword Reply",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD,
            priority=1,
            keywords=["sale"],
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        # 4. General Time-based (Priority 4 - lowest)
        general_time_auto_reply = AutoReply(
            id=4,
            organization_id=1,
            name="General Time-based Reply",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.TIME,
            priority=1,
            trigger_schedule_settings=schedule_settings,
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        triggers = [
            WebhookTriggerSetting(
                id=i,
                auto_reply_id=i,
                bot_id=1,
                enable=True,
                name=f"Trigger {i}",
                event_type=WebhookTriggerEventType.MESSAGE,
                created_at=datetime.now(ZoneInfo("UTC")),
                updated_at=datetime.now(ZoneInfo("UTC")),
            )
            for i in range(1, 5)
        ]

        auto_replies = {
            1: ig_story_keyword_auto_reply,
            2: ig_story_general_auto_reply,
            3: general_keyword_auto_reply,
            4: general_time_auto_reply,
        }

        # Act: Send message that could match all rules
        event_time = datetime(2024, 1, 15, 14, 0, 0, tzinfo=ZoneInfo("Asia/Taipei"))
        result = validate_trigger(
            trigger_settings=triggers,
            auto_replies=auto_replies,
            message_content="sale",
            event_time=event_time,
            organization_timezone="Asia/Taipei",
            ig_story_id="story123",
        )

        # Assert: Only IG story keyword reply is triggered (highest priority)
        assert result is not None
        assert result.auto_reply_id == 1

    def test_complete_priority_test2_ig_story_general_wins(self):
        """[Complete-Priority-Test2]: Create IG story general, general keyword, and general time-based rules.
        Send a message during scheduled time with story ID but non-matching keyword.
        Expected Result: Only the IG story general reply is triggered (priority 2).
        """
        # Arrange: Create 3 types (no IG story keyword)
        schedule_settings = WebhookTriggerScheduleSettings(
            schedules=[DailySchedule(start_time="09:00", end_time="17:00")]
        )

        # 2. IG Story General (Priority 2)
        ig_story_general_auto_reply = AutoReply(
            id=2,
            organization_id=1,
            name="IG Story General Reply",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.TIME,
            priority=1,
            trigger_schedule_settings=schedule_settings,
            ig_story_ids=["story123"],
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        # 3. General Keyword (Priority 3)
        general_keyword_auto_reply = AutoReply(
            id=3,
            organization_id=1,
            name="General Keyword Reply",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD,
            priority=1,
            keywords=["discount"],  # Non-matching keyword
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        # 4. General Time-based (Priority 4)
        general_time_auto_reply = AutoReply(
            id=4,
            organization_id=1,
            name="General Time-based Reply",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.TIME,
            priority=1,
            trigger_schedule_settings=schedule_settings,
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        triggers = [
            WebhookTriggerSetting(
                id=i,
                auto_reply_id=i,
                bot_id=1,
                enable=True,
                name=f"Trigger {i}",
                event_type=WebhookTriggerEventType.MESSAGE,
                created_at=datetime.now(ZoneInfo("UTC")),
                updated_at=datetime.now(ZoneInfo("UTC")),
            )
            for i in [2, 3, 4]
        ]

        auto_replies = {2: ig_story_general_auto_reply, 3: general_keyword_auto_reply, 4: general_time_auto_reply}

        # Act: Send message with story ID, during schedule, non-matching keyword
        event_time = datetime(2024, 1, 15, 14, 0, 0, tzinfo=ZoneInfo("Asia/Taipei"))
        result = validate_trigger(
            trigger_settings=triggers,
            auto_replies=auto_replies,
            message_content="sale",  # Does not match "discount" keyword
            event_time=event_time,
            organization_timezone="Asia/Taipei",
            ig_story_id="story123",
        )

        # Assert: Only IG story general reply is triggered (priority 2)
        assert result is not None
        assert result.auto_reply_id == 2

    def test_complete_priority_test3_general_keyword_wins(self):
        """[Complete-Priority-Test3]: Create general keyword and general time-based rules.
        Send a message with matching keyword during scheduled time but no story ID.
        Expected Result: Only the general keyword reply is triggered (priority 3).
        """
        # Arrange: Create only general rules (no IG story rules)
        schedule_settings = WebhookTriggerScheduleSettings(
            schedules=[DailySchedule(start_time="09:00", end_time="17:00")]
        )

        # 3. General Keyword (Priority 3)
        general_keyword_auto_reply = AutoReply(
            id=3,
            organization_id=1,
            name="General Keyword Reply",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD,
            priority=1,
            keywords=["help"],
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        # 4. General Time-based (Priority 4)
        general_time_auto_reply = AutoReply(
            id=4,
            organization_id=1,
            name="General Time-based Reply",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.TIME,
            priority=1,
            trigger_schedule_settings=schedule_settings,
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        triggers = [
            WebhookTriggerSetting(
                id=i,
                auto_reply_id=i,
                bot_id=1,
                enable=True,
                name=f"Trigger {i}",
                event_type=WebhookTriggerEventType.MESSAGE,
                created_at=datetime.now(ZoneInfo("UTC")),
                updated_at=datetime.now(ZoneInfo("UTC")),
            )
            for i in [3, 4]
        ]

        auto_replies = {3: general_keyword_auto_reply, 4: general_time_auto_reply}

        # Act: Send message with matching keyword, during schedule, no story ID
        event_time = datetime(2024, 1, 15, 14, 0, 0, tzinfo=ZoneInfo("Asia/Taipei"))
        result = validate_trigger(
            trigger_settings=triggers,
            auto_replies=auto_replies,
            message_content="help",  # Matches keyword
            event_time=event_time,
            organization_timezone="Asia/Taipei",
            ig_story_id=None,  # No story ID
        )

        # Assert: Only general keyword reply is triggered (priority 3)
        assert result is not None
        assert result.auto_reply_id == 3

    def test_complete_priority_test4_general_time_based_wins(self):
        """[Complete-Priority-Test4]: Create only general time-based rule.
        Send a message during scheduled time with no keyword and no story ID.
        Expected Result: Only the general time-based reply is triggered (priority 4).
        """
        # Arrange: Create only general time-based rule
        schedule_settings = WebhookTriggerScheduleSettings(
            schedules=[DailySchedule(start_time="09:00", end_time="17:00")]
        )

        # 4. General Time-based (Priority 4)
        general_time_auto_reply = AutoReply(
            id=4,
            organization_id=1,
            name="General Time-based Reply",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.TIME,
            priority=1,
            trigger_schedule_settings=schedule_settings,
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        trigger = WebhookTriggerSetting(
            id=4,
            auto_reply_id=4,
            bot_id=1,
            enable=True,
            name="General Time-based Trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        # Act: Send message during scheduled time with no keyword and no story ID
        event_time = datetime(2024, 1, 15, 14, 0, 0, tzinfo=ZoneInfo("Asia/Taipei"))
        result = validate_trigger(
            trigger_settings=[trigger],
            auto_replies={4: general_time_auto_reply},
            message_content="random message",  # No specific keyword
            event_time=event_time,
            organization_timezone="Asia/Taipei",
            ig_story_id=None,  # No story ID
        )

        # Assert: Only general time-based reply is triggered (priority 4)
        assert result is not None
        assert result.auto_reply_id == 4


class TestIGStoryExclusionLogic:
    """Test cases for Story 11: IG Story Exclusion Logic."""

    def test_ig_story_exclusion_test1_story_specific_not_triggered_for_normal_message(self):
        """[IG-Story-Exclusion-Test1]: Create an IG story-specific keyword setting with keyword "hello".
        Send a normal message with keyword "hello" (no IG story ID).
        Expected Result: The auto-reply is NOT triggered because the setting is IG story-specific.
        """
        # Arrange: Create IG story-specific keyword setting
        auto_reply = AutoReply(
            id=1,
            organization_id=1,
            name="IG Story Specific Keyword Reply",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD,
            priority=1,
            keywords=["hello"],
            ig_story_ids=["story123"],  # IG story-specific
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        trigger_setting = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="IG Story Specific Keyword Trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        # Act: Send normal message with keyword but no IG story ID
        result = validate_trigger(
            trigger_settings=[trigger_setting],
            auto_replies={1: auto_reply},
            message_content="hello",
            event_time=datetime.now(ZoneInfo("UTC")),
            ig_story_id=None,  # No IG story context
        )

        # Assert: Auto-reply is NOT triggered because setting is IG story-specific
        assert result is None

    def test_ig_story_exclusion_test2_normal_keyword_triggered_for_normal_message(self):
        """[IG-Story-Exclusion-Test2]: Create a normal keyword setting without IG story configuration.
        Send a normal message with matching keyword.
        Expected Result: The auto-reply IS triggered because the setting is not IG story-specific.
        """
        # Arrange: Create normal keyword setting (no IG story configuration)
        auto_reply = AutoReply(
            id=1,
            organization_id=1,
            name="Normal Keyword Reply",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD,
            priority=1,
            keywords=["hello"],
            # No ig_story_ids - this is a general setting
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        trigger_setting = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="Normal Keyword Trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        # Act: Send normal message with matching keyword
        result = validate_trigger(
            trigger_settings=[trigger_setting],
            auto_replies={1: auto_reply},
            message_content="hello",
            event_time=datetime.now(ZoneInfo("UTC")),
            ig_story_id=None,  # Normal message, no story context
        )

        # Assert: Auto-reply IS triggered because setting is not IG story-specific
        assert result is not None
        assert result.auto_reply_id == 1

    def test_ig_story_exclusion_test3_only_general_keyword_triggered(self):
        """[IG-Story-Exclusion-Test3]: Create both IG story-specific and general keyword settings for the same keyword.
        Send a message with keyword but no story ID.
        Expected Result: Only the general keyword setting is triggered, not the IG story-specific one.
        """
        # Arrange: Create both IG story-specific and general keyword settings
        ig_story_auto_reply = AutoReply(
            id=1,
            organization_id=1,
            name="IG Story Specific Keyword Reply",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD,
            priority=1,
            keywords=["info"],
            ig_story_ids=["story123"],  # IG story-specific
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        general_auto_reply = AutoReply(
            id=2,
            organization_id=1,
            name="General Keyword Reply",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD,
            priority=1,
            keywords=["info"],
            # No ig_story_ids - this is a general setting
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        ig_story_trigger = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="IG Story Specific Keyword Trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        general_trigger = WebhookTriggerSetting(
            id=2,
            auto_reply_id=2,
            bot_id=1,
            enable=True,
            name="General Keyword Trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        # Act: Send message with keyword but no story ID
        result = validate_trigger(
            trigger_settings=[ig_story_trigger, general_trigger],
            auto_replies={1: ig_story_auto_reply, 2: general_auto_reply},
            message_content="info",
            event_time=datetime.now(ZoneInfo("UTC")),
            ig_story_id=None,  # No story context
        )

        # Assert: Only general keyword setting is triggered, not IG story-specific one
        assert result is not None
        assert result.auto_reply_id == 2  # General setting, not IG story-specific

    def test_general_keyword_not_triggered_when_ig_story_id_present(self):
        """Test that general keyword triggers are excluded when ig_story_id is present.
        This implements the IG Story Exclusion Logic where general triggers don't match IG story messages.
        """
        # Arrange: Create general keyword setting
        general_auto_reply = AutoReply(
            id=1,
            organization_id=1,
            name="General Keyword Reply",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD,
            priority=1,
            keywords=["help"],
            # No ig_story_ids - this is a general setting
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        trigger_setting = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="General Keyword Trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(ZoneInfo("UTC")),
            updated_at=datetime.now(ZoneInfo("UTC")),
        )

        # Act: Send message with keyword and IG story ID
        result = validate_trigger(
            trigger_settings=[trigger_setting],
            auto_replies={1: general_auto_reply},
            message_content="help",
            event_time=datetime.now(ZoneInfo("UTC")),
            ig_story_id="story123",  # IG story context present
        )

        # Assert: General keyword trigger is NOT triggered when IG story ID is present
        assert result is None
