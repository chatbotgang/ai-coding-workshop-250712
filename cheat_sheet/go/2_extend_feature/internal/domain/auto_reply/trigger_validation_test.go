package auto_reply

import (
	"encoding/json"
	"testing"
	"time"

	"github.com/chatbotgang/workshop/internal/domain/organization"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// Helper functions for tests
func stringPtr(s string) *string {
	return &s
}

func intPtr(i int) *int {
	return &i
}

func parseTime(timeStr string) time.Time {
	t, _ := time.Parse("15:04", timeStr)
	return t
}

func parseDateTime(dateTimeStr string) time.Time {
	t, _ := time.Parse("2006-01-02 15:04:05", dateTimeStr)
	return t
}

// TestNormalizeKeyword tests the keyword normalization function
func TestNormalizeKeyword(t *testing.T) {
	t.Parallel()

	tests := []struct {
		name     string
		input    string
		expected string
	}{
		{"lowercase", "hello", "hello"},
		{"uppercase", "HELLO", "hello"},
		{"mixed case", "HeLLo", "hello"},
		{"leading spaces", "  hello", "hello"},
		{"trailing spaces", "hello  ", "hello"},
		{"both spaces", "  hello  ", "hello"},
		{"multiple spaces", "  hello world  ", "hello world"},
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

// TestValidateKeywordTrigger tests keyword trigger validation
func TestValidateKeywordTrigger(t *testing.T) {
	t.Parallel()

	// Create test aggregate
	aggregate := &AutoReplyChannelSettingAggregate{
		BotID: 1,
		TriggerSettings: []AutoReplyTriggerSetting{
			{
				AutoReplyID:       1,
				AutoReplyPriority: 10,
				AutoReplyStatus:   AutoReplyStatusActive,
				WebhookTriggerID:  1,
				BotID:             1,
				Enable:            true,
				EventType:         EventTypeMessage,
				Keywords:          []string{"hello", "hi"},
				Archived:          false,
			},
			{
				AutoReplyID:       2,
				AutoReplyPriority: 5,
				AutoReplyStatus:   AutoReplyStatusActive,
				WebhookTriggerID:  2,
				BotID:             1,
				Enable:            true,
				EventType:         EventTypeMessage,
				Keywords:          []string{"hello"},
				Archived:          false,
			},
		},
	}

	tests := []struct {
		name        string
		messageText *string
		expected    *int // AutoReplyID of expected match
	}{
		{
			name:        "exact match hello",
			messageText: stringPtr("hello"),
			expected:    intPtr(1), // Higher priority (10 > 5)
		},
		{
			name:        "exact match hi",
			messageText: stringPtr("hi"),
			expected:    intPtr(1), // Only matches first setting
		},
		{
			name:        "case insensitive HELLO",
			messageText: stringPtr("HELLO"),
			expected:    intPtr(1), // Higher priority
		},
		{
			name:        "trim spaces",
			messageText: stringPtr("  hello  "),
			expected:    intPtr(1), // Higher priority
		},
		{
			name:        "partial match should fail",
			messageText: stringPtr("hello world"),
			expected:    nil, // No match
		},
		{
			name:        "no message text",
			messageText: nil,
			expected:    nil, // No match
		},
		{
			name:        "no keyword match",
			messageText: stringPtr("goodbye"),
			expected:    nil, // No match
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			event := WebhookEvent{
				EventType:   "message",
				MessageText: tt.messageText,
				Timestamp:   time.Now(),
				ChannelType: organization.BotTypeLine,
			}

			result, err := aggregate.validateKeywordTrigger(event)
			require.NoError(t, err)

			if tt.expected == nil {
				assert.Nil(t, result)
			} else {
				require.NotNil(t, result)
				assert.Equal(t, *tt.expected, result.AutoReplyID)
			}
		})
	}
}

// TestValidateGeneralTimeTrigger tests general time-based trigger validation
func TestValidateGeneralTimeTrigger(t *testing.T) {
	t.Parallel()

	// Create daily schedule settings
	dailySettings, _ := json.Marshal([]map[string]string{
		{"start_time": "09:00", "end_time": "17:00"},
	})

	// Create monthly schedule settings
	monthlySettings, _ := json.Marshal([]map[string]interface{}{
		{"day": 15, "start_time": "10:00", "end_time": "12:00"},
	})

	// Create test aggregate
	aggregate := &AutoReplyChannelSettingAggregate{
		BotID: 1,
		TriggerSettings: []AutoReplyTriggerSetting{
			{
				AutoReplyID:             1,
				AutoReplyPriority:       10,
				AutoReplyStatus:         AutoReplyStatusActive,
				WebhookTriggerID:        1,
				BotID:                   1,
				Enable:                  true,
				EventType:               EventTypeTime,
				TriggerScheduleType:     &[]WebhookTriggerScheduleType{WebhookTriggerScheduleTypeDaily}[0],
				TriggerScheduleSettings: dailySettings,
				Archived:                false,
			},
			{
				AutoReplyID:             2,
				AutoReplyPriority:       20,
				AutoReplyStatus:         AutoReplyStatusActive,
				WebhookTriggerID:        2,
				BotID:                   1,
				Enable:                  true,
				EventType:               EventTypeTime,
				TriggerScheduleType:     &[]WebhookTriggerScheduleType{WebhookTriggerScheduleTypeMonthly}[0],
				TriggerScheduleSettings: monthlySettings,
				Archived:                false,
			},
		},
		BusinessHours: []organization.BusinessHour{
			{
				Weekday:   organization.Monday,
				StartTime: parseTime("09:00"),
				EndTime:   parseTime("17:00"),
			},
		},
		Timezone: "UTC",
	}

	tests := []struct {
		name      string
		timestamp time.Time
		expected  *int // AutoReplyID of expected match
	}{
		{
			name:      "daily schedule match",
			timestamp: parseDateTime("2025-01-13 14:00:00"), // Monday 14:00
			expected:  intPtr(1),
		},
		{
			name:      "monthly schedule match",
			timestamp: parseDateTime("2025-01-15 11:00:00"), // 15th day 11:00
			expected:  intPtr(2),                            // Monthly has higher schedule priority
		},
		{
			name:      "no schedule match",
			timestamp: parseDateTime("2025-01-13 20:00:00"), // Monday 20:00 (outside hours)
			expected:  nil,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			event := WebhookEvent{
				EventType:   "message",
				MessageText: stringPtr("any message"),
				Timestamp:   tt.timestamp,
				ChannelType: organization.BotTypeLine,
			}

			result, err := aggregate.validateGeneralTimeTrigger(event)
			require.NoError(t, err)

			if tt.expected == nil {
				assert.Nil(t, result)
			} else {
				require.NotNil(t, result)
				assert.Equal(t, *tt.expected, result.AutoReplyID)
			}
		})
	}
}

// TestValidateTriggerPriority tests the complete priority system
func TestValidateTriggerPriority(t *testing.T) {
	t.Parallel()

	// Create daily schedule settings
	dailySettings, _ := json.Marshal([]map[string]string{
		{"start_time": "09:00", "end_time": "17:00"},
	})

	// Create test aggregate with both keyword and time triggers
	aggregate := &AutoReplyChannelSettingAggregate{
		BotID: 1,
		TriggerSettings: []AutoReplyTriggerSetting{
			{
				AutoReplyID:       1,
				AutoReplyPriority: 10,
				AutoReplyStatus:   AutoReplyStatusActive,
				WebhookTriggerID:  1,
				BotID:             1,
				Enable:            true,
				EventType:         EventTypeMessage,
				Keywords:          []string{"hello"},
				Archived:          false,
			},
			{
				AutoReplyID:             2,
				AutoReplyPriority:       20,
				AutoReplyStatus:         AutoReplyStatusActive,
				WebhookTriggerID:        2,
				BotID:                   1,
				Enable:                  true,
				EventType:               EventTypeTime,
				TriggerScheduleType:     &[]WebhookTriggerScheduleType{WebhookTriggerScheduleTypeDaily}[0],
				TriggerScheduleSettings: dailySettings,
				Archived:                false,
			},
		},
		Timezone: "UTC",
	}

	tests := []struct {
		name        string
		messageText *string
		timestamp   time.Time
		expected    *int // AutoReplyID of expected match
	}{
		{
			name:        "keyword trigger has priority over time trigger",
			messageText: stringPtr("hello"),
			timestamp:   parseDateTime("2025-01-13 14:00:00"), // Would match both
			expected:    intPtr(1),                            // Keyword trigger wins
		},
		{
			name:        "time trigger when no keyword match",
			messageText: stringPtr("goodbye"),
			timestamp:   parseDateTime("2025-01-13 14:00:00"), // Matches time trigger
			expected:    intPtr(2),                            // Time trigger wins
		},
		{
			name:        "no match when outside schedule",
			messageText: stringPtr("goodbye"),
			timestamp:   parseDateTime("2025-01-13 20:00:00"), // Outside schedule
			expected:    nil,                                  // No match
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			event := WebhookEvent{
				EventType:   "message",
				MessageText: tt.messageText,
				Timestamp:   tt.timestamp,
				ChannelType: organization.BotTypeLine,
			}

			result, err := aggregate.ValidateTrigger(event)
			require.NoError(t, err)

			if tt.expected == nil {
				assert.Nil(t, result)
			} else {
				require.NotNil(t, result)
				assert.Equal(t, *tt.expected, result.AutoReplyID)
			}
		})
	}
}

