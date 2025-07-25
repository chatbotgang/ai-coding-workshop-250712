package auto_reply

import (
	"encoding/json"
	"testing"
	"time"

	"github.com/chatbotgang/workshop/internal/domain/organization"
	"github.com/stretchr/testify/assert"
)

// MockTriggerSettingsFetcher for testing
type MockTriggerSettingsFetcher struct {
	Settings []*WebhookTriggerSetting
}

func (m *MockTriggerSettingsFetcher) FetchWebhookTriggerSettings(botID int, organizationID int) ([]*WebhookTriggerSetting, error) {
	return m.Settings, nil
}

// MockBusinessHourRepository for testing
type MockBusinessHourRepository struct {
	BusinessHours []*organization.BusinessHour
	Organization  *organization.Organization
}

func (m *MockBusinessHourRepository) GetBusinessHours(organizationID int) ([]*organization.BusinessHour, error) {
	return m.BusinessHours, nil
}

func (m *MockBusinessHourRepository) GetOrganization(organizationID int) (*organization.Organization, error) {
	if m.Organization != nil {
		return m.Organization, nil
	}
	return &organization.Organization{
		ID:       organizationID,
		Name:     "Test Organization",
		Timezone: "UTC",
		Enable:   true,
	}, nil
}

// Test helper to set up mock data
func setupMockTriggerSettings(settings []*WebhookTriggerSetting) {
	mockFetcher := &MockTriggerSettingsFetcher{Settings: settings}
	SetTriggerSettingsFetcher(mockFetcher)
}

// Test helper to set up mock business hours
func setupMockBusinessHours(businessHours []*organization.BusinessHour, org *organization.Organization) {
	mockRepo := &MockBusinessHourRepository{
		BusinessHours: businessHours,
		Organization:  org,
	}
	SetBusinessHourRepository(mockRepo)
}

// Reset to default fetcher after tests
func resetTriggerSettingsFetcher() {
	SetTriggerSettingsFetcher(&DefaultTriggerSettingsFetcher{})
}

