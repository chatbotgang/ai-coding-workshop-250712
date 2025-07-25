package auto_reply

import (
	"testing"
	"time"
)

// TestCompleteIntegration tests the complete auto-reply system end-to-end
// covering all PRD requirements and user stories.
func TestCompleteIntegration(t *testing.T) {
	processor := NewWebhookProcessor()
	timezone := time.UTC

	// Setup complete test scenario with all 4 priority levels
	autoReplies := []*AutoReply{
		// Priority 4: General Time-based (lowest)
		{
			ID:     1,
			Name:   "General Time Rule",
			Status: AutoReplyStatusActive,
			TriggerScheduleType: stringToScheduleType(WebhookTriggerScheduleTypeDaily),
			TriggerScheduleSettings: &WebhookTriggerScheduleSettings{
				Schedules: []WebhookTriggerSchedule{
					&DailySchedule{
						StartTime: "09:00",
						EndTime:   "17:00",
					},
				},
			},
		},
		// Priority 3: General Keyword
		{
			ID:       2,
			Name:     "General Keyword Rule",
			Status:   AutoReplyStatusActive,
			Keywords: []string{"hello", "hi", "hey"},
		},
		// Priority 2: IG Story General
		{
			ID:         3,
			Name:       "IG Story General Rule",
			Status:     AutoReplyStatusActive,
			IGStoryIDs: []string{"story123", "story456"},
			TriggerScheduleType: stringToScheduleType(WebhookTriggerScheduleTypeDaily),
			TriggerScheduleSettings: &WebhookTriggerScheduleSettings{
				Schedules: []WebhookTriggerSchedule{
					&DailySchedule{
						StartTime: "09:00",
						EndTime:   "17:00",
					},
				},
			},
		},
		// Priority 1: IG Story Keyword (highest)
		{
			ID:         4,
			Name:       "IG Story Keyword Rule",
			Status:     AutoReplyStatusActive,
			Keywords:   []string{"hello", "special"},
			IGStoryIDs: []string{"story123"},
		},
	}

	businessHours := []*BusinessHour{
		{
			Weekday:   1, // Monday
			StartTime: time.Date(0, 1, 1, 9, 0, 0, 0, time.UTC),
			EndTime:   time.Date(0, 1, 1, 17, 0, 0, 0, time.UTC),
		},
	}

	// Test all PRD scenarios
	testCases := []struct {
		name           string
		event          *WebhookEvent
		expectedMatch  bool
		expectedPriority AutoReplyPriority
		expectedRuleID int
		description    string
	}{
		// PRD Story 10: Complete Priority System Tests
		{
			name: "priority_1_ig_story_keyword",
			event: &WebhookEvent{
				ID:          "test1",
				EventType:   WebhookEventTypeMessage,
				ChannelType: BotTypeInstagram,
				MessageText: "hello",
				IGStoryID:   stringPtr("story123"),
				Timestamp:   time.Date(2024, 1, 15, 14, 0, 0, 0, timezone), // Monday 2PM
			},
			expectedMatch:    true,
			expectedPriority: AutoReplyPriorityIGStoryKeyword,
			expectedRuleID:   4,
			description:      "Priority 1: IG Story Keyword should have highest priority",
		},
		{
			name: "priority_2_ig_story_general",
			event: &WebhookEvent{
				ID:          "test2",
				EventType:   WebhookEventTypeMessage,
				ChannelType: BotTypeInstagram,
				MessageText: "random message",
				IGStoryID:   stringPtr("story456"),
				Timestamp:   time.Date(2024, 1, 15, 14, 0, 0, 0, timezone), // Monday 2PM
			},
			expectedMatch:    true,
			expectedPriority: AutoReplyPriorityIGStoryGeneral,
			expectedRuleID:   3,
			description:      "Priority 2: IG Story General when no keyword match",
		},
		{
			name: "priority_3_general_keyword",
			event: &WebhookEvent{
				ID:          "test3",
				EventType:   WebhookEventTypeMessage,
				ChannelType: BotTypeLine,
				MessageText: "hello",
				Timestamp:   time.Date(2024, 1, 15, 14, 0, 0, 0, timezone), // Monday 2PM
			},
			expectedMatch:    true,
			expectedPriority: AutoReplyPriorityGeneralKeyword,
			expectedRuleID:   2,
			description:      "Priority 3: General Keyword for non-IG Story messages",
		},
		{
			name: "priority_4_general_time",
			event: &WebhookEvent{
				ID:          "test4",
				EventType:   WebhookEventTypeMessage,
				ChannelType: BotTypeLine,
				MessageText: "random message",
				Timestamp:   time.Date(2024, 1, 15, 14, 0, 0, 0, timezone), // Monday 2PM
			},
			expectedMatch:    true,
			expectedPriority: AutoReplyPriorityGeneralTime,
			expectedRuleID:   1,
			description:      "Priority 4: General Time as fallback",
		},

		// PRD Story 1: Keyword normalization tests
		{
			name: "keyword_case_insensitive",
			event: &WebhookEvent{
				ID:          "test5",
				EventType:   WebhookEventTypeMessage,
				ChannelType: BotTypeLine,
				MessageText: "HELLO",
				Timestamp:   time.Date(2024, 1, 15, 14, 0, 0, 0, timezone),
			},
			expectedMatch:    true,
			expectedPriority: AutoReplyPriorityGeneralKeyword,
			expectedRuleID:   2,
			description:      "B-P0-7-Test2: Case insensitive keyword matching",
		},
		{
			name: "keyword_with_spaces",
			event: &WebhookEvent{
				ID:          "test6",
				EventType:   WebhookEventTypeMessage,
				ChannelType: BotTypeLine,
				MessageText: " hello ",
				Timestamp:   time.Date(2024, 1, 15, 14, 0, 0, 0, timezone),
			},
			expectedMatch:    true,
			expectedPriority: AutoReplyPriorityGeneralKeyword,
			expectedRuleID:   2,
			description:      "B-P0-7-Test3: Spaces are trimmed",
		},
		{
			name: "keyword_partial_match_fails",
			event: &WebhookEvent{
				ID:          "test7",
				EventType:   WebhookEventTypeMessage,
				ChannelType: BotTypeLine,
				MessageText: "hello world",
				Timestamp:   time.Date(2024, 1, 15, 14, 0, 0, 0, timezone),
			},
			expectedMatch:    true,
			expectedPriority: AutoReplyPriorityGeneralTime,
			expectedRuleID:   1,
			description:      "B-P0-7-Test4: Partial match fails, falls back to general time",
		},

		// PRD Story 2: Multiple keywords
		{
			name: "multiple_keywords_hi",
			event: &WebhookEvent{
				ID:          "test8",
				EventType:   WebhookEventTypeMessage,
				ChannelType: BotTypeLine,
				MessageText: "hi",
				Timestamp:   time.Date(2024, 1, 15, 14, 0, 0, 0, timezone),
			},
			expectedMatch:    true,
			expectedPriority: AutoReplyPriorityGeneralKeyword,
			expectedRuleID:   2,
			description:      "Multiple-Keywords-Test1: Second keyword matches",
		},

		// PRD Story 6: IG Story exclusion
		{
			name: "ig_story_exclusion",
			event: &WebhookEvent{
				ID:          "test9",
				EventType:   WebhookEventTypeMessage,
				ChannelType: BotTypeInstagram,
				MessageText: "hello",
				IGStoryID:   nil, // No story context
				Timestamp:   time.Date(2024, 1, 15, 14, 0, 0, 0, timezone),
			},
			expectedMatch:    true,
			expectedPriority: AutoReplyPriorityGeneralKeyword,
			expectedRuleID:   2,
			description:      "IG-Story-Exclusion-Test1: IG story rule excluded without story context",
		},

		// Edge cases
		{
			name: "outside_business_hours",
			event: &WebhookEvent{
				ID:          "test10",
				EventType:   WebhookEventTypeMessage,
				ChannelType: BotTypeLine,
				MessageText: "random message",
				Timestamp:   time.Date(2024, 1, 15, 20, 0, 0, 0, timezone), // Monday 8PM
			},
			expectedMatch: false,
			description:   "Outside business hours should not match time-based rules",
		},
		{
			name: "non_message_event",
			event: &WebhookEvent{
				ID:          "test11",
				EventType:   WebhookEventTypePostback,
				ChannelType: BotTypeLine,
				MessageText: "hello",
				Timestamp:   time.Date(2024, 1, 15, 14, 0, 0, 0, timezone),
			},
			expectedMatch: false,
			description:   "Non-message events should not match keyword triggers",
		},
	}

	// Execute all test cases
	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			result := processor.ProcessWebhookEvent(tc.event, autoReplies, businessHours, timezone)
			
			if !result.Success {
				t.Errorf("ProcessWebhookEvent() failed: %s. Description: %s", 
					result.Error, tc.description)
				return
			}
			
			if result.HasMatch != tc.expectedMatch {
				t.Errorf("ProcessWebhookEvent() match = %v, want %v. Reason: %s. Description: %s", 
					result.HasMatch, tc.expectedMatch, result.Reason, tc.description)
				return
			}
			
			if tc.expectedMatch {
				if result.Priority != tc.expectedPriority {
					t.Errorf("ProcessWebhookEvent() priority = %v, want %v. Description: %s", 
						result.Priority, tc.expectedPriority, tc.description)
				}
				
				if result.MatchedAutoReply.ID != tc.expectedRuleID {
					t.Errorf("ProcessWebhookEvent() matched rule ID = %v, want %v. Description: %s", 
						result.MatchedAutoReply.ID, tc.expectedRuleID, tc.description)
				}
			}
		})
	}
}

