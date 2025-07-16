package auto_reply

import (
	"encoding/json"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
)

// MockTriggerSettingsFetcher for testing
type MockTriggerSettingsFetcher struct {
	Settings []*WebhookTriggerSetting
}

func (m *MockTriggerSettingsFetcher) FetchWebhookTriggerSettings(botID int, organizationID int) ([]*WebhookTriggerSetting, error) {
	return m.Settings, nil
}

// Test helper to set up mock data
func setupMockTriggerSettings(settings []*WebhookTriggerSetting) {
	mockFetcher := &MockTriggerSettingsFetcher{Settings: settings}
	SetTriggerSettingsFetcher(mockFetcher)
}

// Reset to default fetcher after tests
func resetTriggerSettingsFetcher() {
	SetTriggerSettingsFetcher(&DefaultTriggerSettingsFetcher{})
}

// Test helper to create test trigger settings
func createKeywordTrigger(id int, keyword string, enable bool) *WebhookTriggerSetting {
	return &WebhookTriggerSetting{
		ID:          id,
		BotID:       1,
		Enable:      enable,
		EventType:   EventTypeMessage,
		TriggerCode: stringPtr(keyword),
		Archived:    false,
	}
}

func createTimeTrigger(id int, scheduleType WebhookTriggerScheduleType, settings interface{}, enable bool) *WebhookTriggerSetting {
	settingsJSON, _ := json.Marshal(settings)
	return &WebhookTriggerSetting{
		ID:                      id,
		BotID:                   1,
		Enable:                  enable,
		EventType:               EventTypeTime,
		TriggerScheduleType:     &scheduleType,
		TriggerScheduleSettings: settingsJSON,
		Archived:                false,
	}
}

// Story 1: Keyword Reply Logic Tests
func TestPRD_B_P0_7_Test2_KeywordReply_ExactMatch_VariousCases(t *testing.T) {
	// PRD Test Case: [B-P0-7-Test2]
	// Expected Result: An auto-reply is triggered when a message exactly matches the keyword, regardless of case.
	
	setupMockTriggerSettings([]*WebhookTriggerSetting{
		createKeywordTrigger(1, "hello", true),
	})
	defer resetTriggerSettingsFetcher()
	
	testTime := time.Date(2024, 1, 1, 14, 30, 0, 0, time.UTC)
	
	tests := []struct {
		name         string
		message      string
		expectMatch  bool
		description  string
	}{
		{"lowercase exact match", "hello", true, "exact match with same case"},
		{"uppercase exact match", "HELLO", true, "exact match with different case"},
		{"mixed case exact match", "HeLLo", true, "exact match with mixed case"},
		{"capitalized exact match", "Hello", true, "exact match with capitalization"},
	}
	
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result, err := ValidateTrigger(tt.message, testTime, 1, 1)
			assert.NoError(t, err)
			
			if tt.expectMatch {
				assert.NotNil(t, result, "Expected trigger to match for: %s", tt.description)
				assert.Equal(t, 1, result.ID, "Expected trigger ID 1 to match")
			} else {
				assert.Nil(t, result, "Expected no trigger to match for: %s", tt.description)
			}
		})
	}
}

func TestPRD_B_P0_7_Test3_KeywordReply_LeadingTrailingSpaces(t *testing.T) {
	// PRD Test Case: [B-P0-7-Test3]
	// Expected Result: Leading and trailing spaces are trimmed, and the auto-reply is triggered if the core keyword matches exactly.
	
	setupMockTriggerSettings([]*WebhookTriggerSetting{
		createKeywordTrigger(1, "hello", true),
	})
	defer resetTriggerSettingsFetcher()
	
	testTime := time.Date(2024, 1, 1, 14, 30, 0, 0, time.UTC)
	
	tests := []struct {
		name    string
		message string
	}{
		{"leading spaces", "  hello"},
		{"trailing spaces", "hello  "},
		{"leading and trailing spaces", "  hello  "},
		{"multiple spaces", "   hello   "},
		{"tabs and spaces", "\t hello \t"},
	}
	
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result, err := ValidateTrigger(tt.message, testTime, 1, 1)
			assert.NoError(t, err)
			assert.NotNil(t, result, "Expected trigger to match when spaces are trimmed")
			assert.Equal(t, 1, result.ID)
		})
	}
}

