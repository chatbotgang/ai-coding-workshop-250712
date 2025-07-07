"""Tests for auto-reply service layer."""

from datetime import datetime

import pytest

from internal.domain.auto_reply.auto_reply import AutoReply, AutoReplyEventType, AutoReplyStatus
from internal.services.auto_reply_service import AutoReplyService


class TestAutoReplyService:
    """Test the auto-reply service layer."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = AutoReplyService()
        self.base_datetime = datetime(2024, 1, 15, 14, 30, 0)

    def create_line_message_event(self, content: str = "hello") -> dict:
        """Create a LINE message event for testing."""
        return {
            "type": "message",
            "message": {"type": "text", "text": content},
            "source": {"type": "user", "userId": "user123"},
            "timestamp": int(self.base_datetime.timestamp() * 1000),
            "replyToken": "reply_token_123",
        }

    def create_instagram_story_event(self, content: str = "hello", story_id: str = "story123") -> dict:
        """Create an Instagram story reply event for testing."""
        return {
            "messaging": [
                {
                    "sender": {"id": "user123"},
                    "message": {"text": content, "story": {"id": story_id}},
                    "timestamp": int(self.base_datetime.timestamp() * 1000),
                }
            ]
        }

    def create_keyword_trigger(
        self, trigger_id: int = 1, keywords: list[str] = None, ig_story_ids: list[str] = None
    ) -> AutoReply:
        """Create a keyword trigger for testing."""
        if keywords is None:
            keywords = ["hello"]

        return AutoReply(
            id=trigger_id,
            organization_id=1,
            name="Test Keyword Trigger",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD,
            priority=3 if not ig_story_ids else 1,
            keywords=keywords,
            ig_story_ids=ig_story_ids,
            created_at=self.base_datetime,
            updated_at=self.base_datetime,
        )

    def test_validate_line_webhook_event_success(self):
        """Test successful validation of LINE webhook event."""
        trigger = self.create_keyword_trigger()
        event_data = self.create_line_message_event("hello")

        result = self.service.validate_webhook_event([trigger], bot_id=1, event_data=event_data, channel_type="line")

        assert result.has_match()
        assert result.matched_trigger.id == 1
        assert result.is_schedule_match  # No schedule configured, so should be True

    def test_validate_instagram_story_event_success(self):
        """Test successful validation of Instagram story event."""
        trigger = self.create_keyword_trigger(keywords=["hello"], ig_story_ids=["story123"])
        event_data = self.create_instagram_story_event("hello", "story123")

        result = self.service.validate_webhook_event(
            [trigger], bot_id=1, event_data=event_data, channel_type="instagram"
        )

        assert result.has_match()
        assert result.matched_trigger.id == 1

    def test_validate_no_matching_keyword(self):
        """Test validation with no matching keyword."""
        trigger = self.create_keyword_trigger(keywords=["goodbye"])
        event_data = self.create_line_message_event("hello")

        result = self.service.validate_webhook_event([trigger], bot_id=1, event_data=event_data, channel_type="line")

        assert not result.has_match()

    def test_validate_ig_story_wrong_story_id(self):
        """Test IG story trigger with wrong story ID."""
        trigger = self.create_keyword_trigger(keywords=["hello"], ig_story_ids=["story123"])
        event_data = self.create_instagram_story_event("hello", "story456")  # Wrong story ID

        result = self.service.validate_webhook_event(
            [trigger], bot_id=1, event_data=event_data, channel_type="instagram"
        )

        assert not result.has_match()

    def test_unsupported_channel_type(self):
        """Test validation with unsupported channel type."""
        trigger = self.create_keyword_trigger()
        event_data = self.create_line_message_event()

        with pytest.raises(ValueError, match="Unsupported channel type"):
            self.service.validate_webhook_event([trigger], bot_id=1, event_data=event_data, channel_type="invalid")

    def test_get_matching_triggers_by_priority(self):
        """Test getting all matching triggers sorted by priority."""
        triggers = [
            # Priority 3: General keyword (should NOT match when IG story context exists)
            self.create_keyword_trigger(trigger_id=1, keywords=["hello"]),
            # Priority 1: IG Story keyword (should match)
            self.create_keyword_trigger(trigger_id=2, keywords=["hello"], ig_story_ids=["story123"]),
        ]

        # Event that has IG story context - only IG story specific trigger should match
        event_data = self.create_instagram_story_event("hello", "story123")

        matching_triggers = self.service.get_matching_triggers_by_priority(
            triggers, bot_id=1, event_data=event_data, channel_type="instagram"
        )

        # Only IG Story trigger should match due to exclusion logic
        assert len(matching_triggers) == 1
        assert matching_triggers[0].id == 2  # IG Story keyword trigger

    def test_get_matching_triggers_general_context(self):
        """Test matching triggers without IG story context."""
        triggers = [
            # Priority 3: General keyword (should match when no IG story context)
            self.create_keyword_trigger(trigger_id=1, keywords=["hello"]),
            # Priority 1: IG Story keyword (should NOT match without story context)
            self.create_keyword_trigger(trigger_id=2, keywords=["hello"], ig_story_ids=["story123"]),
        ]

        # Regular LINE event without IG story context
        event_data = self.create_line_message_event("hello")

        matching_triggers = self.service.get_matching_triggers_by_priority(
            triggers, bot_id=1, event_data=event_data, channel_type="line"
        )

        # Only general trigger should match
        assert len(matching_triggers) == 1
        assert matching_triggers[0].id == 1  # General keyword trigger

    def test_get_matching_triggers_case_insensitive(self):
        """Test matching triggers with case insensitive keywords."""
        trigger = self.create_keyword_trigger(keywords=["hello"])
        event_data = self.create_line_message_event("HELLO")  # Different case

        matching_triggers = self.service.get_matching_triggers_by_priority(
            [trigger], bot_id=1, event_data=event_data, channel_type="line"
        )

        assert len(matching_triggers) == 1
        assert matching_triggers[0].id == 1

    def test_multiple_keywords_support(self):
        """Test trigger with multiple keywords."""
        trigger = self.create_keyword_trigger(keywords=["hello", "hi", "hey"])

        # Test each keyword triggers the same rule
        for keyword in ["hello", "hi", "hey"]:
            event_data = self.create_line_message_event(keyword)
            result = self.service.validate_webhook_event(
                [trigger], bot_id=1, event_data=event_data, channel_type="line"
            )

            assert result.has_match(), f"Should match keyword: {keyword}"
            assert result.matched_trigger.id == 1

    def test_inactive_trigger_ignored(self):
        """Test that inactive triggers are ignored."""
        trigger = self.create_keyword_trigger()
        trigger.status = AutoReplyStatus.INACTIVE

        event_data = self.create_line_message_event("hello")
        result = self.service.validate_webhook_event([trigger], bot_id=1, event_data=event_data, channel_type="line")

        assert not result.has_match()

    def test_empty_triggers_list(self):
        """Test validation with empty triggers list."""
        event_data = self.create_line_message_event("hello")
        result = self.service.validate_webhook_event([], bot_id=1, event_data=event_data, channel_type="line")

        assert not result.has_match()

    def test_service_factory(self):
        """Test the service factory function."""
        from internal.services.auto_reply_service import create_auto_reply_service

        service = create_auto_reply_service()
        assert isinstance(service, AutoReplyService)
        assert service.validator is not None
