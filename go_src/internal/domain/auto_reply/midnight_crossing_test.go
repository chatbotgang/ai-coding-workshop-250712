package auto_reply

import (
	"testing"
	"time"
)

// TestMidnightCrossing tests the midnight crossing functionality for daily schedules
func TestMidnightCrossing(t *testing.T) {
	validator := NewScheduleValidator()
	timezone := time.UTC

	// Create a daily schedule that crosses midnight (22:00 to 06:00)
	autoReply := createDailyScheduleAutoReply("22:00", "06:00")

	tests := []struct {
		name        string
		eventTime   time.Time
		shouldMatch bool
		description string
	}{
		{
			name:        "within_range_before_midnight",
			eventTime:   time.Date(2024, 1, 15, 23, 30, 0, 0, timezone), // 23:30 (before midnight)
			shouldMatch: true,
			description: "Should match at 23:30 (within 22:00-06:00 range)",
		},
		{
			name:        "within_range_after_midnight",
			eventTime:   time.Date(2024, 1, 16, 3, 30, 0, 0, timezone), // 03:30 (after midnight)
			shouldMatch: true,
			description: "Should match at 03:30 (within 22:00-06:00 range)",
		},
		{
			name:        "exactly_at_start_time",
			eventTime:   time.Date(2024, 1, 15, 22, 0, 0, 0, timezone), // 22:00 exactly
			shouldMatch: true,
			description: "Should match at exactly 22:00 (start time)",
		},
		{
			name:        "exactly_at_end_time",
			eventTime:   time.Date(2024, 1, 16, 6, 0, 0, 0, timezone), // 06:00 exactly
			shouldMatch: false,
			description: "Should NOT match at exactly 06:00 (end time is exclusive)",
		},
		{
			name:        "just_before_end_time",
			eventTime:   time.Date(2024, 1, 16, 5, 59, 59, 0, timezone), // 05:59:59
			shouldMatch: true,
			description: "Should match at 05:59:59 (just before end time)",
		},
		{
			name:        "outside_range_morning",
			eventTime:   time.Date(2024, 1, 15, 8, 0, 0, 0, timezone), // 08:00 (outside range)
			shouldMatch: false,
			description: "Should NOT match at 08:00 (outside 22:00-06:00 range)",
		},
		{
			name:        "outside_range_afternoon",
			eventTime:   time.Date(2024, 1, 15, 14, 0, 0, 0, timezone), // 14:00 (outside range)
			shouldMatch: false,
			description: "Should NOT match at 14:00 (outside 22:00-06:00 range)",
		},
		{
			name:        "outside_range_evening",
			eventTime:   time.Date(2024, 1, 15, 20, 0, 0, 0, timezone), // 20:00 (outside range)
			shouldMatch: false,
			description: "Should NOT match at 20:00 (outside 22:00-06:00 range)",
		},
		{
			name:        "edge_case_just_before_start",
			eventTime:   time.Date(2024, 1, 15, 21, 59, 59, 0, timezone), // 21:59:59
			shouldMatch: false,
			description: "Should NOT match at 21:59:59 (just before start time)",
		},
		{
			name:        "edge_case_just_after_end",
			eventTime:   time.Date(2024, 1, 16, 6, 0, 1, 0, timezone), // 06:00:01
			shouldMatch: false,
			description: "Should NOT match at 06:00:01 (just after end time)",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := validator.ValidateSchedule(autoReply, tt.eventTime, nil, timezone)
			
			if result.IsMatch != tt.shouldMatch {
				t.Errorf("ValidateSchedule() for midnight crossing = %v, want %v at %s. Description: %s", 
					result.IsMatch, tt.shouldMatch, tt.eventTime.Format("15:04:05"), tt.description)
			}
		})
	}
}

// TestMidnightCrossingMultipleRanges tests midnight crossing with multiple time ranges
func TestMidnightCrossingMultipleRanges(t *testing.T) {
	validator := NewScheduleValidator()
	timezone := time.UTC

	// Create an auto-reply with multiple daily schedules, some crossing midnight
	scheduleType := WebhookTriggerScheduleTypeDaily
	schedule1 := DailySchedule{StartTime: "22:00", EndTime: "06:00"} // Crosses midnight
	schedule2 := DailySchedule{StartTime: "12:00", EndTime: "14:00"} // Normal range
	
	autoReply := &AutoReply{
		ID:                  1,
		TriggerScheduleType: &scheduleType,
		TriggerScheduleSettings: &WebhookTriggerScheduleSettings{
			Schedules: []WebhookTriggerSchedule{&schedule1, &schedule2},
		},
	}

	tests := []struct {
		name        string
		eventTime   time.Time
		shouldMatch bool
		description string
	}{
		{
			name:        "midnight_crossing_range_late_night",
			eventTime:   time.Date(2024, 1, 15, 23, 0, 0, 0, timezone), // 23:00
			shouldMatch: true,
			description: "Should match midnight crossing range at 23:00",
		},
		{
			name:        "midnight_crossing_range_early_morning",
			eventTime:   time.Date(2024, 1, 16, 5, 0, 0, 0, timezone), // 05:00
			shouldMatch: true,
			description: "Should match midnight crossing range at 05:00",
		},
		{
			name:        "normal_range_lunch_time",
			eventTime:   time.Date(2024, 1, 15, 13, 0, 0, 0, timezone), // 13:00
			shouldMatch: true,
			description: "Should match normal range at 13:00",
		},
		{
			name:        "outside_all_ranges",
			eventTime:   time.Date(2024, 1, 15, 16, 0, 0, 0, timezone), // 16:00
			shouldMatch: false,
			description: "Should NOT match outside all ranges at 16:00",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := validator.ValidateSchedule(autoReply, tt.eventTime, nil, timezone)
			
			if result.IsMatch != tt.shouldMatch {
				t.Errorf("ValidateSchedule() for multiple ranges = %v, want %v at %s. Description: %s", 
					result.IsMatch, tt.shouldMatch, tt.eventTime.Format("15:04:05"), tt.description)
			}
		})
	}
}

