package auto_reply

import (
	"testing"
)

func TestTriggerValidator_ValidateTrigger(t *testing.T) {
	validator := NewTriggerValidator()

	tests := []struct {
		name        string
		autoReply   *AutoReply
		event       *WebhookEvent
		shouldMatch bool
		expectedPriority AutoReplyPriority
		description string
	}{
		// PRD Test Cases from Story 1: Keyword Reply Logic
		{
			name: "keyword_exact_match",
			autoReply: &AutoReply{
				ID:     1,
				Status: AutoReplyStatusActive,
				Keywords: []string{"hello"},
			},
			event: &WebhookEvent{
				EventType:   WebhookEventTypeMessage,
				MessageText: "hello",
				ChannelType: BotTypeLine,
			},
			shouldMatch: true,
			expectedPriority: AutoReplyPriorityGeneralKeyword,
			description: "B-P0-7-Test2: exact keyword match",
		},
		{
			name: "keyword_case_insensitive",
			autoReply: &AutoReply{
				ID:     1,
				Status: AutoReplyStatusActive,
				Keywords: []string{"hello"},
			},
			event: &WebhookEvent{
				EventType:   WebhookEventTypeMessage,
				MessageText: "HELLO",
				ChannelType: BotTypeLine,
			},
			shouldMatch: true,
			expectedPriority: AutoReplyPriorityGeneralKeyword,
			description: "B-P0-7-Test2: case insensitive match",
		},
		{
			name: "keyword_with_spaces",
			autoReply: &AutoReply{
				ID:     1,
				Status: AutoReplyStatusActive,
				Keywords: []string{"hello"},
			},
			event: &WebhookEvent{
				EventType:   WebhookEventTypeMessage,
				MessageText: " hello ",
				ChannelType: BotTypeLine,
			},
			shouldMatch: true,
			expectedPriority: AutoReplyPriorityGeneralKeyword,
			description: "B-P0-7-Test3: spaces trimmed",
		},
		{
			name: "keyword_partial_match_fails",
			autoReply: &AutoReply{
				ID:     1,
				Status: AutoReplyStatusActive,
				Keywords: []string{"hello"},
			},
			event: &WebhookEvent{
				EventType:   WebhookEventTypeMessage,
				MessageText: "hello world",
				ChannelType: BotTypeLine,
			},
			shouldMatch: false,
			description: "B-P0-7-Test4: partial match should fail",
		},
		{
			name: "keyword_close_variation_fails",
			autoReply: &AutoReply{
				ID:     1,
				Status: AutoReplyStatusActive,
				Keywords: []string{"hello"},
			},
			event: &WebhookEvent{
				EventType:   WebhookEventTypeMessage,
				MessageText: "helo",
				ChannelType: BotTypeLine,
			},
			shouldMatch: false,
			description: "B-P0-7-Test5: close variation should fail",
		},

		// PRD Test Cases from Story 2: Multiple Keywords Support
		{
			name: "multiple_keywords_first_match",
			autoReply: &AutoReply{
				ID:     1,
				Status: AutoReplyStatusActive,
				Keywords: []string{"hello", "hi", "hey"},
			},
			event: &WebhookEvent{
				EventType:   WebhookEventTypeMessage,
				MessageText: "hello",
				ChannelType: BotTypeLine,
			},
			shouldMatch: true,
			expectedPriority: AutoReplyPriorityGeneralKeyword,
			description: "Multiple-Keywords-Test1: first keyword match",
		},
		{
			name: "multiple_keywords_second_match",
			autoReply: &AutoReply{
				ID:     1,
				Status: AutoReplyStatusActive,
				Keywords: []string{"hello", "hi", "hey"},
			},
			event: &WebhookEvent{
				EventType:   WebhookEventTypeMessage,
				MessageText: "hi",
				ChannelType: BotTypeLine,
			},
			shouldMatch: true,
			expectedPriority: AutoReplyPriorityGeneralKeyword,
			description: "Multiple-Keywords-Test1: second keyword match",
		},
		{
			name: "multiple_keywords_case_insensitive",
			autoReply: &AutoReply{
				ID:     1,
				Status: AutoReplyStatusActive,
				Keywords: []string{"hello", "hi", "hey"},
			},
			event: &WebhookEvent{
				EventType:   WebhookEventTypeMessage,
				MessageText: "HI",
				ChannelType: BotTypeLine,
			},
			shouldMatch: true,
			expectedPriority: AutoReplyPriorityGeneralKeyword,
			description: "Multiple-Keywords-Test2: case insensitive",
		},
		{
			name: "multiple_keywords_no_match",
			autoReply: &AutoReply{
				ID:     1,
				Status: AutoReplyStatusActive,
				Keywords: []string{"hello", "hi", "hey"},
			},
			event: &WebhookEvent{
				EventType:   WebhookEventTypeMessage,
				MessageText: "goodbye",
				ChannelType: BotTypeLine,
			},
			shouldMatch: false,
			description: "Multiple-Keywords-Test3: no match",
		},

		// PRD Test Cases from Story 6: IG Story Keyword Logic
		{
			name: "ig_story_keyword_match",
			autoReply: &AutoReply{
				ID:         1,
				Status:     AutoReplyStatusActive,
				Keywords:   []string{"hello"},
				IGStoryIDs: []string{"story123"},
			},
			event: &WebhookEvent{
				EventType:   WebhookEventTypeMessage,
				MessageText: "hello",
				ChannelType: BotTypeInstagram,
				IGStoryID:   stringPtr("story123"),
			},
			shouldMatch: true,
			expectedPriority: AutoReplyPriorityIGStoryKeyword,
			description: "IG-Story-Keyword-Test1: IG story keyword match",
		},
		{
			name: "ig_story_keyword_wrong_story",
			autoReply: &AutoReply{
				ID:         1,
				Status:     AutoReplyStatusActive,
				Keywords:   []string{"hello"},
				IGStoryIDs: []string{"story123"},
			},
			event: &WebhookEvent{
				EventType:   WebhookEventTypeMessage,
				MessageText: "hello",
				ChannelType: BotTypeInstagram,
				IGStoryID:   stringPtr("story456"),
			},
			shouldMatch: false,
			description: "IG-Story-Keyword-Test2: wrong story ID",
		},
		{
			name: "ig_story_keyword_no_story_context",
			autoReply: &AutoReply{
				ID:         1,
				Status:     AutoReplyStatusActive,
				Keywords:   []string{"hello"},
				IGStoryIDs: []string{"story123"},
			},
			event: &WebhookEvent{
				EventType:   WebhookEventTypeMessage,
				MessageText: "hello",
				ChannelType: BotTypeInstagram,
				IGStoryID:   nil,
			},
			shouldMatch: false,
			description: "IG-Story-Keyword-Test3: no story context",
		},

		// PRD Test Cases from Story 7: IG Story General Logic
		{
			name: "ig_story_general_match",
			autoReply: &AutoReply{
				ID:         1,
				Status:     AutoReplyStatusActive,
				IGStoryIDs: []string{"story123"},
				TriggerScheduleType: stringToScheduleType(WebhookTriggerScheduleTypeDaily),
			},
			event: &WebhookEvent{
				EventType:   WebhookEventTypeMessage,
				MessageText: "any message",
				ChannelType: BotTypeInstagram,
				IGStoryID:   stringPtr("story123"),
			},
			shouldMatch: true,
			expectedPriority: AutoReplyPriorityIGStoryGeneral,
			description: "IG-Story-General-Test1: IG story general match",
		},

		// PRD Test Cases from Story 11: IG Story Exclusion Logic
		{
			name: "ig_story_exclusion_no_story_id",
			autoReply: &AutoReply{
				ID:         1,
				Status:     AutoReplyStatusActive,
				Keywords:   []string{"hello"},
				IGStoryIDs: []string{"story123"},
			},
			event: &WebhookEvent{
				EventType:   WebhookEventTypeMessage,
				MessageText: "hello",
				ChannelType: BotTypeInstagram,
				IGStoryID:   nil,
			},
			shouldMatch: false,
			description: "IG-Story-Exclusion-Test1: IG story specific setting without story ID",
		},

		// General Time-based triggers
		{
			name: "general_time_trigger",
			autoReply: &AutoReply{
				ID:     1,
				Status: AutoReplyStatusActive,
				TriggerScheduleType: stringToScheduleType(WebhookTriggerScheduleTypeDaily),
			},
			event: &WebhookEvent{
				EventType:   WebhookEventTypeMessage,
				MessageText: "any message",
				ChannelType: BotTypeLine,
			},
			shouldMatch: true,
			expectedPriority: AutoReplyPriorityGeneralTime,
			description: "General time-based trigger",
		},

		// Edge Cases
		{
			name: "inactive_auto_reply",
			autoReply: &AutoReply{
				ID:       1,
				Status:   AutoReplyStatusInactive,
				Keywords: []string{"hello"},
			},
			event: &WebhookEvent{
				EventType:   WebhookEventTypeMessage,
				MessageText: "hello",
				ChannelType: BotTypeLine,
			},
			shouldMatch: false,
			description: "inactive auto-reply should not match",
		},
		{
			name: "keyword_trigger_non_message_event",
			autoReply: &AutoReply{
				ID:       1,
				Status:   AutoReplyStatusActive,
				Keywords: []string{"hello"},
			},
			event: &WebhookEvent{
				EventType:   WebhookEventTypePostback,
				MessageText: "hello",
				ChannelType: BotTypeLine,
			},
			shouldMatch: false,
			description: "keyword triggers only support MESSAGE events",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := validator.ValidateTrigger(tt.autoReply, tt.event)
			
			if result.Matches != tt.shouldMatch {
				t.Errorf("ValidateTrigger() matches = %v, want %v. Reason: %s. Description: %s", 
					result.Matches, tt.shouldMatch, result.Reason, tt.description)
				return
			}
			
			if tt.shouldMatch && result.Priority != tt.expectedPriority {
				t.Errorf("ValidateTrigger() priority = %v, want %v. Description: %s", 
					result.Priority, tt.expectedPriority, tt.description)
			}
		})
	}
}

