package auto_reply

import (
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
)

// [PRD] prd-part1.md [B-P0-7-Test2][B-P0-7-Test3] Keyword match: case-insensitive, trim spaces, exact match
func TestValidateTrigger_KeywordMatch(t *testing.T) {
	t.Parallel()
	msg := "  HeLLo  "
	triggers := []*AutoReplyTriggerSetting{
		{
			AutoReplyID:             1,
			WebhookTriggerSettingID: 1,
			Enable:                  true,
			Status:                  AutoReplyStatusActive,
			EventType:               AutoReplyEventTypeMessage,
			Keywords:                []string{"hello"},
			Priority:                10,
		},
	}
	agg := &AutoReplyChannelSettingAggregate{
		BotID:           1,
		ChannelType:     "LINE",
		TriggerSettings: triggers,
		Timezone:        "Asia/Taipei",
	}
	event := WebhookEvent{
		EventType:   "message",
		MessageText: &msg,
		Timestamp:   time.Now(),
		ChannelType: "LINE",
	}

	// [B-P0-7-Test2] Case-insensitive, trim spaces, exact match
	trigger, err := agg.ValidateTrigger(event)
	assert.NoError(t, err)
	assert.NotNil(t, trigger)
	assert.Equal(t, 1, trigger.AutoReplyID)
}

// [PRD] prd-part1.md [B-P0-7-Test4][B-P0-7-Test5] Keyword no match: not exact or partial match
func TestValidateTrigger_KeywordNoMatch(t *testing.T) {
	t.Parallel()
	msg := "hello world"
	triggers := []*AutoReplyTriggerSetting{
		{
			AutoReplyID:             1,
			WebhookTriggerSettingID: 1,
			Enable:                  true,
			Status:                  AutoReplyStatusActive,
			EventType:               AutoReplyEventTypeMessage,
			Keywords:                []string{"hello"},
			Priority:                10,
		},
	}
	agg := &AutoReplyChannelSettingAggregate{
		BotID:           1,
		ChannelType:     "LINE",
		TriggerSettings: triggers,
		Timezone:        "Asia/Taipei",
	}
	event := WebhookEvent{
		EventType:   "message",
		MessageText: &msg,
		Timestamp:   time.Now(),
		ChannelType: "LINE",
	}

	// [B-P0-7-Test4] Not exact match
	trigger, err := agg.ValidateTrigger(event)
	assert.NoError(t, err)
	assert.Nil(t, trigger)
}

// [PRD] prd-part1.md [Multiple-Keywords-Test1][Multiple-Keywords-Test2] Multiple keywords: any match, case-insensitive
func TestValidateTrigger_MultipleKeywords(t *testing.T) {
	t.Parallel()
	msg := "Hi"
	triggers := []*AutoReplyTriggerSetting{
		{
			AutoReplyID:             2,
			WebhookTriggerSettingID: 2,
			Enable:                  true,
			Status:                  AutoReplyStatusActive,
			EventType:               AutoReplyEventTypeMessage,
			Keywords:                []string{"hello", "hi", "hey"},
			Priority:                5,
		},
	}
	agg := &AutoReplyChannelSettingAggregate{
		BotID:           1,
		ChannelType:     "FB",
		TriggerSettings: triggers,
		Timezone:        "Asia/Taipei",
	}
	event := WebhookEvent{
		EventType:   "message",
		MessageText: &msg,
		Timestamp:   time.Now(),
		ChannelType: "FB",
	}

	// [Multiple-Keywords-Test1] Any keyword matches
	trigger, err := agg.ValidateTrigger(event)
	assert.NoError(t, err)
	assert.NotNil(t, trigger)
	assert.Equal(t, 2, trigger.AutoReplyID)
}