// TestValidateTriggerNonMessageEvent tests that non-message events are ignored
func TestValidateTriggerNonMessageEvent(t *testing.T) {
	t.Parallel()

	aggregate := &AutoReplyChannelSettingAggregate{
		BotID: 1,
		TriggerSettings: []AutoReplyTriggerSetting{
			{
				AutoReplyID:       1,
				AutoReplyPriority: 10,
				AutoReplyStatus:   AutoReplyStatusActive,
				WebhookTriggerID:  1,
				BotID:             1,
				Enable:            true,
				EventType:         EventTypeMessage,
				Keywords:          []string{"hello"},
				Archived:          false,
			},
		},
	}

	event := WebhookEvent{
		EventType:   "postback", // Non-message event
		MessageText: stringPtr("hello"),
		Timestamp:   time.Now(),
		ChannelType: organization.BotTypeLine,
	}

	result, err := aggregate.ValidateTrigger(event)
	require.NoError(t, err)
	assert.Nil(t, result)
}

// TestIsTimeInRange tests the time range checking function
func TestIsTimeInRange(t *testing.T) {
	t.Parallel()

	aggregate := &AutoReplyChannelSettingAggregate{}

	tests := []struct {
		name        string
		currentTime string
		startTime   string
		endTime     string
		expected    bool
	}{
		{"normal range - within", "14:00", "09:00", "17:00", true},
		{"normal range - before", "08:00", "09:00", "17:00", false},
		{"normal range - after", "18:00", "09:00", "17:00", false},
		{"normal range - at start", "09:00", "09:00", "17:00", true},
		{"normal range - at end", "17:00", "09:00", "17:00", false}, // End is exclusive
		{"midnight crossing - within night", "23:00", "22:00", "06:00", true},
		{"midnight crossing - within morning", "05:00", "22:00", "06:00", true},
		{"midnight crossing - outside", "12:00", "22:00", "06:00", false},
		{"midnight crossing - at start", "22:00", "22:00", "06:00", true},
		{"midnight crossing - at end", "06:00", "22:00", "06:00", false}, // End is exclusive
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := aggregate.isTimeInRange(tt.currentTime, tt.startTime, tt.endTime)
			assert.Equal(t, tt.expected, result)
		})
	}
}

// PRD Test Cases Coverage
// 1. B-P0-7: Keyword Reply Logic Tests
// Test 2: Exact keyword match with various cases (lowercase, uppercase, mixed case) ✅
// Test 3: Keyword with leading/trailing spaces (trimmed and normalized) ✅
// Test 4: Keyword with additional text should NOT match (exact match only) ✅
// Test 5: Partial match or close variation should NOT match ✅
// 2. Multiple Keywords Support Tests
// Test 1: Each keyword triggers the same auto-reply ✅
// Test 2: Case insensitive matching for multiple keywords ✅
// Test 3: Non-matching message validation ✅
// 3. B-P0-6: General Time-Based Logic Tests
// Test 3: Daily schedule within time window ✅
// Test 3b: Daily schedule when no business hours configured ✅
// Test 4: Monthly schedule on scheduled date and time ✅
// Test 5: Business hours during configured hours ✅
// Test 5: Outside business hours validation ✅
// 4. Priority Logic Tests
// Test 1: Keyword reply has priority over general reply ✅
// Test 2: General reply when no keyword match ✅
// Test 3: Keyword reply outside general time window ✅
// 5. Message Content Handling Tests
// Test 1: Keyword reply triggered with matching keyword ✅
// Test 2: No keyword reply for non-matching message ✅
// Test 3: General reply regardless of message content during schedule ✅
// 6. AutoReply Priority Within Same Type Tests
// Test: Keyword triggers sorted by AutoReplyPriority (higher number wins) ✅
// 7. Schedule Type Priority Tests
// Test: Monthly schedule type has priority over daily and business hour ✅

