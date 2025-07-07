"""Test cases for trigger validation logic."""

from datetime import datetime, time
from zoneinfo import ZoneInfo

from freezegun import freeze_time

from internal.domain.auto_reply.auto_reply import AutoReply, AutoReplyEventType, AutoReplyStatus
from internal.domain.auto_reply.trigger_validator import TriggerValidator
from internal.domain.auto_reply.webhook_event import ChannelType, WebhookEvent, WebhookEventType
from internal.domain.auto_reply.webhook_trigger import (
    BusinessHourSchedule,
    DailySchedule,
    MonthlySchedule,
    NonBusinessHourSchedule,
    WebhookTriggerScheduleSettings,
    WebhookTriggerScheduleType,
)
from internal.domain.organization.business_hour import BusinessHour, WeekDay


class TestKeywordLogic:
    """Test keyword reply logic with case insensitive and space trimming."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = TriggerValidator()
        self.base_datetime = datetime(2024, 1, 15, 14, 30, 0)  # Monday 2:30 PM

    def create_keyword_trigger(self, keywords: list[str], ig_story_ids: list[str] = None) -> AutoReply:
        """Create a keyword trigger for testing."""
        return AutoReply(
            id=1,
            organization_id=1,
            name="Test Keyword Trigger",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD,
            priority=3,
            keywords=keywords,
            ig_story_ids=ig_story_ids,
            created_at=self.base_datetime,
            updated_at=self.base_datetime,
        )

    def create_message_event(self, content: str, ig_story_id: str = None) -> WebhookEvent:
        """Create a message event for testing."""
        return WebhookEvent(
            event_type=WebhookEventType.MESSAGE,
            channel_type=ChannelType.LINE,
            bot_id=1,
            user_id="user123",
            message_content=content,
            ig_story_id=ig_story_id,
            timestamp=self.base_datetime,
        )

    def test_exact_keyword_match(self):
        """Test B-P0-7-Test2: Exact keyword match with various cases."""
        trigger = self.create_keyword_trigger(["hello"])

        # Test exact match
        event = self.create_message_event("hello")
        result = self.validator.validate_trigger([trigger], event)
        assert result.has_match()
        assert result.matched_trigger.id == 1

    def test_case_insensitive_matching(self):
        """Test case insensitive keyword matching."""
        trigger = self.create_keyword_trigger(["hello"])

        # Test various case combinations
        test_cases = ["hello", "HELLO", "Hello", "hELLo", "HeLLo"]
        for content in test_cases:
            event = self.create_message_event(content)
            result = self.validator.validate_trigger([trigger], event)
            assert result.has_match(), f"Failed for content: {content}"

    def test_space_trimming(self):
        """Test B-P0-7-Test3: Leading and trailing spaces are trimmed."""
        trigger = self.create_keyword_trigger(["hello"])

        # Test various space combinations
        test_cases = [" hello", "hello ", " hello ", "  hello  ", "\thello\t"]
        for content in test_cases:
            event = self.create_message_event(content)
            result = self.validator.validate_trigger([trigger], event)
            assert result.has_match(), f"Failed for content: '{content}'"

    def test_non_exact_match_rejected(self):
        """Test B-P0-7-Test4: Non-exact matches are rejected."""
        trigger = self.create_keyword_trigger(["hello"])

        # Test cases that should NOT match
        non_matching_cases = [
            "hello world",
            "say hello",
            "hello there",
            "hello123",
            "123hello",
            "helloworld",
            "hi hello",
            "hello hi",
        ]

        for content in non_matching_cases:
            event = self.create_message_event(content)
            result = self.validator.validate_trigger([trigger], event)
            assert not result.has_match(), f"Should not match content: '{content}'"

    def test_partial_match_rejected(self):
        """Test B-P0-7-Test5: Partial matches are rejected."""
        trigger = self.create_keyword_trigger(["hello"])

        # Test partial matches that should be rejected
        partial_cases = ["hell", "ello", "hel", "lo", "h", ""]

        for content in partial_cases:
            event = self.create_message_event(content)
            result = self.validator.validate_trigger([trigger], event)
            assert not result.has_match(), f"Should not match partial content: '{content}'"

    def test_multiple_keywords_support(self):
        """Test Multiple-Keywords-Test1: Multiple keywords trigger same response."""
        trigger = self.create_keyword_trigger(["hello", "hi", "hey"])

        # Test each keyword triggers the same response
        for keyword in ["hello", "hi", "hey"]:
            event = self.create_message_event(keyword)
            result = self.validator.validate_trigger([trigger], event)
            assert result.has_match(), f"Failed for keyword: {keyword}"
            assert result.matched_trigger.id == 1

    def test_multiple_keywords_case_insensitive(self):
        """Test Multiple-Keywords-Test2: Case insensitive with multiple keywords."""
        trigger = self.create_keyword_trigger(["hello", "hi", "hey"])

        # Test case variations for each keyword
        test_cases = [
            ("HELLO", True),
            ("Hi", True),
            ("HEY", True),
            ("hELLo", True),
            ("goodbye", False),
            ("greetings", False),
        ]

        for content, should_match in test_cases:
            event = self.create_message_event(content)
            result = self.validator.validate_trigger([trigger], event)
            if should_match:
                assert result.has_match(), f"Should match: {content}"
            else:
                assert not result.has_match(), f"Should not match: {content}"

    def test_no_keywords_no_match(self):
        """Test Multiple-Keywords-Test3: No match when no keywords match."""
        trigger = self.create_keyword_trigger(["hello", "hi", "hey"])

        non_matching_cases = ["goodbye", "greetings", "welcome", "thanks"]

        for content in non_matching_cases:
            event = self.create_message_event(content)
            result = self.validator.validate_trigger([trigger], event)
            assert not result.has_match(), f"Should not match: {content}"

    def test_empty_content_no_match(self):
        """Test that empty or None content doesn't match."""
        trigger = self.create_keyword_trigger(["hello"])

        # Test empty and None content
        for content in ["", None]:
            event = self.create_message_event(content)
            result = self.validator.validate_trigger([trigger], event)
            assert not result.has_match(), f"Should not match empty content: {content}"

    def test_inactive_trigger_no_match(self):
        """Test that inactive triggers don't match."""
        trigger = self.create_keyword_trigger(["hello"])
        trigger.status = AutoReplyStatus.INACTIVE

        event = self.create_message_event("hello")
        result = self.validator.validate_trigger([trigger], event)
        assert not result.has_match(), "Inactive trigger should not match"


