package auto_reply

import (
	"testing"
	"time"
)

// TestTimezoneHandling tests timezone conversion and handling in business hours
func TestTimezoneHandling(t *testing.T) {
	validator := NewScheduleValidator()

	// Define different timezones
	utc, _ := time.LoadLocation("UTC")
	est, _ := time.LoadLocation("America/New_York")
	jst, _ := time.LoadLocation("Asia/Tokyo")
	pst, _ := time.LoadLocation("America/Los_Angeles")

	// Create business hours in UTC (9 AM to 5 PM)
	businessHours := []*BusinessHour{
		{
			Weekday:   1, // Monday
			StartTime: time.Date(0, 1, 1, 9, 0, 0, 0, utc),
			EndTime:   time.Date(0, 1, 1, 17, 0, 0, 0, utc),
		},
		{
			Weekday:   2, // Tuesday
			StartTime: time.Date(0, 1, 1, 9, 0, 0, 0, utc),
			EndTime:   time.Date(0, 1, 1, 17, 0, 0, 0, utc),
		},
	}

	// Create business hour auto-reply
	autoReply := createBusinessHourScheduleAutoReply()

	tests := []struct {
		name        string
		eventTime   time.Time
		timezone    *time.Location
		shouldMatch bool
		description string
	}{
		{
			name:        "utc_within_business_hours",
			eventTime:   time.Date(2024, 1, 15, 14, 0, 0, 0, utc), // Monday 2 PM UTC
			timezone:    utc,
			shouldMatch: true,
			description: "Should match at 2 PM UTC (within 9 AM - 5 PM UTC business hours)",
		},
		{
			name:        "utc_outside_business_hours",
			eventTime:   time.Date(2024, 1, 15, 20, 0, 0, 0, utc), // Monday 8 PM UTC
			timezone:    utc,
			shouldMatch: false,
			description: "Should NOT match at 8 PM UTC (outside business hours)",
		},
		{
			name:        "est_within_business_hours",
			eventTime:   time.Date(2024, 1, 15, 9, 0, 0, 0, est), // Monday 9 AM EST = 2 PM UTC
			timezone:    est,
			shouldMatch: true,
			description: "Should match at 9 AM EST (converts to 2 PM UTC, within business hours)",
		},
		{
			name:        "est_outside_business_hours",
			eventTime:   time.Date(2024, 1, 15, 3, 0, 0, 0, est), // Monday 3 AM EST = 8 AM UTC
			timezone:    est,
			shouldMatch: false,
			description: "Should NOT match at 3 AM EST (converts to 8 AM UTC, before business hours)",
		},
		{
			name:        "jst_within_business_hours",
			eventTime:   time.Date(2024, 1, 15, 23, 0, 0, 0, jst), // Monday 11 PM JST = 2 PM UTC
			timezone:    jst,
			shouldMatch: true,
			description: "Should match at 11 PM JST (converts to 2 PM UTC, within business hours)",
		},
		{
			name:        "jst_outside_business_hours",
			eventTime:   time.Date(2024, 1, 16, 4, 0, 0, 0, jst), // Tuesday 4 AM JST = Monday 7 PM UTC
			timezone:    jst,
			shouldMatch: false,
			description: "Should NOT match at 4 AM JST (converts to 7 PM UTC, after business hours)",
		},
		{
			name:        "pst_within_business_hours",
			eventTime:   time.Date(2024, 1, 15, 6, 0, 0, 0, pst), // Monday 6 AM PST = 2 PM UTC
			timezone:    pst,
			shouldMatch: true,
			description: "Should match at 6 AM PST (converts to 2 PM UTC, within business hours)",
		},
		{
			name:        "pst_outside_business_hours",
			eventTime:   time.Date(2024, 1, 14, 23, 0, 0, 0, pst), // Sunday 11 PM PST = Monday 7 AM UTC
			timezone:    pst,
			shouldMatch: false,
			description: "Should NOT match at 11 PM PST (converts to 7 AM UTC, before business hours)",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := validator.ValidateSchedule(autoReply, tt.eventTime, businessHours, tt.timezone)
			
			if result.IsMatch != tt.shouldMatch {
				t.Errorf("ValidateSchedule() timezone handling = %v, want %v at %s %s. Description: %s", 
					result.IsMatch, tt.shouldMatch, 
					tt.eventTime.Format("15:04:05"), tt.timezone.String(), tt.description)
			}
		})
	}
}

