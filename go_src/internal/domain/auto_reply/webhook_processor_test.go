package auto_reply

import (
	"testing"
	"time"
)

func TestWebhookProcessor_ProcessWebhookEvent(t *testing.T) {
	processor := NewWebhookProcessor()
	timezone := time.UTC

	tests := []struct {
		name          string
		event         *WebhookEvent
		autoReplies   []*AutoReply
		businessHours []*BusinessHour
		expectMatch   bool
		expectPriority AutoReplyPriority
		expectError   bool
		description   string
	}{
		// PRD Complete Priority System Tests
		{
			name: "complete_priority_test_ig_story_keyword_wins",
			event: &WebhookEvent{
				ID:          "event1",
				EventType:   WebhookEventTypeMessage,
				ChannelType: BotTypeInstagram,
				MessageText: "hello",
				IGStoryID:   stringPtr("story123"),
				Timestamp:   time.Now(),
			},
			autoReplies: []*AutoReply{
				{
					ID:       1,
					Name:     "General Time",
					Status:   AutoReplyStatusActive,
					TriggerScheduleType: stringToScheduleType(WebhookTriggerScheduleTypeDaily),
				},
				{
					ID:       2,
					Name:     "General Keyword",
					Status:   AutoReplyStatusActive,
					Keywords: []string{"hello"},
				},
				{
					ID:         3,
					Name:       "IG Story General",
					Status:     AutoReplyStatusActive,
					IGStoryIDs: []string{"story123"},
					TriggerScheduleType: stringToScheduleType(WebhookTriggerScheduleTypeDaily),
				},
				{
					ID:         4,
					Name:       "IG Story Keyword",
					Status:     AutoReplyStatusActive,
					Keywords:   []string{"hello"},
					IGStoryIDs: []string{"story123"},
				},
			},
			expectMatch:    true,
			expectPriority: AutoReplyPriorityIGStoryKeyword,
			description:    "Complete-Priority-Test1: IG Story Keyword should win",
		},

		// PRD Message Content Handling Tests
		{
			name: "message_content_keyword_match",
			event: &WebhookEvent{
				ID:          "event2",
				EventType:   WebhookEventTypeMessage,
				ChannelType: BotTypeLine,
				MessageText: "hello",
				Timestamp:   time.Now(),
			},
			autoReplies: []*AutoReply{
				{
					ID:       1,
					Name:     "Test Keyword",
					Status:   AutoReplyStatusActive,
					Keywords: []string{"hello"},
				},
			},
			expectMatch:    true,
			expectPriority: AutoReplyPriorityGeneralKeyword,
			description:    "Message-Content-Test1: Keyword reply triggered",
		},
		{
			name: "message_content_no_keyword_match",
			event: &WebhookEvent{
				ID:          "event3",
				EventType:   WebhookEventTypeMessage,
				ChannelType: BotTypeLine,
				MessageText: "goodbye",
				Timestamp:   time.Now(),
			},
			autoReplies: []*AutoReply{
				{
					ID:       1,
					Name:     "Test Keyword",
					Status:   AutoReplyStatusActive,
					Keywords: []string{"hello"},
				},
			},
			expectMatch: false,
			description: "Message-Content-Test2: No keyword match",
		},
		{
			name: "message_content_general_reply_any_content",
			event: &WebhookEvent{
				ID:          "event4",
				EventType:   WebhookEventTypeMessage,
				ChannelType: BotTypeLine,
				MessageText: "any content",
				Timestamp:   time.Now(),
			},
			autoReplies: []*AutoReply{
				{
					ID:     1,
					Name:   "General Time",
					Status: AutoReplyStatusActive,
					TriggerScheduleType: stringToScheduleType(WebhookTriggerScheduleTypeDaily),
					TriggerScheduleSettings: &WebhookTriggerScheduleSettings{
						Schedules: []WebhookTriggerSchedule{
							&DailySchedule{
								StartTime: "00:00",
								EndTime:   "23:59",
							},
						},
					},
				},
			},
			expectMatch:    true,
			expectPriority: AutoReplyPriorityGeneralTime,
			description:    "Message-Content-Test3: General reply regardless of content",
		},

		// PRD IG Story Priority Tests
		{
			name: "ig_story_priority_over_general",
			event: &WebhookEvent{
				ID:          "event5",
				EventType:   WebhookEventTypeMessage,
				ChannelType: BotTypeInstagram,
				MessageText: "hello",
				IGStoryID:   stringPtr("story123"),
				Timestamp:   time.Now(),
			},
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
			},
			expectMatch:    true,
			expectPriority: AutoReplyPriorityIGStoryKeyword,
			description:    "IG-Story-Priority-Test1: IG Story keyword over general",
		},

		// Edge Cases
		{
			name:        "nil_event",
			event:       nil,
			autoReplies: []*AutoReply{},
			expectMatch: false,
			expectError: true,
			description: "Nil event should return error",
		},
		{
			name: "empty_auto_replies",
			event: &WebhookEvent{
				ID:          "event6",
				EventType:   WebhookEventTypeMessage,
				ChannelType: BotTypeLine,
				MessageText: "hello",
				Timestamp:   time.Now(),
			},
			autoReplies: []*AutoReply{},
			expectMatch: false,
			description: "Empty auto-replies should not match",
		},
		{
			name: "inactive_auto_replies",
			event: &WebhookEvent{
				ID:          "event7",
				EventType:   WebhookEventTypeMessage,
				ChannelType: BotTypeLine,
				MessageText: "hello",
				Timestamp:   time.Now(),
			},
			autoReplies: []*AutoReply{
				{
					ID:       1,
					Name:     "Inactive Rule",
					Status:   AutoReplyStatusInactive,
					Keywords: []string{"hello"},
				},
			},
			expectMatch: false,
			description: "Inactive auto-replies should not match",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := processor.ProcessWebhookEvent(tt.event, tt.autoReplies, tt.businessHours, timezone)
			
			if tt.expectError {
				if result.Success {
					t.Errorf("ProcessWebhookEvent() should have failed for %s", tt.description)
				}
				return
			}
			
			if !result.Success {
				t.Errorf("ProcessWebhookEvent() failed unexpectedly: %s. Description: %s", 
					result.Error, tt.description)
				return
			}
			
			if result.HasMatch != tt.expectMatch {
				t.Errorf("ProcessWebhookEvent() match = %v, want %v. Reason: %s. Description: %s", 
					result.HasMatch, tt.expectMatch, result.Reason, tt.description)
				return
			}
			
			if tt.expectMatch && result.Priority != tt.expectPriority {
				t.Errorf("ProcessWebhookEvent() priority = %v, want %v. Description: %s", 
					result.Priority, tt.expectPriority, tt.description)
			}
		})
	}
}

