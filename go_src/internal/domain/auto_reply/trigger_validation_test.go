package auto_reply

import (
	"testing"
	"time"
)

func TestValidateTrigger_KeywordPriority(t *testing.T) {
	t.Parallel()
	// 測試：keyword trigger 比對完全符合時，優先於 general trigger
	kw := &AutoReplyTriggerSetting{
		AutoReplyID: 1,
		Status:      AutoReplyStatusActive,
		Enable:      true,
		EventType:   AutoReplyEventTypeKeyword,
		Priority:    10,
		Keywords:    []string{"hello"},
	}
	gen := &AutoReplyTriggerSetting{
		AutoReplyID:         2,
		Status:              AutoReplyStatusActive,
		Enable:              true,
		EventType:           AutoReplyEventTypeTime,
		Priority:            5,
		TriggerScheduleType: ptrScheduleType(WebhookTriggerScheduleTypeDaily),
		TriggerScheduleSettings: &WebhookTriggerScheduleSettings{
			Schedules: []WebhookTriggerSchedule{&DailySchedule{StartTime: "00:00", EndTime: "23:59"}},
		},
	}
	event := WebhookEvent{
		EventType:   "message",
		MessageText: ptrString("hello"),
		Timestamp:   time.Date(2024, 7, 1, 12, 0, 0, 0, time.UTC),
	}
	agg := &AutoReplyChannelSettingAggregate{
		TriggerSettings: []*AutoReplyTriggerSetting{gen, kw},
	}
	result, _ := agg.ValidateTrigger(event)
	if result == nil || result.AutoReplyID != 1 {
		t.Errorf("expected keyword trigger to match, got %+v", result)
	}
}

func TestValidateTrigger_KeywordExactMatch(t *testing.T) {
	t.Parallel()
	tests := []struct {
		name     string
		input    string
		keywords []string
		expect   bool
	}{
		{"exact match", "hello", []string{"hello"}, true},
		{"case insensitive", "HELLO", []string{"hello"}, true},
		{"trim spaces", " hello ", []string{"hello"}, true},
		{"not partial", "hello world", []string{"hello"}, false},
		{"multiple keywords", "hi", []string{"hello", "hi"}, true},
		{"no match", "bye", []string{"hello", "hi"}, false},
	}
	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()
			kw := &AutoReplyTriggerSetting{
				AutoReplyID: 1,
				Status:      AutoReplyStatusActive,
				Enable:      true,
				EventType:   AutoReplyEventTypeKeyword,
				Priority:    10,
				Keywords:    tc.keywords,
			}
			event := WebhookEvent{
				EventType:   "message",
				MessageText: ptrString(tc.input),
				Timestamp:   time.Now(),
			}
			agg := &AutoReplyChannelSettingAggregate{
				TriggerSettings: []*AutoReplyTriggerSetting{kw},
			}
			result, _ := agg.ValidateTrigger(event)
			if (result != nil) != tc.expect {
				t.Errorf("input=%q, keywords=%v, expect match=%v, got %+v", tc.input, tc.keywords, tc.expect, result)
			}
		})
	}
}

func TestValidateTrigger_GeneralTimePriority(t *testing.T) {
	t.Parallel()
	// 測試：general trigger 依 schedule type 與 priority 排序
	monthly := &AutoReplyTriggerSetting{
		AutoReplyID:         1,
		Status:              AutoReplyStatusActive,
		Enable:              true,
		EventType:           AutoReplyEventTypeTime,
		Priority:            5,
		TriggerScheduleType: ptrScheduleType(WebhookTriggerScheduleTypeMonthly),
		TriggerScheduleSettings: &WebhookTriggerScheduleSettings{
			Schedules: []WebhookTriggerSchedule{&MonthlySchedule{Day: 1, StartTime: "00:00", EndTime: "23:59"}},
		},
	}
	daily := &AutoReplyTriggerSetting{
		AutoReplyID:         2,
		Status:              AutoReplyStatusActive,
		Enable:              true,
		EventType:           AutoReplyEventTypeTime,
		Priority:            10,
		TriggerScheduleType: ptrScheduleType(WebhookTriggerScheduleTypeDaily),
		TriggerScheduleSettings: &WebhookTriggerScheduleSettings{
			Schedules: []WebhookTriggerSchedule{&DailySchedule{StartTime: "00:00", EndTime: "23:59"}},
		},
	}
	event := WebhookEvent{
		EventType:   "message",
		MessageText: ptrString("notmatch"),
		Timestamp:   time.Date(2024, 7, 1, 12, 0, 0, 0, time.UTC),
	}
	agg := &AutoReplyChannelSettingAggregate{
		TriggerSettings: []*AutoReplyTriggerSetting{daily, monthly},
	}
	result, _ := agg.ValidateTrigger(event)
	if result == nil || result.AutoReplyID != 1 {
		t.Errorf("expected monthly trigger to match, got %+v", result)
	}
}