// TestTimezoneWithDailySchedule tests timezone conversion with daily schedules
func TestTimezoneWithDailySchedule(t *testing.T) {
	validator := NewScheduleValidator()

	// Define timezones
	utc, _ := time.LoadLocation("UTC")
	est, _ := time.LoadLocation("America/New_York")
	jst, _ := time.LoadLocation("Asia/Tokyo")

	// Create daily schedule: 9 AM to 5 PM
	autoReply := createDailyScheduleAutoReply("09:00", "17:00")

	tests := []struct {
		name        string
		eventTime   time.Time
		timezone    *time.Location
		shouldMatch bool
		description string
	}{
		{
			name:        "utc_within_daily_schedule",
			eventTime:   time.Date(2024, 1, 15, 14, 0, 0, 0, utc), // 2 PM UTC
			timezone:    utc,
			shouldMatch: true,
			description: "Should match at 2 PM UTC (within 9 AM - 5 PM daily schedule)",
		},
		{
			name:        "est_within_daily_schedule",
			eventTime:   time.Date(2024, 1, 15, 14, 0, 0, 0, est), // 2 PM EST
			timezone:    est,
			shouldMatch: true,
			description: "Should match at 2 PM EST (within 9 AM - 5 PM daily schedule in EST)",
		},
		{
			name:        "jst_within_daily_schedule",
			eventTime:   time.Date(2024, 1, 15, 14, 0, 0, 0, jst), // 2 PM JST
			timezone:    jst,
			shouldMatch: true,
			description: "Should match at 2 PM JST (within 9 AM - 5 PM daily schedule in JST)",
		},
		{
			name:        "est_outside_daily_schedule",
			eventTime:   time.Date(2024, 1, 15, 20, 0, 0, 0, est), // 8 PM EST
			timezone:    est,
			shouldMatch: false,
			description: "Should NOT match at 8 PM EST (outside 9 AM - 5 PM daily schedule)",
		},
		{
			name:        "jst_outside_daily_schedule",
			eventTime:   time.Date(2024, 1, 15, 6, 0, 0, 0, jst), // 6 AM JST
			timezone:    jst,
			shouldMatch: false,
			description: "Should NOT match at 6 AM JST (outside 9 AM - 5 PM daily schedule)",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := validator.ValidateSchedule(autoReply, tt.eventTime, nil, tt.timezone)
			
			if result.IsMatch != tt.shouldMatch {
				t.Errorf("ValidateSchedule() daily schedule timezone = %v, want %v at %s %s. Description: %s", 
					result.IsMatch, tt.shouldMatch, 
					tt.eventTime.Format("15:04:05"), tt.timezone.String(), tt.description)
			}
		})
	}
}

// TestTimezoneWithMidnightCrossing tests timezone handling with midnight crossing schedules
func TestTimezoneWithMidnightCrossing(t *testing.T) {
	validator := NewScheduleValidator()

	// Define timezones
	utc, _ := time.LoadLocation("UTC")
	est, _ := time.LoadLocation("America/New_York")
	jst, _ := time.LoadLocation("Asia/Tokyo")

	// Create midnight crossing schedule: 10 PM to 6 AM
	autoReply := createDailyScheduleAutoReply("22:00", "06:00")

	tests := []struct {
		name        string
		eventTime   time.Time
		timezone    *time.Location
		shouldMatch bool
		description string
	}{
		{
			name:        "utc_midnight_crossing_before",
			eventTime:   time.Date(2024, 1, 15, 23, 0, 0, 0, utc), // 11 PM UTC
			timezone:    utc,
			shouldMatch: true,
			description: "Should match at 11 PM UTC (within 10 PM - 6 AM midnight crossing)",
		},
		{
			name:        "utc_midnight_crossing_after",
			eventTime:   time.Date(2024, 1, 16, 3, 0, 0, 0, utc), // 3 AM UTC next day
			timezone:    utc,
			shouldMatch: true,
			description: "Should match at 3 AM UTC (within 10 PM - 6 AM midnight crossing)",
		},
		{
			name:        "est_midnight_crossing_before",
			eventTime:   time.Date(2024, 1, 15, 23, 0, 0, 0, est), // 11 PM EST
			timezone:    est,
			shouldMatch: true,
			description: "Should match at 11 PM EST (within 10 PM - 6 AM midnight crossing in EST)",
		},
		{
			name:        "est_midnight_crossing_after",
			eventTime:   time.Date(2024, 1, 16, 3, 0, 0, 0, est), // 3 AM EST next day
			timezone:    est,
			shouldMatch: true,
			description: "Should match at 3 AM EST (within 10 PM - 6 AM midnight crossing in EST)",
		},
		{
			name:        "jst_midnight_crossing_outside",
			eventTime:   time.Date(2024, 1, 15, 12, 0, 0, 0, jst), // 12 PM JST
			timezone:    jst,
			shouldMatch: false,
			description: "Should NOT match at 12 PM JST (outside 10 PM - 6 AM midnight crossing)",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := validator.ValidateSchedule(autoReply, tt.eventTime, nil, tt.timezone)
			
			if result.IsMatch != tt.shouldMatch {
				t.Errorf("ValidateSchedule() midnight crossing timezone = %v, want %v at %s %s. Description: %s", 
					result.IsMatch, tt.shouldMatch, 
					tt.eventTime.Format("15:04:05"), tt.timezone.String(), tt.description)
			}
		})
	}
}