func TestWebhookProcessor_ProcessWebhookEventSimple(t *testing.T) {
	processor := NewWebhookProcessor()

	event := &WebhookEvent{
		ID:          "simple_event",
		EventType:   WebhookEventTypeMessage,
		ChannelType: BotTypeLine,
		MessageText: "hello",
		Timestamp:   time.Now(),
	}

	autoReplies := []*AutoReply{
		{
			ID:       1,
			Name:     "Simple Test",
			Status:   AutoReplyStatusActive,
			Keywords: []string{"hello"},
		},
	}

	result := processor.ProcessWebhookEventSimple(event, autoReplies)

	if !result.Success {
		t.Errorf("ProcessWebhookEventSimple() failed: %s", result.Error)
		return
	}

	if !result.HasMatch {
		t.Errorf("ProcessWebhookEventSimple() should have matched")
		return
	}

	if result.Priority != AutoReplyPriorityGeneralKeyword {
		t.Errorf("ProcessWebhookEventSimple() priority = %v, want %v", 
			result.Priority, AutoReplyPriorityGeneralKeyword)
	}
}

func TestWebhookProcessor_ValidateAutoReplyConfiguration(t *testing.T) {
	processor := NewWebhookProcessor()

	tests := []struct {
		name           string
		autoReplies    []*AutoReply
		expectValid    bool
		expectWarnings int
		description    string
	}{
		{
			name:        "empty_configuration",
			autoReplies: []*AutoReply{},
			expectValid: true,
			description: "Empty configuration should be valid",
		},
		{
			name: "valid_configuration",
			autoReplies: []*AutoReply{
				{
					ID:       1,
					Name:     "Rule 1",
					Status:   AutoReplyStatusActive,
					Keywords: []string{"hello"},
				},
				{
					ID:       2,
					Name:     "Rule 2",
					Status:   AutoReplyStatusActive,
					Keywords: []string{"hi"},
				},
			},
			expectValid: true,
			description: "Valid configuration should be valid",
		},
		{
			name: "conflicting_keywords",
			autoReplies: []*AutoReply{
				{
					ID:       1,
					Name:     "General Rule",
					Status:   AutoReplyStatusActive,
					Keywords: []string{"hello"},
				},
				{
					ID:         2,
					Name:       "IG Story Rule",
					Status:     AutoReplyStatusActive,
					Keywords:   []string{"hello"},
					IGStoryIDs: []string{"story123"},
				},
			},
			expectValid:    false,
			expectWarnings: 1,
			description:    "Conflicting keywords should generate warnings",
		},
		{
			name: "inactive_rules_ignored",
			autoReplies: []*AutoReply{
				{
					ID:       1,
					Name:     "Active Rule",
					Status:   AutoReplyStatusActive,
					Keywords: []string{"hello"},
				},
				{
					ID:       2,
					Name:     "Inactive Rule",
					Status:   AutoReplyStatusInactive,
					Keywords: []string{"hello"},
				},
			},
			expectValid: true,
			description: "Inactive rules should be ignored in validation",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := processor.ValidateAutoReplyConfiguration(tt.autoReplies)
			
			if result.Valid != tt.expectValid {
				t.Errorf("ValidateAutoReplyConfiguration() valid = %v, want %v. Description: %s", 
					result.Valid, tt.expectValid, tt.description)
			}
			
			if len(result.Warnings) != tt.expectWarnings {
				t.Errorf("ValidateAutoReplyConfiguration() warnings = %v, want %v. Description: %s", 
					len(result.Warnings), tt.expectWarnings, tt.description)
			}
		})
	}
}