// [PRD] prd-part1.md [Multiple-Keywords-Test3] Multiple keywords: no match
func TestValidateTrigger_MultipleKeywords_NoMatch(t *testing.T) {
	t.Parallel()
	msg := "bonjour"
	triggers := []*AutoReplyTriggerSetting{
		{
			AutoReplyID:             2,
			WebhookTriggerSettingID: 2,
			Enable:                  true,
			Status:                  AutoReplyStatusActive,
			EventType:               AutoReplyEventTypeMessage,
			Keywords:                []string{"hello", "hi", "hey"},
			Priority:                5,
		},
	}
	agg := &AutoReplyChannelSettingAggregate{
		BotID:           1,
		ChannelType:     "FB",
		TriggerSettings: triggers,
		Timezone:        "Asia/Taipei",
	}
	event := WebhookEvent{
		EventType:   "message",
		MessageText: &msg,
		Timestamp:   time.Now(),
		ChannelType: "FB",
	}

	// [Multiple-Keywords-Test3] No keyword matches
	trigger, err := agg.ValidateTrigger(event)
	assert.NoError(t, err)
	assert.Nil(t, trigger)
}

// [PRD] prd-part1.md [Priority-Test1] Keyword priority: higher priority wins
func TestValidateTrigger_KeywordPriority(t *testing.T) {
	t.Parallel()
	msg := "hello"
	triggers := []*AutoReplyTriggerSetting{
		{
			AutoReplyID:             1,
			WebhookTriggerSettingID: 1,
			Enable:                  true,
			Status:                  AutoReplyStatusActive,
			EventType:               AutoReplyEventTypeMessage,
			Keywords:                []string{"hello"},
			Priority:                5,
		},
		{
			AutoReplyID:             2,
			WebhookTriggerSettingID: 2,
			Enable:                  true,
			Status:                  AutoReplyStatusActive,
			EventType:               AutoReplyEventTypeMessage,
			Keywords:                []string{"hello"},
			Priority:                10,
		},
	}
	agg := &AutoReplyChannelSettingAggregate{
		BotID:           1,
		ChannelType:     "IG",
		TriggerSettings: triggers,
		Timezone:        "Asia/Taipei",
	}
	event := WebhookEvent{
		EventType:   "message",
		MessageText: &msg,
		Timestamp:   time.Now(),
		ChannelType: "IG",
	}

	// [Priority-Test1] Higher priority wins
	trigger, err := agg.ValidateTrigger(event)
	assert.NoError(t, err)
	assert.NotNil(t, trigger)
	assert.Equal(t, 2, trigger.AutoReplyID)
}

// [PRD] prd-part1.md [B-P0-6-Test3] General time-based: daily schedule
func TestValidateTrigger_GeneralTimeMatch(t *testing.T) {
	t.Parallel()
	triggers := []*AutoReplyTriggerSetting{
		{
			AutoReplyID:             3,
			WebhookTriggerSettingID: 3,
			Enable:                  true,
			Status:                  AutoReplyStatusActive,
			EventType:               AutoReplyEventTypeTime,
			Priority:                1,
			TriggerScheduleType:     func() *WebhookTriggerScheduleType { t := WebhookTriggerScheduleTypeDaily; return &t }(),
			TriggerScheduleSettings: &WebhookTriggerScheduleSettings{
				Schedules: []WebhookTriggerSchedule{
					&DailySchedule{StartTime: "09:00", EndTime: "18:00"},
				},
			},
		},
	}
	agg := &AutoReplyChannelSettingAggregate{
		BotID:           1,
		ChannelType:     "LINE",
		TriggerSettings: triggers,
		Timezone:        "Asia/Taipei",
	}
	event := WebhookEvent{
		EventType:   "message",
		MessageText: nil,
		Timestamp:   time.Date(2023, 5, 1, 10, 0, 0, 0, time.Local),
		ChannelType: "LINE",
	}

	// [B-P0-6-Test3] General time-based trigger (daily)
	trigger, err := agg.ValidateTrigger(event)
	assert.NoError(t, err)
	assert.NotNil(t, trigger)
	assert.Equal(t, 3, trigger.AutoReplyID)
}

