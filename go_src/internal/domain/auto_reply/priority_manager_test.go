package auto_reply

import (
	"testing"
)

func TestPriorityManager_CalculatePriority(t *testing.T) {
	manager := NewPriorityManager()

	tests := []struct {
		name              string
		autoReply         *AutoReply
		event             *WebhookEvent
		expectedPriority  AutoReplyPriority
		expectedContext   string
		shouldBeNil       bool
		description       string
	}{
		// PRD Test Cases from Story 10: Complete Priority System
		{
			name: "ig_story_keyword_highest",
			autoReply: &AutoReply{
				ID:         1,
				Keywords:   []string{"hello"},
				IGStoryIDs: []string{"story123"},
			},
			event: &WebhookEvent{
				EventType:   WebhookEventTypeMessage,
				MessageText: "hello",
				ChannelType: BotTypeInstagram,
				IGStoryID:   stringPtr("story123"),
			},
			expectedPriority: AutoReplyPriorityIGStoryKeyword,
			expectedContext:  "IG Story + Keyword match",
			description:      "Complete-Priority-Test1: IG story keyword highest priority",
		},
		{
			name: "ig_story_general_second",
			autoReply: &AutoReply{
				ID:         2,
				IGStoryIDs: []string{"story123"},
				TriggerScheduleType: stringToScheduleType(WebhookTriggerScheduleTypeDaily),
			},
			event: &WebhookEvent{
				EventType:   WebhookEventTypeMessage,
				MessageText: "any message",
				ChannelType: BotTypeInstagram,
				IGStoryID:   stringPtr("story123"),
			},
			expectedPriority: AutoReplyPriorityIGStoryGeneral,
			expectedContext:  "IG Story + General/Time match",
			description:      "Complete-Priority-Test2: IG story general second priority",
		},
		{
			name: "general_keyword_third",
			autoReply: &AutoReply{
				ID:       3,
				Keywords: []string{"hello"},
			},
			event: &WebhookEvent{
				EventType:   WebhookEventTypeMessage,
				MessageText: "hello",
				ChannelType: BotTypeLine,
			},
			expectedPriority: AutoReplyPriorityGeneralKeyword,
			expectedContext:  "General Keyword match",
			description:      "Complete-Priority-Test3: General keyword third priority",
		},
		{
			name: "general_time_lowest",
			autoReply: &AutoReply{
				ID: 4,
				TriggerScheduleType: stringToScheduleType(WebhookTriggerScheduleTypeDaily),
			},
			event: &WebhookEvent{
				EventType:   WebhookEventTypeMessage,
				MessageText: "any message",
				ChannelType: BotTypeLine,
			},
			expectedPriority: AutoReplyPriorityGeneralTime,
			expectedContext:  "General Time-based match",
			description:      "Complete-Priority-Test4: General time lowest priority",
		},
		{
			name: "ig_story_specific_wrong_story",
			autoReply: &AutoReply{
				ID:         5,
				Keywords:   []string{"hello"},
				IGStoryIDs: []string{"story123"},
			},
			event: &WebhookEvent{
				EventType:   WebhookEventTypeMessage,
				MessageText: "hello",
				ChannelType: BotTypeInstagram,
				IGStoryID:   stringPtr("story456"),
			},
			shouldBeNil: true,
			description: "IG story specific but wrong story context",
		},
		{
			name: "ig_story_specific_no_story_context",
			autoReply: &AutoReply{
				ID:         6,
				Keywords:   []string{"hello"},
				IGStoryIDs: []string{"story123"},
			},
			event: &WebhookEvent{
				EventType:   WebhookEventTypeMessage,
				MessageText: "hello",
				ChannelType: BotTypeInstagram,
				IGStoryID:   nil,
			},
			shouldBeNil: true,
			description: "IG story specific but no story context",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := manager.CalculatePriority(tt.autoReply, tt.event)
			
			if tt.shouldBeNil {
				if result != nil {
					t.Errorf("CalculatePriority() should return nil for %s", tt.description)
				}
				return
			}
			
			if result == nil {
				t.Errorf("CalculatePriority() should not return nil for %s", tt.description)
				return
			}
			
			if result.Priority != tt.expectedPriority {
				t.Errorf("CalculatePriority() priority = %v, want %v. Description: %s", 
					result.Priority, tt.expectedPriority, tt.description)
			}
			
			if result.Context != tt.expectedContext {
				t.Errorf("CalculatePriority() context = %v, want %v. Description: %s", 
					result.Context, tt.expectedContext, tt.description)
			}
		})
	}
}