func TestValidateTrigger_DailySchedule_CrossMidnight(t *testing.T) {
	t.Parallel()
	// 測試：daily schedule 跨午夜
	trigger := &AutoReplyTriggerSetting{
		AutoReplyID:         1,
		Status:              AutoReplyStatusActive,
		Enable:              true,
		EventType:           AutoReplyEventTypeTime,
		Priority:            10,
		TriggerScheduleType: ptrScheduleType(WebhookTriggerScheduleTypeDaily),
		TriggerScheduleSettings: &WebhookTriggerScheduleSettings{
			Schedules: []WebhookTriggerSchedule{&DailySchedule{StartTime: "22:00", EndTime: "06:00"}},
		},
	}
	tests := []struct {
		hour   int
		expect bool
	}{
		{23, true},  // 23:00 應該觸發
		{2, true},   // 02:00 應該觸發
		{12, false}, // 12:00 不應觸發
	}
	for _, tc := range tests {
		event := WebhookEvent{
			EventType:   "message",
			MessageText: ptrString("notmatch"),
			Timestamp:   time.Date(2024, 7, 1, tc.hour, 0, 0, 0, time.UTC),
		}
		agg := &AutoReplyChannelSettingAggregate{
			TriggerSettings: []*AutoReplyTriggerSetting{trigger},
		}
		result, _ := agg.ValidateTrigger(event)
		if (result != nil) != tc.expect {
			t.Errorf("hour=%d, expect match=%v, got %+v", tc.hour, tc.expect, result)
		}
	}
}

func TestValidateTrigger_Timezone_Support(t *testing.T) {
	t.Parallel()
	// 測試：時區轉換功能
	daily := &AutoReplyTriggerSetting{
		AutoReplyID:         1,
		Status:              AutoReplyStatusActive,
		Enable:              true,
		EventType:           AutoReplyEventTypeTime,
		Priority:            5,
		TriggerScheduleType: ptrScheduleType(WebhookTriggerScheduleTypeDaily),
		TriggerScheduleSettings: &WebhookTriggerScheduleSettings{
			Schedules: []WebhookTriggerSchedule{&DailySchedule{StartTime: "09:00", EndTime: "17:00"}},
		},
	}
	
	// Test case 1: UTC time 02:00 should match Asia/Taipei 10:00 (UTC+8)
	t.Run("UTC to Asia/Taipei conversion", func(t *testing.T) {
		t.Parallel()
		// UTC 02:00 = Asia/Taipei 10:00 (UTC+8)
		event := WebhookEvent{
			EventType:   "message",
			MessageText: ptrString("notmatch"),
			Timestamp:   time.Date(2024, 7, 1, 2, 0, 0, 0, time.UTC),
		}
		agg := &AutoReplyChannelSettingAggregate{
			TriggerSettings: []*AutoReplyTriggerSetting{daily},
			Timezone:        "Asia/Taipei",
		}
		result, _ := agg.ValidateTrigger(event)
		if result == nil || result.AutoReplyID != 1 {
			t.Errorf("expect daily trigger for UTC 02:00 (Asia/Taipei 10:00), got %+v", result)
		}
	})
	
	// Test case 2: UTC time 10:00 should NOT match Asia/Taipei 18:00 (outside 09:00-17:00)
	t.Run("UTC time outside bot timezone range", func(t *testing.T) {
		t.Parallel()
		// UTC 10:00 = Asia/Taipei 18:00 (outside 09:00-17:00)
		event := WebhookEvent{
			EventType:   "message",
			MessageText: ptrString("notmatch"),
			Timestamp:   time.Date(2024, 7, 1, 10, 0, 0, 0, time.UTC),
		}
		agg := &AutoReplyChannelSettingAggregate{
			TriggerSettings: []*AutoReplyTriggerSetting{daily},
			Timezone:        "Asia/Taipei",
		}
		result, _ := agg.ValidateTrigger(event)
		if result != nil {
			t.Errorf("expect no trigger for UTC 10:00 (Asia/Taipei 18:00), got %+v", result)
		}
	})
	
	// Test case 3: Cross-midnight with timezone
	t.Run("Cross-midnight with timezone", func(t *testing.T) {
		t.Parallel()
		crossMidnightTrigger := &AutoReplyTriggerSetting{
			AutoReplyID:         2,
			Status:              AutoReplyStatusActive,
			Enable:              true,
			EventType:           AutoReplyEventTypeTime,
			Priority:            5,
			TriggerScheduleType: ptrScheduleType(WebhookTriggerScheduleTypeDaily),
			TriggerScheduleSettings: &WebhookTriggerScheduleSettings{
				Schedules: []WebhookTriggerSchedule{&DailySchedule{StartTime: "22:00", EndTime: "06:00"}},
			},
		}
		
		tests := []struct {
			name     string
			utcHour  int
			expect   bool
			comment  string
		}{
			{"late night", 15, true, "UTC 15:00 = Asia/Taipei 23:00 (should trigger)"},
			{"early morning", 22, true, "UTC 22:00 = Asia/Taipei 06:00 (should trigger)"},
			{"midday", 6, false, "UTC 06:00 = Asia/Taipei 14:00 (should NOT trigger)"},
		}
		
		for _, tc := range tests {
			t.Run(tc.name, func(t *testing.T) {
				t.Parallel()
				event := WebhookEvent{
					EventType:   "message",
					MessageText: ptrString("notmatch"),
					Timestamp:   time.Date(2024, 7, 1, tc.utcHour, 0, 0, 0, time.UTC),
				}
				agg := &AutoReplyChannelSettingAggregate{
					TriggerSettings: []*AutoReplyTriggerSetting{crossMidnightTrigger},
					Timezone:        "Asia/Taipei",
				}
				result, _ := agg.ValidateTrigger(event)
				if (result != nil) != tc.expect {
					t.Errorf("%s: %s, got %+v", tc.name, tc.comment, result)
				}
			})
		}
	})
}