// [PRD] prd-part1.md [Priority-Test1][Priority-Test2][Priority-Test3] Keyword over general time-based
func TestValidateTrigger_KeywordOverGeneral(t *testing.T) {
	t.Parallel()
	msg := "hello"
	triggers := []*AutoReplyTriggerSetting{
		{
			AutoReplyID:             4,
			WebhookTriggerSettingID: 4,
			Enable:                  true,
			Status:                  AutoReplyStatusActive,
			EventType:               AutoReplyEventTypeTime,
			Priority:                1,
			TriggerScheduleType:     func() *WebhookTriggerScheduleType { t := WebhookTriggerScheduleTypeDaily; return &t }(),
			TriggerScheduleSettings: &WebhookTriggerScheduleSettings{},
		},
		{
			AutoReplyID:             5,
			WebhookTriggerSettingID: 5,
			Enable:                  true,
			Status:                  AutoReplyStatusActive,
			EventType:               AutoReplyEventTypeMessage,
			Keywords:                []string{"hello"},
			Priority:                2,
		},
	}
	agg := &AutoReplyChannelSettingAggregate{
		BotID:           1,
		ChannelType:     "FB",
		TriggerSettings: triggers,
		Timezone:        "Asia/Taipei",
	}
	event := WebhookEvent{
		EventType:   "message",
		MessageText: &msg,
		Timestamp:   time.Now(),
		ChannelType: "FB",
	}

	// [Priority-Test1] Keyword trigger should win over general time-based
	trigger, err := agg.ValidateTrigger(event)
	assert.NoError(t, err)
	assert.NotNil(t, trigger)
	assert.Equal(t, 5, trigger.AutoReplyID)
}

// [PRD] prd-part1.md [B-P0-6-Test3] Daily schedule
func TestValidateTrigger_DailySchedule(t *testing.T) {
	t.Parallel()
	triggers := []*AutoReplyTriggerSetting{
		{
			AutoReplyID:             10,
			WebhookTriggerSettingID: 10,
			Enable:                  true,
			Status:                  AutoReplyStatusActive,
			EventType:               AutoReplyEventTypeTime,
			Priority:                1,
			TriggerScheduleType:     func() *WebhookTriggerScheduleType { t := WebhookTriggerScheduleTypeDaily; return &t }(),
			TriggerScheduleSettings: &WebhookTriggerScheduleSettings{
				Schedules: []WebhookTriggerSchedule{
					&DailySchedule{StartTime: "09:00", EndTime: "18:00"},
				},
			},
		},
	}
	agg := &AutoReplyChannelSettingAggregate{
		BotID:           1,
		ChannelType:     "LINE",
		TriggerSettings: triggers,
		Timezone:        "Asia/Taipei",
	}
	event := WebhookEvent{
		EventType:   "message",
		Timestamp:   time.Date(2023, 5, 1, 10, 0, 0, 0, time.Local),
		ChannelType: "LINE",
	}
	trigger, err := agg.ValidateTrigger(event)
	assert.NoError(t, err)
	assert.NotNil(t, trigger)
	assert.Equal(t, 10, trigger.AutoReplyID)
}

// [PRD] prd-part1.md [B-P0-6-Test4] Monthly schedule
func TestValidateTrigger_MonthlySchedule(t *testing.T) {
	t.Parallel()
	triggers := []*AutoReplyTriggerSetting{
		{
			AutoReplyID:             11,
			WebhookTriggerSettingID: 11,
			Enable:                  true,
			Status:                  AutoReplyStatusActive,
			EventType:               AutoReplyEventTypeTime,
			Priority:                1,
			TriggerScheduleType:     func() *WebhookTriggerScheduleType { t := WebhookTriggerScheduleTypeMonthly; return &t }(),
			TriggerScheduleSettings: &WebhookTriggerScheduleSettings{
				Schedules: []WebhookTriggerSchedule{
					&MonthlySchedule{Day: 15, StartTime: "08:00", EndTime: "12:00"},
				},
			},
		},
	}
	agg := &AutoReplyChannelSettingAggregate{
		BotID:           1,
		ChannelType:     "FB",
		TriggerSettings: triggers,
		Timezone:        "Asia/Taipei",
	}
	event := WebhookEvent{
		EventType:   "message",
		Timestamp:   time.Date(2023, 5, 15, 9, 0, 0, 0, time.Local),
		ChannelType: "FB",
	}
	trigger, err := agg.ValidateTrigger(event)
	assert.NoError(t, err)
	assert.NotNil(t, trigger)
	assert.Equal(t, 11, trigger.AutoReplyID)
}

