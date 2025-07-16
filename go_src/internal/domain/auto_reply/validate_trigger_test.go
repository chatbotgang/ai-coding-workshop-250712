package auto_reply

import (
	"testing"
	"time"
)

func TestValidateTrigger_KeywordMatch(t *testing.T) {
	input := ValidateTriggerInput{
		Channel:   ChannelFacebook,
		EventType: AutoReplyEventTypeMessage,
		Message:   "  HeLLo  ",
		Keywords:  []string{"hello"},
		Now:       time.Now(),
	}
	result := ValidateTrigger(input)
	if !result.Triggered || result.Type != TriggerTypeKeyword {
		t.Errorf("should trigger by keyword, got %+v", result)
	}
}

func TestValidateTrigger_KeywordNoMatch(t *testing.T) {
	input := ValidateTriggerInput{
		Channel:   ChannelInstagram,
		EventType: AutoReplyEventTypeMessage,
		Message:   "hello world",
		Keywords:  []string{"hello"},
		Now:       time.Now(),
	}
	result := ValidateTrigger(input)
	if result.Triggered {
		t.Errorf("should not trigger for partial match, got %+v", result)
	}
}

func TestValidateTrigger_MultiKeyword(t *testing.T) {
	input := ValidateTriggerInput{
		Channel:   ChannelLINE,
		EventType: AutoReplyEventTypeMessage,
		Message:   "HI",
		Keywords:  []string{"hello", "hi"},
		Now:       time.Now(),
	}
	result := ValidateTrigger(input)
	if !result.Triggered || result.Type != TriggerTypeKeyword || result.MatchedKeyword != "hi" {
		t.Errorf("should trigger by any keyword, got %+v", result)
	}
}

func TestValidateTrigger_ScheduleDaily(t *testing.T) {
	// 09:00~18:00 內
	dd := &DailySchedule{StartTime: "09:00", EndTime: "18:00"}
	settings := &WebhookTriggerScheduleSettings{Schedules: []WebhookTriggerSchedule{dd}}
	input := ValidateTriggerInput{
		Channel:          ChannelLINE,
		EventType:        AutoReplyEventTypeMessage,
		Message:          "",
		Keywords:         nil,
		Now:              mustParseTime("2024-06-01T10:00:00Z"),
		ScheduleType:     ptrScheduleType(WebhookTriggerScheduleTypeDaily),
		ScheduleSettings: settings,
	}
	result := ValidateTrigger(input)
	if !result.Triggered || result.Type != TriggerTypeSchedule {
		t.Errorf("should trigger by daily schedule, got %+v", result)
	}
}

func TestValidateTrigger_ScheduleMonthly(t *testing.T) {
	mm := &MonthlySchedule{Day: 1, StartTime: "09:00", EndTime: "18:00"}
	settings := &WebhookTriggerScheduleSettings{Schedules: []WebhookTriggerSchedule{mm}}
	input := ValidateTriggerInput{
		Channel:          ChannelLINE,
		EventType:        AutoReplyEventTypeMessage,
		Message:          "",
		Keywords:         nil,
		Now:              mustParseTime("2024-06-01T10:00:00Z"),
		ScheduleType:     ptrScheduleType(WebhookTriggerScheduleTypeMonthly),
		ScheduleSettings: settings,
	}
	result := ValidateTrigger(input)
	if !result.Triggered || result.Type != TriggerTypeSchedule {
		t.Errorf("should trigger by monthly schedule, got %+v", result)
	}
}

func TestValidateTrigger_KeywordPriorityOverSchedule(t *testing.T) {
	// 同時符合關鍵字與排程，應只觸發關鍵字
	dd := &DailySchedule{StartTime: "09:00", EndTime: "18:00"}
	settings := &WebhookTriggerScheduleSettings{Schedules: []WebhookTriggerSchedule{dd}}
	input := ValidateTriggerInput{
		Channel:          ChannelLINE,
		EventType:        AutoReplyEventTypeMessage,
		Message:          "hello",
		Keywords:         []string{"hello"},
		Now:              mustParseTime("2024-06-01T10:00:00Z"),
		ScheduleType:     ptrScheduleType(WebhookTriggerScheduleTypeDaily),
		ScheduleSettings: settings,
	}
	result := ValidateTrigger(input)
	if !result.Triggered || result.Type != TriggerTypeKeyword {
		t.Errorf("keyword should have priority, got %+v", result)
	}
}

func TestValidateTrigger_NotMessageEvent(t *testing.T) {
	input := ValidateTriggerInput{
		Channel:   ChannelLINE,
		EventType: AutoReplyEventTypePostback,
		Message:   "hello",
		Keywords:  []string{"hello"},
		Now:       time.Now(),
	}
	result := ValidateTrigger(input)
	if result.Triggered {
		t.Errorf("should not trigger for non-message event, got %+v", result)
	}
}

// --- helpers ---
func mustParseTime(s string) time.Time {
	t, err := time.Parse(time.RFC3339, s)
	if err != nil {
		panic(err)
	}
	return t
}

func ptrScheduleType(t WebhookTriggerScheduleType) *WebhookTriggerScheduleType {
	return &t
}
