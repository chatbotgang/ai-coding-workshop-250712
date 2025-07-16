"""Unit tests for the auto-reply domain service."""

import pytest
from datetime import datetime

from internal.domain.auto_reply.auto_reply import AutoReply, AutoReplyEventType, AutoReplyStatus
from internal.domain.auto_reply.events import EventContext, IGStoryContext, IncomingEvent
from internal.domain.auto_reply.service import TriggerValidationService

NOW = datetime.utcnow()


@pytest.fixture
def trigger_validation_service() -> TriggerValidationService:
    """Returns a TriggerValidationService instance for testing."""
    return TriggerValidationService()


class TestTriggerValidationService:
    """Test cases for TriggerValidationService."""

    def test_ig_story_keyword_trigger(self, trigger_validation_service: TriggerValidationService):
        """
        Tests the IG Story Keyword trigger logic based on PRD scenarios.
        - [IG-Story-Keyword-Test1]
        - [IG-Story-Keyword-Test2]
        - [IG-Story-Keyword-Test3]
        """
        rule = AutoReply(
            id=1,
            organization_id=1,
            name="IG Story Hello",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.IG_STORY_KEYWORD,
            priority=1,
            keywords=["hello", "hi"],
            ig_story_ids=["story123"],
            created_at=NOW,
            updated_at=NOW,
        )

        # Test 1: Matching story ID and keyword
        event_match = IncomingEvent(
            text=" HELLO ",
            context=EventContext(ig_story=IGStoryContext(id="story123")),
        )
        assert trigger_validation_service.find_best_trigger(event_match, [rule], NOW) == rule

        # Test 2: Wrong story ID
        event_wrong_story = IncomingEvent(
            text="hello",
            context=EventContext(ig_story=IGStoryContext(id="story456")),
        )
        assert trigger_validation_service.find_best_trigger(event_wrong_story, [rule], NOW) is None

        # Test 3: No story ID
        event_no_story = IncomingEvent(text="hello")
        assert trigger_validation_service.find_best_trigger(event_no_story, [rule], NOW) is None

    def test_ig_story_general_trigger(self, trigger_validation_service: TriggerValidationService):
        """
        Tests the IG Story General trigger logic.
        - [IG-Story-General-Test1]
        - [IG-Story-General-Test3]
        """
        rule = AutoReply(
            id=2,
            organization_id=1,
            name="IG Story General",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.IG_STORY_GENERAL,
            priority=2,
            ig_story_ids=["story123"],
            created_at=NOW,
            updated_at=NOW,
        )

        # Test 1: Matching story ID
        event_match = IncomingEvent(
            context=EventContext(ig_story=IGStoryContext(id="story123")),
        )
        assert trigger_validation_service.find_best_trigger(event_match, [rule], NOW) == rule

        # Test 3: Wrong story ID
        event_wrong_story = IncomingEvent(
            context=EventContext(ig_story=IGStoryContext(id="story456")),
        )
        assert trigger_validation_service.find_best_trigger(event_wrong_story, [rule], NOW) is None

    def test_priority_ig_story_keyword_vs_general_keyword(self, trigger_validation_service: TriggerValidationService):
        """
        Tests the priority logic between IG Story Keyword and General Keyword.
        - [IG-Story-Priority-Test1]
        """
        ig_story_rule = AutoReply(
            id=1,
            organization_id=1,
            name="IG Story Keyword Rule",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.IG_STORY_KEYWORD,
            priority=1,
            keywords=["promo"],
            ig_story_ids=["story-abc"],
            created_at=NOW,
            updated_at=NOW,
        )
        general_rule = AutoReply(
            id=3,
            organization_id=1,
            name="General Keyword Rule",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD,
            priority=3,
            keywords=["promo"],
            created_at=NOW,
            updated_at=NOW,
        )

        event = IncomingEvent(
            text="promo",
            context=EventContext(ig_story=IGStoryContext(id="story-abc")),
        )

        # The service should pick the higher-priority IG Story rule
        matched_rule = trigger_validation_service.find_best_trigger(event, [ig_story_rule, general_rule], NOW)
        assert matched_rule == ig_story_rule
        assert matched_rule.id == 1

    def test_complete_priority_system(self, trigger_validation_service: TriggerValidationService):
        """
        Tests the complete 4-tier priority system.
        - [Complete-Priority-Test1]
        - [Complete-Priority-Test2]
        - [Complete-Priority-Test3]
        - [Complete-Priority-Test4]
        """
        p1_rule = AutoReply(
            id=1, event_type=AutoReplyEventType.IG_STORY_KEYWORD, priority=1, name="P1",
            organization_id=1, status=AutoReplyStatus.ACTIVE, created_at=NOW, updated_at=NOW,
            keywords=["match"], ig_story_ids=["story1"],
        )
        p2_rule = AutoReply(
            id=2, event_type=AutoReplyEventType.IG_STORY_GENERAL, priority=2, name="P2",
            organization_id=1, status=AutoReplyStatus.ACTIVE, created_at=NOW, updated_at=NOW,
            ig_story_ids=["story1"],
        )
        p3_rule = AutoReply(
            id=3, event_type=AutoReplyEventType.KEYWORD, priority=3, name="P3",
            organization_id=1, status=AutoReplyStatus.ACTIVE, created_at=NOW, updated_at=NOW,
            keywords=["match"],
        )
        p4_rule = AutoReply(
            id=4, event_type=AutoReplyEventType.TIME, priority=4, name="P4",
            organization_id=1, status=AutoReplyStatus.ACTIVE, created_at=NOW, updated_at=NOW,
        )
        all_rules = [p1_rule, p2_rule, p3_rule, p4_rule]

        # Test 1: Event matches all rules, should pick P1
        event1 = IncomingEvent(text="match", context=EventContext(ig_story=IGStoryContext(id="story1")))
        assert trigger_validation_service.find_best_trigger(event1, all_rules, NOW) == p1_rule

        # Test 2: Event matches P2, P3, P4, should pick P2
        event2 = IncomingEvent(text="no-match", context=EventContext(ig_story=IGStoryContext(id="story1")))
        assert trigger_validation_service.find_best_trigger(event2, all_rules, NOW) == p2_rule

        # Test 3: Event matches P3, P4, should pick P3
        event3 = IncomingEvent(text="match")
        assert trigger_validation_service.find_best_trigger(event3, all_rules, NOW) == p3_rule

        # Test 4: Event matches only P4, should pick P4
        event4 = IncomingEvent(text="no-match")
        assert trigger_validation_service.find_best_trigger(event4, all_rules, NOW) == p4_rule 