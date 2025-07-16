"""Tests for priority sorting functionality.

These tests verify PRD requirements for priority logic:
- KEYWORD event type has higher priority than TIME event type
- Within same event type, lower priority number = higher priority
- Priority system ensures most specific triggers take precedence
"""

from datetime import datetime
import pytest

from internal.domain.auto_reply.auto_reply import AutoReply, AutoReplyEventType, AutoReplyStatus
from internal.domain.auto_reply.webhook_trigger import WebhookTriggerSetting, WebhookTriggerEventType
from internal.domain.auto_reply.priority_sorter import sort_triggers_by_priority


class TestPrioritySorter:
    """Test cases for priority sorting logic."""
    
    def test_keyword_has_higher_priority_than_time(self):
        """Test that KEYWORD event type has higher priority than TIME event type."""
        # Create AutoReply objects
        keyword_auto_reply = AutoReply(
            id=1, organization_id=1, name="Keyword Reply", status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD, priority=5, keywords=["hello"],
            trigger_schedule_type=None, trigger_schedule_settings=None,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        time_auto_reply = AutoReply(
            id=2, organization_id=1, name="Time Reply", status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.TIME, priority=1, keywords=None,
            trigger_schedule_type=None, trigger_schedule_settings=None,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        # Create WebhookTriggerSettings (in reverse priority order)
        time_trigger = WebhookTriggerSetting(
            id=1, auto_reply_id=2, bot_id=1, enable=True, name="Time Trigger",
            event_type=WebhookTriggerEventType.TIME,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        keyword_trigger = WebhookTriggerSetting(
            id=2, auto_reply_id=1, bot_id=1, enable=True, name="Keyword Trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        # Test sorting
        trigger_settings = [time_trigger, keyword_trigger]  # TIME first, KEYWORD second
        auto_replies = {1: keyword_auto_reply, 2: time_auto_reply}
        
        sorted_triggers = sort_triggers_by_priority(trigger_settings, auto_replies)
        
        # KEYWORD should come first despite higher priority number (5 > 1)
        assert sorted_triggers[0].auto_reply_id == 1  # Keyword trigger
        assert sorted_triggers[1].auto_reply_id == 2  # Time trigger
    
    def test_priority_within_same_event_type(self):
        """Test priority sorting within same event type (lower number = higher priority)."""
        # Create multiple KEYWORD AutoReply objects with different priorities
        keyword_auto_reply_high = AutoReply(
            id=1, organization_id=1, name="High Priority Keyword", status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD, priority=1, keywords=["urgent"],
            trigger_schedule_type=None, trigger_schedule_settings=None,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        keyword_auto_reply_low = AutoReply(
            id=2, organization_id=1, name="Low Priority Keyword", status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD, priority=5, keywords=["hello"],
            trigger_schedule_type=None, trigger_schedule_settings=None,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        keyword_auto_reply_medium = AutoReply(
            id=3, organization_id=1, name="Medium Priority Keyword", status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD, priority=3, keywords=["info"],
            trigger_schedule_type=None, trigger_schedule_settings=None,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        # Create WebhookTriggerSettings (in random order)
        low_trigger = WebhookTriggerSetting(
            id=1, auto_reply_id=2, bot_id=1, enable=True, name="Low Priority Trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        high_trigger = WebhookTriggerSetting(
            id=2, auto_reply_id=1, bot_id=1, enable=True, name="High Priority Trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        medium_trigger = WebhookTriggerSetting(
            id=3, auto_reply_id=3, bot_id=1, enable=True, name="Medium Priority Trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        # Test sorting
        trigger_settings = [low_trigger, high_trigger, medium_trigger]  # Random order
        auto_replies = {1: keyword_auto_reply_high, 2: keyword_auto_reply_low, 3: keyword_auto_reply_medium}
        
        sorted_triggers = sort_triggers_by_priority(trigger_settings, auto_replies)
        
        # Should be sorted by priority: 1 (high) < 3 (medium) < 5 (low)
        assert sorted_triggers[0].auto_reply_id == 1  # priority=1
        assert sorted_triggers[1].auto_reply_id == 3  # priority=3
        assert sorted_triggers[2].auto_reply_id == 2  # priority=5
    
    def test_mixed_event_types_with_priorities(self):
        """Test sorting with mixed event types and different priorities."""
        # Create mixed AutoReply objects
        keyword_low_priority = AutoReply(
            id=1, organization_id=1, name="Low Priority Keyword", status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD, priority=10, keywords=["hello"],
            trigger_schedule_type=None, trigger_schedule_settings=None,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        time_high_priority = AutoReply(
            id=2, organization_id=1, name="High Priority Time", status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.TIME, priority=1, keywords=None,
            trigger_schedule_type=None, trigger_schedule_settings=None,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        keyword_high_priority = AutoReply(
            id=3, organization_id=1, name="High Priority Keyword", status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD, priority=2, keywords=["urgent"],
            trigger_schedule_type=None, trigger_schedule_settings=None,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        time_low_priority = AutoReply(
            id=4, organization_id=1, name="Low Priority Time", status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.TIME, priority=5, keywords=None,
            trigger_schedule_type=None, trigger_schedule_settings=None,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        # Create corresponding trigger settings
        triggers = [
            WebhookTriggerSetting(id=1, auto_reply_id=1, bot_id=1, enable=True, name="Keyword Low",
                                event_type=WebhookTriggerEventType.MESSAGE, created_at=datetime.now(), updated_at=datetime.now()),
            WebhookTriggerSetting(id=2, auto_reply_id=2, bot_id=1, enable=True, name="Time High",
                                event_type=WebhookTriggerEventType.TIME, created_at=datetime.now(), updated_at=datetime.now()),
            WebhookTriggerSetting(id=3, auto_reply_id=3, bot_id=1, enable=True, name="Keyword High",
                                event_type=WebhookTriggerEventType.MESSAGE, created_at=datetime.now(), updated_at=datetime.now()),
            WebhookTriggerSetting(id=4, auto_reply_id=4, bot_id=1, enable=True, name="Time Low",
                                event_type=WebhookTriggerEventType.TIME, created_at=datetime.now(), updated_at=datetime.now()),
        ]
        
        auto_replies = {
            1: keyword_low_priority, 2: time_high_priority,
            3: keyword_high_priority, 4: time_low_priority
        }
        
        sorted_triggers = sort_triggers_by_priority(triggers, auto_replies)
        
        # Expected order: KEYWORD (priority 2) > KEYWORD (priority 10) > TIME (priority 1) > TIME (priority 5)
        assert sorted_triggers[0].auto_reply_id == 3  # KEYWORD, priority=2
        assert sorted_triggers[1].auto_reply_id == 1  # KEYWORD, priority=10
        assert sorted_triggers[2].auto_reply_id == 2  # TIME, priority=1
        assert sorted_triggers[3].auto_reply_id == 4  # TIME, priority=5
    
    def test_missing_auto_reply_handled_gracefully(self):
        """Test that missing AutoReply entries are handled gracefully (lowest priority)."""
        keyword_auto_reply = AutoReply(
            id=1, organization_id=1, name="Valid Keyword", status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.KEYWORD, priority=5, keywords=["hello"],
            trigger_schedule_type=None, trigger_schedule_settings=None,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        valid_trigger = WebhookTriggerSetting(
            id=1, auto_reply_id=1, bot_id=1, enable=True, name="Valid Trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        invalid_trigger = WebhookTriggerSetting(
            id=2, auto_reply_id=999, bot_id=1, enable=True, name="Invalid Trigger",  # auto_reply_id not in map
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        trigger_settings = [invalid_trigger, valid_trigger]  # Invalid first
        auto_replies = {1: keyword_auto_reply}  # Missing ID 999
        
        sorted_triggers = sort_triggers_by_priority(trigger_settings, auto_replies)
        
        # Valid trigger should come first, invalid should be last
        assert sorted_triggers[0].auto_reply_id == 1   # Valid trigger
        assert sorted_triggers[1].auto_reply_id == 999 # Invalid trigger (lowest priority)
    
    def test_empty_lists(self):
        """Test edge case with empty inputs."""
        result = sort_triggers_by_priority([], {})
        assert result == []
        
        # Empty auto_replies with triggers should put all triggers at end
        trigger = WebhookTriggerSetting(
            id=1, auto_reply_id=1, bot_id=1, enable=True, name="Trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        result = sort_triggers_by_priority([trigger], {})
        assert len(result) == 1
        assert result[0].auto_reply_id == 1