class TestPrioritySystem:
    """Test 4-level priority system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = TriggerValidator()
        self.base_datetime = datetime(2024, 1, 15, 14, 30, 0)  # Monday 2:30 PM

    def create_triggers_all_types(self) -> list[AutoReply]:
        """Create triggers for all 4 priority levels."""
        daily_schedule = WebhookTriggerScheduleSettings(schedules=[DailySchedule(start_time="09:00", end_time="17:00")])

        triggers = [
            # Priority 4: General Time-based (lowest)
            AutoReply(
                id=4,
                organization_id=1,
                name="General Time",
                status=AutoReplyStatus.ACTIVE,
                event_type=AutoReplyEventType.TIME,
                priority=4,
                trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
                trigger_schedule_settings=daily_schedule,
                created_at=self.base_datetime,
                updated_at=self.base_datetime,
            ),
            # Priority 3: General Keyword
            AutoReply(
                id=3,
                organization_id=1,
                name="General Keyword",
                status=AutoReplyStatus.ACTIVE,
                event_type=AutoReplyEventType.KEYWORD,
                priority=3,
                keywords=["hello"],
                created_at=self.base_datetime,
                updated_at=self.base_datetime,
            ),
            # Priority 2: IG Story General
            AutoReply(
                id=2,
                organization_id=1,
                name="IG Story General",
                status=AutoReplyStatus.ACTIVE,
                event_type=AutoReplyEventType.TIME,
                priority=2,
                ig_story_ids=["story123"],
                trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
                trigger_schedule_settings=daily_schedule,
                created_at=self.base_datetime,
                updated_at=self.base_datetime,
            ),
            # Priority 1: IG Story Keyword (highest)
            AutoReply(
                id=1,
                organization_id=1,
                name="IG Story Keyword",
                status=AutoReplyStatus.ACTIVE,
                event_type=AutoReplyEventType.KEYWORD,
                priority=1,
                keywords=["hello"],
                ig_story_ids=["story123"],
                created_at=self.base_datetime,
                updated_at=self.base_datetime,
            ),
        ]

        return triggers

    def test_priority_1_ig_story_keyword_highest(self):
        """Test Complete-Priority-Test1: IG Story Keyword has highest priority."""
        triggers = self.create_triggers_all_types()

        # Message that could match all triggers
        event = WebhookEvent(
            event_type=WebhookEventType.MESSAGE,
            channel_type=ChannelType.INSTAGRAM,
            bot_id=1,
            user_id="user123",
            message_content="hello",
            ig_story_id="story123",
            timestamp=self.base_datetime,
        )

        result = self.validator.validate_trigger(triggers, event)
        assert result.has_match()
        assert result.matched_trigger.id == 1, "IG Story Keyword should have highest priority"

    def test_priority_2_ig_story_general(self):
        """Test Complete-Priority-Test2: IG Story General has priority 2."""
        triggers = self.create_triggers_all_types()

        # Remove IG Story Keyword trigger to test priority 2
        triggers = [t for t in triggers if t.id != 1]

        # Message during scheduled time with story ID but non-matching keyword
        event = WebhookEvent(
            event_type=WebhookEventType.MESSAGE,
            channel_type=ChannelType.INSTAGRAM,
            bot_id=1,
            user_id="user123",
            message_content="goodbye",  # Non-matching keyword
            ig_story_id="story123",
            timestamp=self.base_datetime,
        )

        result = self.validator.validate_trigger(triggers, event)
        assert result.has_match()
        assert result.matched_trigger.id == 2, "IG Story General should have priority 2"

    def test_priority_3_general_keyword(self):
        """Test Complete-Priority-Test3: General Keyword has priority 3."""
        triggers = self.create_triggers_all_types()

        # Remove higher priority triggers
        triggers = [t for t in triggers if t.id in [3, 4]]

        # Message with matching keyword during scheduled time but no story ID
        event = WebhookEvent(
            event_type=WebhookEventType.MESSAGE,
            channel_type=ChannelType.LINE,
            bot_id=1,
            user_id="user123",
            message_content="hello",
            ig_story_id=None,
            timestamp=self.base_datetime,
        )

        result = self.validator.validate_trigger(triggers, event)
        assert result.has_match()
        assert result.matched_trigger.id == 3, "General Keyword should have priority 3"

    def test_priority_4_general_time_lowest(self):
        """Test Complete-Priority-Test4: General Time has lowest priority."""
        triggers = self.create_triggers_all_types()

        # Keep only lowest priority trigger
        triggers = [t for t in triggers if t.id == 4]

        # Message during scheduled time with no keyword and no story ID
        event = WebhookEvent(
            event_type=WebhookEventType.MESSAGE,
            channel_type=ChannelType.LINE,
            bot_id=1,
            user_id="user123",
            message_content="anything",
            ig_story_id=None,
            timestamp=self.base_datetime,
        )

        result = self.validator.validate_trigger(triggers, event)
        assert result.has_match()
        assert result.matched_trigger.id == 4, "General Time should have lowest priority"

    def test_keyword_over_general_priority(self):
        """Test Priority-Test1: Keyword replies have higher priority than general."""
        daily_schedule = WebhookTriggerScheduleSettings(schedules=[DailySchedule(start_time="09:00", end_time="17:00")])

        triggers = [
            # General time-based trigger
            AutoReply(
                id=1,
                organization_id=1,
                name="General Time",
                status=AutoReplyStatus.ACTIVE,
                event_type=AutoReplyEventType.TIME,
                priority=4,
                trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
                trigger_schedule_settings=daily_schedule,
                created_at=self.base_datetime,
                updated_at=self.base_datetime,
            ),
            # Keyword trigger
            AutoReply(
                id=2,
                organization_id=1,
                name="Keyword",
                status=AutoReplyStatus.ACTIVE,
                event_type=AutoReplyEventType.KEYWORD,
                priority=3,
                keywords=["hello"],
                created_at=self.base_datetime,
                updated_at=self.base_datetime,
            ),
        ]

        # Message matches keyword during general reply time window
        event = WebhookEvent(
            event_type=WebhookEventType.MESSAGE,
            channel_type=ChannelType.LINE,
            bot_id=1,
            user_id="user123",
            message_content="hello",
            ig_story_id=None,
            timestamp=self.base_datetime,
        )

        result = self.validator.validate_trigger(triggers, event)
        assert result.has_match()
        assert result.matched_trigger.id == 2, "Keyword trigger should have higher priority"


class TestIGStoryContext:
    """Test IG Story context matching with multiple story IDs."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = TriggerValidator()
        self.base_datetime = datetime(2024, 1, 15, 14, 30, 0)  # Monday 2:30 PM

    def test_ig_story_keyword_matching(self):
        """Test IG-Story-Keyword-Test1: IG Story keyword trigger matches specific story."""
        trigger = AutoReply(
            id=1,
            organization_id=1,
            name="IG Story Keyword",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD,
            priority=1,
            keywords=["hello"],
            ig_story_ids=["story123"],
            created_at=self.base_datetime,
            updated_at=self.base_datetime,
        )

        # Test matching story ID with keyword
        event = WebhookEvent(
            event_type=WebhookEventType.MESSAGE,
            channel_type=ChannelType.INSTAGRAM,
            bot_id=1,
            user_id="user123",
            message_content="hello",
            ig_story_id="story123",
            timestamp=self.base_datetime,
        )

        result = self.validator.validate_trigger([trigger], event)
        assert result.has_match()
        assert result.matched_trigger.id == 1

    def test_ig_story_keyword_wrong_story(self):
        """Test IG-Story-Keyword-Test2: IG Story keyword trigger doesn't match wrong story."""
        trigger = AutoReply(
            id=1,
            organization_id=1,
            name="IG Story Keyword",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD,
            priority=1,
            keywords=["hello"],
            ig_story_ids=["story123"],
            created_at=self.base_datetime,
            updated_at=self.base_datetime,
        )

        # Test wrong story ID
        event = WebhookEvent(
            event_type=WebhookEventType.MESSAGE,
            channel_type=ChannelType.INSTAGRAM,
            bot_id=1,
            user_id="user123",
            message_content="hello",
            ig_story_id="story456",  # Different story ID
            timestamp=self.base_datetime,
        )

        result = self.validator.validate_trigger([trigger], event)
        assert not result.has_match(), "Should not match wrong story ID"

    def test_ig_story_keyword_no_story_context(self):
        """Test IG-Story-Keyword-Test3: IG Story keyword trigger requires story context."""
        trigger = AutoReply(
            id=1,
            organization_id=1,
            name="IG Story Keyword",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD,
            priority=1,
            keywords=["hello"],
            ig_story_ids=["story123"],
            created_at=self.base_datetime,
            updated_at=self.base_datetime,
        )

        # Test no story context
        event = WebhookEvent(
            event_type=WebhookEventType.MESSAGE,
            channel_type=ChannelType.INSTAGRAM,
            bot_id=1,
            user_id="user123",
            message_content="hello",
            ig_story_id=None,  # No story context
            timestamp=self.base_datetime,
        )

        result = self.validator.validate_trigger([trigger], event)
        assert not result.has_match(), "Should not match without story context"

    def test_ig_story_multiple_keywords(self):
        """Test IG-Story-Multiple-Keywords-Test1: Multiple keywords with IG Story."""
        trigger = AutoReply(
            id=1,
            organization_id=1,
            name="IG Story Multiple Keywords",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD,
            priority=1,
            keywords=["hello", "hi"],
            ig_story_ids=["story123"],
            created_at=self.base_datetime,
            updated_at=self.base_datetime,
        )

        # Test each keyword with correct story ID
        for keyword in ["hello", "hi"]:
            event = WebhookEvent(
                event_type=WebhookEventType.MESSAGE,
                channel_type=ChannelType.INSTAGRAM,
                bot_id=1,
                user_id="user123",
                message_content=keyword,
                ig_story_id="story123",
                timestamp=self.base_datetime,
            )

            result = self.validator.validate_trigger([trigger], event)
            assert result.has_match(), f"Should match keyword: {keyword}"

    def test_ig_story_multiple_keywords_wrong_story(self):
        """Test IG-Story-Multiple-Keywords-Test2: Multiple keywords with wrong story."""
        trigger = AutoReply(
            id=1,
            organization_id=1,
            name="IG Story Multiple Keywords",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD,
            priority=1,
            keywords=["hello", "hi"],
            ig_story_ids=["story123"],
            created_at=self.base_datetime,
            updated_at=self.base_datetime,
        )

        # Test with wrong story ID
        event = WebhookEvent(
            event_type=WebhookEventType.MESSAGE,
            channel_type=ChannelType.INSTAGRAM,
            bot_id=1,
            user_id="user123",
            message_content="hello",
            ig_story_id="story456",
            timestamp=self.base_datetime,
        )

        result = self.validator.validate_trigger([trigger], event)
        assert not result.has_match(), "Should not match with wrong story ID"

    def test_ig_story_exclusion_logic(self):
        """Test IG-Story-Exclusion-Test1: IG Story specific settings excluded from general."""
        ig_story_trigger = AutoReply(
            id=1,
            organization_id=1,
            name="IG Story Specific",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD,
            priority=1,
            keywords=["hello"],
            ig_story_ids=["story123"],
            created_at=self.base_datetime,
            updated_at=self.base_datetime,
        )

        # Test normal message without IG story context
        event = WebhookEvent(
            event_type=WebhookEventType.MESSAGE,
            channel_type=ChannelType.LINE,
            bot_id=1,
            user_id="user123",
            message_content="hello",
            ig_story_id=None,
            timestamp=self.base_datetime,
        )

        result = self.validator.validate_trigger([ig_story_trigger], event)
        assert not result.has_match(), "IG Story specific trigger should not match general messages"

    def test_multiple_story_ids_support(self):
        """Test support for multiple story IDs in a single trigger."""
        trigger = AutoReply(
            id=1,
            organization_id=1,
            name="Multiple Stories",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD,
            priority=1,
            keywords=["hello"],
            ig_story_ids=["story123", "story456", "story789"],
            created_at=self.base_datetime,
            updated_at=self.base_datetime,
        )

        # Test each story ID matches
        for story_id in ["story123", "story456", "story789"]:
            event = WebhookEvent(
                event_type=WebhookEventType.MESSAGE,
                channel_type=ChannelType.INSTAGRAM,
                bot_id=1,
                user_id="user123",
                message_content="hello",
                ig_story_id=story_id,
                timestamp=self.base_datetime,
            )

            result = self.validator.validate_trigger([trigger], event)
            assert result.has_match(), f"Should match story ID: {story_id}"

    def test_ig_story_priority_over_general(self):
        """Test B-P1-18-Test9: IG Story specific triggers have higher priority."""
        triggers = [
            # General keyword trigger
            AutoReply(
                id=1,
                organization_id=1,
                name="General Keyword",
                status=AutoReplyStatus.ACTIVE,
                event_type=AutoReplyEventType.KEYWORD,
                priority=3,
                keywords=["hello"],
                created_at=self.base_datetime,
                updated_at=self.base_datetime,
            ),
            # IG Story keyword trigger
            AutoReply(
                id=2,
                organization_id=1,
                name="IG Story Keyword",
                status=AutoReplyStatus.ACTIVE,
                event_type=AutoReplyEventType.KEYWORD,
                priority=1,
                keywords=["hello"],
                ig_story_ids=["story123"],
                created_at=self.base_datetime,
                updated_at=self.base_datetime,
            ),
        ]

        # Message that matches both rules (story reply + keyword)
        event = WebhookEvent(
            event_type=WebhookEventType.MESSAGE,
            channel_type=ChannelType.INSTAGRAM,
            bot_id=1,
            user_id="user123",
            message_content="hello",
            ig_story_id="story123",
            timestamp=self.base_datetime,
        )

        result = self.validator.validate_trigger(triggers, event)
        assert result.has_match()
        assert result.matched_trigger.id == 2, "IG Story trigger should have higher priority"