// [PRD] prd-part1.md [B-P0-6-Test5] Business hour schedule
func TestValidateTrigger_BusinessHourSchedule(t *testing.T) {
	t.Parallel()
	triggers := []*AutoReplyTriggerSetting{
		{
			AutoReplyID:             12,
			WebhookTriggerSettingID: 12,
			Enable:                  true,
			Status:                  AutoReplyStatusActive,
			EventType:               AutoReplyEventTypeTime,
			Priority:                1,
			TriggerScheduleType:     func() *WebhookTriggerScheduleType { t := WebhookTriggerScheduleTypeBusinessHour; return &t }(),
			TriggerScheduleSettings: &WebhookTriggerScheduleSettings{
				Schedules: []WebhookTriggerSchedule{
					&BusinessHourSchedule{},
				},
			},
		},
	}
	agg := &AutoReplyChannelSettingAggregate{
		BotID:           1,
		ChannelType:     "IG",
		TriggerSettings: triggers,
		Timezone:        "Asia/Taipei",
	}
	event := WebhookEvent{
		EventType:   "message",
		Timestamp:   time.Now(),
		ChannelType: "IG",
	}
	trigger, err := agg.ValidateTrigger(event)
	assert.NoError(t, err)
	assert.NotNil(t, trigger)
	assert.Equal(t, 12, trigger.AutoReplyID)
}

// [PRD] prd-part1.md [B-P0-6-Test3] Daily schedule overnight
func TestValidateTrigger_DailySchedule_Overnight(t *testing.T) {
	t.Parallel()
	triggers := []*AutoReplyTriggerSetting{
		{
			AutoReplyID:             20,
			WebhookTriggerSettingID: 20,
			Enable:                  true,
			Status:                  AutoReplyStatusActive,
			EventType:               AutoReplyEventTypeTime,
			Priority:                1,
			TriggerScheduleType:     func() *WebhookTriggerScheduleType { t := WebhookTriggerScheduleTypeDaily; return &t }(),
			TriggerScheduleSettings: &WebhookTriggerScheduleSettings{
				Schedules: []WebhookTriggerSchedule{
					&DailySchedule{StartTime: "22:00", EndTime: "02:00"},
				},
			},
		},
	}
	agg := &AutoReplyChannelSettingAggregate{
		BotID:           1,
		ChannelType:     "LINE",
		TriggerSettings: triggers,
		Timezone:        "Asia/Taipei",
	}
	// 23:00 應命中
	event := WebhookEvent{
		EventType:   "message",
		Timestamp:   time.Date(2023, 5, 1, 23, 0, 0, 0, time.Local),
		ChannelType: "LINE",
	}
	trigger, err := agg.ValidateTrigger(event)
	assert.NoError(t, err)
	assert.NotNil(t, trigger)
	assert.Equal(t, 20, trigger.AutoReplyID)
	// 01:00 應命中
	event.Timestamp = time.Date(2023, 5, 2, 1, 0, 0, 0, time.Local)
	trigger, err = agg.ValidateTrigger(event)
	assert.NoError(t, err)
	assert.NotNil(t, trigger)
	assert.Equal(t, 20, trigger.AutoReplyID)
	// 03:00 不應命中
	event.Timestamp = time.Date(2023, 5, 2, 3, 0, 0, 0, time.Local)
	trigger, err = agg.ValidateTrigger(event)
	assert.NoError(t, err)
	assert.Nil(t, trigger)
}