func TestPriorityManager_SortByPriority(t *testing.T) {
	manager := NewPriorityManager()

	triggers := []*TriggerWithPriority{
		{
			AutoReply: &AutoReply{ID: 1, Name: "General Time"},
			Priority:  AutoReplyPriorityGeneralTime,
		},
		{
			AutoReply: &AutoReply{ID: 2, Name: "IG Story Keyword"},
			Priority:  AutoReplyPriorityIGStoryKeyword,
		},
		{
			AutoReply: &AutoReply{ID: 3, Name: "General Keyword"},
			Priority:  AutoReplyPriorityGeneralKeyword,
		},
		{
			AutoReply: &AutoReply{ID: 4, Name: "IG Story General"},
			Priority:  AutoReplyPriorityIGStoryGeneral,
		},
	}

	sorted := manager.SortByPriority(triggers)

	expectedOrder := []AutoReplyPriority{
		AutoReplyPriorityIGStoryKeyword,
		AutoReplyPriorityIGStoryGeneral,
		AutoReplyPriorityGeneralKeyword,
		AutoReplyPriorityGeneralTime,
	}

	if len(sorted) != len(expectedOrder) {
		t.Errorf("SortByPriority() length = %v, want %v", len(sorted), len(expectedOrder))
		return
	}

	for i, expected := range expectedOrder {
		if sorted[i].Priority != expected {
			t.Errorf("SortByPriority()[%d] priority = %v, want %v", i, sorted[i].Priority, expected)
		}
	}
}

func TestPriorityManager_GetHighestPriorityTrigger(t *testing.T) {
	manager := NewPriorityManager()

	triggers := []*TriggerWithPriority{
		{
			AutoReply: &AutoReply{ID: 1, Name: "General Time"},
			Priority:  AutoReplyPriorityGeneralTime,
		},
		{
			AutoReply: &AutoReply{ID: 2, Name: "IG Story Keyword"},
			Priority:  AutoReplyPriorityIGStoryKeyword,
		},
		{
			AutoReply: &AutoReply{ID: 3, Name: "General Keyword"},
			Priority:  AutoReplyPriorityGeneralKeyword,
		},
	}

	highest := manager.GetHighestPriorityTrigger(triggers)

	if highest == nil {
		t.Error("GetHighestPriorityTrigger() should not return nil")
		return
	}

	if highest.Priority != AutoReplyPriorityIGStoryKeyword {
		t.Errorf("GetHighestPriorityTrigger() priority = %v, want %v", 
			highest.Priority, AutoReplyPriorityIGStoryKeyword)
	}

	if highest.AutoReply.ID != 2 {
		t.Errorf("GetHighestPriorityTrigger() autoReply.ID = %v, want %v", 
			highest.AutoReply.ID, 2)
	}
}