// TestPRD_B_P0_7_KeywordReplyLogic tests keyword reply logic based on PRD test cases
func TestPRD_B_P0_7_KeywordReplyLogic(t *testing.T) {
	t.Parallel()

	// Create test aggregate for keyword reply testing
	aggregate := &AutoReplyChannelSettingAggregate{
		BotID: 1,
		TriggerSettings: []AutoReplyTriggerSetting{
			{
				AutoReplyID:       1,
				AutoReplyPriority: 10,
				AutoReplyStatus:   AutoReplyStatusActive,
				WebhookTriggerID:  1,
				BotID:             1,
				Enable:            true,
				EventType:         EventTypeMessage,
				Keywords:          []string{"hello"},
				Archived:          false,
			},
		},
		Timezone: "UTC",
	}

	t.Run("B-P0-7-Test2: Exact keyword match with various cases", func(t *testing.T) {
		testCases := []struct {
			name        string
			messageText string
			shouldMatch bool
		}{
			{"exact match lowercase", "hello", true},
			{"exact match uppercase", "HELLO", true},
			{"exact match mixed case", "HeLLo", true},
		}

		for _, tc := range testCases {
			t.Run(tc.name, func(t *testing.T) {
				event := WebhookEvent{
					EventType:   "message",
					MessageText: &tc.messageText,
					Timestamp:   time.Now(),
					ChannelType: organization.BotTypeLine,
				}

				result, err := aggregate.ValidateTrigger(event)
				require.NoError(t, err)

				if tc.shouldMatch {
					assert.NotNil(t, result, "Expected auto-reply to be triggered")
					assert.Equal(t, 1, result.AutoReplyID)
				} else {
					assert.Nil(t, result, "Expected no auto-reply to be triggered")
				}
			})
		}
	})

	t.Run("B-P0-7-Test3: Keyword with leading/trailing spaces", func(t *testing.T) {
		testCases := []struct {
			name        string
			messageText string
			shouldMatch bool
		}{
			{"leading spaces", "  hello", true},
			{"trailing spaces", "hello  ", true},
			{"both spaces", "  hello  ", true},
			{"multiple spaces", "   hello   ", true},
		}

		for _, tc := range testCases {
			t.Run(tc.name, func(t *testing.T) {
				event := WebhookEvent{
					EventType:   "message",
					MessageText: &tc.messageText,
					Timestamp:   time.Now(),
					ChannelType: organization.BotTypeLine,
				}

				result, err := aggregate.ValidateTrigger(event)
				require.NoError(t, err)

				if tc.shouldMatch {
					assert.NotNil(t, result, "Expected auto-reply to be triggered with trimmed spaces")
					assert.Equal(t, 1, result.AutoReplyID)
				} else {
					assert.Nil(t, result, "Expected no auto-reply to be triggered")
				}
			})
		}
	})

	t.Run("B-P0-7-Test4: Keyword with additional text should NOT match", func(t *testing.T) {
		testCases := []struct {
			name        string
			messageText string
			shouldMatch bool
		}{
			{"keyword with suffix", "hello world", false},
			{"keyword with prefix", "say hello", false},
			{"keyword in middle", "say hello world", false},
			{"keyword as substring", "helloworld", false},
		}

		for _, tc := range testCases {
			t.Run(tc.name, func(t *testing.T) {
				event := WebhookEvent{
					EventType:   "message",
					MessageText: &tc.messageText,
					Timestamp:   time.Now(),
					ChannelType: organization.BotTypeLine,
				}

				result, err := aggregate.ValidateTrigger(event)
				require.NoError(t, err)

				assert.Nil(t, result, "Expected no auto-reply for non-exact match")
			})
		}
	})

	t.Run("B-P0-7-Test5: Partial match or close variation should NOT match", func(t *testing.T) {
		testCases := []struct {
			name        string
			messageText string
			shouldMatch bool
		}{
			{"partial match", "hell", false},
			{"close variation", "helo", false},
			{"typo", "hllo", false},
			{"different word", "goodbye", false},
		}

		for _, tc := range testCases {
			t.Run(tc.name, func(t *testing.T) {
				event := WebhookEvent{
					EventType:   "message",
					MessageText: &tc.messageText,
					Timestamp:   time.Now(),
					ChannelType: organization.BotTypeLine,
				}

				result, err := aggregate.ValidateTrigger(event)
				require.NoError(t, err)

				assert.Nil(t, result, "Expected no auto-reply for partial/close variation")
			})
		}
	})
}

// TestPRD_MultipleKeywords tests multiple keywords support
func TestPRD_MultipleKeywords(t *testing.T) {
	t.Parallel()

	// Create test aggregate with multiple keywords
	aggregate := &AutoReplyChannelSettingAggregate{
		BotID: 1,
		TriggerSettings: []AutoReplyTriggerSetting{
			{
				AutoReplyID:       1,
				AutoReplyPriority: 10,
				AutoReplyStatus:   AutoReplyStatusActive,
				WebhookTriggerID:  1,
				BotID:             1,
				Enable:            true,
				EventType:         EventTypeMessage,
				Keywords:          []string{"hello", "hi", "hey"},
				Archived:          false,
			},
		},
		Timezone: "UTC",
	}

	t.Run("Multiple-Keywords-Test1: Each keyword triggers the same auto-reply", func(t *testing.T) {
		keywords := []string{"hello", "hi", "hey"}

		for _, keyword := range keywords {
			t.Run("keyword_"+keyword, func(t *testing.T) {
				event := WebhookEvent{
					EventType:   "message",
					MessageText: &keyword,
					Timestamp:   time.Now(),
					ChannelType: organization.BotTypeLine,
				}

				result, err := aggregate.ValidateTrigger(event)
				require.NoError(t, err)
				assert.NotNil(t, result, "Expected auto-reply to be triggered for keyword: "+keyword)
				assert.Equal(t, 1, result.AutoReplyID)
			})
		}
	})

	t.Run("Multiple-Keywords-Test2: Case insensitive matching for multiple keywords", func(t *testing.T) {
		testCases := []struct {
			keyword     string
			messageText string
		}{
			{"hello", "HELLO"},
			{"hi", "HI"},
			{"hey", "HEY"},
		}

		for _, tc := range testCases {
			t.Run("case_insensitive_"+tc.keyword, func(t *testing.T) {
				event := WebhookEvent{
					EventType:   "message",
					MessageText: &tc.messageText,
					Timestamp:   time.Now(),
					ChannelType: organization.BotTypeLine,
				}

				result, err := aggregate.ValidateTrigger(event)
				require.NoError(t, err)
				assert.NotNil(t, result, "Expected auto-reply to be triggered for case insensitive: "+tc.messageText)
				assert.Equal(t, 1, result.AutoReplyID)
			})
		}
	})

	t.Run("Multiple-Keywords-Test3: Non-matching message", func(t *testing.T) {
		event := WebhookEvent{
			EventType:   "message",
			MessageText: stringPtr("goodbye"),
			Timestamp:   time.Now(),
			ChannelType: organization.BotTypeLine,
		}

		result, err := aggregate.ValidateTrigger(event)
		require.NoError(t, err)
		assert.Nil(t, result, "Expected no auto-reply for non-matching keyword")
	})
}