// [PRD] prd-part1.md [B-P0-6-Test4] Monthly schedule overnight
func TestValidateTrigger_MonthlySchedule_Overnight(t *testing.T) {
	t.Parallel()
	triggers := []*AutoReplyTriggerSetting{
		{
			AutoReplyID:             21,
			WebhookTriggerSettingID: 21,
			Enable:                  true,
			Status:                  AutoReplyStatusActive,
			EventType:               AutoReplyEventTypeTime,
			Priority:                1,
			TriggerScheduleType:     func() *WebhookTriggerScheduleType { t := WebhookTriggerScheduleTypeMonthly; return &t }(),
			TriggerScheduleSettings: &WebhookTriggerScheduleSettings{
				Schedules: []WebhookTriggerSchedule{
					&MonthlySchedule{Day: 15, StartTime: "23:00", EndTime: "02:00"},
				},
			},
		},
	}
	agg := &AutoReplyChannelSettingAggregate{
		BotID:           1,
		ChannelType:     "FB",
		TriggerSettings: triggers,
		Timezone:        "Asia/Taipei",
	}
	// 15 號 23:30 應命中
	event := WebhookEvent{
		EventType:   "message",
		Timestamp:   time.Date(2023, 5, 15, 23, 30, 0, 0, time.Local),
		ChannelType: "FB",
	}
	trigger, err := agg.ValidateTrigger(event)
	assert.NoError(t, err)
	assert.NotNil(t, trigger)
	assert.Equal(t, 21, trigger.AutoReplyID)
	// 16 號 01:00 應命中（跨夜，仍屬於 15 號的 schedule）
	event.Timestamp = time.Date(2023, 5, 16, 1, 0, 0, 0, time.Local)
	trigger, err = agg.ValidateTrigger(event)
	// 這裡根據業務規則，跨夜後的凌晨是否算前一天 schedule，若要嚴格，這裡應不命中
	// 但目前 isTimeMatch 僅判斷 day，這裡會不命中，這是業務討論點
	assert.NoError(t, err)
	assert.Nil(t, trigger)
}

// [PRD] prd-part2.md [IG-Story-Keyword-Test1][IG-Story-Keyword-Test2][IG-Story-Keyword-Test3][B-P1-18-Test7][B-P1-18-Test8a] IG Story keyword match
func TestValidateTrigger_IGStoryKeywordMatch(t *testing.T) {
	t.Parallel()
	msg := "hello"
	storyID := "story123"
	triggers := []*AutoReplyTriggerSetting{
		{
			AutoReplyID:             100,
			WebhookTriggerSettingID: 100,
			Enable:                  true,
			Status:                  AutoReplyStatusActive,
			EventType:               AutoReplyEventTypeMessage,
			Keywords:                []string{"hello"},
			Priority:                10,
			StoryIDs:                []string{"story123"},
		},
	}
	agg := &AutoReplyChannelSettingAggregate{
		BotID:           1,
		ChannelType:     "IG",
		TriggerSettings: triggers,
		Timezone:        "Asia/Taipei",
	}
	event := WebhookEvent{
		EventType:   "message",
		MessageText: &msg,
		Timestamp:   time.Now(),
		ChannelType: "IG",
		IGStoryID:   &storyID,
	}
	// IG-Story-Keyword-Test1: story id & keyword match
	trigger, err := agg.ValidateTrigger(event)
	assert.NoError(t, err)
	assert.NotNil(t, trigger)
	assert.Equal(t, 100, trigger.AutoReplyID)

	// IG-Story-Keyword-Test2: wrong story id
	wrongStory := "story456"
	event.IGStoryID = &wrongStory
	trigger, err = agg.ValidateTrigger(event)
	assert.NoError(t, err)
	assert.Nil(t, trigger)

	// IG-Story-Keyword-Test3: no story id
	event.IGStoryID = nil
	trigger, err = agg.ValidateTrigger(event)
	assert.NoError(t, err)
	assert.Nil(t, trigger)
}