class TestScheduleValidation:
    """Test schedule validation for time-based triggers."""

    def setup_method(self):
        """Set up test fixtures."""
        business_hours = [
            BusinessHour(
                id=1,
                organization_id=1,
                day_of_week=WeekDay.MONDAY,
                start_time=time(9, 0),
                end_time=time(17, 0),
                is_active=True,
            ),
            BusinessHour(
                id=2,
                organization_id=1,
                day_of_week=WeekDay.TUESDAY,
                start_time=time(9, 0),
                end_time=time(17, 0),
                is_active=True,
            ),
        ]
        self.validator = TriggerValidator(business_hours=business_hours)

    @freeze_time("2024-01-15 14:30:00")  # Monday 2:30 PM
    def test_daily_schedule_within_window(self):
        """Test B-P0-6-Test3: Daily schedule within time window."""
        daily_schedule = WebhookTriggerScheduleSettings(schedules=[DailySchedule(start_time="09:00", end_time="17:00")])

        trigger = AutoReply(
            id=1,
            organization_id=1,
            name="Daily Schedule",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.TIME,
            priority=4,
            trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
            trigger_schedule_settings=daily_schedule,
            created_at=datetime(2024, 1, 15, 14, 30, 0),
            updated_at=datetime(2024, 1, 15, 14, 30, 0),
        )

        event = WebhookEvent(
            event_type=WebhookEventType.MESSAGE,
            channel_type=ChannelType.LINE,
            bot_id=1,
            user_id="user123",
            message_content="anything",
            ig_story_id=None,
            timestamp=datetime(2024, 1, 15, 14, 30, 0),
        )

        result = self.validator.validate_trigger([trigger], event)
        assert result.has_match()
        assert result.is_schedule_match, "Should match daily schedule"

    @freeze_time("2024-01-15 20:30:00")  # Monday 8:30 PM (outside schedule)
    def test_daily_schedule_outside_window(self):
        """Test daily schedule outside time window."""
        daily_schedule = WebhookTriggerScheduleSettings(schedules=[DailySchedule(start_time="09:00", end_time="17:00")])

        trigger = AutoReply(
            id=1,
            organization_id=1,
            name="Daily Schedule",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.TIME,
            priority=4,
            trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
            trigger_schedule_settings=daily_schedule,
            created_at=datetime(2024, 1, 15, 20, 30, 0),
            updated_at=datetime(2024, 1, 15, 20, 30, 0),
        )

        event = WebhookEvent(
            event_type=WebhookEventType.MESSAGE,
            channel_type=ChannelType.LINE,
            bot_id=1,
            user_id="user123",
            message_content="anything",
            ig_story_id=None,
            timestamp=datetime(2024, 1, 15, 20, 30, 0),
        )

        result = self.validator.validate_trigger([trigger], event)
        assert result.has_match()
        assert not result.is_schedule_match, "Should not match outside daily schedule"

    @freeze_time("2024-01-15 14:30:00")  # Monday 2:30 PM (15th day of month)
    def test_monthly_schedule_matching_day(self):
        """Test B-P0-6-Test4: Monthly schedule on matching day."""
        monthly_schedule = WebhookTriggerScheduleSettings(
            schedules=[MonthlySchedule(day=15, start_time="10:00", end_time="16:00")]
        )

        trigger = AutoReply(
            id=1,
            organization_id=1,
            name="Monthly Schedule",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.TIME,
            priority=4,
            trigger_schedule_type=WebhookTriggerScheduleType.MONTHLY,
            trigger_schedule_settings=monthly_schedule,
            created_at=datetime(2024, 1, 15, 14, 30, 0),
            updated_at=datetime(2024, 1, 15, 14, 30, 0),
        )

        event = WebhookEvent(
            event_type=WebhookEventType.MESSAGE,
            channel_type=ChannelType.LINE,
            bot_id=1,
            user_id="user123",
            message_content="anything",
            ig_story_id=None,
            timestamp=datetime(2024, 1, 15, 14, 30, 0),
        )

        result = self.validator.validate_trigger([trigger], event)
        assert result.has_match()
        assert result.is_schedule_match, "Should match monthly schedule"

    @freeze_time("2024-01-15 14:30:00")  # Monday 2:30 PM (within business hours)
    def test_business_hours_schedule(self):
        """Test B-P0-6-Test5: Business hours schedule matching."""
        trigger = AutoReply(
            id=1,
            organization_id=1,
            name="Business Hours",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.TIME,
            priority=4,
            trigger_schedule_type=WebhookTriggerScheduleType.BUSINESS_HOUR,
            trigger_schedule_settings=WebhookTriggerScheduleSettings(schedules=[BusinessHourSchedule()]),
            created_at=datetime(2024, 1, 15, 14, 30, 0),
            updated_at=datetime(2024, 1, 15, 14, 30, 0),
        )

        event = WebhookEvent(
            event_type=WebhookEventType.MESSAGE,
            channel_type=ChannelType.LINE,
            bot_id=1,
            user_id="user123",
            message_content="anything",
            ig_story_id=None,
            timestamp=datetime(2024, 1, 15, 14, 30, 0),
        )

        result = self.validator.validate_trigger([trigger], event)
        assert result.has_match()
        assert result.is_schedule_match, "Should match business hours"

    @freeze_time("2024-01-15 20:30:00")  # Monday 8:30 PM (outside business hours)
    def test_non_business_hours_schedule(self):
        """Test non-business hours schedule."""
        trigger = AutoReply(
            id=1,
            organization_id=1,
            name="Non-Business Hours",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.TIME,
            priority=4,
            trigger_schedule_type=WebhookTriggerScheduleType.NON_BUSINESS_HOUR,
            trigger_schedule_settings=WebhookTriggerScheduleSettings(schedules=[NonBusinessHourSchedule()]),
            created_at=datetime(2024, 1, 15, 20, 30, 0),
            updated_at=datetime(2024, 1, 15, 20, 30, 0),
        )

        event = WebhookEvent(
            event_type=WebhookEventType.MESSAGE,
            channel_type=ChannelType.LINE,
            bot_id=1,
            user_id="user123",
            message_content="anything",
            ig_story_id=None,
            timestamp=datetime(2024, 1, 15, 20, 30, 0),
        )

        result = self.validator.validate_trigger([trigger], event)
        assert result.has_match()
        assert result.is_schedule_match, "Should match non-business hours"

    @freeze_time("2024-01-15 23:30:00")  # Monday 11:30 PM (during midnight crossing schedule)
    def test_daily_schedule_midnight_crossing_late_night(self):
        """Test daily schedule that crosses midnight - late night event."""
        # Schedule from 22:00 to 06:00 (crosses midnight)
        daily_schedule = WebhookTriggerScheduleSettings(schedules=[DailySchedule(start_time="22:00", end_time="06:00")])

        trigger = AutoReply(
            id=1,
            organization_id=1,
            name="Midnight Crossing Daily",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.TIME,
            priority=4,
            trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
            trigger_schedule_settings=daily_schedule,
            created_at=datetime(2024, 1, 15, 23, 30, 0),
            updated_at=datetime(2024, 1, 15, 23, 30, 0),
        )

        event = WebhookEvent(
            event_type=WebhookEventType.MESSAGE,
            channel_type=ChannelType.LINE,
            bot_id=1,
            user_id="user123",
            message_content="anything",
            ig_story_id=None,
            timestamp=datetime(2024, 1, 15, 23, 30, 0),
        )

        result = self.validator.validate_trigger([trigger], event)
        assert result.has_match()
        assert result.is_schedule_match, "Should match midnight crossing schedule (late night)"

    @freeze_time("2024-01-16 02:30:00")  # Tuesday 2:30 AM (during midnight crossing schedule)
    def test_daily_schedule_midnight_crossing_early_morning(self):
        """Test daily schedule that crosses midnight - early morning event."""
        # Schedule from 22:00 to 06:00 (crosses midnight)
        daily_schedule = WebhookTriggerScheduleSettings(schedules=[DailySchedule(start_time="22:00", end_time="06:00")])

        trigger = AutoReply(
            id=1,
            organization_id=1,
            name="Midnight Crossing Daily",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.TIME,
            priority=4,
            trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
            trigger_schedule_settings=daily_schedule,
            created_at=datetime(2024, 1, 16, 2, 30, 0),
            updated_at=datetime(2024, 1, 16, 2, 30, 0),
        )

        event = WebhookEvent(
            event_type=WebhookEventType.MESSAGE,
            channel_type=ChannelType.LINE,
            bot_id=1,
            user_id="user123",
            message_content="anything",
            ig_story_id=None,
            timestamp=datetime(2024, 1, 16, 2, 30, 0),
        )

        result = self.validator.validate_trigger([trigger], event)
        assert result.has_match()
        assert result.is_schedule_match, "Should match midnight crossing schedule (early morning)"

    @freeze_time("2024-01-15 10:30:00")  # Monday 10:30 AM (outside midnight crossing schedule)
    def test_daily_schedule_midnight_crossing_outside_window(self):
        """Test daily schedule that crosses midnight - outside window."""
        # Schedule from 22:00 to 06:00 (crosses midnight)
        daily_schedule = WebhookTriggerScheduleSettings(schedules=[DailySchedule(start_time="22:00", end_time="06:00")])

        trigger = AutoReply(
            id=1,
            organization_id=1,
            name="Midnight Crossing Daily",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.TIME,
            priority=4,
            trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
            trigger_schedule_settings=daily_schedule,
            created_at=datetime(2024, 1, 15, 10, 30, 0),
            updated_at=datetime(2024, 1, 15, 10, 30, 0),
        )

        event = WebhookEvent(
            event_type=WebhookEventType.MESSAGE,
            channel_type=ChannelType.LINE,
            bot_id=1,
            user_id="user123",
            message_content="anything",
            ig_story_id=None,
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
        )

        result = self.validator.validate_trigger([trigger], event)
        assert result.has_match()
        assert not result.is_schedule_match, "Should not match outside midnight crossing schedule"