// TestPRD_B_P0_6_GeneralTimeBasedLogic tests general time-based logic
func TestPRD_B_P0_6_GeneralTimeBasedLogic(t *testing.T) {
	t.Parallel()

	// Create daily schedule settings (9:00-17:00)
	dailySettings, _ := json.Marshal([]map[string]string{
		{"start_time": "09:00", "end_time": "17:00"},
	})

	// Create monthly schedule settings (15th day, 10:00-12:00)
	monthlySettings, _ := json.Marshal([]map[string]interface{}{
		{"day": 15, "start_time": "10:00", "end_time": "12:00"},
	})

	// Create test aggregate
	aggregate := &AutoReplyChannelSettingAggregate{
		BotID: 1,
		TriggerSettings: []AutoReplyTriggerSetting{
			{
				AutoReplyID:             1,
				AutoReplyPriority:       10,
				AutoReplyStatus:         AutoReplyStatusActive,
				WebhookTriggerID:        1,
				BotID:                   1,
				Enable:                  true,
				EventType:               EventTypeTime,
				TriggerScheduleType:     &[]WebhookTriggerScheduleType{WebhookTriggerScheduleTypeDaily}[0],
				TriggerScheduleSettings: dailySettings,
				Archived:                false,
			},
			{
				AutoReplyID:             2,
				AutoReplyPriority:       20,
				AutoReplyStatus:         AutoReplyStatusActive,
				WebhookTriggerID:        2,
				BotID:                   1,
				Enable:                  true,
				EventType:               EventTypeTime,
				TriggerScheduleType:     &[]WebhookTriggerScheduleType{WebhookTriggerScheduleTypeMonthly}[0],
				TriggerScheduleSettings: monthlySettings,
				Archived:                false,
			},
			{
				AutoReplyID:         3,
				AutoReplyPriority:   15,
				AutoReplyStatus:     AutoReplyStatusActive,
				WebhookTriggerID:    3,
				BotID:               1,
				Enable:              true,
				EventType:           EventTypeTime,
				TriggerScheduleType: &[]WebhookTriggerScheduleType{WebhookTriggerScheduleTypeBusinessHour}[0],
				Archived:            false,
			},
		},
		BusinessHours: []organization.BusinessHour{
			{
				Weekday:   organization.Monday,
				StartTime: parseTime("09:00"),
				EndTime:   parseTime("17:00"),
			},
		},
		Timezone: "UTC",
	}

	t.Run("B-P0-6-Test3: Daily schedule within time window", func(t *testing.T) {
		// Monday 14:00 - should match daily schedule, but business hour has higher schedule priority
		timestamp := parseDateTime("2025-01-13 14:00:00")
		event := WebhookEvent{
			EventType:   "message",
			MessageText: stringPtr("any message"),
			Timestamp:   timestamp,
			ChannelType: organization.BotTypeLine,
		}

		result, err := aggregate.ValidateTrigger(event)
		require.NoError(t, err)
		assert.NotNil(t, result, "Expected auto-reply for schedule match")
		// Business hour trigger (ID 3) should win due to higher schedule type priority
		assert.Equal(t, 3, result.AutoReplyID) // Business hour trigger wins over daily
	})

	t.Run("B-P0-6-Test3b: Daily schedule when no business hours configured", func(t *testing.T) {
		// Create aggregate without business hours to test daily trigger specifically
		dailyOnlyAggregate := &AutoReplyChannelSettingAggregate{
			BotID: 1,
			TriggerSettings: []AutoReplyTriggerSetting{
				{
					AutoReplyID:             1,
					AutoReplyPriority:       10,
					AutoReplyStatus:         AutoReplyStatusActive,
					WebhookTriggerID:        1,
					BotID:                   1,
					Enable:                  true,
					EventType:               EventTypeTime,
					TriggerScheduleType:     &[]WebhookTriggerScheduleType{WebhookTriggerScheduleTypeDaily}[0],
					TriggerScheduleSettings: dailySettings,
					Archived:                false,
				},
			},
			BusinessHours: []organization.BusinessHour{}, // No business hours
			Timezone:      "UTC",
		}

		// Monday 14:00 - should match daily schedule
		timestamp := parseDateTime("2025-01-13 14:00:00")
		event := WebhookEvent{
			EventType:   "message",
			MessageText: stringPtr("any message"),
			Timestamp:   timestamp,
			ChannelType: organization.BotTypeLine,
		}

		result, err := dailyOnlyAggregate.ValidateTrigger(event)
		require.NoError(t, err)
		assert.NotNil(t, result, "Expected auto-reply for daily schedule")
		assert.Equal(t, 1, result.AutoReplyID) // Daily trigger
	})

	t.Run("B-P0-6-Test4: Monthly schedule on scheduled date and time", func(t *testing.T) {
		// 15th day 11:00 - should match monthly schedule
		timestamp := parseDateTime("2025-01-15 11:00:00")
		event := WebhookEvent{
			EventType:   "message",
			MessageText: stringPtr("any message"),
			Timestamp:   timestamp,
			ChannelType: organization.BotTypeLine,
		}

		result, err := aggregate.ValidateTrigger(event)
		require.NoError(t, err)
		assert.NotNil(t, result, "Expected auto-reply for monthly schedule")
		assert.Equal(t, 2, result.AutoReplyID) // Monthly trigger (higher schedule priority)
	})

	t.Run("B-P0-6-Test5: Business hours during configured hours", func(t *testing.T) {
		// Monday 14:00 - should match business hours
		timestamp := parseDateTime("2025-01-13 14:00:00")

		// Check business hours validation
		isBusinessHour := aggregate.isWithinBusinessHours(timestamp)
		assert.True(t, isBusinessHour, "Expected timestamp to be within business hours")
	})

	t.Run("B-P0-6-Test5: Outside business hours", func(t *testing.T) {
		// Monday 20:00 - should be outside business hours
		timestamp := parseDateTime("2025-01-13 20:00:00")

		isBusinessHour := aggregate.isWithinBusinessHours(timestamp)
		assert.False(t, isBusinessHour, "Expected timestamp to be outside business hours")
	})
}