func TestValidateTrigger_PRD_AllCases(t *testing.T) {
	t.Parallel()
	// 準備共用 trigger
	kw := &AutoReplyTriggerSetting{
		AutoReplyID: 1,
		Status:      AutoReplyStatusActive,
		Enable:      true,
		EventType:   AutoReplyEventTypeKeyword,
		Priority:    10,
		Keywords:    []string{"hello", "hi"},
	}
	kw2 := &AutoReplyTriggerSetting{
		AutoReplyID: 2,
		Status:      AutoReplyStatusActive,
		Enable:      true,
		EventType:   AutoReplyEventTypeKeyword,
		Priority:    5,
		Keywords:    []string{"bye"},
	}
	daily := &AutoReplyTriggerSetting{
		AutoReplyID:         3,
		Status:              AutoReplyStatusActive,
		Enable:              true,
		EventType:           AutoReplyEventTypeTime,
		Priority:            5,
		TriggerScheduleType: ptrScheduleType(WebhookTriggerScheduleTypeDaily),
		TriggerScheduleSettings: &WebhookTriggerScheduleSettings{
			Schedules: []WebhookTriggerSchedule{&DailySchedule{StartTime: "09:00", EndTime: "17:00"}},
		},
	}
	monthly := &AutoReplyTriggerSetting{
		AutoReplyID:         4,
		Status:              AutoReplyStatusActive,
		Enable:              true,
		EventType:           AutoReplyEventTypeTime,
		Priority:            5,
		TriggerScheduleType: ptrScheduleType(WebhookTriggerScheduleTypeMonthly),
		TriggerScheduleSettings: &WebhookTriggerScheduleSettings{
			Schedules: []WebhookTriggerSchedule{&MonthlySchedule{Day: 1, StartTime: "10:00", EndTime: "12:00"}},
		},
	}
	bh := BusinessHour{
		Weekday:   2, // Tuesday
		StartTime: time.Date(0, 1, 1, 9, 0, 0, 0, time.UTC),
		EndTime:   time.Date(0, 1, 1, 18, 0, 0, 0, time.UTC),
	}
	agg := &AutoReplyChannelSettingAggregate{
		BotID:           1,
		TriggerSettings: []*AutoReplyTriggerSetting{kw, kw2, daily, monthly},
		BusinessHours:   []BusinessHour{bh},
		Timezone:        "Asia/Taipei",
	}
	t.Run("B-P0-7-Test2: keyword exact match, case insensitive", func(t *testing.T) {
		t.Parallel()
		event := WebhookEvent{EventType: "message", MessageText: ptrString("HELLO"), Timestamp: time.Now()}
		result, _ := agg.ValidateTrigger(event)
		if result == nil || result.AutoReplyID != 1 {
			t.Errorf("expect keyword trigger, got %+v", result)
		}
	})
	t.Run("B-P0-7-Test3: keyword match, trim spaces", func(t *testing.T) {
		t.Parallel()
		event := WebhookEvent{EventType: "message", MessageText: ptrString(" hello "), Timestamp: time.Now()}
		result, _ := agg.ValidateTrigger(event)
		if result == nil || result.AutoReplyID != 1 {
			t.Errorf("expect keyword trigger, got %+v", result)
		}
	})
	t.Run("B-P0-7-Test4: partial match should not trigger", func(t *testing.T) {
		t.Parallel()
		event := WebhookEvent{EventType: "message", MessageText: ptrString("hello world"), Timestamp: time.Now()}
		result, _ := agg.ValidateTrigger(event)
		if result != nil {
			t.Errorf("expect no trigger, got %+v", result)
		}
	})
	t.Run("B-P0-7-Test5: close variation should not trigger", func(t *testing.T) {
		t.Parallel()
		event := WebhookEvent{EventType: "message", MessageText: ptrString("helloo"), Timestamp: time.Now()}
		result, _ := agg.ValidateTrigger(event)
		if result != nil {
			t.Errorf("expect no trigger, got %+v", result)
		}
	})
	t.Run("Multiple-Keywords-Test1: multiple keywords, any match", func(t *testing.T) {
		t.Parallel()
		event := WebhookEvent{EventType: "message", MessageText: ptrString("hi"), Timestamp: time.Now()}
		result, _ := agg.ValidateTrigger(event)
		if result == nil || result.AutoReplyID != 1 {
			t.Errorf("expect keyword trigger, got %+v", result)
		}
	})
	t.Run("Multiple-Keywords-Test2: multiple keywords, case insensitive", func(t *testing.T) {
		t.Parallel()
		event := WebhookEvent{EventType: "message", MessageText: ptrString("HI"), Timestamp: time.Now()}
		result, _ := agg.ValidateTrigger(event)
		if result == nil || result.AutoReplyID != 1 {
			t.Errorf("expect keyword trigger, got %+v", result)
		}
	})
	t.Run("Multiple-Keywords-Test3: multiple keywords, no match", func(t *testing.T) {
		t.Parallel()
		event := WebhookEvent{EventType: "message", MessageText: ptrString("bye"), Timestamp: time.Now()}
		result, _ := agg.ValidateTrigger(event)
		if result == nil || result.AutoReplyID != 2 {
			t.Errorf("expect fallback to second keyword trigger, got %+v", result)
		}
	})
	t.Run("B-P0-6-Test3: daily schedule, in time window", func(t *testing.T) {
		t.Parallel()
		// UTC 02:00 = Asia/Taipei 10:00 (in daily schedule 09:00-17:00)
		event := WebhookEvent{EventType: "message", MessageText: ptrString("notmatch"), Timestamp: time.Date(2024, 7, 1, 2, 0, 0, 0, time.UTC)}
		result, _ := agg.ValidateTrigger(event)
		if result == nil || result.AutoReplyID != 3 {
			t.Errorf("expect daily trigger, got %+v", result)
		}
	})
	t.Run("B-P0-6-Test4: monthly schedule, correct day/time", func(t *testing.T) {
		t.Parallel()
		// UTC 03:00 = Asia/Taipei 11:00 (in monthly schedule Day 1, 10:00-12:00)
		event := WebhookEvent{EventType: "message", MessageText: ptrString("notmatch"), Timestamp: time.Date(2024, 7, 1, 3, 0, 0, 0, time.UTC)}
		result, _ := agg.ValidateTrigger(event)
		if result == nil || result.AutoReplyID != 4 {
			t.Errorf("expect monthly trigger, got %+v", result)
		}
	})
	// Business hour/non-business hour 需額外設計 business hour trigger，這裡略
	// Priority logic
	t.Run("Priority-Test1: keyword and general both match, keyword wins", func(t *testing.T) {
		t.Parallel()
		// UTC 02:00 = Asia/Taipei 10:00 (keyword should win over general)
		event := WebhookEvent{EventType: "message", MessageText: ptrString("hello"), Timestamp: time.Date(2024, 7, 1, 2, 0, 0, 0, time.UTC)}
		result, _ := agg.ValidateTrigger(event)
		if result == nil || result.AutoReplyID != 1 {
			t.Errorf("expect keyword trigger, got %+v", result)
		}
	})
	t.Run("Priority-Test2: keyword not match, general triggers", func(t *testing.T) {
		t.Parallel()
		// UTC 02:00 = Asia/Taipei 10:00 (should trigger daily schedule)
		event := WebhookEvent{EventType: "message", MessageText: ptrString("notmatch"), Timestamp: time.Date(2024, 7, 1, 2, 0, 0, 0, time.UTC)}
		result, _ := agg.ValidateTrigger(event)
		if result == nil || result.AutoReplyID != 3 {
			t.Errorf("expect daily trigger, got %+v", result)
		}
	})
	t.Run("Priority-Test3: keyword match, not in general time, keyword still triggers", func(t *testing.T) {
		t.Parallel()
		// UTC 12:00 = Asia/Taipei 20:00 (outside general time, but keyword should still trigger)
		event := WebhookEvent{EventType: "message", MessageText: ptrString("hello"), Timestamp: time.Date(2024, 7, 1, 12, 0, 0, 0, time.UTC)}
		result, _ := agg.ValidateTrigger(event)
		if result == nil || result.AutoReplyID != 1 {
			t.Errorf("expect keyword trigger, got %+v", result)
		}
	})
	// Message content handling
	t.Run("Message-Content-Test1: message equals keyword triggers", func(t *testing.T) {
		t.Parallel()
		event := WebhookEvent{EventType: "message", MessageText: ptrString("hello"), Timestamp: time.Now()}
		result, _ := agg.ValidateTrigger(event)
		if result == nil || result.AutoReplyID != 1 {
			t.Errorf("expect keyword trigger, got %+v", result)
		}
	})
	t.Run("Message-Content-Test2: message without keyword, no trigger", func(t *testing.T) {
		t.Parallel()
		event := WebhookEvent{EventType: "message", MessageText: ptrString("random"), Timestamp: time.Now()}
		result, _ := agg.ValidateTrigger(event)
		if result == nil || (result.AutoReplyID != 3 && result.AutoReplyID != 4) {
			t.Errorf("expect general trigger, got %+v", result)
		}
	})
	t.Run("Message-Content-Test3: general reply, any message triggers if schedule matches", func(t *testing.T) {
		t.Parallel()
		// UTC 02:00 = Asia/Taipei 10:00 (should trigger general schedule)
		event := WebhookEvent{EventType: "message", MessageText: ptrString("anything"), Timestamp: time.Date(2024, 7, 1, 2, 0, 0, 0, time.UTC)}
		result, _ := agg.ValidateTrigger(event)
		if result == nil || (result.AutoReplyID != 3 && result.AutoReplyID != 4) {
			t.Errorf("expect general trigger, got %+v", result)
		}
	})
	
	// B-P0-6-Test5: Business hours triggering test
	t.Run("B-P0-6-Test5: business hours triggering", func(t *testing.T) {
		t.Parallel()
		
		// Create business hours trigger
		businessHoursTrigger := &AutoReplyTriggerSetting{
			AutoReplyID:         5,
			Status:              AutoReplyStatusActive,
			Enable:              true,
			EventType:           AutoReplyEventTypeTime,
			Priority:            10,
			TriggerScheduleType: ptrScheduleType(WebhookTriggerScheduleTypeBusinessHour),
		}
		
		// Create test business hours: Monday 09:00-17:00 (weekday = 1 for Monday)
		businessHours := []BusinessHour{
			{
				Weekday:   1, // Monday (organization.Monday = 1)
				StartTime: time.Date(0, 1, 1, 9, 0, 0, 0, time.UTC),
				EndTime:   time.Date(0, 1, 1, 17, 0, 0, 0, time.UTC),
			},
		}
		
		aggWithBH := &AutoReplyChannelSettingAggregate{
			TriggerSettings: []*AutoReplyTriggerSetting{businessHoursTrigger},
			BusinessHours:   businessHours,
			Timezone:        "Asia/Taipei",
		}
		
		// Test during business hours: Monday 14:00 (UTC 06:00 = Asia/Taipei 14:00)
		t.Run("during business hours", func(t *testing.T) {
			// July 1, 2024 is a Monday
			event := WebhookEvent{
				EventType:   "message",
				MessageText: ptrString("anything"),
				Timestamp:   time.Date(2024, 7, 1, 6, 0, 0, 0, time.UTC), // Monday 14:00 in Asia/Taipei
			}
			result, _ := aggWithBH.ValidateTrigger(event)
			if result == nil || result.AutoReplyID != 5 {
				t.Errorf("expect business hours trigger during business hours, got %+v", result)
			}
		})
		
		// Test outside business hours: Monday 20:00 (UTC 12:00 = Asia/Taipei 20:00)
		t.Run("outside business hours", func(t *testing.T) {
			event := WebhookEvent{
				EventType:   "message",
				MessageText: ptrString("anything"),
				Timestamp:   time.Date(2024, 7, 1, 12, 0, 0, 0, time.UTC), // Monday 20:00 in Asia/Taipei
			}
			result, _ := aggWithBH.ValidateTrigger(event)
			if result != nil {
				t.Errorf("expect no trigger outside business hours, got %+v", result)
			}
		})
		
		// Test on non-business day: Sunday 14:00 (UTC 06:00 = Asia/Taipei 14:00)
		t.Run("on non-business day", func(t *testing.T) {
			// June 30, 2024 is a Sunday
			event := WebhookEvent{
				EventType:   "message",
				MessageText: ptrString("anything"),
				Timestamp:   time.Date(2024, 6, 30, 6, 0, 0, 0, time.UTC), // Sunday 14:00 in Asia/Taipei
			}
			result, _ := aggWithBH.ValidateTrigger(event)
			if result != nil {
				t.Errorf("expect no trigger on non-business day, got %+v", result)
			}
		})
	})
}