// TestConfigurationValidation tests the configuration validation functionality.
func TestConfigurationValidation(t *testing.T) {
	processor := NewWebhookProcessor()

	// Test configuration with conflicts
	conflictingRules := []*AutoReply{
		{
			ID:       1,
			Name:     "General Hello",
			Status:   AutoReplyStatusActive,
			Keywords: []string{"hello"},
		},
		{
			ID:         2,
			Name:       "IG Story Hello",
			Status:     AutoReplyStatusActive,
			Keywords:   []string{"hello"},
			IGStoryIDs: []string{"story123"},
		},
		{
			ID:       3,
			Name:     "Another General Hello",
			Status:   AutoReplyStatusActive,
			Keywords: []string{"hello"},
		},
	}

	result := processor.ValidateAutoReplyConfiguration(conflictingRules)
	
	if result.Valid {
		t.Error("ValidateAutoReplyConfiguration() should detect conflicts")
	}
	
	if len(result.Warnings) == 0 {
		t.Error("ValidateAutoReplyConfiguration() should generate warnings for conflicts")
	}
	
	if result.TotalRules != 3 {
		t.Errorf("ValidateAutoReplyConfiguration() TotalRules = %v, want %v", result.TotalRules, 3)
	}
	
	if result.ActiveRules != 3 {
		t.Errorf("ValidateAutoReplyConfiguration() ActiveRules = %v, want %v", result.ActiveRules, 3)
	}
}