// TestPRD_PriorityLogic tests priority logic (Keyword over General)
func TestPRD_PriorityLogic(t *testing.T) {
	t.Parallel()

	// Create daily schedule settings
	dailySettings, _ := json.Marshal([]map[string]string{
		{"start_time": "09:00", "end_time": "17:00"},
	})

	// Create test aggregate with both keyword and time triggers
	aggregate := &AutoReplyChannelSettingAggregate{
		BotID: 1,
		TriggerSettings: []AutoReplyTriggerSetting{
			{
				AutoReplyID:       1,
				AutoReplyPriority: 10,
				AutoReplyStatus:   AutoReplyStatusActive,
				WebhookTriggerID:  1,
				BotID:             1,
				Enable:            true,
				EventType:         EventTypeMessage,
				Keywords:          []string{"hello"},
				Archived:          false,
			},
			{
				AutoReplyID:             2,
				AutoReplyPriority:       20,
				AutoReplyStatus:         AutoReplyStatusActive,
				WebhookTriggerID:        2,
				BotID:                   1,
				Enable:                  true,
				EventType:               EventTypeTime,
				TriggerScheduleType:     &[]WebhookTriggerScheduleType{WebhookTriggerScheduleTypeDaily}[0],
				TriggerScheduleSettings: dailySettings,
				Archived:                false,
			},
		},
		Timezone: "UTC",
	}

	t.Run("Priority-Test1: Keyword reply has priority over general reply", func(t *testing.T) {
		// Monday 14:00 with keyword "hello" - should match both but keyword wins
		timestamp := parseDateTime("2025-01-13 14:00:00")
		event := WebhookEvent{
			EventType:   "message",
			MessageText: stringPtr("hello"),
			Timestamp:   timestamp,
			ChannelType: organization.BotTypeLine,
		}

		result, err := aggregate.ValidateTrigger(event)
		require.NoError(t, err)
		assert.NotNil(t, result, "Expected auto-reply to be triggered")
		assert.Equal(t, 1, result.AutoReplyID, "Expected keyword reply to have priority over general reply")
	})

	t.Run("Priority-Test2: General reply when no keyword match", func(t *testing.T) {
		// Monday 14:00 with non-matching keyword - should match general time trigger
		timestamp := parseDateTime("2025-01-13 14:00:00")
		event := WebhookEvent{
			EventType:   "message",
			MessageText: stringPtr("goodbye"),
			Timestamp:   timestamp,
			ChannelType: organization.BotTypeLine,
		}

		result, err := aggregate.ValidateTrigger(event)
		require.NoError(t, err)
		assert.NotNil(t, result, "Expected auto-reply to be triggered")
		assert.Equal(t, 2, result.AutoReplyID, "Expected general reply when no keyword match")
	})

	t.Run("Priority-Test3: Keyword reply outside general time window", func(t *testing.T) {
		// Monday 20:00 with keyword "hello" - outside general time but keyword should still match
		timestamp := parseDateTime("2025-01-13 20:00:00")
		event := WebhookEvent{
			EventType:   "message",
			MessageText: stringPtr("hello"),
			Timestamp:   timestamp,
			ChannelType: organization.BotTypeLine,
		}

		result, err := aggregate.ValidateTrigger(event)
		require.NoError(t, err)
		assert.NotNil(t, result, "Expected auto-reply to be triggered")
		assert.Equal(t, 1, result.AutoReplyID, "Expected keyword reply even outside general time window")
	})
}

// TestPRD_MessageContentHandling tests message content handling
func TestPRD_MessageContentHandling(t *testing.T) {
	t.Parallel()

	// Create daily schedule settings
	dailySettings, _ := json.Marshal([]map[string]string{
		{"start_time": "09:00", "end_time": "17:00"},
	})

	// Create test aggregate
	aggregate := &AutoReplyChannelSettingAggregate{
		BotID: 1,
		TriggerSettings: []AutoReplyTriggerSetting{
			{
				AutoReplyID:       1,
				AutoReplyPriority: 10,
				AutoReplyStatus:   AutoReplyStatusActive,
				WebhookTriggerID:  1,
				BotID:             1,
				Enable:            true,
				EventType:         EventTypeMessage,
				Keywords:          []string{"hello"},
				Archived:          false,
			},
			{
				AutoReplyID:             2,
				AutoReplyPriority:       20,
				AutoReplyStatus:         AutoReplyStatusActive,
				WebhookTriggerID:        2,
				BotID:                   1,
				Enable:                  true,
				EventType:               EventTypeTime,
				TriggerScheduleType:     &[]WebhookTriggerScheduleType{WebhookTriggerScheduleTypeDaily}[0],
				TriggerScheduleSettings: dailySettings,
				Archived:                false,
			},
		},
		Timezone: "UTC",
	}

	t.Run("Message-Content-Test1: Keyword reply triggered with matching keyword", func(t *testing.T) {
		event := WebhookEvent{
			EventType:   "message",
			MessageText: stringPtr("hello"),
			Timestamp:   time.Now(),
			ChannelType: organization.BotTypeLine,
		}

		result, err := aggregate.ValidateTrigger(event)
		require.NoError(t, err)
		assert.NotNil(t, result, "Expected keyword reply to be triggered")
		assert.Equal(t, 1, result.AutoReplyID)
	})

	t.Run("Message-Content-Test2: No keyword reply for non-matching message", func(t *testing.T) {
		event := WebhookEvent{
			EventType:   "message",
			MessageText: stringPtr("goodbye"),
			Timestamp:   parseDateTime("2025-01-13 08:00:00"), // Outside schedule too
			ChannelType: organization.BotTypeLine,
		}

		result, err := aggregate.ValidateTrigger(event)
		require.NoError(t, err)
		assert.Nil(t, result, "Expected no keyword reply for non-matching message outside schedule")
	})

	t.Run("Message-Content-Test3: General reply regardless of message content during schedule", func(t *testing.T) {
		testMessages := []string{"any message", "random text", "123", "!@#"}

		for _, message := range testMessages {
			t.Run("message_"+message, func(t *testing.T) {
				event := WebhookEvent{
					EventType:   "message",
					MessageText: &message,
					Timestamp:   parseDateTime("2025-01-13 14:00:00"), // Within schedule
					ChannelType: organization.BotTypeLine,
				}

				result, err := aggregate.ValidateTrigger(event)
				require.NoError(t, err)
				assert.NotNil(t, result, "Expected general reply regardless of message content during schedule")
				assert.Equal(t, 2, result.AutoReplyID)
			})
		}
	})
}