// TestTimezoneIntegration tests timezone handling in complete webhook processing
func TestTimezoneIntegration(t *testing.T) {
	processor := NewWebhookProcessor()

	// Define timezones
	utc, _ := time.LoadLocation("UTC")
	est, _ := time.LoadLocation("America/New_York")
	jst, _ := time.LoadLocation("Asia/Tokyo")

	// Create auto-reply with business hours
	autoReplies := []*AutoReply{
		{
			ID:     1,
			Name:   "Business Hours Support",
			Status: AutoReplyStatusActive,
			TriggerScheduleType: stringToScheduleType(WebhookTriggerScheduleTypeBusinessHour),
		},
	}

	// Business hours: 9 AM to 5 PM UTC
	businessHours := []*BusinessHour{
		{
			Weekday:   1, // Monday
			StartTime: time.Date(0, 1, 1, 9, 0, 0, 0, utc),
			EndTime:   time.Date(0, 1, 1, 17, 0, 0, 0, utc),
		},
	}

	tests := []struct {
		name        string
		eventTime   time.Time
		timezone    *time.Location
		shouldMatch bool
		description string
	}{
		{
			name:        "integration_est_within_business_hours",
			eventTime:   time.Date(2024, 1, 15, 9, 0, 0, 0, est), // 9 AM EST = 2 PM UTC
			timezone:    est,
			shouldMatch: true,
			description: "Integration: Should match at 9 AM EST (converts to 2 PM UTC, within business hours)",
		},
		{
			name:        "integration_est_outside_business_hours",
			eventTime:   time.Date(2024, 1, 15, 3, 0, 0, 0, est), // 3 AM EST = 8 AM UTC
			timezone:    est,
			shouldMatch: false,
			description: "Integration: Should NOT match at 3 AM EST (converts to 8 AM UTC, before business hours)",
		},
		{
			name:        "integration_jst_within_business_hours",
			eventTime:   time.Date(2024, 1, 15, 23, 0, 0, 0, jst), // 11 PM JST = 2 PM UTC
			timezone:    jst,
			shouldMatch: true,
			description: "Integration: Should match at 11 PM JST (converts to 2 PM UTC, within business hours)",
		},
		{
			name:        "integration_jst_outside_business_hours",
			eventTime:   time.Date(2024, 1, 16, 4, 0, 0, 0, jst), // 4 AM JST = 7 PM UTC previous day
			timezone:    jst,
			shouldMatch: false,
			description: "Integration: Should NOT match at 4 AM JST (converts to 7 PM UTC, after business hours)",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			event := &WebhookEvent{
				ID:          "timezone_test",
				EventType:   WebhookEventTypeMessage,
				ChannelType: BotTypeLine,
				MessageText: "help",
				Timestamp:   tt.eventTime,
			}

			result := processor.ProcessWebhookEvent(event, autoReplies, businessHours, tt.timezone)
			
			if !result.Success {
				t.Errorf("ProcessWebhookEvent() failed: %s", result.Error)
				return
			}

			if result.HasMatch != tt.shouldMatch {
				t.Errorf("ProcessWebhookEvent() timezone integration = %v, want %v at %s %s. Description: %s", 
					result.HasMatch, tt.shouldMatch, 
					tt.eventTime.Format("15:04:05"), tt.timezone.String(), tt.description)
			}

			if tt.shouldMatch {
				if result.MatchedAutoReply == nil {
					t.Error("ProcessWebhookEvent() MatchedAutoReply is nil")
				} else if result.MatchedAutoReply.Name != "Business Hours Support" {
					t.Errorf("ProcessWebhookEvent() matched wrong rule: %s", result.MatchedAutoReply.Name)
				}
				if result.Timezone != tt.timezone.String() {
					t.Errorf("ProcessWebhookEvent() timezone not recorded: got %s, want %s", 
						result.Timezone, tt.timezone.String())
				}
			}
		})
	}
}

// TestTimezoneEdgeCases tests edge cases for timezone handling
func TestTimezoneEdgeCases(t *testing.T) {
	validator := NewScheduleValidator()

	// Test DST transitions and edge cases
	est, _ := time.LoadLocation("America/New_York")
	
	// Create daily schedule
	autoReply := createDailyScheduleAutoReply("09:00", "17:00")

	tests := []struct {
		name        string
		eventTime   time.Time
		timezone    *time.Location
		shouldMatch bool
		description string
	}{
		{
			name:        "dst_spring_forward",
			eventTime:   time.Date(2024, 3, 10, 14, 0, 0, 0, est), // During DST transition
			timezone:    est,
			shouldMatch: true,
			description: "Should handle DST spring forward correctly",
		},
		{
			name:        "dst_fall_back",
			eventTime:   time.Date(2024, 11, 3, 14, 0, 0, 0, est), // During DST transition
			timezone:    est,
			shouldMatch: true,
			description: "Should handle DST fall back correctly",
		},
		{
			name:        "nil_timezone_defaults_to_utc",
			eventTime:   time.Date(2024, 1, 15, 14, 0, 0, 0, time.UTC),
			timezone:    nil,
			shouldMatch: true,
			description: "Should default to UTC when timezone is nil",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := validator.ValidateSchedule(autoReply, tt.eventTime, nil, tt.timezone)
			
			if result.IsMatch != tt.shouldMatch {
				t.Errorf("ValidateSchedule() timezone edge case = %v, want %v. Description: %s", 
					result.IsMatch, tt.shouldMatch, tt.description)
			}
		})
	}
}