// TestProcessingStats tests the processing statistics functionality.
func TestProcessingStats(t *testing.T) {
	processor := NewWebhookProcessor()
	timezone := time.UTC

	// Create test events
	events := []*WebhookEvent{
		{
			ID:          "stat1",
			EventType:   WebhookEventTypeMessage,
			ChannelType: BotTypeInstagram,
			MessageText: "hello",
			IGStoryID:   stringPtr("story123"),
			Timestamp:   time.Date(2024, 1, 15, 14, 0, 0, 0, timezone),
		},
		{
			ID:          "stat2",
			EventType:   WebhookEventTypeMessage,
			ChannelType: BotTypeLine,
			MessageText: "hello",
			Timestamp:   time.Date(2024, 1, 15, 14, 0, 0, 0, timezone),
		},
		{
			ID:          "stat3",
			EventType:   WebhookEventTypeMessage,
			ChannelType: BotTypeLine,
			MessageText: "nomatch",
			Timestamp:   time.Date(2024, 1, 15, 20, 0, 0, 0, timezone), // Outside hours
		},
	}

	autoReplies := []*AutoReply{
		{
			ID:         1,
			Name:       "IG Story Rule",
			Status:     AutoReplyStatusActive,
			Keywords:   []string{"hello"},
			IGStoryIDs: []string{"story123"},
		},
		{
			ID:       2,
			Name:     "General Rule",
			Status:   AutoReplyStatusActive,
			Keywords: []string{"hello"},
		},
	}

	// Process all events
	var results []*WebhookProcessResult
	for _, event := range events {
		result := processor.ProcessWebhookEvent(event, autoReplies, nil, timezone)
		results = append(results, result)
	}

	// Get statistics
	stats := processor.GetProcessingStats(results)
	
	if stats.TotalEvents != 3 {
		t.Errorf("GetProcessingStats() TotalEvents = %v, want %v", stats.TotalEvents, 3)
	}
	
	if stats.SuccessfulEvents != 3 {
		t.Errorf("GetProcessingStats() SuccessfulEvents = %v, want %v", stats.SuccessfulEvents, 3)
	}
	
	if stats.MatchedEvents != 2 {
		t.Errorf("GetProcessingStats() MatchedEvents = %v, want %v", stats.MatchedEvents, 2)
	}
	
	if stats.PriorityBreakdown[AutoReplyPriorityIGStoryKeyword] != 1 {
		t.Errorf("GetProcessingStats() IGStoryKeyword priority count = %v, want %v", 
			stats.PriorityBreakdown[AutoReplyPriorityIGStoryKeyword], 1)
	}
	
	if stats.PriorityBreakdown[AutoReplyPriorityGeneralKeyword] != 1 {
		t.Errorf("GetProcessingStats() GeneralKeyword priority count = %v, want %v", 
			stats.PriorityBreakdown[AutoReplyPriorityGeneralKeyword], 1)
	}
}