// TestPRD_AutoReplyPriorityWithinSameType tests priority within same trigger type
func TestPRD_AutoReplyPriorityWithinSameType(t *testing.T) {
	t.Parallel()

	// Create test aggregate with multiple keyword triggers with different priorities
	aggregate := &AutoReplyChannelSettingAggregate{
		BotID: 1,
		TriggerSettings: []AutoReplyTriggerSetting{
			{
				AutoReplyID:       1,
				AutoReplyPriority: 5, // Lower priority
				AutoReplyStatus:   AutoReplyStatusActive,
				WebhookTriggerID:  1,
				BotID:             1,
				Enable:            true,
				EventType:         EventTypeMessage,
				Keywords:          []string{"hello"},
				Archived:          false,
			},
			{
				AutoReplyID:       2,
				AutoReplyPriority: 15, // Higher priority
				AutoReplyStatus:   AutoReplyStatusActive,
				WebhookTriggerID:  2,
				BotID:             1,
				Enable:            true,
				EventType:         EventTypeMessage,
				Keywords:          []string{"hello"},
				Archived:          false,
			},
			{
				AutoReplyID:       3,
				AutoReplyPriority: 10, // Medium priority
				AutoReplyStatus:   AutoReplyStatusActive,
				WebhookTriggerID:  3,
				BotID:             1,
				Enable:            true,
				EventType:         EventTypeMessage,
				Keywords:          []string{"hello"},
				Archived:          false,
			},
		},
		Timezone: "UTC",
	}

	t.Run("Keyword triggers sorted by AutoReplyPriority (higher number wins)", func(t *testing.T) {
		event := WebhookEvent{
			EventType:   "message",
			MessageText: stringPtr("hello"),
			Timestamp:   time.Now(),
			ChannelType: organization.BotTypeLine,
		}

		result, err := aggregate.ValidateTrigger(event)
		require.NoError(t, err)
		assert.NotNil(t, result, "Expected auto-reply to be triggered")
		assert.Equal(t, 2, result.AutoReplyID, "Expected highest priority (15) auto-reply to be selected")
	})
}

// TestPRD_ScheduleTypePriority tests schedule type priority for general time triggers
func TestPRD_ScheduleTypePriority(t *testing.T) {
	t.Parallel()

	// Create schedule settings
	dailySettings, _ := json.Marshal([]map[string]string{
		{"start_time": "09:00", "end_time": "17:00"},
	})
	monthlySettings, _ := json.Marshal([]map[string]interface{}{
		{"day": 13, "start_time": "09:00", "end_time": "17:00"}, // Monday 13th
	})

	// Create test aggregate with different schedule types
	aggregate := &AutoReplyChannelSettingAggregate{
		BotID: 1,
		TriggerSettings: []AutoReplyTriggerSetting{
			{
				AutoReplyID:             1,
				AutoReplyPriority:       10,
				AutoReplyStatus:         AutoReplyStatusActive,
				WebhookTriggerID:        1,
				BotID:                   1,
				Enable:                  true,
				EventType:               EventTypeTime,
				TriggerScheduleType:     &[]WebhookTriggerScheduleType{WebhookTriggerScheduleTypeDaily}[0],
				TriggerScheduleSettings: dailySettings,
				Archived:                false,
			},
			{
				AutoReplyID:             2,
				AutoReplyPriority:       5, // Lower AutoReply priority
				AutoReplyStatus:         AutoReplyStatusActive,
				WebhookTriggerID:        2,
				BotID:                   1,
				Enable:                  true,
				EventType:               EventTypeTime,
				TriggerScheduleType:     &[]WebhookTriggerScheduleType{WebhookTriggerScheduleTypeMonthly}[0],
				TriggerScheduleSettings: monthlySettings,
				Archived:                false,
			},
			{
				AutoReplyID:         3,
				AutoReplyPriority:   15, // Higher AutoReply priority
				AutoReplyStatus:     AutoReplyStatusActive,
				WebhookTriggerID:    3,
				BotID:               1,
				Enable:              true,
				EventType:           EventTypeTime,
				TriggerScheduleType: &[]WebhookTriggerScheduleType{WebhookTriggerScheduleTypeBusinessHour}[0],
				Archived:            false,
			},
		},
		BusinessHours: []organization.BusinessHour{
			{
				Weekday:   organization.Monday,
				StartTime: parseTime("09:00"),
				EndTime:   parseTime("17:00"),
			},
		},
		Timezone: "UTC",
	}

	t.Run("Monthly schedule type has priority over daily and business hour", func(t *testing.T) {
		// Monday 13th 14:00 - matches all three schedules
		timestamp := parseDateTime("2025-01-13 14:00:00")
		event := WebhookEvent{
			EventType:   "message",
			MessageText: stringPtr("any message"),
			Timestamp:   timestamp,
			ChannelType: organization.BotTypeLine,
		}

		result, err := aggregate.ValidateTrigger(event)
		require.NoError(t, err)
		assert.NotNil(t, result, "Expected auto-reply to be triggered")
		assert.Equal(t, 2, result.AutoReplyID, "Expected monthly schedule to have priority despite lower AutoReply priority")
	})
}

// ============================================================================
// Feature 2: IG Story-Specific Auto-Reply Tests
// ============================================================================
// Story 6: IG Story Keyword Logic [B-P1-18-Keyword]
// ✅ B-P1-18-Test7: IG Story keyword rule - message matches keyword but NOT reply to selected story
// ✅ B-P1-18-Test8a: IG Story keyword rule - message is reply to selected story and matches keyword
// ✅ IG-Story-Keyword-Test1: Keyword hello with matching story ID
// ✅ IG-Story-Keyword-Test2: Keyword hello with wrong story ID
// ✅ IG-Story-Keyword-Test3: Keyword hello with no story ID
// Story 7: IG Story General Logic [B-P1-18-General]
// ✅ B-P1-18-Test8b: IG Story general rule - message is reply to selected story and within schedule
// ✅ IG-Story-General-Test1: Daily 9-17 schedule at 14:00 with matching story ID
// ✅ IG-Story-General-Test2: Daily 9-17 schedule at 20:00 (outside schedule) with matching story ID
// ✅ IG-Story-General-Test3: Daily 9-17 schedule at 14:00 with wrong story ID
// Story 10: Complete Priority System
// ✅ Complete-Priority-Test1: All 4 rules could match - IG story keyword wins (Priority 1)
// ✅ Complete-Priority-Test2: IG story general, general keyword, general time match - IG story general wins (Priority 2)
// ✅ Complete-Priority-Test3: General keyword and general time match - general keyword wins (Priority 3)
// ✅ Complete-Priority-Test4: Only general time-based matches (Priority 4)
// Additional Validation Tests
// ✅ AutoReplyPriorityWithinSameType: Keyword triggers sorted by AutoReplyPriority
// ✅ ScheduleTypePriority: Monthly schedule type has priority over daily and business hour