func TestValidateTrigger_IGStory_Features(t *testing.T) {
	t.Parallel()
	
	// Test Story 6: IG Story Keyword Logic
	t.Run("Story6_IGStoryKeywordLogic", func(t *testing.T) {
		t.Parallel()
		
		// Prepare IG Story Keyword trigger
		igStoryKeywordTrigger := &AutoReplyTriggerSetting{
			AutoReplyID: 1,
			Status:      AutoReplyStatusActive,
			Enable:      true,
			EventType:   AutoReplyEventTypeIGStoryKeyword,
			Priority:    10,
			Keywords:    []string{"hello"},
			IGStoryIDs:  []string{"story123"},
		}
		
		agg := &AutoReplyChannelSettingAggregate{
			TriggerSettings: []*AutoReplyTriggerSetting{igStoryKeywordTrigger},
			Timezone:        "Asia/Taipei",
		}
		
		// [IG-Story-Keyword-Test1]: Story "story123" + keyword "hello" + ig_story_id "story123" → trigger
		t.Run("IG-Story-Keyword-Test1", func(t *testing.T) {
			t.Parallel()
			event := WebhookEvent{
				EventType:   "message",
				MessageText: ptrString("hello"),
				Timestamp:   time.Now(),
				IGStoryID:   ptrString("story123"),
			}
			result, _ := agg.ValidateTrigger(event)
			if result == nil || result.AutoReplyID != 1 {
				t.Errorf("expect IG story keyword trigger, got %+v", result)
			}
		})
		
		// [IG-Story-Keyword-Test2]: Story "story123" + keyword "hello" + ig_story_id "story456" → NOT trigger
		t.Run("IG-Story-Keyword-Test2", func(t *testing.T) {
			t.Parallel()
			event := WebhookEvent{
				EventType:   "message",
				MessageText: ptrString("hello"),
				Timestamp:   time.Now(),
				IGStoryID:   ptrString("story456"),
			}
			result, _ := agg.ValidateTrigger(event)
			if result != nil {
				t.Errorf("expect no trigger for wrong story ID, got %+v", result)
			}
		})
		
		// [IG-Story-Keyword-Test3]: Story "story123" + keyword "hello" + no ig_story_id → NOT trigger
		t.Run("IG-Story-Keyword-Test3", func(t *testing.T) {
			t.Parallel()
			event := WebhookEvent{
				EventType:   "message",
				MessageText: ptrString("hello"),
				Timestamp:   time.Now(),
				IGStoryID:   nil,
			}
			result, _ := agg.ValidateTrigger(event)
			if result != nil {
				t.Errorf("expect no trigger for no story ID, got %+v", result)
			}
		})
	})
	
	// Test Story 7: IG Story General Logic
	t.Run("Story7_IGStoryGeneralLogic", func(t *testing.T) {
		t.Parallel()
		
		// Prepare IG Story General trigger
		igStoryGeneralTrigger := &AutoReplyTriggerSetting{
			AutoReplyID:         2,
			Status:              AutoReplyStatusActive,
			Enable:              true,
			EventType:           AutoReplyEventTypeIGStoryGeneral,
			Priority:            5,
			IGStoryIDs:          []string{"story123"},
			TriggerScheduleType: ptrScheduleType(WebhookTriggerScheduleTypeDaily),
			TriggerScheduleSettings: &WebhookTriggerScheduleSettings{
				Schedules: []WebhookTriggerSchedule{&DailySchedule{StartTime: "09:00", EndTime: "17:00"}},
			},
		}
		
		agg := &AutoReplyChannelSettingAggregate{
			TriggerSettings: []*AutoReplyTriggerSetting{igStoryGeneralTrigger},
			Timezone:        "Asia/Taipei",
		}
		
		// [IG-Story-General-Test1]: Story "story123" + schedule 9-17 + 14:00 + ig_story_id "story123" → trigger
		t.Run("IG-Story-General-Test1", func(t *testing.T) {
			t.Parallel()
			// UTC 06:00 = Asia/Taipei 14:00
			event := WebhookEvent{
				EventType:   "message",
				MessageText: ptrString("anything"),
				Timestamp:   time.Date(2024, 7, 1, 6, 0, 0, 0, time.UTC),
				IGStoryID:   ptrString("story123"),
			}
			result, _ := agg.ValidateTrigger(event)
			if result == nil || result.AutoReplyID != 2 {
				t.Errorf("expect IG story general trigger, got %+v", result)
			}
		})
		
		// [IG-Story-General-Test2]: Story "story123" + schedule 9-17 + 20:00 + ig_story_id "story123" → NOT trigger
		t.Run("IG-Story-General-Test2", func(t *testing.T) {
			t.Parallel()
			// UTC 12:00 = Asia/Taipei 20:00 (outside 9-17)
			event := WebhookEvent{
				EventType:   "message",
				MessageText: ptrString("anything"),
				Timestamp:   time.Date(2024, 7, 1, 12, 0, 0, 0, time.UTC),
				IGStoryID:   ptrString("story123"),
			}
			result, _ := agg.ValidateTrigger(event)
			if result != nil {
				t.Errorf("expect no trigger for outside schedule, got %+v", result)
			}
		})
		
		// [IG-Story-General-Test3]: Story "story123" + schedule 9-17 + 14:00 + ig_story_id "story456" → NOT trigger
		t.Run("IG-Story-General-Test3", func(t *testing.T) {
			t.Parallel()
			// UTC 06:00 = Asia/Taipei 14:00
			event := WebhookEvent{
				EventType:   "message",
				MessageText: ptrString("anything"),
				Timestamp:   time.Date(2024, 7, 1, 6, 0, 0, 0, time.UTC),
				IGStoryID:   ptrString("story456"),
			}
			result, _ := agg.ValidateTrigger(event)
			if result != nil {
				t.Errorf("expect no trigger for wrong story ID, got %+v", result)
			}
		})
	})
	
	// Test Story 8: IG Story Priority over General
	t.Run("Story8_IGStoryPriorityOverGeneral", func(t *testing.T) {
		t.Parallel()
		
		// Prepare both IG Story and General triggers
		igStoryKeywordTrigger := &AutoReplyTriggerSetting{
			AutoReplyID: 1,
			Status:      AutoReplyStatusActive,
			Enable:      true,
			EventType:   AutoReplyEventTypeIGStoryKeyword,
			Priority:    10,
			Keywords:    []string{"hello"},
			IGStoryIDs:  []string{"story123"},
		}
		
		generalKeywordTrigger := &AutoReplyTriggerSetting{
			AutoReplyID: 2,
			Status:      AutoReplyStatusActive,
			Enable:      true,
			EventType:   AutoReplyEventTypeKeyword,
			Priority:    15, // Higher priority than IG Story, but should still lose
			Keywords:    []string{"hello"},
		}
		
		agg := &AutoReplyChannelSettingAggregate{
			TriggerSettings: []*AutoReplyTriggerSetting{igStoryKeywordTrigger, generalKeywordTrigger},
			Timezone:        "Asia/Taipei",
		}
		
		// [IG-Story-Priority-Test1]: Both match, but IG Story should win
		t.Run("IG-Story-Priority-Test1", func(t *testing.T) {
			t.Parallel()
			event := WebhookEvent{
				EventType:   "message",
				MessageText: ptrString("hello"),
				Timestamp:   time.Now(),
				IGStoryID:   ptrString("story123"),
			}
			result, _ := agg.ValidateTrigger(event)
			if result == nil || result.AutoReplyID != 1 {
				t.Errorf("expect IG story keyword trigger (priority 1), got %+v", result)
			}
		})
		
		// [IG-Story-Priority-Test2]: IG Story General vs General Time-based priority
		t.Run("IG-Story-Priority-Test2", func(t *testing.T) {
			t.Parallel()
			
			// Prepare IG Story General and General Time-based triggers
			igStoryGeneralTrigger := &AutoReplyTriggerSetting{
				AutoReplyID:         3,
				Status:              AutoReplyStatusActive,
				Enable:              true,
				EventType:           AutoReplyEventTypeIGStoryGeneral,
				Priority:            5,
				IGStoryIDs:          []string{"story123"},
				TriggerScheduleType: ptrScheduleType(WebhookTriggerScheduleTypeDaily),
				TriggerScheduleSettings: &WebhookTriggerScheduleSettings{
					Schedules: []WebhookTriggerSchedule{&DailySchedule{StartTime: "09:00", EndTime: "17:00"}},
				},
			}
			
			generalTimeTrigger := &AutoReplyTriggerSetting{
				AutoReplyID:         4,
				Status:              AutoReplyStatusActive,
				Enable:              true,
				EventType:           AutoReplyEventTypeTime,
				Priority:            10, // Higher priority than IG Story General, but should still lose
				TriggerScheduleType: ptrScheduleType(WebhookTriggerScheduleTypeDaily),
				TriggerScheduleSettings: &WebhookTriggerScheduleSettings{
					Schedules: []WebhookTriggerSchedule{&DailySchedule{StartTime: "09:00", EndTime: "17:00"}},
				},
			}
			
			aggWithTime := &AutoReplyChannelSettingAggregate{
				TriggerSettings: []*AutoReplyTriggerSetting{igStoryGeneralTrigger, generalTimeTrigger},
				Timezone:        "Asia/Taipei",
			}
			
			// UTC 06:00 = Asia/Taipei 14:00 (in schedule)
			event := WebhookEvent{
				EventType:   "message",
				MessageText: ptrString("anything"),
				Timestamp:   time.Date(2024, 7, 1, 6, 0, 0, 0, time.UTC),
				IGStoryID:   ptrString("story123"),
			}
			result, _ := aggWithTime.ValidateTrigger(event)
			if result == nil || result.AutoReplyID != 3 {
				t.Errorf("expect IG story general trigger (priority 2), got %+v", result)
			}
		})
	})
	
	// Test Story 9: IG Story Multiple Keywords
	t.Run("Story9_IGStoryMultipleKeywords", func(t *testing.T) {
		t.Parallel()
		
		// Prepare IG Story trigger with multiple keywords
		igStoryKeywordTrigger := &AutoReplyTriggerSetting{
			AutoReplyID: 1,
			Status:      AutoReplyStatusActive,
			Enable:      true,
			EventType:   AutoReplyEventTypeIGStoryKeyword,
			Priority:    10,
			Keywords:    []string{"hello", "hi"},
			IGStoryIDs:  []string{"story123"},
		}
		
		agg := &AutoReplyChannelSettingAggregate{
			TriggerSettings: []*AutoReplyTriggerSetting{igStoryKeywordTrigger},
			Timezone:        "Asia/Taipei",
		}
		
		// [IG-Story-Multiple-Keywords-Test1]: Test each keyword
		t.Run("IG-Story-Multiple-Keywords-Test1", func(t *testing.T) {
			t.Parallel()
			
			// Test "hello"
			event1 := WebhookEvent{
				EventType:   "message",
				MessageText: ptrString("hello"),
				Timestamp:   time.Now(),
				IGStoryID:   ptrString("story123"),
			}
			result1, _ := agg.ValidateTrigger(event1)
			if result1 == nil || result1.AutoReplyID != 1 {
				t.Errorf("expect IG story keyword trigger for 'hello', got %+v", result1)
			}
			
			// Test "hi"
			event2 := WebhookEvent{
				EventType:   "message",
				MessageText: ptrString("hi"),
				Timestamp:   time.Now(),
				IGStoryID:   ptrString("story123"),
			}
			result2, _ := agg.ValidateTrigger(event2)
			if result2 == nil || result2.AutoReplyID != 1 {
				t.Errorf("expect IG story keyword trigger for 'hi', got %+v", result2)
			}
		})
		
		// [IG-Story-Multiple-Keywords-Test2]: Right keyword, wrong story ID
		t.Run("IG-Story-Multiple-Keywords-Test2", func(t *testing.T) {
			t.Parallel()
			event := WebhookEvent{
				EventType:   "message",
				MessageText: ptrString("hello"),
				Timestamp:   time.Now(),
				IGStoryID:   ptrString("story456"),
			}
			result, _ := agg.ValidateTrigger(event)
			if result != nil {
				t.Errorf("expect no trigger for wrong story ID, got %+v", result)
			}
		})
	})
	
	// Test Story 10: Complete Priority System
	t.Run("Story10_CompletePrioritySystem", func(t *testing.T) {
		t.Parallel()
		
		// Prepare all 4 types of triggers
		igStoryKeywordTrigger := &AutoReplyTriggerSetting{
			AutoReplyID: 1,
			Status:      AutoReplyStatusActive,
			Enable:      true,
			EventType:   AutoReplyEventTypeIGStoryKeyword,
			Priority:    10,
			Keywords:    []string{"hello"},
			IGStoryIDs:  []string{"story123"},
		}
		
		igStoryGeneralTrigger := &AutoReplyTriggerSetting{
			AutoReplyID:         2,
			Status:              AutoReplyStatusActive,
			Enable:              true,
			EventType:           AutoReplyEventTypeIGStoryGeneral,
			Priority:            10,
			IGStoryIDs:          []string{"story123"},
			TriggerScheduleType: ptrScheduleType(WebhookTriggerScheduleTypeDaily),
			TriggerScheduleSettings: &WebhookTriggerScheduleSettings{
				Schedules: []WebhookTriggerSchedule{&DailySchedule{StartTime: "09:00", EndTime: "17:00"}},
			},
		}
		
		generalKeywordTrigger := &AutoReplyTriggerSetting{
			AutoReplyID: 3,
			Status:      AutoReplyStatusActive,
			Enable:      true,
			EventType:   AutoReplyEventTypeKeyword,
			Priority:    10,
			Keywords:    []string{"hello"},
		}
		
		generalTimeTrigger := &AutoReplyTriggerSetting{
			AutoReplyID:         4,
			Status:              AutoReplyStatusActive,
			Enable:              true,
			EventType:           AutoReplyEventTypeTime,
			Priority:            10,
			TriggerScheduleType: ptrScheduleType(WebhookTriggerScheduleTypeDaily),
			TriggerScheduleSettings: &WebhookTriggerScheduleSettings{
				Schedules: []WebhookTriggerSchedule{&DailySchedule{StartTime: "09:00", EndTime: "17:00"}},
			},
		}
		
		agg := &AutoReplyChannelSettingAggregate{
			TriggerSettings: []*AutoReplyTriggerSetting{
				igStoryKeywordTrigger,
				igStoryGeneralTrigger,
				generalKeywordTrigger,
				generalTimeTrigger,
			},
			Timezone: "Asia/Taipei",
		}
		
		// [Complete-Priority-Test1]: All 4 rules match, should trigger IG Story Keyword (priority 1)
		t.Run("Complete-Priority-Test1", func(t *testing.T) {
			t.Parallel()
			// UTC 06:00 = Asia/Taipei 14:00 (in schedule)
			event := WebhookEvent{
				EventType:   "message",
				MessageText: ptrString("hello"),
				Timestamp:   time.Date(2024, 7, 1, 6, 0, 0, 0, time.UTC),
				IGStoryID:   ptrString("story123"),
			}
			result, _ := agg.ValidateTrigger(event)
			if result == nil || result.AutoReplyID != 1 {
				t.Errorf("expect IG story keyword trigger (priority 1), got %+v", result)
			}
		})
		
		// [Complete-Priority-Test2]: No keyword match, should trigger IG Story General (priority 2)
		t.Run("Complete-Priority-Test2", func(t *testing.T) {
			t.Parallel()
			// UTC 06:00 = Asia/Taipei 14:00 (in schedule)
			event := WebhookEvent{
				EventType:   "message",
				MessageText: ptrString("nomatch"),
				Timestamp:   time.Date(2024, 7, 1, 6, 0, 0, 0, time.UTC),
				IGStoryID:   ptrString("story123"),
			}
			result, _ := agg.ValidateTrigger(event)
			if result == nil || result.AutoReplyID != 2 {
				t.Errorf("expect IG story general trigger (priority 2), got %+v", result)
			}
		})
		
		// [Complete-Priority-Test3]: No IG Story ID, should trigger General Keyword (priority 3)
		t.Run("Complete-Priority-Test3", func(t *testing.T) {
			t.Parallel()
			// UTC 06:00 = Asia/Taipei 14:00 (in schedule)
			event := WebhookEvent{
				EventType:   "message",
				MessageText: ptrString("hello"),
				Timestamp:   time.Date(2024, 7, 1, 6, 0, 0, 0, time.UTC),
				IGStoryID:   nil,
			}
			result, _ := agg.ValidateTrigger(event)
			if result == nil || result.AutoReplyID != 3 {
				t.Errorf("expect general keyword trigger (priority 3), got %+v", result)
			}
		})
		
		// [Complete-Priority-Test4]: No keyword, no IG Story ID, should trigger General Time (priority 4)
		t.Run("Complete-Priority-Test4", func(t *testing.T) {
			t.Parallel()
			// UTC 06:00 = Asia/Taipei 14:00 (in schedule)
			event := WebhookEvent{
				EventType:   "message",
				MessageText: ptrString("nomatch"),
				Timestamp:   time.Date(2024, 7, 1, 6, 0, 0, 0, time.UTC),
				IGStoryID:   nil,
			}
			result, _ := agg.ValidateTrigger(event)
			if result == nil || result.AutoReplyID != 4 {
				t.Errorf("expect general time trigger (priority 4), got %+v", result)
			}
		})
	})
	
	// Test Story 11: IG Story Exclusion Logic
	t.Run("Story11_IGStoryExclusionLogic", func(t *testing.T) {
		t.Parallel()
		
		// Prepare both IG Story and General triggers
		igStoryKeywordTrigger := &AutoReplyTriggerSetting{
			AutoReplyID: 1,
			Status:      AutoReplyStatusActive,
			Enable:      true,
			EventType:   AutoReplyEventTypeIGStoryKeyword,
			Priority:    10,
			Keywords:    []string{"hello"},
			IGStoryIDs:  []string{"story123"},
		}
		
		generalKeywordTrigger := &AutoReplyTriggerSetting{
			AutoReplyID: 2,
			Status:      AutoReplyStatusActive,
			Enable:      true,
			EventType:   AutoReplyEventTypeKeyword,
			Priority:    10,
			Keywords:    []string{"hello"},
		}
		
		agg := &AutoReplyChannelSettingAggregate{
			TriggerSettings: []*AutoReplyTriggerSetting{igStoryKeywordTrigger, generalKeywordTrigger},
			Timezone:        "Asia/Taipei",
		}
		
		// [IG-Story-Exclusion-Test1]: IG Story setting + normal message (no story ID) → NOT trigger
		t.Run("IG-Story-Exclusion-Test1", func(t *testing.T) {
			t.Parallel()
			event := WebhookEvent{
				EventType:   "message",
				MessageText: ptrString("hello"),
				Timestamp:   time.Now(),
				IGStoryID:   nil,
			}
			result, _ := agg.ValidateTrigger(event)
			// Should trigger general keyword trigger (ID 2), not IG Story trigger (ID 1)
			if result == nil || result.AutoReplyID != 2 {
				t.Errorf("expect general keyword trigger, got %+v", result)
			}
		})
		
		// [IG-Story-Exclusion-Test2]: General setting + normal message → trigger
		t.Run("IG-Story-Exclusion-Test2", func(t *testing.T) {
			t.Parallel()
			
			// Create aggregate with only general trigger
			generalOnlyAgg := &AutoReplyChannelSettingAggregate{
				TriggerSettings: []*AutoReplyTriggerSetting{generalKeywordTrigger},
				Timezone:        "Asia/Taipei",
			}
			
			event := WebhookEvent{
				EventType:   "message",
				MessageText: ptrString("hello"),
				Timestamp:   time.Now(),
				IGStoryID:   nil,
			}
			result, _ := generalOnlyAgg.ValidateTrigger(event)
			if result == nil || result.AutoReplyID != 2 {
				t.Errorf("expect general keyword trigger, got %+v", result)
			}
		})
		
		// [IG-Story-Exclusion-Test3]: Both settings + normal message → only general triggers
		t.Run("IG-Story-Exclusion-Test3", func(t *testing.T) {
			t.Parallel()
			event := WebhookEvent{
				EventType:   "message",
				MessageText: ptrString("hello"),
				Timestamp:   time.Now(),
				IGStoryID:   nil,
			}
			result, _ := agg.ValidateTrigger(event)
			if result == nil || result.AutoReplyID != 2 {
				t.Errorf("expect general keyword trigger, not IG Story trigger, got %+v", result)
			}
		})
	})
}

// --- helper ---
func ptrString(s string) *string                                               { return &s }
func ptrScheduleType(t WebhookTriggerScheduleType) *WebhookTriggerScheduleType { return &t }
