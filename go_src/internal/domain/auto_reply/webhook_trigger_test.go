package auto_reply

import (
	"encoding/json"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
)

// Test helper to create a pointer to string
func stringPtr(s string) *string {
	return &s
}

// Test helper to create a pointer to WebhookTriggerScheduleType
func scheduleTypePtr(t WebhookTriggerScheduleType) *WebhookTriggerScheduleType {
	return &t
}

// Test helper to create JSON settings
func createJSONSettings(v interface{}) json.RawMessage {
	data, _ := json.Marshal(v)
	return data
}

func TestNormalizeKeyword(t *testing.T) {
	tests := []struct {
		name     string
		input    string
		expected string
	}{
		{"lowercase", "hello", "hello"},
		{"uppercase", "HELLO", "hello"},
		{"mixed case", "HeLLo", "hello"},
		{"with spaces", "  hello  ", "hello"},
		{"empty string", "", ""},
		{"only spaces", "   ", ""},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := normalizeKeyword(tt.input)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestMatchesKeyword(t *testing.T) {
	tests := []struct {
		name         string
		message      string
		keywords     []string
		expectedMatch bool
	}{
		// PRD Test Cases
		{"exact match lowercase", "hello", []string{"hello"}, true},
		{"exact match uppercase", "HELLO", []string{"hello"}, true},
		{"exact match with spaces", "  hello  ", []string{"hello"}, true},
		{"partial match should fail", "hello world", []string{"hello"}, false},
		{"no match", "goodbye", []string{"hello"}, false},
		{"multiple keywords - first match", "hello", []string{"hello", "hi"}, true},
		{"multiple keywords - second match", "hi", []string{"hello", "hi"}, true},
		{"multiple keywords - no match", "goodbye", []string{"hello", "hi"}, false},
		{"empty keywords", "hello", []string{}, false},
		{"empty message", "", []string{"hello"}, false},
		{"empty keyword in list", "hello", []string{"", "hello"}, true},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := matchesKeyword(tt.message, tt.keywords)
			assert.Equal(t, tt.expectedMatch, result)
		})
	}
}