// TestPRD_IG_Story_KeywordLogic tests IG Story keyword logic based on PRD test cases
func TestPRD_IG_Story_KeywordLogic(t *testing.T) {
	t.Parallel()

	// Create test aggregate for IG Story keyword testing
	aggregate := &AutoReplyChannelSettingAggregate{
		BotID: 1,
		TriggerSettings: []AutoReplyTriggerSetting{
			{
				AutoReplyID:       1,
				AutoReplyPriority: 10,
				AutoReplyStatus:   AutoReplyStatusActive,
				WebhookTriggerID:  1,
				BotID:             1,
				Enable:            true,
				EventType:         EventTypeMessage,
				Keywords:          []string{"hello"},
				IGStoryIDs:        []string{"story123"},
				Archived:          false,
			},
		},
		Timezone: "UTC",
	}

	t.Run("B-P1-18-Test7: IG Story keyword rule - message matches keyword but NOT reply to selected story", func(t *testing.T) {
		event := WebhookEvent{
			EventType:   "message",
			MessageText: stringPtr("hello"),
			Timestamp:   time.Now(),
			ChannelType: organization.BotTypeInstagram,
			IGStoryID:   nil, // No story ID
		}

		result, err := aggregate.ValidateTrigger(event)
		require.NoError(t, err)
		assert.Nil(t, result, "Expected no auto-reply when message matches keyword but is not a story reply")
	})

	t.Run("B-P1-18-Test8a: IG Story keyword rule - message is reply to selected story and matches keyword", func(t *testing.T) {
		event := WebhookEvent{
			EventType:   "message",
			MessageText: stringPtr("hello"),
			Timestamp:   time.Now(),
			ChannelType: organization.BotTypeInstagram,
			IGStoryID:   stringPtr("story123"), // Matching story ID
		}

		result, err := aggregate.ValidateTrigger(event)
		require.NoError(t, err)
		assert.NotNil(t, result, "Expected auto-reply when message is reply to selected story and matches keyword")
		assert.Equal(t, 1, result.AutoReplyID)
	})

	t.Run("IG-Story-Keyword-Test1: Keyword hello with matching story ID", func(t *testing.T) {
		event := WebhookEvent{
			EventType:   "message",
			MessageText: stringPtr("hello"),
			Timestamp:   time.Now(),
			ChannelType: organization.BotTypeInstagram,
			IGStoryID:   stringPtr("story123"),
		}

		result, err := aggregate.ValidateTrigger(event)
		require.NoError(t, err)
		assert.NotNil(t, result, "Expected IG story keyword reply to be triggered")
		assert.Equal(t, 1, result.AutoReplyID)
	})

	t.Run("IG-Story-Keyword-Test2: Keyword hello with wrong story ID", func(t *testing.T) {
		event := WebhookEvent{
			EventType:   "message",
			MessageText: stringPtr("hello"),
			Timestamp:   time.Now(),
			ChannelType: organization.BotTypeInstagram,
			IGStoryID:   stringPtr("story456"), // Wrong story ID
		}

		result, err := aggregate.ValidateTrigger(event)
		require.NoError(t, err)
		assert.Nil(t, result, "Expected no IG story keyword reply for wrong story ID")
	})

	t.Run("IG-Story-Keyword-Test3: Keyword hello with no story ID", func(t *testing.T) {
		event := WebhookEvent{
			EventType:   "message",
			MessageText: stringPtr("hello"),
			Timestamp:   time.Now(),
			ChannelType: organization.BotTypeInstagram,
			IGStoryID:   nil, // No story ID
		}

		result, err := aggregate.ValidateTrigger(event)
		require.NoError(t, err)
		assert.Nil(t, result, "Expected no IG story keyword reply when no story context")
	})
}

// TestPRD_IG_Story_GeneralLogic tests IG Story general logic based on PRD test cases
func TestPRD_IG_Story_GeneralLogic(t *testing.T) {
	t.Parallel()

	// Create daily schedule settings (9:00-17:00)
	dailySettings, _ := json.Marshal([]map[string]string{
		{"start_time": "09:00", "end_time": "17:00"},
	})

	// Create test aggregate for IG Story general testing
	aggregate := &AutoReplyChannelSettingAggregate{
		BotID: 1,
		TriggerSettings: []AutoReplyTriggerSetting{
			{
				AutoReplyID:             1,
				AutoReplyPriority:       10,
				AutoReplyStatus:         AutoReplyStatusActive,
				WebhookTriggerID:        1,
				BotID:                   1,
				Enable:                  true,
				EventType:               EventTypeTime,
				TriggerScheduleType:     &[]WebhookTriggerScheduleType{WebhookTriggerScheduleTypeDaily}[0],
				TriggerScheduleSettings: dailySettings,
				IGStoryIDs:              []string{"story123"},
				Archived:                false,
			},
		},
		Timezone: "UTC",
	}

	t.Run("B-P1-18-Test8b: IG Story general rule - message is reply to selected story and within schedule", func(t *testing.T) {
		event := WebhookEvent{
			EventType:   "message",
			MessageText: stringPtr("any message"),
			Timestamp:   parseDateTime("2025-01-13 14:00:00"), // Within schedule
			ChannelType: organization.BotTypeInstagram,
			IGStoryID:   stringPtr("story123"), // Matching story ID
		}

		result, err := aggregate.ValidateTrigger(event)
		require.NoError(t, err)
		assert.NotNil(t, result, "Expected auto-reply when message is reply to selected story and within schedule")
		assert.Equal(t, 1, result.AutoReplyID)
	})

	t.Run("IG-Story-General-Test1: Daily 9-17 schedule at 14:00 with matching story ID", func(t *testing.T) {
		event := WebhookEvent{
			EventType:   "message",
			MessageText: stringPtr("any message"),
			Timestamp:   parseDateTime("2025-01-13 14:00:00"),
			ChannelType: organization.BotTypeInstagram,
			IGStoryID:   stringPtr("story123"),
		}

		result, err := aggregate.ValidateTrigger(event)
		require.NoError(t, err)
		assert.NotNil(t, result, "Expected IG story general reply to be triggered")
		assert.Equal(t, 1, result.AutoReplyID)
	})

	t.Run("IG-Story-General-Test2: Daily 9-17 schedule at 20:00 (outside schedule) with matching story ID", func(t *testing.T) {
		event := WebhookEvent{
			EventType:   "message",
			MessageText: stringPtr("any message"),
			Timestamp:   parseDateTime("2025-01-13 20:00:00"), // Outside schedule
			ChannelType: organization.BotTypeInstagram,
			IGStoryID:   stringPtr("story123"),
		}

		result, err := aggregate.ValidateTrigger(event)
		require.NoError(t, err)
		assert.Nil(t, result, "Expected no IG story general reply outside schedule")
	})

	t.Run("IG-Story-General-Test3: Daily 9-17 schedule at 14:00 with wrong story ID", func(t *testing.T) {
		event := WebhookEvent{
			EventType:   "message",
			MessageText: stringPtr("any message"),
			Timestamp:   parseDateTime("2025-01-13 14:00:00"),
			ChannelType: organization.BotTypeInstagram,
			IGStoryID:   stringPtr("story456"), // Wrong story ID
		}

		result, err := aggregate.ValidateTrigger(event)
		require.NoError(t, err)
		assert.Nil(t, result, "Expected no IG story general reply for wrong story ID")
	})
}