class TestEdgeCases:
    """Test edge cases and complex scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = TriggerValidator()
        self.base_datetime = datetime(2024, 1, 15, 14, 30, 0)

    def test_non_message_event_no_match(self):
        """Test that non-MESSAGE events don't trigger auto-replies."""
        trigger = AutoReply(
            id=1,
            organization_id=1,
            name="Keyword Trigger",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD,
            priority=3,
            keywords=["hello"],
            created_at=self.base_datetime,
            updated_at=self.base_datetime,
        )

        # Test POSTBACK event
        event = WebhookEvent(
            event_type=WebhookEventType.POSTBACK,
            channel_type=ChannelType.LINE,
            bot_id=1,
            user_id="user123",
            message_content="hello",
            ig_story_id=None,
            timestamp=self.base_datetime,
        )

        result = self.validator.validate_trigger([trigger], event)
        assert not result.has_match(), "POSTBACK events should not trigger auto-replies"

    def test_empty_triggers_list(self):
        """Test empty triggers list returns no match."""
        event = WebhookEvent(
            event_type=WebhookEventType.MESSAGE,
            channel_type=ChannelType.LINE,
            bot_id=1,
            user_id="user123",
            message_content="hello",
            ig_story_id=None,
            timestamp=self.base_datetime,
        )

        result = self.validator.validate_trigger([], event)
        assert not result.has_match(), "Empty triggers list should return no match"

    def test_mixed_channel_types(self):
        """Test triggers work across different channel types."""
        trigger = AutoReply(
            id=1,
            organization_id=1,
            name="Cross-Channel Trigger",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD,
            priority=3,
            keywords=["hello"],
            created_at=self.base_datetime,
            updated_at=self.base_datetime,
        )

        # Test different channel types
        for channel_type in [ChannelType.LINE, ChannelType.FACEBOOK, ChannelType.INSTAGRAM]:
            event = WebhookEvent(
                event_type=WebhookEventType.MESSAGE,
                channel_type=channel_type,
                bot_id=1,
                user_id="user123",
                message_content="hello",
                ig_story_id=None,
                timestamp=self.base_datetime,
            )

            result = self.validator.validate_trigger([trigger], event)
            assert result.has_match(), f"Should work for {channel_type} channel"

    def test_complex_priority_scenario(self):
        """Test complex scenario with all priority levels and exclusions."""
        daily_schedule = WebhookTriggerScheduleSettings(schedules=[DailySchedule(start_time="09:00", end_time="17:00")])

        triggers = [
            # Priority 1: IG Story Keyword
            AutoReply(
                id=1,
                organization_id=1,
                name="IG Story Keyword",
                status=AutoReplyStatus.ACTIVE,
                event_type=AutoReplyEventType.KEYWORD,
                priority=1,
                keywords=["hello"],
                ig_story_ids=["story123"],
                created_at=self.base_datetime,
                updated_at=self.base_datetime,
            ),
            # Priority 2: IG Story General
            AutoReply(
                id=2,
                organization_id=1,
                name="IG Story General",
                status=AutoReplyStatus.ACTIVE,
                event_type=AutoReplyEventType.TIME,
                priority=2,
                ig_story_ids=["story456"],
                trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
                trigger_schedule_settings=daily_schedule,
                created_at=self.base_datetime,
                updated_at=self.base_datetime,
            ),
            # Priority 3: General Keyword
            AutoReply(
                id=3,
                organization_id=1,
                name="General Keyword",
                status=AutoReplyStatus.ACTIVE,
                event_type=AutoReplyEventType.KEYWORD,
                priority=3,
                keywords=["hello"],
                created_at=self.base_datetime,
                updated_at=self.base_datetime,
            ),
        ]

        # Test various scenarios
        test_cases = [
            # IG Story Keyword should win (Priority 1)
            ("hello", "story123", 1),
            # IG Story General should win (Priority 2)
            ("anything", "story456", 2),
            # General Keyword should win (Priority 3)
            ("hello", None, 3),
        ]

        for content, story_id, expected_trigger_id in test_cases:
            event = WebhookEvent(
                event_type=WebhookEventType.MESSAGE,
                channel_type=ChannelType.INSTAGRAM,
                bot_id=1,
                user_id="user123",
                message_content=content,
                ig_story_id=story_id,
                timestamp=self.base_datetime,
            )

            result = self.validator.validate_trigger(triggers, event)
            assert result.has_match(), f"Should match for content: {content}, story: {story_id}"
            assert (
                result.matched_trigger.id == expected_trigger_id
            ), f"Expected trigger {expected_trigger_id} for content: {content}, story: {story_id}"