func TestWebhookProcessor_CreateWebhookEvent(t *testing.T) {
	processor := NewWebhookProcessor()
	
	timestamp := time.Now()
	extra := map[string]any{"platform": "line"}
	
	event := processor.CreateWebhookEvent(
		"test_id",
		WebhookEventTypeMessage,
		BotTypeLine,
		123,
		"user456",
		"hello world",
		stringPtr("story789"),
		timestamp,
		extra,
	)

	if event.ID != "test_id" {
		t.Errorf("CreateWebhookEvent() ID = %v, want %v", event.ID, "test_id")
	}
	
	if event.EventType != WebhookEventTypeMessage {
		t.Errorf("CreateWebhookEvent() EventType = %v, want %v", event.EventType, WebhookEventTypeMessage)
	}
	
	if event.ChannelType != BotTypeLine {
		t.Errorf("CreateWebhookEvent() ChannelType = %v, want %v", event.ChannelType, BotTypeLine)
	}
	
	if event.MessageText != "hello world" {
		t.Errorf("CreateWebhookEvent() MessageText = %v, want %v", event.MessageText, "hello world")
	}
	
	if event.IGStoryID == nil || *event.IGStoryID != "story789" {
		t.Errorf("CreateWebhookEvent() IGStoryID = %v, want %v", event.IGStoryID, "story789")
	}
	
	if !event.Timestamp.Equal(timestamp) {
		t.Errorf("CreateWebhookEvent() Timestamp = %v, want %v", event.Timestamp, timestamp)
	}
	
	if event.Extra["platform"] != "line" {
		t.Errorf("CreateWebhookEvent() Extra[platform] = %v, want %v", event.Extra["platform"], "line")
	}
}