// TestPRD_CompletePriority tests the complete 4-level priority system
func TestPRD_CompletePriority(t *testing.T) {
	t.Parallel()

	// Create daily schedule settings
	dailySettings, _ := json.Marshal([]map[string]string{
		{"start_time": "09:00", "end_time": "17:00"},
	})

	// Create test aggregate with all 4 types of triggers
	aggregate := &AutoReplyChannelSettingAggregate{
		BotID: 1,
		TriggerSettings: []AutoReplyTriggerSetting{
			// Priority 1: IG Story keyword
			{
				AutoReplyID:       1,
				AutoReplyPriority: 5, // Lowest AutoReply priority
				AutoReplyStatus:   AutoReplyStatusActive,
				WebhookTriggerID:  1,
				BotID:             1,
				Enable:            true,
				EventType:         EventTypeMessage,
				Keywords:          []string{"hello"},
				IGStoryIDs:        []string{"story123"},
				Archived:          false,
			},
			// Priority 2: IG Story general
			{
				AutoReplyID:             2,
				AutoReplyPriority:       10,
				AutoReplyStatus:         AutoReplyStatusActive,
				WebhookTriggerID:        2,
				BotID:                   1,
				Enable:                  true,
				EventType:               EventTypeTime,
				TriggerScheduleType:     &[]WebhookTriggerScheduleType{WebhookTriggerScheduleTypeDaily}[0],
				TriggerScheduleSettings: dailySettings,
				IGStoryIDs:              []string{"story123"},
				Archived:                false,
			},
			// Priority 3: General keyword
			{
				AutoReplyID:       3,
				AutoReplyPriority: 15,
				AutoReplyStatus:   AutoReplyStatusActive,
				WebhookTriggerID:  3,
				BotID:             1,
				Enable:            true,
				EventType:         EventTypeMessage,
				Keywords:          []string{"hello"},
				Archived:          false,
			},
			// Priority 4: General time-based
			{
				AutoReplyID:             4,
				AutoReplyPriority:       20, // Highest AutoReply priority
				AutoReplyStatus:         AutoReplyStatusActive,
				WebhookTriggerID:        4,
				BotID:                   1,
				Enable:                  true,
				EventType:               EventTypeTime,
				TriggerScheduleType:     &[]WebhookTriggerScheduleType{WebhookTriggerScheduleTypeDaily}[0],
				TriggerScheduleSettings: dailySettings,
				Archived:                false,
			},
		},
		Timezone: "UTC",
	}

	t.Run("Complete-Priority-Test1: All 4 rules could match - IG story keyword wins", func(t *testing.T) {
		event := WebhookEvent{
			EventType:   "message",
			MessageText: stringPtr("hello"),                   // Matches keyword triggers
			Timestamp:   parseDateTime("2025-01-13 14:00:00"), // Matches time triggers
			ChannelType: organization.BotTypeInstagram,
			IGStoryID:   stringPtr("story123"), // Matches IG story triggers
		}

		result, err := aggregate.ValidateTrigger(event)
		require.NoError(t, err)
		assert.NotNil(t, result, "Expected auto-reply to be triggered")
		assert.Equal(t, 1, result.AutoReplyID, "Expected IG story keyword reply (Priority 1) to win")
	})

	t.Run("Complete-Priority-Test2: IG story general, general keyword, general time match - IG story general wins", func(t *testing.T) {
		event := WebhookEvent{
			EventType:   "message",
			MessageText: stringPtr("goodbye"),                 // No keyword match
			Timestamp:   parseDateTime("2025-01-13 14:00:00"), // Matches time triggers
			ChannelType: organization.BotTypeInstagram,
			IGStoryID:   stringPtr("story123"), // Matches IG story triggers
		}

		result, err := aggregate.ValidateTrigger(event)
		require.NoError(t, err)
		assert.NotNil(t, result, "Expected auto-reply to be triggered")
		assert.Equal(t, 2, result.AutoReplyID, "Expected IG story general reply (Priority 2) to win")
	})

	t.Run("Complete-Priority-Test3: General keyword and general time match - general keyword wins", func(t *testing.T) {
		event := WebhookEvent{
			EventType:   "message",
			MessageText: stringPtr("hello"),                   // Matches keyword trigger
			Timestamp:   parseDateTime("2025-01-13 14:00:00"), // Matches time trigger
			ChannelType: organization.BotTypeInstagram,
			IGStoryID:   nil, // No story ID - excludes IG story triggers
		}

		result, err := aggregate.ValidateTrigger(event)
		require.NoError(t, err)
		assert.NotNil(t, result, "Expected auto-reply to be triggered")
		assert.Equal(t, 3, result.AutoReplyID, "Expected general keyword reply (Priority 3) to win")
	})

	t.Run("Complete-Priority-Test4: Only general time-based matches", func(t *testing.T) {
		event := WebhookEvent{
			EventType:   "message",
			MessageText: stringPtr("goodbye"),                 // No keyword match
			Timestamp:   parseDateTime("2025-01-13 14:00:00"), // Matches time trigger
			ChannelType: organization.BotTypeInstagram,
			IGStoryID:   nil, // No story ID
		}

		result, err := aggregate.ValidateTrigger(event)
		require.NoError(t, err)
		assert.NotNil(t, result, "Expected auto-reply to be triggered")
		assert.Equal(t, 4, result.AutoReplyID, "Expected general time-based reply (Priority 4) to win")
	})
}
