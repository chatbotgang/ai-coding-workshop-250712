package auto_reply

import (
	"testing"
	"time"
)

func TestScheduleValidator_ValidateSchedule(t *testing.T) {
	validator := NewScheduleValidator()
	timezone := time.UTC

	tests := []struct {
		name            string
		autoReply       *AutoReply
		eventTime       time.Time
		businessHours   []*BusinessHour
		shouldMatch     bool
		description     string
	}{
		// PRD Test Cases from Story 3: General Time-based Logic
		{
			name: "daily_schedule_within_time",
			autoReply: createDailyScheduleAutoReply("09:00", "17:00"),
			eventTime: parseTime("2024-01-15 14:00:00"), // Monday 2PM
			shouldMatch: true,
			description: "B-P0-6-Test3: Daily schedule match",
		},
		{
			name: "daily_schedule_outside_time",
			autoReply: createDailyScheduleAutoReply("09:00", "17:00"),
			eventTime: parseTime("2024-01-15 20:00:00"), // Monday 8PM
			shouldMatch: false,
			description: "Daily schedule outside time window",
		},
		{
			name: "daily_schedule_midnight_crossing_within",
			autoReply: createDailyScheduleAutoReply("22:00", "06:00"),
			eventTime: parseTime("2024-01-15 23:00:00"), // Monday 11PM
			shouldMatch: true,
			description: "Daily schedule crossing midnight - within range",
		},
		{
			name: "daily_schedule_midnight_crossing_early_morning",
			autoReply: createDailyScheduleAutoReply("22:00", "06:00"),
			eventTime: parseTime("2024-01-15 03:00:00"), // Monday 3AM
			shouldMatch: true,
			description: "Daily schedule crossing midnight - early morning",
		},
		{
			name: "daily_schedule_midnight_crossing_outside",
			autoReply: createDailyScheduleAutoReply("22:00", "06:00"),
			eventTime: parseTime("2024-01-15 12:00:00"), // Monday 12PM
			shouldMatch: false,
			description: "Daily schedule crossing midnight - outside range",
		},
		{
			name: "monthly_schedule_correct_day_and_time",
			autoReply: createMonthlyScheduleAutoReply(15, "10:00", "12:00"),
			eventTime: parseTime("2024-01-15 11:00:00"), // 15th at 11AM
			shouldMatch: true,
			description: "B-P0-6-Test4: Monthly schedule match",
		},
		{
			name: "monthly_schedule_correct_day_wrong_time",
			autoReply: createMonthlyScheduleAutoReply(15, "10:00", "12:00"),
			eventTime: parseTime("2024-01-15 14:00:00"), // 15th at 2PM
			shouldMatch: false,
			description: "Monthly schedule wrong time",
		},
		{
			name: "monthly_schedule_wrong_day",
			autoReply: createMonthlyScheduleAutoReply(15, "10:00", "12:00"),
			eventTime: parseTime("2024-01-16 11:00:00"), // 16th at 11AM
			shouldMatch: false,
			description: "Monthly schedule wrong day",
		},
		{
			name: "business_hour_match",
			autoReply: createBusinessHourScheduleAutoReply(),
			eventTime: parseTime("2024-01-15 14:00:00"), // Monday 2PM
			businessHours: []*BusinessHour{
				{Weekday: 1, StartTime: parseTime("2024-01-01 09:00:00"), EndTime: parseTime("2024-01-01 17:00:00")}, // Monday
			},
			shouldMatch: true,
			description: "B-P0-6-Test5: Business hours match",
		},
		{
			name: "business_hour_outside_time",
			autoReply: createBusinessHourScheduleAutoReply(),
			eventTime: parseTime("2024-01-15 20:00:00"), // Monday 8PM
			businessHours: []*BusinessHour{
				{Weekday: 1, StartTime: parseTime("2024-01-01 09:00:00"), EndTime: parseTime("2024-01-01 17:00:00")}, // Monday
			},
			shouldMatch: false,
			description: "Business hours outside time",
		},
		{
			name: "business_hour_wrong_day",
			autoReply: createBusinessHourScheduleAutoReply(),
			eventTime: parseTime("2024-01-16 14:00:00"), // Tuesday 2PM
			businessHours: []*BusinessHour{
				{Weekday: 1, StartTime: parseTime("2024-01-01 09:00:00"), EndTime: parseTime("2024-01-01 17:00:00")}, // Monday only
			},
			shouldMatch: false,
			description: "Business hours wrong day",
		},
		{
			name: "non_business_hour_match",
			autoReply: createNonBusinessHourScheduleAutoReply(),
			eventTime: parseTime("2024-01-15 20:00:00"), // Monday 8PM
			businessHours: []*BusinessHour{
				{Weekday: 1, StartTime: parseTime("2024-01-01 09:00:00"), EndTime: parseTime("2024-01-01 17:00:00")}, // Monday 9-5
			},
			shouldMatch: true,
			description: "Non-business hours match",
		},
		{
			name: "non_business_hour_during_business",
			autoReply: createNonBusinessHourScheduleAutoReply(),
			eventTime: parseTime("2024-01-15 14:00:00"), // Monday 2PM
			businessHours: []*BusinessHour{
				{Weekday: 1, StartTime: parseTime("2024-01-01 09:00:00"), EndTime: parseTime("2024-01-01 17:00:00")}, // Monday 9-5
			},
			shouldMatch: false,
			description: "Non-business hours during business time",
		},
		{
			name: "date_range_within_range",
			autoReply: createDateRangeScheduleAutoReply("2024-01-01", "2024-01-31"),
			eventTime: parseTime("2024-01-15 14:00:00"),
			shouldMatch: true,
			description: "Date range within range",
		},
		{
			name: "date_range_outside_range",
			autoReply: createDateRangeScheduleAutoReply("2024-01-01", "2024-01-31"),
			eventTime: parseTime("2024-02-15 14:00:00"),
			shouldMatch: false,
			description: "Date range outside range",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := validator.ValidateSchedule(tt.autoReply, tt.eventTime, tt.businessHours, timezone)
			
			if result.IsMatch != tt.shouldMatch {
				t.Errorf("ValidateSchedule() = %v, want %v. Reason: %s. Description: %s", 
					result.IsMatch, tt.shouldMatch, result.Reason, tt.description)
			}
		})
	}
}