func TestPriorityManager_FilterByPriorityLevel(t *testing.T) {
	manager := NewPriorityManager()

	triggers := []*TriggerWithPriority{
		{
			AutoReply: &AutoReply{ID: 1, Name: "General Time"},
			Priority:  AutoReplyPriorityGeneralTime,
		},
		{
			AutoReply: &AutoReply{ID: 2, Name: "IG Story Keyword"},
			Priority:  AutoReplyPriorityIGStoryKeyword,
		},
		{
			AutoReply: &AutoReply{ID: 3, Name: "General Keyword"},
			Priority:  AutoReplyPriorityGeneralKeyword,
		},
		{
			AutoReply: &AutoReply{ID: 4, Name: "Another General Keyword"},
			Priority:  AutoReplyPriorityGeneralKeyword,
		},
	}

	filtered := manager.FilterByPriorityLevel(triggers, AutoReplyPriorityGeneralKeyword)

	if len(filtered) != 2 {
		t.Errorf("FilterByPriorityLevel() length = %v, want %v", len(filtered), 2)
		return
	}

	for _, trigger := range filtered {
		if trigger.Priority != AutoReplyPriorityGeneralKeyword {
			t.Errorf("FilterByPriorityLevel() trigger priority = %v, want %v", 
				trigger.Priority, AutoReplyPriorityGeneralKeyword)
		}
	}
}

func TestPriorityManager_GroupByPriorityLevel(t *testing.T) {
	manager := NewPriorityManager()

	triggers := []*TriggerWithPriority{
		{
			AutoReply: &AutoReply{ID: 1, Name: "General Time"},
			Priority:  AutoReplyPriorityGeneralTime,
		},
		{
			AutoReply: &AutoReply{ID: 2, Name: "IG Story Keyword"},
			Priority:  AutoReplyPriorityIGStoryKeyword,
		},
		{
			AutoReply: &AutoReply{ID: 3, Name: "General Keyword 1"},
			Priority:  AutoReplyPriorityGeneralKeyword,
		},
		{
			AutoReply: &AutoReply{ID: 4, Name: "General Keyword 2"},
			Priority:  AutoReplyPriorityGeneralKeyword,
		},
	}

	groups := manager.GroupByPriorityLevel(triggers)

	if len(groups) != 3 {
		t.Errorf("GroupByPriorityLevel() groups count = %v, want %v", len(groups), 3)
	}

	if len(groups[AutoReplyPriorityGeneralKeyword]) != 2 {
		t.Errorf("GroupByPriorityLevel() general keyword count = %v, want %v", 
			len(groups[AutoReplyPriorityGeneralKeyword]), 2)
	}

	if len(groups[AutoReplyPriorityIGStoryKeyword]) != 1 {
		t.Errorf("GroupByPriorityLevel() IG story keyword count = %v, want %v", 
			len(groups[AutoReplyPriorityIGStoryKeyword]), 1)
	}

	if len(groups[AutoReplyPriorityGeneralTime]) != 1 {
		t.Errorf("GroupByPriorityLevel() general time count = %v, want %v", 
			len(groups[AutoReplyPriorityGeneralTime]), 1)
	}
}

func TestPriorityManager_ValidatePriorityConfiguration(t *testing.T) {
	manager := NewPriorityManager()

	tests := []struct {
		name           string
		autoReplies    []*AutoReply
		expectedWarnings int
		description    string
	}{
		{
			name: "no_conflicts",
			autoReplies: []*AutoReply{
				{
					ID:       1,
					Status:   AutoReplyStatusActive,
					Keywords: []string{"hello"},
				},
				{
					ID:       2,
					Status:   AutoReplyStatusActive,
					Keywords: []string{"hi"},
				},
			},
			expectedWarnings: 0,
			description:      "No conflicts should generate no warnings",
		},
		{
			name: "keyword_conflict_different_priorities",
			autoReplies: []*AutoReply{
				{
					ID:       1,
					Status:   AutoReplyStatusActive,
					Keywords: []string{"hello"},
				},
				{
					ID:         2,
					Status:     AutoReplyStatusActive,
					Keywords:   []string{"hello"},
					IGStoryIDs: []string{"story123"},
				},
			},
			expectedWarnings: 1,
			description:      "Same keyword with different priorities should generate warning",
		},
		{
			name: "inactive_auto_reply_ignored",
			autoReplies: []*AutoReply{
				{
					ID:       1,
					Status:   AutoReplyStatusActive,
					Keywords: []string{"hello"},
				},
				{
					ID:       2,
					Status:   AutoReplyStatusInactive,
					Keywords: []string{"hello"},
				},
			},
			expectedWarnings: 0,
			description:      "Inactive auto-replies should be ignored",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			warnings := manager.ValidatePriorityConfiguration(tt.autoReplies)
			
			if len(warnings) != tt.expectedWarnings {
				t.Errorf("ValidatePriorityConfiguration() warnings count = %v, want %v. Description: %s", 
					len(warnings), tt.expectedWarnings, tt.description)
			}
		})
	}
}