func TestPRD_B_P0_7_Test4_KeywordReply_ContainsKeyword_NoMatch(t *testing.T) {
	// PRD Test Case: [B-P0-7-Test4]
	// Expected Result: The auto-reply is NOT triggered as the match must be exact.
	
	setupMockTriggerSettings([]*WebhookTriggerSetting{
		createKeywordTrigger(1, "hello", true),
	})
	defer resetTriggerSettingsFetcher()
	
	testTime := time.Date(2024, 1, 1, 14, 30, 0, 0, time.UTC)
	
	tests := []struct {
		name    string
		message string
	}{
		{"keyword with additional text", "hello world"},
		{"keyword at start", "hello there"},
		{"keyword at end", "say hello"},
		{"keyword in middle", "say hello there"},
		{"keyword with punctuation", "hello!"},
		{"keyword with numbers", "hello123"},
	}
	
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result, err := ValidateTrigger(tt.message, testTime, 1, 1)
			assert.NoError(t, err)
			assert.Nil(t, result, "Expected no trigger match for partial match: %s", tt.message)
		})
	}
}

func TestPRD_B_P0_7_Test5_KeywordReply_PartialMatch_NoMatch(t *testing.T) {
	// PRD Test Case: [B-P0-7-Test5]
	// Expected Result: The auto-reply is NOT triggered.
	
	setupMockTriggerSettings([]*WebhookTriggerSetting{
		createKeywordTrigger(1, "hello", true),
	})
	defer resetTriggerSettingsFetcher()
	
	testTime := time.Date(2024, 1, 1, 14, 30, 0, 0, time.UTC)
	
	tests := []struct {
		name    string
		message string
	}{
		{"partial match - prefix", "hell"},
		{"partial match - suffix", "ello"},
		{"similar word", "hallo"},
		{"typo", "helo"},
		{"different word", "goodbye"},
		{"empty message", ""},
	}
	
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result, err := ValidateTrigger(tt.message, testTime, 1, 1)
			if tt.message == "" {
				assert.Error(t, err, "Expected error for empty message")
				return
			}
			assert.NoError(t, err)
			assert.Nil(t, result, "Expected no trigger match for partial/variation: %s", tt.message)
		})
	}
}

// Story 2: Multiple Keywords Support Tests
func TestPRD_Multiple_Keywords_Test1_MultipleKeywords_EachTriggers(t *testing.T) {
	// PRD Test Case: [Multiple-Keywords-Test1]
	// Expected Result: The auto-reply is triggered when any of the configured keywords matches exactly.
	// Note: Current implementation uses single TriggerCode, so we simulate multiple keywords with separate triggers
	
	setupMockTriggerSettings([]*WebhookTriggerSetting{
		createKeywordTrigger(1, "hello", true),
		createKeywordTrigger(2, "hi", true),
		createKeywordTrigger(3, "hey", true),
	})
	defer resetTriggerSettingsFetcher()
	
	testTime := time.Date(2024, 1, 1, 14, 30, 0, 0, time.UTC)
	
	tests := []struct {
		name           string
		message        string
		expectedTriggerID int
	}{
		{"first keyword", "hello", 1},
		{"second keyword", "hi", 2},
		{"third keyword", "hey", 3},
	}
	
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result, err := ValidateTrigger(tt.message, testTime, 1, 1)
			assert.NoError(t, err)
			assert.NotNil(t, result, "Expected trigger to match for keyword: %s", tt.message)
			assert.Equal(t, tt.expectedTriggerID, result.ID)
		})
	}
}