func TestIsKeywordTrigger(t *testing.T) {
	tests := []struct {
		name      string
		eventType WebhookTriggerEventType
		expected  bool
	}{
		{"MESSAGE", EventTypeMessage, true},
		{"POSTBACK", EventTypePostback, true},
		{"BEACON", EventTypeBeacon, true},
		{"MESSAGE_EDITOR", EventTypeMessageEditor, true},
		{"POSTBACK_EDITOR", EventTypePostbackEditor, true},
		{"TIME", EventTypeTime, false},
		{"FOLLOW", EventTypeFollow, false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			setting := &WebhookTriggerSetting{EventType: tt.eventType}
			result := isKeywordTrigger(setting)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestIsTimeTrigger(t *testing.T) {
	tests := []struct {
		name      string
		eventType WebhookTriggerEventType
		expected  bool
	}{
		{"TIME", EventTypeTime, true},
		{"MESSAGE", EventTypeMessage, false},
		{"POSTBACK", EventTypePostback, false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			setting := &WebhookTriggerSetting{EventType: tt.eventType}
			result := isTimeTrigger(setting)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestExtractKeywords(t *testing.T) {
	tests := []struct {
		name     string
		setting  *WebhookTriggerSetting
		expected []string
	}{
		{"with trigger code", &WebhookTriggerSetting{TriggerCode: stringPtr("hello")}, []string{"hello"}},
		{"empty trigger code", &WebhookTriggerSetting{TriggerCode: stringPtr("")}, []string{}},
		{"nil trigger code", &WebhookTriggerSetting{TriggerCode: nil}, []string{}},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := extractKeywords(tt.setting)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestEvaluateKeywordTrigger(t *testing.T) {
	tests := []struct {
		name     string
		setting  *WebhookTriggerSetting
		message  string
		expected bool
	}{
		{
			"keyword trigger matches",
			&WebhookTriggerSetting{
				EventType:   EventTypeMessage,
				TriggerCode: stringPtr("hello"),
			},
			"hello",
			true,
		},
		{
			"keyword trigger no match",
			&WebhookTriggerSetting{
				EventType:   EventTypeMessage,
				TriggerCode: stringPtr("hello"),
			},
			"goodbye",
			false,
		},
		{
			"time trigger ignored",
			&WebhookTriggerSetting{
				EventType:   EventTypeTime,
				TriggerCode: stringPtr("hello"),
			},
			"hello",
			false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := evaluateKeywordTrigger(tt.setting, tt.message)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestParseTimeString(t *testing.T) {
	tests := []struct {
		name        string
		timeStr     string
		expectedH   int
		expectedM   int
		expectError bool
	}{
		{"valid time", "14:30", 14, 30, false},
		{"midnight", "00:00", 0, 0, false},
		{"end of day", "23:59", 23, 59, false},
		{"invalid format", "14:30:00", 0, 0, true},
		{"invalid hour", "25:30", 0, 0, true},
		{"invalid minute", "14:60", 0, 0, true},
		{"empty string", "", 0, 0, true},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			hour, minute, err := parseTimeString(tt.timeStr)
			if tt.expectError {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
				assert.Equal(t, tt.expectedH, hour)
				assert.Equal(t, tt.expectedM, minute)
			}
		})
	}
}

func TestIsInTimeRange(t *testing.T) {
	// Create a test time: 2024-01-01 14:30:00
	testTime := time.Date(2024, 1, 1, 14, 30, 0, 0, time.UTC)

	tests := []struct {
		name        string
		eventTime   time.Time
		startTime   string
		endTime     string
		expected    bool
		expectError bool
	}{
		{"within range", testTime, "14:00", "15:00", true, false},
		{"exactly at start", testTime, "14:30", "15:00", true, false},
		{"exactly at end", testTime, "14:00", "14:30", false, false},
		{"outside range", testTime, "15:00", "16:00", false, false},
		{"midnight crossing - within", time.Date(2024, 1, 1, 23, 30, 0, 0, time.UTC), "22:00", "06:00", true, false},
		{"midnight crossing - outside", time.Date(2024, 1, 1, 12, 30, 0, 0, time.UTC), "22:00", "06:00", false, false},
		{"invalid start time", testTime, "25:00", "15:00", false, true},
		{"invalid end time", testTime, "14:00", "25:00", false, true},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result, err := isInTimeRange(tt.eventTime, tt.startTime, tt.endTime)
			if tt.expectError {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
				assert.Equal(t, tt.expected, result)
			}
		})
	}
}

func TestEvaluateDailySchedule(t *testing.T) {
	testTime := time.Date(2024, 1, 1, 14, 30, 0, 0, time.UTC)

	tests := []struct {
		name           string
		scheduleSettings json.RawMessage
		eventTime      time.Time
		expected       bool
		expectError    bool
	}{
		{
			"matches single schedule",
			createJSONSettings([]DailySchedule{
				{StartTime: "14:00", EndTime: "15:00"},
			}),
			testTime,
			true,
			false,
		},
		{
			"matches second schedule",
			createJSONSettings([]DailySchedule{
				{StartTime: "10:00", EndTime: "12:00"},
				{StartTime: "14:00", EndTime: "16:00"},
			}),
			testTime,
			true,
			false,
		},
		{
			"no match",
			createJSONSettings([]DailySchedule{
				{StartTime: "10:00", EndTime: "12:00"},
			}),
			testTime,
			false,
			false,
		},
		{
			"nil settings",
			nil,
			testTime,
			false,
			true,
		},
		{
			"invalid JSON",
			json.RawMessage(`invalid json`),
			testTime,
			false,
			true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result, err := evaluateDailySchedule(tt.scheduleSettings, tt.eventTime)
			if tt.expectError {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
				assert.Equal(t, tt.expected, result)
			}
		})
	}
}

func TestEvaluateMonthlySchedule(t *testing.T) {
	// Test time: January 15th, 14:30
	testTime := time.Date(2024, 1, 15, 14, 30, 0, 0, time.UTC)

	tests := []struct {
		name           string
		scheduleSettings json.RawMessage
		eventTime      time.Time
		expected       bool
		expectError    bool
	}{
		{
			"matches day and time",
			createJSONSettings([]MonthlySchedule{
				{Day: 15, StartTime: "14:00", EndTime: "15:00"},
			}),
			testTime,
			true,
			false,
		},
		{
			"matches day, wrong time",
			createJSONSettings([]MonthlySchedule{
				{Day: 15, StartTime: "10:00", EndTime: "12:00"},
			}),
			testTime,
			false,
			false,
		},
		{
			"wrong day",
			createJSONSettings([]MonthlySchedule{
				{Day: 20, StartTime: "14:00", EndTime: "15:00"},
			}),
			testTime,
			false,
			false,
		},
		{
			"multiple schedules - second matches",
			createJSONSettings([]MonthlySchedule{
				{Day: 10, StartTime: "14:00", EndTime: "15:00"},
				{Day: 15, StartTime: "14:00", EndTime: "15:00"},
			}),
			testTime,
			true,
			false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result, err := evaluateMonthlySchedule(tt.scheduleSettings, tt.eventTime)
			if tt.expectError {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
				assert.Equal(t, tt.expected, result)
			}
		})
	}
}

func TestEvaluateTimeBasedTrigger(t *testing.T) {
	testTime := time.Date(2024, 1, 1, 14, 30, 0, 0, time.UTC)

	tests := []struct {
		name         string
		setting      *WebhookTriggerSetting
		eventTime    time.Time
		orgID        int
		expected     bool
		expectError  bool
	}{
		{
			"daily schedule match",
			&WebhookTriggerSetting{
				EventType:               EventTypeTime,
				TriggerScheduleType:     scheduleTypePtr(WebhookTriggerScheduleTypeDaily),
				TriggerScheduleSettings: createJSONSettings([]DailySchedule{{StartTime: "14:00", EndTime: "15:00"}}),
			},
			testTime,
			1,
			true,
			false,
		},
		{
			"monthly schedule match",
			&WebhookTriggerSetting{
				EventType:               EventTypeTime,
				TriggerScheduleType:     scheduleTypePtr(WebhookTriggerScheduleTypeMonthly),
				TriggerScheduleSettings: createJSONSettings([]MonthlySchedule{{Day: 1, StartTime: "14:00", EndTime: "15:00"}}),
			},
			testTime,
			1,
			true,
			false,
		},
		{
			"non-time trigger",
			&WebhookTriggerSetting{
				EventType: EventTypeMessage,
			},
			testTime,
			1,
			false,
			false,
		},
		{
			"nil schedule type",
			&WebhookTriggerSetting{
				EventType:           EventTypeTime,
				TriggerScheduleType: nil,
			},
			testTime,
			1,
			false,
			true,
		},
		{
			"business hour - not implemented",
			&WebhookTriggerSetting{
				EventType:           EventTypeTime,
				TriggerScheduleType: scheduleTypePtr(WebhookTriggerScheduleTypeBusinessHour),
			},
			testTime,
			1,
			false,
			true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result, err := evaluateTimeBasedTrigger(tt.setting, tt.eventTime, tt.orgID)
			if tt.expectError {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
				assert.Equal(t, tt.expected, result)
			}
		})
	}
}

func TestValidateTrigger_InputValidation(t *testing.T) {
	validTime := time.Date(2024, 1, 1, 14, 30, 0, 0, time.UTC)

	tests := []struct {
		name            string
		messageContent  string
		eventTime       time.Time
		botID           int
		organizationID  int
		expectError     bool
		errorContains   string
	}{
		{"valid inputs", "hello", validTime, 1, 1, false, ""},
		{"empty message", "", validTime, 1, 1, true, "messageContent cannot be empty"},
		{"zero bot ID", "hello", validTime, 0, 1, true, "botID must be positive"},
		{"negative bot ID", "hello", validTime, -1, 1, true, "botID must be positive"},
		{"zero organization ID", "hello", validTime, 1, 0, true, "organizationID must be positive"},
		{"negative organization ID", "hello", validTime, 1, -1, true, "organizationID must be positive"},
		{"zero time", "hello", time.Time{}, 1, 1, true, "eventTime cannot be zero"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result, err := ValidateTrigger(tt.messageContent, tt.eventTime, tt.botID, tt.organizationID)
			if tt.expectError {
				assert.Error(t, err)
				assert.Contains(t, err.Error(), tt.errorContains)
				assert.Nil(t, result)
			} else {
				assert.NoError(t, err)
				// With mock implementation, should return nil (no match)
				assert.Nil(t, result)
			}
		})
	}
}