class TestTimezoneHandling:
    """Test timezone handling for schedule validation."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create business hours for Asia/Taipei timezone (UTC+8)
        self.business_hours = [
            BusinessHour(
                id=1,
                organization_id=1,
                day_of_week=WeekDay.MONDAY,
                start_time=time(9, 0),  # 9:00 AM
                end_time=time(17, 0),  # 5:00 PM
                is_active=True,
            ),
            BusinessHour(
                id=2,
                organization_id=1,
                day_of_week=WeekDay.TUESDAY,
                start_time=time(9, 0),  # 9:00 AM
                end_time=time(17, 0),  # 5:00 PM
                is_active=True,
            ),
        ]

    def test_business_hours_with_timezone_conversion(self):
        """Test business hours validation with timezone conversion."""
        # Create validator with Asia/Taipei timezone
        validator = TriggerValidator(business_hours=self.business_hours, organization_timezone="Asia/Taipei")

        # Create trigger for business hours
        trigger = AutoReply(
            id=1,
            organization_id=1,
            name="Business Hours Test",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.TIME,
            priority=4,
            trigger_schedule_type=WebhookTriggerScheduleType.BUSINESS_HOUR,
            trigger_schedule_settings=WebhookTriggerScheduleSettings(schedules=[BusinessHourSchedule()]),
            created_at=datetime(2024, 1, 15, 10, 0, 0),
            updated_at=datetime(2024, 1, 15, 10, 0, 0),
        )

        # Test case 1: UTC 02:00 (Monday) = 10:00 Asia/Taipei (Monday) - within business hours
        event_utc = WebhookEvent(
            event_type=WebhookEventType.MESSAGE,
            channel_type=ChannelType.LINE,
            bot_id=1,
            user_id="user123",
            message_content="test",
            ig_story_id=None,
            timestamp=datetime(2024, 1, 15, 2, 0, 0, tzinfo=ZoneInfo("UTC")),  # Monday 2:00 AM UTC
        )

        result = validator.validate_trigger([trigger], event_utc)
        assert result.has_match()
        assert result.is_schedule_match, "Should match business hours (UTC 02:00 = Taipei 10:00)"

    def test_business_hours_outside_timezone_conversion(self):
        """Test business hours validation outside converted timezone."""
        # Create validator with Asia/Taipei timezone
        validator = TriggerValidator(business_hours=self.business_hours, organization_timezone="Asia/Taipei")

        # Create trigger for business hours
        trigger = AutoReply(
            id=1,
            organization_id=1,
            name="Business Hours Test",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.TIME,
            priority=4,
            trigger_schedule_type=WebhookTriggerScheduleType.BUSINESS_HOUR,
            trigger_schedule_settings=WebhookTriggerScheduleSettings(schedules=[BusinessHourSchedule()]),
            created_at=datetime(2024, 1, 15, 10, 0, 0),
            updated_at=datetime(2024, 1, 15, 10, 0, 0),
        )

        # Test case: UTC 10:00 (Monday) = 18:00 Asia/Taipei (Monday) - outside business hours
        event_utc = WebhookEvent(
            event_type=WebhookEventType.MESSAGE,
            channel_type=ChannelType.LINE,
            bot_id=1,
            user_id="user123",
            message_content="test",
            ig_story_id=None,
            timestamp=datetime(2024, 1, 15, 10, 0, 0, tzinfo=ZoneInfo("UTC")),  # Monday 10:00 AM UTC
        )

        result = validator.validate_trigger([trigger], event_utc)
        assert result.has_match()
        assert not result.is_schedule_match, "Should not match business hours (UTC 10:00 = Taipei 18:00)"

    def test_daily_schedule_with_timezone_conversion(self):
        """Test daily schedule validation with timezone conversion."""
        # Create validator with Asia/Taipei timezone
        validator = TriggerValidator(organization_timezone="Asia/Taipei")

        # Create trigger for daily schedule 10:00-16:00
        daily_schedule = WebhookTriggerScheduleSettings(schedules=[DailySchedule(start_time="10:00", end_time="16:00")])

        trigger = AutoReply(
            id=1,
            organization_id=1,
            name="Daily Schedule Test",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.TIME,
            priority=4,
            trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
            trigger_schedule_settings=daily_schedule,
            created_at=datetime(2024, 1, 15, 12, 0, 0),
            updated_at=datetime(2024, 1, 15, 12, 0, 0),
        )

        # Test case: UTC 04:00 = 12:00 Asia/Taipei - within daily schedule
        event_utc = WebhookEvent(
            event_type=WebhookEventType.MESSAGE,
            channel_type=ChannelType.LINE,
            bot_id=1,
            user_id="user123",
            message_content="test",
            ig_story_id=None,
            timestamp=datetime(2024, 1, 15, 4, 0, 0, tzinfo=ZoneInfo("UTC")),
        )

        result = validator.validate_trigger([trigger], event_utc)
        assert result.has_match()
        assert result.is_schedule_match, "Should match daily schedule (UTC 04:00 = Taipei 12:00)"

    def test_naive_datetime_assumed_utc(self):
        """Test that naive datetime is assumed to be UTC."""
        validator = TriggerValidator(organization_timezone="Asia/Taipei")

        # Create trigger for daily schedule 10:00-16:00
        daily_schedule = WebhookTriggerScheduleSettings(schedules=[DailySchedule(start_time="10:00", end_time="16:00")])

        trigger = AutoReply(
            id=1,
            organization_id=1,
            name="Daily Schedule Test",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.TIME,
            priority=4,
            trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
            trigger_schedule_settings=daily_schedule,
            created_at=datetime(2024, 1, 15, 12, 0, 0),
            updated_at=datetime(2024, 1, 15, 12, 0, 0),
        )

        # Test case: Naive datetime 04:00 (assumed UTC) = 12:00 Asia/Taipei
        event_naive = WebhookEvent(
            event_type=WebhookEventType.MESSAGE,
            channel_type=ChannelType.LINE,
            bot_id=1,
            user_id="user123",
            message_content="test",
            ig_story_id=None,
            timestamp=datetime(2024, 1, 15, 4, 0, 0),  # Naive datetime
        )

        result = validator.validate_trigger([trigger], event_naive)
        assert result.has_match()
        assert result.is_schedule_match, "Should match daily schedule (naive 04:00 assumed UTC = Taipei 12:00)"

    def test_no_timezone_configured_fallback(self):
        """Test that without timezone configuration, times are used as-is."""
        validator = TriggerValidator(organization_timezone=None)

        # Create trigger for daily schedule 10:00-16:00
        daily_schedule = WebhookTriggerScheduleSettings(schedules=[DailySchedule(start_time="10:00", end_time="16:00")])

        trigger = AutoReply(
            id=1,
            organization_id=1,
            name="Daily Schedule Test",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.TIME,
            priority=4,
            trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
            trigger_schedule_settings=daily_schedule,
            created_at=datetime(2024, 1, 15, 12, 0, 0),
            updated_at=datetime(2024, 1, 15, 12, 0, 0),
        )

        # Test case: 12:00 should match 10:00-16:00 schedule directly
        event = WebhookEvent(
            event_type=WebhookEventType.MESSAGE,
            channel_type=ChannelType.LINE,
            bot_id=1,
            user_id="user123",
            message_content="test",
            ig_story_id=None,
            timestamp=datetime(2024, 1, 15, 12, 0, 0),
        )

        result = validator.validate_trigger([trigger], event)
        assert result.has_match()
        assert result.is_schedule_match, "Should match daily schedule without timezone conversion"

    def test_business_hours_midnight_crossing_with_timezone(self):
        """Test business hours that cross midnight with timezone conversion."""
        # Create business hours that cross midnight (22:00 - 06:00)
        midnight_business_hours = [
            BusinessHour(
                id=1,
                organization_id=1,
                day_of_week=WeekDay.MONDAY,
                start_time=time(22, 0),  # 10:00 PM
                end_time=time(6, 0),  # 6:00 AM (next day)
                is_active=True,
            )
        ]

        validator = TriggerValidator(business_hours=midnight_business_hours, organization_timezone="Asia/Taipei")

        trigger = AutoReply(
            id=1,
            organization_id=1,
            name="Midnight Business Hours",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.TIME,
            priority=4,
            trigger_schedule_type=WebhookTriggerScheduleType.BUSINESS_HOUR,
            trigger_schedule_settings=WebhookTriggerScheduleSettings(schedules=[BusinessHourSchedule()]),
            created_at=datetime(2024, 1, 15, 23, 0, 0),
            updated_at=datetime(2024, 1, 15, 23, 0, 0),
        )

        # Test case: UTC 15:00 (Monday) = 23:00 Asia/Taipei (Monday) - within midnight crossing business hours
        event_utc = WebhookEvent(
            event_type=WebhookEventType.MESSAGE,
            channel_type=ChannelType.LINE,
            bot_id=1,
            user_id="user123",
            message_content="test",
            ig_story_id=None,
            timestamp=datetime(2024, 1, 15, 15, 0, 0, tzinfo=ZoneInfo("UTC")),  # Monday 3:00 PM UTC
        )

        result = validator.validate_trigger([trigger], event_utc)
        assert result.has_match()
        assert result.is_schedule_match, "Should match midnight crossing business hours (UTC 15:00 = Taipei 23:00)"