func TestPRD_Multiple_Keywords_Test2_CaseInsensitive_MultipleKeywords(t *testing.T) {
	// PRD Test Case: [Multiple-Keywords-Test2]
	// Expected Result: The auto-reply is triggered due to case-insensitive matching.
	
	setupMockTriggerSettings([]*WebhookTriggerSetting{
		createKeywordTrigger(1, "hello", true),
		createKeywordTrigger(2, "hi", true),
	})
	defer resetTriggerSettingsFetcher()
	
	testTime := time.Date(2024, 1, 1, 14, 30, 0, 0, time.UTC)
	
	tests := []struct {
		name           string
		message        string
		expectedTriggerID int
	}{
		{"uppercase first keyword", "HELLO", 1},
		{"uppercase second keyword", "HI", 2},
		{"mixed case first keyword", "HeLLo", 1},
		{"mixed case second keyword", "Hi", 2},
	}
	
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result, err := ValidateTrigger(tt.message, testTime, 1, 1)
			assert.NoError(t, err)
			assert.NotNil(t, result, "Expected case-insensitive match for: %s", tt.message)
			assert.Equal(t, tt.expectedTriggerID, result.ID)
		})
	}
}

func TestPRD_Multiple_Keywords_Test3_NoMatch_MultipleKeywords(t *testing.T) {
	// PRD Test Case: [Multiple-Keywords-Test3]
	// Expected Result: The auto-reply is NOT triggered.
	
	setupMockTriggerSettings([]*WebhookTriggerSetting{
		createKeywordTrigger(1, "hello", true),
		createKeywordTrigger(2, "hi", true),
	})
	defer resetTriggerSettingsFetcher()
	
	testTime := time.Date(2024, 1, 1, 14, 30, 0, 0, time.UTC)
	
	tests := []struct {
		name    string
		message string
	}{
		{"different word", "goodbye"},
		{"partial match", "hel"},
		{"combined keywords", "hello hi"},
		{"similar word", "help"},
	}
	
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result, err := ValidateTrigger(tt.message, testTime, 1, 1)
			assert.NoError(t, err)
			assert.Nil(t, result, "Expected no match for: %s", tt.message)
		})
	}
}

// Story 3: General Time-based Logic Tests
func TestPRD_B_P0_6_Test3_GeneralReply_DailySchedule(t *testing.T) {
	// PRD Test Case: [B-P0-6-Test3]
	// Expected Result: An auto-reply is sent when a message is received within the scheduled daily time.
	
	dailySchedule := []DailySchedule{
		{StartTime: "09:00", EndTime: "17:00"},
	}
	
	setupMockTriggerSettings([]*WebhookTriggerSetting{
		createTimeTrigger(1, WebhookTriggerScheduleTypeDaily, dailySchedule, true),
	})
	defer resetTriggerSettingsFetcher()
	
	tests := []struct {
		name        string
		eventTime   time.Time
		expectMatch bool
		description string
	}{
		{
			"within daily schedule",
			time.Date(2024, 1, 1, 14, 30, 0, 0, time.UTC),
			true,
			"14:30 is within 09:00-17:00",
		},
		{
			"at start of schedule",
			time.Date(2024, 1, 1, 9, 0, 0, 0, time.UTC),
			true,
			"09:00 is at the start of 09:00-17:00",
		},
		{
			"at end of schedule",
			time.Date(2024, 1, 1, 17, 0, 0, 0, time.UTC),
			false,
			"17:00 is at the end of 09:00-17:00 (exclusive)",
		},
		{
			"before schedule",
			time.Date(2024, 1, 1, 8, 30, 0, 0, time.UTC),
			false,
			"08:30 is before 09:00-17:00",
		},
		{
			"after schedule",
			time.Date(2024, 1, 1, 18, 0, 0, 0, time.UTC),
			false,
			"18:00 is after 09:00-17:00",
		},
	}
	
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result, err := ValidateTrigger("any message", tt.eventTime, 1, 1)
			assert.NoError(t, err)
			
			if tt.expectMatch {
				assert.NotNil(t, result, "Expected daily schedule match: %s", tt.description)
				assert.Equal(t, 1, result.ID)
			} else {
				assert.Nil(t, result, "Expected no daily schedule match: %s", tt.description)
			}
		})
	}
}