// Reset to default business hour repository after tests
func resetBusinessHourRepository() {
	SetBusinessHourRepository(&DefaultBusinessHourRepository{})
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
		name        string
		message     string
		expectMatch bool
		description string
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
		name              string
		message           string
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
		name              string
		message           string
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
	// IMPORTANT: This test addresses timezone and midnight crossing issues that are critical for business hours

	// Test business hours trigger
	t.Run("business_hours_trigger", func(t *testing.T) {
		// Set up business hours: Monday-Friday 09:00-17:00 UTC
		businessHours := []*organization.BusinessHour{
			{
				ID:             1,
				OrganizationID: 1,
				Weekday:        organization.Monday,
				StartTime:      time.Date(0, 1, 1, 9, 0, 0, 0, time.UTC),
				EndTime:        time.Date(0, 1, 1, 17, 0, 0, 0, time.UTC),
			},
			{
				ID:             2,
				OrganizationID: 1,
				Weekday:        organization.Friday,
				StartTime:      time.Date(0, 1, 1, 9, 0, 0, 0, time.UTC),
				EndTime:        time.Date(0, 1, 1, 17, 0, 0, 0, time.UTC),
			},
		}

		org := &organization.Organization{
			ID:       1,
			Name:     "Test Organization",
			Timezone: "UTC",
			Enable:   true,
		}

		setupMockTriggerSettings([]*WebhookTriggerSetting{
			createTimeTrigger(1, WebhookTriggerScheduleTypeBusinessHour, nil, true),
		})
		setupMockBusinessHours(businessHours, org)
		defer resetTriggerSettingsFetcher()
		defer resetBusinessHourRepository()

		testCases := []struct {
			name        string
			testTime    time.Time
			expectMatch bool
			description string
		}{
			{
				"monday_afternoon_utc",
				time.Date(2024, 1, 1, 14, 30, 0, 0, time.UTC), // Monday 14:30 UTC
				true,
				"Monday afternoon UTC - should match business hours",
			},
			{
				"monday_late_night_utc",
				time.Date(2024, 1, 1, 23, 30, 0, 0, time.UTC), // Monday 23:30 UTC
				false,
				"Late night UTC - outside business hours",
			},
			{
				"saturday_afternoon_utc",
				time.Date(2024, 1, 6, 14, 30, 0, 0, time.UTC), // Saturday 14:30 UTC
				false,
				"Saturday afternoon - not in business hours config",
			},
			{
				"friday_afternoon_utc",
				time.Date(2024, 1, 5, 15, 0, 0, 0, time.UTC), // Friday 15:00 UTC
				true,
				"Friday afternoon - should match business hours",
			},
		}

		for _, tc := range testCases {
			t.Run(tc.name, func(t *testing.T) {
				result, err := ValidateTrigger("any message", tc.testTime, 1, 1)

				assert.NoError(t, err, "Business hours evaluation should not return error: %s", tc.description)

				if tc.expectMatch {
					assert.NotNil(t, result, "Expected business hours trigger to match: %s", tc.description)
					assert.Equal(t, 1, result.ID)
				} else {
					assert.Nil(t, result, "Expected no business hours trigger match: %s", tc.description)
				}
			})
		}
	})

	// Test non-business hours trigger
	t.Run("non_business_hours_trigger", func(t *testing.T) {
		// Set up business hours: Monday-Friday 09:00-17:00 UTC
		businessHours := []*organization.BusinessHour{
			{
				ID:             1,
				OrganizationID: 1,
				Weekday:        organization.Monday,
				StartTime:      time.Date(0, 1, 1, 9, 0, 0, 0, time.UTC),
				EndTime:        time.Date(0, 1, 1, 17, 0, 0, 0, time.UTC),
			},
			{
				ID:             2,
				OrganizationID: 1,
				Weekday:        organization.Friday,
				StartTime:      time.Date(0, 1, 1, 9, 0, 0, 0, time.UTC),
				EndTime:        time.Date(0, 1, 1, 17, 0, 0, 0, time.UTC),
			},
		}

		org := &organization.Organization{
			ID:       1,
			Name:     "Test Organization",
			Timezone: "UTC",
			Enable:   true,
		}

		setupMockTriggerSettings([]*WebhookTriggerSetting{
			createTimeTrigger(1, WebhookTriggerScheduleTypeNonBusinessHour, nil, true),
		})
		setupMockBusinessHours(businessHours, org)
		defer resetTriggerSettingsFetcher()
		defer resetBusinessHourRepository()

		testCases := []struct {
			name        string
			testTime    time.Time
			expectMatch bool
			description string
		}{
			{
				"early_morning_utc",
				time.Date(2024, 1, 1, 1, 0, 0, 0, time.UTC), // Monday 01:00 UTC
				true,
				"Early morning hours should be non-business",
			},
			{
				"sunday_afternoon_utc",
				time.Date(2024, 1, 7, 14, 30, 0, 0, time.UTC), // Sunday 14:30 UTC
				true,
				"Sunday afternoon - should be non-business",
			},
			{
				"monday_afternoon_utc",
				time.Date(2024, 1, 1, 14, 30, 0, 0, time.UTC), // Monday 14:30 UTC
				false,
				"Monday afternoon - should be business hours, not non-business",
			},
		}

		for _, tc := range testCases {
			t.Run(tc.name, func(t *testing.T) {
				result, err := ValidateTrigger("any message", tc.testTime, 1, 1)

				assert.NoError(t, err, "Non-business hours evaluation should not return error: %s", tc.description)

				if tc.expectMatch {
					assert.NotNil(t, result, "Expected non-business hours trigger to match: %s", tc.description)
					assert.Equal(t, 1, result.ID)
				} else {
					assert.Nil(t, result, "Expected no non-business hours trigger match: %s", tc.description)
				}
			})
		}
	})

	// Test for midnight crossing requirements (now implemented!)
	t.Run("midnight_crossing_scenarios", func(t *testing.T) {
		// Test night shift business hours: Friday 22:00-06:00 (crosses midnight)
		businessHours := []*organization.BusinessHour{
			{
				ID:             1,
				OrganizationID: 1,
				Weekday:        organization.Friday,
				StartTime:      time.Date(0, 1, 1, 22, 0, 0, 0, time.UTC), // 22:00
				EndTime:        time.Date(0, 1, 1, 6, 0, 0, 0, time.UTC),  // 06:00
			},
		}

		org := &organization.Organization{
			ID:       1,
			Name:     "Test Organization",
			Timezone: "UTC",
			Enable:   true,
		}

		setupMockTriggerSettings([]*WebhookTriggerSetting{
			createTimeTrigger(1, WebhookTriggerScheduleTypeBusinessHour, nil, true),
		})
		setupMockBusinessHours(businessHours, org)
		defer resetTriggerSettingsFetcher()
		defer resetBusinessHourRepository()

		testCases := []struct {
			name        string
			testTime    time.Time
			expectMatch bool
			description string
		}{
			{
				"friday_23_00_utc",
				time.Date(2024, 1, 5, 23, 0, 0, 0, time.UTC), // Friday 23:00 UTC
				true,
				"Friday 23:00 should be within 22:00-06:00 range",
			},
			{
				"friday_05_00_utc",
				time.Date(2024, 1, 5, 5, 0, 0, 0, time.UTC), // Friday 05:00 UTC
				true,
				"Friday 05:00 should be within 22:00-06:00 range (before end)",
			},
			{
				"friday_12_00_utc",
				time.Date(2024, 1, 5, 12, 0, 0, 0, time.UTC), // Friday 12:00 UTC
				false,
				"Friday 12:00 should be outside 22:00-06:00 range",
			},
			{
				"saturday_01_00_utc",
				time.Date(2024, 1, 6, 1, 0, 0, 0, time.UTC), // Saturday 01:00 UTC
				false,
				"Saturday 01:00 should not match Friday business hours",
			},
		}

		for _, tc := range testCases {
			t.Run(tc.name, func(t *testing.T) {
				result, err := ValidateTrigger("any message", tc.testTime, 1, 1)

				assert.NoError(t, err, "Midnight crossing evaluation should not return error: %s", tc.description)

				if tc.expectMatch {
					assert.NotNil(t, result, "Expected midnight crossing trigger to match: %s", tc.description)
					assert.Equal(t, 1, result.ID)
				} else {
					assert.Nil(t, result, "Expected no midnight crossing trigger match: %s", tc.description)
				}
			})
		}
	})

	// Test for timezone-aware implementation (now implemented!)
	t.Run("timezone_implementation_test", func(t *testing.T) {
		// Test timezone-aware business hours: Monday 09:00-17:00 JST (Tokyo)
		// For timezone-aware tests, we need to set the business hours correctly
		// Since our implementation uses .In() to convert to org timezone, we can use any timezone for StartTime/EndTime
		loc, err := time.LoadLocation("Asia/Tokyo")
		if err != nil {
			t.Fatalf("Failed to load Asia/Tokyo timezone: %v", err)
		}
		businessHours := []*organization.BusinessHour{
			{
				ID:             1,
				OrganizationID: 1,
				Weekday:        organization.Monday,
				StartTime:      time.Date(0, 1, 1, 9, 0, 0, 0, loc),  // 09:00 JST
				EndTime:        time.Date(0, 1, 1, 17, 0, 0, 0, loc), // 17:00 JST
			},
		}

		org := &organization.Organization{
			ID:       1,
			Name:     "Tokyo Organization",
			Timezone: "Asia/Tokyo", // JST = UTC+9
			Enable:   true,
		}

		setupMockTriggerSettings([]*WebhookTriggerSetting{
			createTimeTrigger(1, WebhookTriggerScheduleTypeBusinessHour, nil, true),
		})
		setupMockBusinessHours(businessHours, org)
		defer resetTriggerSettingsFetcher()
		defer resetBusinessHourRepository()

		testCases := []struct {
			name        string
			testTime    time.Time
			expectMatch bool
			description string
		}{
			{
				"monday_01_00_utc",
				time.Date(2024, 1, 1, 1, 0, 0, 0, time.UTC), // Monday 01:00 UTC = 10:00 JST
				true,
				"Monday 01:00 UTC = 10:00 JST should be business hours",
			},
			{
				"monday_10_00_utc",
				time.Date(2024, 1, 1, 10, 0, 0, 0, time.UTC), // Monday 10:00 UTC = 19:00 JST
				false,
				"Monday 10:00 UTC = 19:00 JST should be outside business hours",
			},
			{
				"sunday_16_00_utc",
				time.Date(2024, 1, 7, 16, 0, 0, 0, time.UTC), // Sunday 16:00 UTC = Monday 01:00 JST
				false,
				"Sunday 16:00 UTC = Monday 01:00 JST should be outside business hours",
			},
		}

		for _, tc := range testCases {
			t.Run(tc.name, func(t *testing.T) {
				result, err := ValidateTrigger("any message", tc.testTime, 1, 1)

				assert.NoError(t, err, "Timezone-aware evaluation should not return error: %s", tc.description)

				if tc.expectMatch {
					assert.NotNil(t, result, "Expected timezone-aware trigger to match: %s", tc.description)
					assert.Equal(t, 1, result.ID)
				} else {
					assert.Nil(t, result, "Expected no timezone-aware trigger match: %s", tc.description)
				}
			})
		}
	})
}

// Story 4: Priority Logic Tests
func TestPRD_Priority_Test1_KeywordOverGeneral_BothMatch(t *testing.T) {
	// PRD Test Case: [Priority-Test1]
	// Expected Result: Only the Keyword Reply is triggered, not the General Reply.

	dailySchedule := []DailySchedule{
		{StartTime: "09:00", EndTime: "17:00"},
	}

	setupMockTriggerSettings([]*WebhookTriggerSetting{
		createKeywordTrigger(1, "hello", true),                                     // Keyword trigger
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
		createKeywordTrigger(1, "hello", true),                                     // Keyword trigger
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
		createKeywordTrigger(1, "hello", true),                                     // Keyword trigger
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