func TestPriorityManager_GetPriorityDescription(t *testing.T) {
	manager := NewPriorityManager()

	tests := []struct {
		priority AutoReplyPriority
		expected string
	}{
		{AutoReplyPriorityIGStoryKeyword, "IG Story Keyword (Highest Priority)"},
		{AutoReplyPriorityIGStoryGeneral, "IG Story General"},
		{AutoReplyPriorityGeneralKeyword, "General Keyword"},
		{AutoReplyPriorityGeneralTime, "General Time-based (Lowest Priority)"},
	}

	for _, tt := range tests {
		t.Run(tt.expected, func(t *testing.T) {
			result := manager.GetPriorityDescription(tt.priority)
			if result != tt.expected {
				t.Errorf("GetPriorityDescription() = %v, want %v", result, tt.expected)
			}
		})
	}
}

func TestPriorityManager_IsHigherPriority(t *testing.T) {
	manager := NewPriorityManager()

	tests := []struct {
		priority1 AutoReplyPriority
		priority2 AutoReplyPriority
		expected  bool
	}{
		{AutoReplyPriorityIGStoryKeyword, AutoReplyPriorityIGStoryGeneral, true},
		{AutoReplyPriorityIGStoryGeneral, AutoReplyPriorityGeneralKeyword, true},
		{AutoReplyPriorityGeneralKeyword, AutoReplyPriorityGeneralTime, true},
		{AutoReplyPriorityGeneralTime, AutoReplyPriorityGeneralKeyword, false},
		{AutoReplyPriorityGeneralKeyword, AutoReplyPriorityGeneralKeyword, false},
	}

	for _, tt := range tests {
		t.Run("priority_comparison", func(t *testing.T) {
			result := manager.IsHigherPriority(tt.priority1, tt.priority2)
			if result != tt.expected {
				t.Errorf("IsHigherPriority(%v, %v) = %v, want %v", 
					tt.priority1, tt.priority2, result, tt.expected)
			}
		})
	}
}

func TestPriorityManager_EdgeCases(t *testing.T) {
	manager := NewPriorityManager()

	t.Run("nil_auto_reply", func(t *testing.T) {
		event := &WebhookEvent{
			EventType:   WebhookEventTypeMessage,
			MessageText: "hello",
			ChannelType: BotTypeLine,
		}
		
		result := manager.CalculatePriority(nil, event)
		if result != nil {
			t.Error("CalculatePriority() with nil autoReply should return nil")
		}
	})

	t.Run("empty_triggers_list", func(t *testing.T) {
		highest := manager.GetHighestPriorityTrigger([]*TriggerWithPriority{})
		if highest != nil {
			t.Error("GetHighestPriorityTrigger() with empty list should return nil")
		}
	})

	t.Run("single_trigger", func(t *testing.T) {
		triggers := []*TriggerWithPriority{
			{
				AutoReply: &AutoReply{ID: 1, Name: "Single"},
				Priority:  AutoReplyPriorityGeneralKeyword,
			},
		}
		
		sorted := manager.SortByPriority(triggers)
		if len(sorted) != 1 {
			t.Error("SortByPriority() with single trigger should return single trigger")
		}
	})
}