func TestPRD_B_P0_6_Test4_GeneralReply_MonthlySchedule(t *testing.T) {
	// PRD Test Case: [B-P0-6-Test4]
	// Expected Result: An auto-reply is sent when a message is received on a scheduled monthly date and time.
	
	monthlySchedule := []MonthlySchedule{
		{Day: 15, StartTime: "10:00", EndTime: "12:00"},
	}
	
	setupMockTriggerSettings([]*WebhookTriggerSetting{
		createTimeTrigger(1, WebhookTriggerScheduleTypeMonthly, monthlySchedule, true),
	})
	defer resetTriggerSettingsFetcher()
	
	tests := []struct {
		name        string
		eventTime   time.Time
		expectMatch bool
		description string
	}{
		{
			"correct day and time",
			time.Date(2024, 1, 15, 11, 0, 0, 0, time.UTC),
			true,
			"January 15th at 11:00 matches monthly schedule",
		},
		{
			"correct day, wrong time",
			time.Date(2024, 1, 15, 14, 0, 0, 0, time.UTC),
			false,
			"January 15th at 14:00 is outside 10:00-12:00",
		},
		{
			"wrong day, correct time",
			time.Date(2024, 1, 20, 11, 0, 0, 0, time.UTC),
			false,
			"January 20th doesn't match monthly day 15",
		},
		{
			"different month, correct day and time",
			time.Date(2024, 2, 15, 11, 0, 0, 0, time.UTC),
			true,
			"February 15th at 11:00 matches monthly schedule",
		},
	}
	
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result, err := ValidateTrigger("any message", tt.eventTime, 1, 1)
			assert.NoError(t, err)
			
			if tt.expectMatch {
				assert.NotNil(t, result, "Expected monthly schedule match: %s", tt.description)
				assert.Equal(t, 1, result.ID)
			} else {
				assert.Nil(t, result, "Expected no monthly schedule match: %s", tt.description)
			}
		})
	}
}

func TestPRD_B_P0_6_Test5_GeneralReply_BusinessHours(t *testing.T) {
	// PRD Test Case: [B-P0-6-Test5]
	// Expected Result: An auto-reply is sent based on whether the message is received during reply hours or non-reply hours.
	// Note: Business hours are not yet implemented, so this test validates the current behavior
	
	setupMockTriggerSettings([]*WebhookTriggerSetting{
		createTimeTrigger(1, WebhookTriggerScheduleTypeBusinessHour, nil, true),
	})
	defer resetTriggerSettingsFetcher()
	
	testTime := time.Date(2024, 1, 1, 14, 30, 0, 0, time.UTC)
	
	// Since business hours are not implemented, we expect an error
	result, err := ValidateTrigger("any message", testTime, 1, 1)
	assert.Error(t, err, "Expected error for unimplemented business hours")
	assert.Contains(t, err.Error(), "business hour evaluation not yet implemented")
	assert.Nil(t, result)
}