func TestScheduleValidator_EdgeCases(t *testing.T) {
	validator := NewScheduleValidator()
	timezone := time.UTC

	t.Run("no_schedule_type", func(t *testing.T) {
		autoReply := &AutoReply{
			ID:                  1,
			TriggerScheduleType: nil,
		}
		eventTime := parseTime("2024-01-15 14:00:00")
		
		result := validator.ValidateSchedule(autoReply, eventTime, nil, timezone)
		if result.IsMatch {
			t.Error("ValidateSchedule() with no schedule type should not match")
		}
	})

	t.Run("unsupported_schedule_type", func(t *testing.T) {
		unsupportedType := WebhookTriggerScheduleType("unsupported")
		autoReply := &AutoReply{
			ID:                  1,
			TriggerScheduleType: &unsupportedType,
		}
		eventTime := parseTime("2024-01-15 14:00:00")
		
		result := validator.ValidateSchedule(autoReply, eventTime, nil, timezone)
		if result.IsMatch {
			t.Error("ValidateSchedule() with unsupported schedule type should not match")
		}
	})

	t.Run("business_hour_no_configuration", func(t *testing.T) {
		autoReply := createBusinessHourScheduleAutoReply()
		eventTime := parseTime("2024-01-15 14:00:00")
		
		result := validator.ValidateSchedule(autoReply, eventTime, []*BusinessHour{}, timezone)
		if result.IsMatch {
			t.Error("ValidateSchedule() with no business hours should not match")
		}
	})
}

func TestScheduleValidator_TimeConversions(t *testing.T) {
	validator := NewScheduleValidator()

	t.Run("timezone_conversion", func(t *testing.T) {
		// Test with different timezone
		est, _ := time.LoadLocation("America/New_York")
		autoReply := createDailyScheduleAutoReply("09:00", "17:00")
		
		// 2PM EST = 7PM UTC, but we're testing in EST context
		eventTime := time.Date(2024, 1, 15, 14, 0, 0, 0, est)
		
		result := validator.ValidateSchedule(autoReply, eventTime, nil, est)
		if !result.IsMatch {
			t.Error("ValidateSchedule() should handle timezone conversion")
		}
	})
}

// Helper functions to create test AutoReply instances

func createDailyScheduleAutoReply(startTime, endTime string) *AutoReply {
	scheduleType := WebhookTriggerScheduleTypeDaily
	schedule := DailySchedule{
		StartTime: startTime,
		EndTime:   endTime,
	}
	
	scheduleSettings := &WebhookTriggerScheduleSettings{
		Schedules: []WebhookTriggerSchedule{&schedule},
	}
	
	return &AutoReply{
		ID:                      1,
		TriggerScheduleType:     &scheduleType,
		TriggerScheduleSettings: scheduleSettings,
	}
}

func createMonthlyScheduleAutoReply(day int, startTime, endTime string) *AutoReply {
	scheduleType := WebhookTriggerScheduleTypeMonthly
	schedule := MonthlySchedule{
		Day:       day,
		StartTime: startTime,
		EndTime:   endTime,
	}
	
	scheduleSettings := &WebhookTriggerScheduleSettings{
		Schedules: []WebhookTriggerSchedule{&schedule},
	}
	
	return &AutoReply{
		ID:                      1,
		TriggerScheduleType:     &scheduleType,
		TriggerScheduleSettings: scheduleSettings,
	}
}

func createBusinessHourScheduleAutoReply() *AutoReply {
	scheduleType := WebhookTriggerScheduleTypeBusinessHour
	schedule := BusinessHourSchedule{}
	
	scheduleSettings := &WebhookTriggerScheduleSettings{
		Schedules: []WebhookTriggerSchedule{&schedule},
	}
	
	return &AutoReply{
		ID:                      1,
		TriggerScheduleType:     &scheduleType,
		TriggerScheduleSettings: scheduleSettings,
	}
}

func createNonBusinessHourScheduleAutoReply() *AutoReply {
	scheduleType := WebhookTriggerScheduleTypeNonBusinessHour
	schedule := NonBusinessHourSchedule{}
	
	scheduleSettings := &WebhookTriggerScheduleSettings{
		Schedules: []WebhookTriggerSchedule{&schedule},
	}
	
	return &AutoReply{
		ID:                      1,
		TriggerScheduleType:     &scheduleType,
		TriggerScheduleSettings: scheduleSettings,
	}
}

func createDateRangeScheduleAutoReply(startDate, endDate string) *AutoReply {
	scheduleType := WebhookTriggerScheduleTypeDateRange
	schedule := DateRangeSchedule{
		StartDate: startDate,
		EndDate:   endDate,
	}
	
	scheduleSettings := &WebhookTriggerScheduleSettings{
		Schedules: []WebhookTriggerSchedule{&schedule},
	}
	
	return &AutoReply{
		ID:                      1,
		TriggerScheduleType:     &scheduleType,
		TriggerScheduleSettings: scheduleSettings,
	}
}

func parseTime(timeStr string) time.Time {
	t, err := time.Parse("2006-01-02 15:04:05", timeStr)
	if err != nil {
		panic(err)
	}
	return t
}