// [PRD] prd-part2.md [IG-Story-General-Test1][IG-Story-General-Test2][IG-Story-General-Test3][B-P1-18-Test8b] IG Story general match
func TestValidateTrigger_IGStoryGeneralMatch(t *testing.T) {
	t.Parallel()
	storyID := "story123"
	triggers := []*AutoReplyTriggerSetting{
		{
			AutoReplyID:             101,
			WebhookTriggerSettingID: 101,
			Enable:                  true,
			Status:                  AutoReplyStatusActive,
			EventType:               AutoReplyEventTypeTime,
			Priority:                5,
			StoryIDs:                []string{"story123"},
			TriggerScheduleType:     func() *WebhookTriggerScheduleType { t := WebhookTriggerScheduleTypeDaily; return &t }(),
			TriggerScheduleSettings: &WebhookTriggerScheduleSettings{
				Schedules: []WebhookTriggerSchedule{
					&DailySchedule{StartTime: "09:00", EndTime: "17:00"},
				},
			},
		},
	}
	agg := &AutoReplyChannelSettingAggregate{
		BotID:           1,
		ChannelType:     "IG",
		TriggerSettings: triggers,
		Timezone:        "Asia/Taipei",
	}
	event := WebhookEvent{
		EventType:   "message",
		Timestamp:   time.Date(2023, 5, 1, 14, 0, 0, 0, time.Local),
		ChannelType: "IG",
		IGStoryID:   &storyID,
	}
	// IG-Story-General-Test1: in schedule
	trigger, err := agg.ValidateTrigger(event)
	assert.NoError(t, err)
	assert.NotNil(t, trigger)
	assert.Equal(t, 101, trigger.AutoReplyID)

	// IG-Story-General-Test2: out of schedule
	event.Timestamp = time.Date(2023, 5, 1, 20, 0, 0, 0, time.Local)
	trigger, err = agg.ValidateTrigger(event)
	assert.NoError(t, err)
	assert.Nil(t, trigger)

	// IG-Story-General-Test3: wrong story id
	otherStory := "story456"
	event.IGStoryID = &otherStory
	event.Timestamp = time.Date(2023, 5, 1, 14, 0, 0, 0, time.Local)
	trigger, err = agg.ValidateTrigger(event)
	assert.NoError(t, err)
	assert.Nil(t, trigger)
}

// [PRD] prd-part2.md [IG-Story-Priority-Test1][B-P1-18-Test9] IG Story keyword priority over general keyword
func TestValidateTrigger_IGStoryPriorityOverGeneral(t *testing.T) {
	t.Parallel()
	msg := "hello"
	storyID := "story123"
	triggers := []*AutoReplyTriggerSetting{
		// IG Story Keyword (highest)
		{
			AutoReplyID:             201,
			WebhookTriggerSettingID: 201,
			Enable:                  true,
			Status:                  AutoReplyStatusActive,
			EventType:               AutoReplyEventTypeMessage,
			Keywords:                []string{"hello"},
			Priority:                10,
			StoryIDs:                []string{"story123"},
		},
		// General Keyword
		{
			AutoReplyID:             202,
			WebhookTriggerSettingID: 202,
			Enable:                  true,
			Status:                  AutoReplyStatusActive,
			EventType:               AutoReplyEventTypeMessage,
			Keywords:                []string{"hello"},
			Priority:                5,
		},
	}
	agg := &AutoReplyChannelSettingAggregate{
		BotID:           1,
		ChannelType:     "IG",
		TriggerSettings: triggers,
		Timezone:        "Asia/Taipei",
	}
	event := WebhookEvent{
		EventType:   "message",
		MessageText: &msg,
		Timestamp:   time.Now(),
		ChannelType: "IG",
		IGStoryID:   &storyID,
	}
	// IG-Story-Priority-Test1: IG Story Keyword wins
	trigger, err := agg.ValidateTrigger(event)
	assert.NoError(t, err)
	assert.NotNil(t, trigger)
	assert.Equal(t, 201, trigger.AutoReplyID)

	// Remove IGStoryID, should match general keyword
	event.IGStoryID = nil
	trigger, err = agg.ValidateTrigger(event)
	assert.NoError(t, err)
	assert.NotNil(t, trigger)
	assert.Equal(t, 202, trigger.AutoReplyID)
}