// Story 4: Priority Logic Tests
func TestPRD_Priority_Test1_KeywordOverGeneral_BothMatch(t *testing.T) {
	// PRD Test Case: [Priority-Test1]
	// Expected Result: Only the Keyword Reply is triggered, not the General Reply.
	
	dailySchedule := []DailySchedule{
		{StartTime: "09:00", EndTime: "17:00"},
	}
	
	setupMockTriggerSettings([]*WebhookTriggerSetting{
		createKeywordTrigger(1, "hello", true),                                                      // Keyword trigger
		createTimeTrigger(2, WebhookTriggerScheduleTypeDaily, dailySchedule, true), // Time trigger
	})
	defer resetTriggerSettingsFetcher()
	
	// Send message during time window that matches keyword
	testTime := time.Date(2024, 1, 1, 14, 30, 0, 0, time.UTC) // Within 09:00-17:00
	
	result, err := ValidateTrigger("hello", testTime, 1, 1)
	assert.NoError(t, err)
	assert.NotNil(t, result, "Expected keyword trigger to match")
	assert.Equal(t, 1, result.ID, "Expected keyword trigger (ID 1) to have priority over time trigger (ID 2)")
}

func TestPRD_Priority_Test2_OnlyGeneral_KeywordNoMatch(t *testing.T) {
	// PRD Test Case: [Priority-Test2]
	// Expected Result: Only the General Reply is triggered.
	
	dailySchedule := []DailySchedule{
		{StartTime: "09:00", EndTime: "17:00"},
	}
	
	setupMockTriggerSettings([]*WebhookTriggerSetting{
		createKeywordTrigger(1, "hello", true),                                                      // Keyword trigger
		createTimeTrigger(2, WebhookTriggerScheduleTypeDaily, dailySchedule, true), // Time trigger
	})
	defer resetTriggerSettingsFetcher()
	
	// Send message during time window that doesn't match keyword
	testTime := time.Date(2024, 1, 1, 14, 30, 0, 0, time.UTC) // Within 09:00-17:00
	
	result, err := ValidateTrigger("goodbye", testTime, 1, 1)
	assert.NoError(t, err)
	assert.NotNil(t, result, "Expected time trigger to match")
	assert.Equal(t, 2, result.ID, "Expected time trigger (ID 2) to match when keyword doesn't match")
}

func TestPRD_Priority_Test3_OnlyKeyword_OutsideTimeWindow(t *testing.T) {
	// PRD Test Case: [Priority-Test3]
	// Expected Result: Only the Keyword Reply is triggered.
	
	dailySchedule := []DailySchedule{
		{StartTime: "09:00", EndTime: "17:00"},
	}
	
	setupMockTriggerSettings([]*WebhookTriggerSetting{
		createKeywordTrigger(1, "hello", true),                                                      // Keyword trigger
		createTimeTrigger(2, WebhookTriggerScheduleTypeDaily, dailySchedule, true), // Time trigger
	})
	defer resetTriggerSettingsFetcher()
	
	// Send message outside time window that matches keyword
	testTime := time.Date(2024, 1, 1, 20, 0, 0, 0, time.UTC) // Outside 09:00-17:00
	
	result, err := ValidateTrigger("hello", testTime, 1, 1)
	assert.NoError(t, err)
	assert.NotNil(t, result, "Expected keyword trigger to match")
	assert.Equal(t, 1, result.ID, "Expected keyword trigger to match even outside time window")
}

// Story 5: Message Content Handling Tests
func TestPRD_Message_Content_Test1_KeywordReply_ExactMatch(t *testing.T) {
	// PRD Test Case: [Message-Content-Test1]
	// Expected Result: The keyword reply is triggered when the message contains the exact keyword.
	
	setupMockTriggerSettings([]*WebhookTriggerSetting{
		createKeywordTrigger(1, "support", true),
	})
	defer resetTriggerSettingsFetcher()
	
	testTime := time.Date(2024, 1, 1, 14, 30, 0, 0, time.UTC)
	
	result, err := ValidateTrigger("support", testTime, 1, 1)
	assert.NoError(t, err)
	assert.NotNil(t, result, "Expected keyword trigger to match exact keyword")
	assert.Equal(t, 1, result.ID)
}