// TestRealWorldScenarios tests realistic webhook processing scenarios.
func TestRealWorldScenarios(t *testing.T) {
	processor := NewWebhookProcessor()
	timezone, _ := time.LoadLocation("Asia/Taipei")

	// Realistic auto-reply configuration
	autoReplies := []*AutoReply{
		// Customer service hours
		{
			ID:     1,
			Name:   "Business Hours Support",
			Status: AutoReplyStatusActive,
			TriggerScheduleType: stringToScheduleType(WebhookTriggerScheduleTypeBusinessHour),
		},
		// After hours message
		{
			ID:     2,
			Name:   "After Hours Message",
			Status: AutoReplyStatusActive,
			TriggerScheduleType: stringToScheduleType(WebhookTriggerScheduleTypeNonBusinessHour),
		},
		// FAQ keywords
		{
			ID:       3,
			Name:     "FAQ - Hours",
			Status:   AutoReplyStatusActive,
			Keywords: []string{"hours", "時間", "営業時間"},
		},
		{
			ID:       4,
			Name:     "FAQ - Contact",
			Status:   AutoReplyStatusActive,
			Keywords: []string{"contact", "電話", "連絡"},
		},
		// Instagram story promotion
		{
			ID:         5,
			Name:       "Story Promotion",
			Status:     AutoReplyStatusActive,
			Keywords:   []string{"interested", "want", "buy"},
			IGStoryIDs: []string{"promo_story_123"},
		},
	}

	businessHours := []*BusinessHour{
		{Weekday: 1, StartTime: time.Date(0, 1, 1, 9, 0, 0, 0, time.UTC), EndTime: time.Date(0, 1, 1, 18, 0, 0, 0, time.UTC)}, // Monday
		{Weekday: 2, StartTime: time.Date(0, 1, 1, 9, 0, 0, 0, time.UTC), EndTime: time.Date(0, 1, 1, 18, 0, 0, 0, time.UTC)}, // Tuesday
		{Weekday: 3, StartTime: time.Date(0, 1, 1, 9, 0, 0, 0, time.UTC), EndTime: time.Date(0, 1, 1, 18, 0, 0, 0, time.UTC)}, // Wednesday
		{Weekday: 4, StartTime: time.Date(0, 1, 1, 9, 0, 0, 0, time.UTC), EndTime: time.Date(0, 1, 1, 18, 0, 0, 0, time.UTC)}, // Thursday
		{Weekday: 5, StartTime: time.Date(0, 1, 1, 9, 0, 0, 0, time.UTC), EndTime: time.Date(0, 1, 1, 18, 0, 0, 0, time.UTC)}, // Friday
	}

	scenarios := []struct {
		name        string
		event       *WebhookEvent
		expectMatch bool
		expectRule  string
		description string
	}{
		{
			name: "instagram_story_promotion",
			event: &WebhookEvent{
				ID:          "promo1",
				EventType:   WebhookEventTypeMessage,
				ChannelType: BotTypeInstagram,
				MessageText: "interested",
				IGStoryID:   stringPtr("promo_story_123"),
				Timestamp:   time.Date(2024, 1, 15, 14, 0, 0, 0, timezone),
			},
			expectMatch: true,
			expectRule:  "Story Promotion",
			description: "Instagram story promotion should have highest priority",
		},
		{
			name: "faq_multilingual",
			event: &WebhookEvent{
				ID:          "faq1",
				EventType:   WebhookEventTypeMessage,
				ChannelType: BotTypeLine,
				MessageText: "営業時間",
				Timestamp:   time.Date(2024, 1, 15, 14, 0, 0, 0, timezone),
			},
			expectMatch: true,
			expectRule:  "FAQ - Hours",
			description: "Japanese FAQ keyword should match",
		},
		{
			name: "business_hours_fallback",
			event: &WebhookEvent{
				ID:          "bh1",
				EventType:   WebhookEventTypeMessage,
				ChannelType: BotTypeLine,
				MessageText: "random question",
				Timestamp:   time.Date(2024, 1, 15, 20, 0, 0, 0, timezone), // Monday 8PM Taipei = 12PM UTC (within business hours)
			},
			expectMatch: true,
			expectRule:  "Business Hours Support",
			description: "Should fall back to business hours during work time",
		},
		{
			name: "after_hours_fallback",
			event: &WebhookEvent{
				ID:          "ah1",
				EventType:   WebhookEventTypeMessage,
				ChannelType: BotTypeLine,
				MessageText: "random question",
				Timestamp:   time.Date(2024, 1, 15, 14, 0, 0, 0, timezone), // Monday 2PM Taipei = 6AM UTC (before business hours)
			},
			expectMatch: true,
			expectRule:  "After Hours Message",
			description: "Should fall back to after hours message",
		},
	}

	for _, scenario := range scenarios {
		t.Run(scenario.name, func(t *testing.T) {
			result := processor.ProcessWebhookEvent(scenario.event, autoReplies, businessHours, timezone)
			
			if !result.Success {
				t.Errorf("ProcessWebhookEvent() failed: %s. Description: %s", 
					result.Error, scenario.description)
				return
			}
			
			if result.HasMatch != scenario.expectMatch {
				t.Errorf("ProcessWebhookEvent() match = %v, want %v. Description: %s", 
					result.HasMatch, scenario.expectMatch, scenario.description)
				return
			}
			
			if scenario.expectMatch {
				if result.MatchedAutoReply.Name != scenario.expectRule {
					t.Errorf("ProcessWebhookEvent() matched rule = %v, want %v. Description: %s", 
						result.MatchedAutoReply.Name, scenario.expectRule, scenario.description)
				}
			}
		})
	}
}