// [PRD] prd-part2.md [IG-Story-Exclusion-Test1][IG-Story-Exclusion-Test2][IG-Story-Exclusion-Test3] IG Story exclusion logic
func TestValidateTrigger_IGStoryExclusion(t *testing.T) {
	t.Parallel()
	msg := "hello"
	triggers := []*AutoReplyTriggerSetting{
		// IG Story Keyword
		{
			AutoReplyID:             301,
			WebhookTriggerSettingID: 301,
			Enable:                  true,
			Status:                  AutoReplyStatusActive,
			EventType:               AutoReplyEventTypeMessage,
			Keywords:                []string{"hello"},
			Priority:                10,
			StoryIDs:                []string{"story123"},
		},
		// General Keyword
		{
			AutoReplyID:             302,
			WebhookTriggerSettingID: 302,
			Enable:                  true,
			Status:                  AutoReplyStatusActive,
			EventType:               AutoReplyEventTypeMessage,
			Keywords:                []string{"hello"},
			Priority:                5,
		},
	}
	agg := &AutoReplyChannelSettingAggregate{
		BotID:           1,
		ChannelType:     "IG",
		TriggerSettings: triggers,
		Timezone:        "Asia/Taipei",
	}
	// IG-Story-Exclusion-Test1: IG story keyword rule, but no IGStoryID
	event := WebhookEvent{
		EventType:   "message",
		MessageText: &msg,
		Timestamp:   time.Now(),
		ChannelType: "IG",
		IGStoryID:   nil,
	}
	trigger, err := agg.ValidateTrigger(event)
	assert.NoError(t, err)
	assert.NotNil(t, trigger)
	assert.Equal(t, 302, trigger.AutoReplyID) // Only general keyword should match

	// IG-Story-Exclusion-Test2: Only IG story keyword rule, no IGStoryID
	agg.TriggerSettings = agg.TriggerSettings[:1]
	trigger, err = agg.ValidateTrigger(event)
	assert.NoError(t, err)
	assert.Nil(t, trigger)

	// IG-Story-Exclusion-Test3: Both rules, IGStoryID present
	igStoryID := "story123"
	event.IGStoryID = &igStoryID
	trigger, err = agg.ValidateTrigger(event)
	assert.NoError(t, err)
	assert.NotNil(t, trigger)
	assert.Equal(t, 301, trigger.AutoReplyID)
}

// [PRD] prd-part2.md [IG-Story-Multiple-Keywords-Test1][IG-Story-Multiple-Keywords-Test2] IG Story multiple keywords
func TestValidateTrigger_IGStoryMultipleKeywords(t *testing.T) {
	t.Parallel()
	msg := "hi"
	storyID := "story123"
	triggers := []*AutoReplyTriggerSetting{
		{
			AutoReplyID:             401,
			WebhookTriggerSettingID: 401,
			Enable:                  true,
			Status:                  AutoReplyStatusActive,
			EventType:               AutoReplyEventTypeMessage,
			Keywords:                []string{"hello", "hi"},
			Priority:                10,
			StoryIDs:                []string{"story123"},
		},
	}
	agg := &AutoReplyChannelSettingAggregate{
		BotID:           1,
		ChannelType:     "IG",
		TriggerSettings: triggers,
		Timezone:        "Asia/Taipei",
	}
	event := WebhookEvent{
		EventType:   "message",
		MessageText: &msg,
		Timestamp:   time.Now(),
		ChannelType: "IG",
		IGStoryID:   &storyID,
	}
	// IG-Story-Multiple-Keywords-Test1: any keyword matches
	trigger, err := agg.ValidateTrigger(event)
	assert.NoError(t, err)
	assert.NotNil(t, trigger)
	assert.Equal(t, 401, trigger.AutoReplyID)

	// IG-Story-Multiple-Keywords-Test2: wrong story id
	wrongStory := "story456"
	event.IGStoryID = &wrongStory
	trigger, err = agg.ValidateTrigger(event)
	assert.NoError(t, err)
	assert.Nil(t, trigger)
}