func TestTriggerValidator_ValidateMultipleTriggers(t *testing.T) {
	validator := NewTriggerValidator()

	// PRD Test Cases from Story 4: Priority Logic
	tests := []struct {
		name              string
		autoReplies       []*AutoReply
		event             *WebhookEvent
		shouldMatch       bool
		expectedPriority  AutoReplyPriority
		expectedAutoReply *AutoReply
		description       string
	}{
		{
			name: "keyword_over_general_priority",
			autoReplies: []*AutoReply{
				{
					ID:     1,
					Name:   "General Time",
					Status: AutoReplyStatusActive,
					TriggerScheduleType: stringToScheduleType(WebhookTriggerScheduleTypeDaily),
				},
				{
					ID:       2,
					Name:     "Keyword",
					Status:   AutoReplyStatusActive,
					Keywords: []string{"hello"},
				},
			},
			event: &WebhookEvent{
				EventType:   WebhookEventTypeMessage,
				MessageText: "hello",
				ChannelType: BotTypeLine,
			},
			shouldMatch: true,
			expectedPriority: AutoReplyPriorityGeneralKeyword,
			expectedAutoReply: &AutoReply{ID: 2, Name: "Keyword"},
			description: "Priority-Test1: Keyword takes precedence over general",
		},
		{
			name: "ig_story_keyword_highest_priority",
			autoReplies: []*AutoReply{
				{
					ID:       1,
					Name:     "General Keyword",
					Status:   AutoReplyStatusActive,
					Keywords: []string{"hello"},
				},
				{
					ID:         2,
					Name:       "IG Story Keyword",
					Status:     AutoReplyStatusActive,
					Keywords:   []string{"hello"},
					IGStoryIDs: []string{"story123"},
				},
				{
					ID:     3,
					Name:   "General Time",
					Status: AutoReplyStatusActive,
					TriggerScheduleType: stringToScheduleType(WebhookTriggerScheduleTypeDaily),
				},
			},
			event: &WebhookEvent{
				EventType:   WebhookEventTypeMessage,
				MessageText: "hello",
				ChannelType: BotTypeInstagram,
				IGStoryID:   stringPtr("story123"),
			},
			shouldMatch: true,
			expectedPriority: AutoReplyPriorityIGStoryKeyword,
			expectedAutoReply: &AutoReply{ID: 2, Name: "IG Story Keyword"},
			description: "Complete-Priority-Test1: IG story keyword has highest priority",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := validator.ValidateMultipleTriggers(tt.autoReplies, tt.event)
			
			if result.Matches != tt.shouldMatch {
				t.Errorf("ValidateMultipleTriggers() matches = %v, want %v. Reason: %s", 
					result.Matches, tt.shouldMatch, result.Reason)
				return
			}
			
			if tt.shouldMatch {
				if result.Priority != tt.expectedPriority {
					t.Errorf("ValidateMultipleTriggers() priority = %v, want %v", 
						result.Priority, tt.expectedPriority)
				}
				if result.AutoReply.ID != tt.expectedAutoReply.ID {
					t.Errorf("ValidateMultipleTriggers() autoReply.ID = %v, want %v", 
						result.AutoReply.ID, tt.expectedAutoReply.ID)
				}
			}
		})
	}
}

func TestTriggerValidator_EdgeCases(t *testing.T) {
	validator := NewTriggerValidator()

	t.Run("nil_auto_reply", func(t *testing.T) {
		event := &WebhookEvent{
			EventType:   WebhookEventTypeMessage,
			MessageText: "hello",
			ChannelType: BotTypeLine,
		}
		
		result := validator.ValidateTrigger(nil, event)
		if result.Matches {
			t.Error("ValidateTrigger() with nil autoReply should not match")
		}
	})

	t.Run("nil_event", func(t *testing.T) {
		autoReply := &AutoReply{
			ID:       1,
			Status:   AutoReplyStatusActive,
			Keywords: []string{"hello"},
		}
		
		result := validator.ValidateTrigger(autoReply, nil)
		if result.Matches {
			t.Error("ValidateTrigger() with nil event should not match")
		}
	})

	t.Run("empty_auto_replies_list", func(t *testing.T) {
		event := &WebhookEvent{
			EventType:   WebhookEventTypeMessage,
			MessageText: "hello",
			ChannelType: BotTypeLine,
		}
		
		result := validator.ValidateMultipleTriggers([]*AutoReply{}, event)
		if result.Matches {
			t.Error("ValidateMultipleTriggers() with empty list should not match")
		}
	})
}