// TestMidnightCrossingEdgeCases tests edge cases for midnight crossing
func TestMidnightCrossingEdgeCases(t *testing.T) {
	validator := NewScheduleValidator()
	timezone := time.UTC

	tests := []struct {
		name        string
		startTime   string
		endTime     string
		eventTime   time.Time
		shouldMatch bool
		description string
	}{
		{
			name:        "full_night_coverage",
			startTime:   "18:00",
			endTime:     "09:00",
			eventTime:   time.Date(2024, 1, 15, 23, 30, 0, 0, timezone), // 23:30
			shouldMatch: true,
			description: "Full night coverage (18:00-09:00) should match at 23:30",
		},
		{
			name:        "full_night_coverage_early_morning",
			startTime:   "18:00",
			endTime:     "09:00",
			eventTime:   time.Date(2024, 1, 16, 7, 30, 0, 0, timezone), // 07:30
			shouldMatch: true,
			description: "Full night coverage (18:00-09:00) should match at 07:30",
		},
		{
			name:        "very_short_midnight_crossing",
			startTime:   "23:59",
			endTime:     "00:01",
			eventTime:   time.Date(2024, 1, 15, 23, 59, 30, 0, timezone), // 23:59:30
			shouldMatch: true,
			description: "Very short midnight crossing should match at 23:59:30",
		},
		{
			name:        "very_short_midnight_crossing_after",
			startTime:   "23:59",
			endTime:     "00:01",
			eventTime:   time.Date(2024, 1, 16, 0, 0, 30, 0, timezone), // 00:00:30
			shouldMatch: true,
			description: "Very short midnight crossing should match at 00:00:30",
		},
		{
			name:        "normal_range_no_crossing",
			startTime:   "09:00",
			endTime:     "17:00",
			eventTime:   time.Date(2024, 1, 15, 14, 0, 0, 0, timezone), // 14:00
			shouldMatch: true,
			description: "Normal range (09:00-17:00) should match at 14:00",
		},
		{
			name:        "normal_range_no_crossing_outside",
			startTime:   "09:00",
			endTime:     "17:00",
			eventTime:   time.Date(2024, 1, 15, 20, 0, 0, 0, timezone), // 20:00
			shouldMatch: false,
			description: "Normal range (09:00-17:00) should NOT match at 20:00",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			autoReply := createDailyScheduleAutoReply(tt.startTime, tt.endTime)
			result := validator.ValidateSchedule(autoReply, tt.eventTime, nil, timezone)
			
			if result.IsMatch != tt.shouldMatch {
				t.Errorf("ValidateSchedule() for %s-%s = %v, want %v at %s. Description: %s", 
					tt.startTime, tt.endTime, result.IsMatch, tt.shouldMatch, 
					tt.eventTime.Format("15:04:05"), tt.description)
			}
		})
	}
}

// TestMidnightCrossingIntegration tests midnight crossing in complete webhook processing
func TestMidnightCrossingIntegration(t *testing.T) {
	processor := NewWebhookProcessor()
	timezone := time.UTC

	// Create auto-reply with midnight crossing schedule
	autoReplies := []*AutoReply{
		{
			ID:     1,
			Name:   "Night Shift Support",
			Status: AutoReplyStatusActive,
			TriggerScheduleType: stringToScheduleType(WebhookTriggerScheduleTypeDaily),
			TriggerScheduleSettings: &WebhookTriggerScheduleSettings{
				Schedules: []WebhookTriggerSchedule{
					&DailySchedule{
						StartTime: "22:00",
						EndTime:   "06:00",
					},
				},
			},
		},
	}

	tests := []struct {
		name        string
		eventTime   time.Time
		shouldMatch bool
		description string
	}{
		{
			name:        "integration_midnight_crossing_night",
			eventTime:   time.Date(2024, 1, 15, 23, 45, 0, 0, timezone), // 23:45
			shouldMatch: true,
			description: "Integration test: should match during night shift at 23:45",
		},
		{
			name:        "integration_midnight_crossing_early_morning",
			eventTime:   time.Date(2024, 1, 16, 4, 30, 0, 0, timezone), // 04:30
			shouldMatch: true,
			description: "Integration test: should match during night shift at 04:30",
		},
		{
			name:        "integration_outside_night_shift",
			eventTime:   time.Date(2024, 1, 15, 10, 0, 0, 0, timezone), // 10:00
			shouldMatch: false,
			description: "Integration test: should NOT match outside night shift at 10:00",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			event := &WebhookEvent{
				ID:          "midnight_test",
				EventType:   WebhookEventTypeMessage,
				ChannelType: BotTypeLine,
				MessageText: "help",
				Timestamp:   tt.eventTime,
			}

			result := processor.ProcessWebhookEvent(event, autoReplies, nil, timezone)
			
			if !result.Success {
				t.Errorf("ProcessWebhookEvent() failed: %s", result.Error)
				return
			}

			if result.HasMatch != tt.shouldMatch {
				t.Errorf("ProcessWebhookEvent() for midnight crossing = %v, want %v at %s. Description: %s", 
					result.HasMatch, tt.shouldMatch, tt.eventTime.Format("15:04:05"), tt.description)
			}

			if tt.shouldMatch {
				if result.MatchedAutoReply.Name != "Night Shift Support" {
					t.Errorf("ProcessWebhookEvent() matched wrong rule: %s", result.MatchedAutoReply.Name)
				}
			}
		})
	}
}