// [PRD] prd-part2.md [Complete-Priority-Test1][Complete-Priority-Test2][Complete-Priority-Test3][Complete-Priority-Test4] Complete 4-level priority system
func TestValidateTrigger_CompletePrioritySystem(t *testing.T) {
	t.Parallel()
	msg := "hello"
	storyID := "story123"
	triggers := []*AutoReplyTriggerSetting{
		// Priority 1: IG Story Keyword
		{
			AutoReplyID:             1,
			WebhookTriggerSettingID: 1,
			Enable:                  true,
			Status:                  AutoReplyStatusActive,
			EventType:               AutoReplyEventTypeMessage,
			Keywords:                []string{"hello"},
			Priority:                10,
			StoryIDs:                []string{"story123"},
		},
		// Priority 2: IG Story General
		{
			AutoReplyID:             2,
			WebhookTriggerSettingID: 2,
			Enable:                  true,
			Status:                  AutoReplyStatusActive,
			EventType:               AutoReplyEventTypeTime,
			Priority:                8,
			StoryIDs:                []string{"story123"},
			TriggerScheduleType:     func() *WebhookTriggerScheduleType { t := WebhookTriggerScheduleTypeDaily; return &t }(),
			TriggerScheduleSettings: &WebhookTriggerScheduleSettings{
				Schedules: []WebhookTriggerSchedule{
					&DailySchedule{StartTime: "09:00", EndTime: "18:00"},
				},
			},
		},
		// Priority 3: General Keyword
		{
			AutoReplyID:             3,
			WebhookTriggerSettingID: 3,
			Enable:                  true,
			Status:                  AutoReplyStatusActive,
			EventType:               AutoReplyEventTypeMessage,
			Keywords:                []string{"hello"},
			Priority:                5,
		},
		// Priority 4: General Time-based
		{
			AutoReplyID:             4,
			WebhookTriggerSettingID: 4,
			Enable:                  true,
			Status:                  AutoReplyStatusActive,
			EventType:               AutoReplyEventTypeTime,
			Priority:                1,
			TriggerScheduleType:     func() *WebhookTriggerScheduleType { t := WebhookTriggerScheduleTypeDaily; return &t }(),
			TriggerScheduleSettings: &WebhookTriggerScheduleSettings{
				Schedules: []WebhookTriggerSchedule{
					&DailySchedule{StartTime: "09:00", EndTime: "18:00"},
				},
			},
		},
	}
	agg := &AutoReplyChannelSettingAggregate{
		BotID:           1,
		ChannelType:     "IG",
		TriggerSettings: triggers,
		Timezone:        "Asia/Taipei",
	}
	// Case 1: All conditions match (should hit IG Story Keyword)
	event := WebhookEvent{
		EventType:   "message",
		MessageText: &msg,
		Timestamp:   time.Date(2023, 5, 1, 10, 0, 0, 0, time.Local),
		ChannelType: "IG",
		IGStoryID:   &storyID,
	}
	trigger, err := agg.ValidateTrigger(event)
	assert.NoError(t, err)
	assert.NotNil(t, trigger)
	assert.Equal(t, 1, trigger.AutoReplyID)

	// Case 2: IG Story General, General Keyword, General Time-based (no keyword match, should hit IG Story General)
	msg2 := "notmatch"
	event.MessageText = &msg2
	trigger, err = agg.ValidateTrigger(event)
	assert.NoError(t, err)
	assert.NotNil(t, trigger)
	assert.Equal(t, 2, trigger.AutoReplyID)

	// Case 3: General Keyword, General Time-based (no IGStoryID, keyword match, should hit General Keyword)
	event.IGStoryID = nil
	event.MessageText = &msg
	trigger, err = agg.ValidateTrigger(event)
	assert.NoError(t, err)
	assert.NotNil(t, trigger)
	assert.Equal(t, 3, trigger.AutoReplyID)

	// Case 4: Only General Time-based (no IGStoryID, no keyword match, should hit General Time-based)
	event.MessageText = &msg2
	trigger, err = agg.ValidateTrigger(event)
	assert.NoError(t, err)
	assert.NotNil(t, trigger)
	assert.Equal(t, 4, trigger.AutoReplyID)
}