func TestPRD_Message_Content_Test2_NoKeywordMatch(t *testing.T) {
	// PRD Test Case: [Message-Content-Test2]
	// Expected Result: No keyword reply is triggered when the message has no matching keyword.
	
	setupMockTriggerSettings([]*WebhookTriggerSetting{
		createKeywordTrigger(1, "support", true),
		createKeywordTrigger(2, "help", true),
	})
	defer resetTriggerSettingsFetcher()
	
	testTime := time.Date(2024, 1, 1, 14, 30, 0, 0, time.UTC)
	
	result, err := ValidateTrigger("information", testTime, 1, 1)
	assert.NoError(t, err)
	assert.Nil(t, result, "Expected no keyword trigger match for non-matching message")
}

func TestPRD_Message_Content_Test3_GeneralReply_AnyContent(t *testing.T) {
	// PRD Test Case: [Message-Content-Test3]
	// Expected Result: The general reply is triggered regardless of message content when schedule matches.
	
	dailySchedule := []DailySchedule{
		{StartTime: "09:00", EndTime: "17:00"},
	}
	
	setupMockTriggerSettings([]*WebhookTriggerSetting{
		createTimeTrigger(1, WebhookTriggerScheduleTypeDaily, dailySchedule, true),
	})
	defer resetTriggerSettingsFetcher()
	
	testTime := time.Date(2024, 1, 1, 14, 30, 0, 0, time.UTC) // Within 09:00-17:00
	
	testMessages := []string{
		"random message",
		"12345",
		"hello world",
		"@#$%^&*",
		"very long message with lots of text that doesn't match any keyword",
	}
	
	for _, message := range testMessages {
		t.Run("message: "+message, func(t *testing.T) {
			result, err := ValidateTrigger(message, testTime, 1, 1)
			assert.NoError(t, err)
			assert.NotNil(t, result, "Expected time trigger to match regardless of message content")
			assert.Equal(t, 1, result.ID)
		})
	}
}

// Additional Edge Cases and Integration Tests
func TestPRD_Integration_ActiveVsInactive_Triggers(t *testing.T) {
	// Test that only active triggers are evaluated
	setupMockTriggerSettings([]*WebhookTriggerSetting{
		createKeywordTrigger(1, "hello", false), // Inactive
		createKeywordTrigger(2, "hello", true),  // Active
	})
	defer resetTriggerSettingsFetcher()
	
	testTime := time.Date(2024, 1, 1, 14, 30, 0, 0, time.UTC)
	
	result, err := ValidateTrigger("hello", testTime, 1, 1)
	assert.NoError(t, err)
	assert.NotNil(t, result, "Expected active trigger to match")
	assert.Equal(t, 2, result.ID, "Expected active trigger (ID 2) to match, not inactive (ID 1)")
}

func TestPRD_Integration_ArchivedTriggers(t *testing.T) {
	// Test that archived triggers are not evaluated
	archivedTrigger := createKeywordTrigger(1, "hello", true)
	archivedTrigger.Archived = true
	
	setupMockTriggerSettings([]*WebhookTriggerSetting{
		archivedTrigger,
		createKeywordTrigger(2, "hello", true), // Active
	})
	defer resetTriggerSettingsFetcher()
	
	testTime := time.Date(2024, 1, 1, 14, 30, 0, 0, time.UTC)
	
	result, err := ValidateTrigger("hello", testTime, 1, 1)
	assert.NoError(t, err)
	assert.NotNil(t, result, "Expected non-archived trigger to match")
	assert.Equal(t, 2, result.ID, "Expected non-archived trigger (ID 2) to match, not archived (ID 1)")
}

func TestPRD_Integration_NoTriggersConfigured(t *testing.T) {
	// Test behavior when no triggers are configured
	setupMockTriggerSettings([]*WebhookTriggerSetting{})
	defer resetTriggerSettingsFetcher()
	
	testTime := time.Date(2024, 1, 1, 14, 30, 0, 0, time.UTC)
	
	result, err := ValidateTrigger("hello", testTime, 1, 1)
	assert.NoError(t, err)
	assert.Nil(t, result, "Expected no match when no triggers are configured")
}