func TestWebhookProcessor_GetProcessingStats(t *testing.T) {
	processor := NewWebhookProcessor()

	results := []*WebhookProcessResult{
		{
			Success:  true,
			HasMatch: true,
			Priority: AutoReplyPriorityIGStoryKeyword,
			MatchType: "ig_story_keyword",
		},
		{
			Success:  true,
			HasMatch: true,
			Priority: AutoReplyPriorityGeneralKeyword,
			MatchType: "general_keyword",
		},
		{
			Success:  true,
			HasMatch: false,
		},
		{
			Success: false,
		},
	}

	stats := processor.GetProcessingStats(results)

	if stats.TotalEvents != 4 {
		t.Errorf("GetProcessingStats() TotalEvents = %v, want %v", stats.TotalEvents, 4)
	}
	
	if stats.SuccessfulEvents != 3 {
		t.Errorf("GetProcessingStats() SuccessfulEvents = %v, want %v", stats.SuccessfulEvents, 3)
	}
	
	if stats.MatchedEvents != 2 {
		t.Errorf("GetProcessingStats() MatchedEvents = %v, want %v", stats.MatchedEvents, 2)
	}
	
	if stats.FailedEvents != 1 {
		t.Errorf("GetProcessingStats() FailedEvents = %v, want %v", stats.FailedEvents, 1)
	}
	
	if stats.PriorityBreakdown[AutoReplyPriorityIGStoryKeyword] != 1 {
		t.Errorf("GetProcessingStats() PriorityBreakdown[IGStoryKeyword] = %v, want %v", 
			stats.PriorityBreakdown[AutoReplyPriorityIGStoryKeyword], 1)
	}
	
	if stats.MatchTypeBreakdown["general_keyword"] != 1 {
		t.Errorf("GetProcessingStats() MatchTypeBreakdown[general_keyword] = %v, want %v", 
			stats.MatchTypeBreakdown["general_keyword"], 1)
	}
}

func TestWebhookProcessResult_Methods(t *testing.T) {
	t.Run("successful_match", func(t *testing.T) {
		result := &WebhookProcessResult{
			Success:  true,
			HasMatch: true,
			Priority: AutoReplyPriorityIGStoryKeyword,
			MatchedAutoReply: &AutoReply{
				ID:   1,
				Name: "Test Rule",
			},
		}
		
		if !result.IsSuccessful() {
			t.Error("IsSuccessful() should return true")
		}
		
		if !result.ShouldTriggerAutoReply() {
			t.Error("ShouldTriggerAutoReply() should return true")
		}
		
		description := result.GetPriorityDescription()
		if description != "IG Story Keyword (Highest Priority)" {
			t.Errorf("GetPriorityDescription() = %v, want %v", description, "IG Story Keyword (Highest Priority)")
		}
		
		summary := result.GetSummary()
		expected := "Matched auto-reply 'Test Rule' with IG Story Keyword (Highest Priority) priority"
		if summary != expected {
			t.Errorf("GetSummary() = %v, want %v", summary, expected)
		}
	})

	t.Run("failed_processing", func(t *testing.T) {
		result := &WebhookProcessResult{
			Success: false,
			Error:   "test error",
		}
		
		if result.IsSuccessful() {
			t.Error("IsSuccessful() should return false")
		}
		
		if result.ShouldTriggerAutoReply() {
			t.Error("ShouldTriggerAutoReply() should return false")
		}
		
		summary := result.GetSummary()
		expected := "Processing failed: test error"
		if summary != expected {
			t.Errorf("GetSummary() = %v, want %v", summary, expected)
		}
	})

	t.Run("no_match", func(t *testing.T) {
		result := &WebhookProcessResult{
			Success:  true,
			HasMatch: false,
			Reason:   "no matching rules",
		}
		
		if !result.IsSuccessful() {
			t.Error("IsSuccessful() should return true")
		}
		
		if result.ShouldTriggerAutoReply() {
			t.Error("ShouldTriggerAutoReply() should return false")
		}
		
		description := result.GetPriorityDescription()
		if description != "No match" {
			t.Errorf("GetPriorityDescription() = %v, want %v", description, "No match")
		}
		
		summary := result.GetSummary()
		expected := "No match found: no matching rules"
		if summary != expected {
			t.Errorf("GetSummary() = %v, want %v", summary, expected)
		}
	})
}