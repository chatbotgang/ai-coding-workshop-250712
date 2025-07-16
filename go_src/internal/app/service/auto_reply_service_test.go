package service

import (
	"context"
	"testing"
	"time"

	"github.com/chatbotgang/workshop/internal/adapter/repository"
	"github.com/chatbotgang/workshop/internal/domain/auto_reply"
)

func TestAutoReplyService_ValidateTrigger_Keyword(t *testing.T) {
	t.Parallel()
	svc := NewAutoReplyService(AutoReplyServiceParam{})
	input := auto_reply.ValidateTriggerInput{
		Channel:   auto_reply.ChannelLINE,
		EventType: auto_reply.AutoReplyEventTypeMessage,
		Message:   "Hi",
		Keywords:  []string{"hi"},
		Now:       time.Now(),
	}
	result := svc.ValidateTrigger(context.Background(), input)
	if !result.Triggered || result.Type != auto_reply.TriggerTypeKeyword {
		t.Errorf("should trigger by keyword, got %+v", result)
	}
}

func TestAutoReplyService_ValidateTrigger_Schedule(t *testing.T) {
	t.Parallel()
	svc := NewAutoReplyService(AutoReplyServiceParam{})
	dd := &auto_reply.DailySchedule{StartTime: "09:00", EndTime: "18:00"}
	settings := &auto_reply.WebhookTriggerScheduleSettings{Schedules: []auto_reply.WebhookTriggerSchedule{dd}}
	input := auto_reply.ValidateTriggerInput{
		Channel:          auto_reply.ChannelLINE,
		EventType:        auto_reply.AutoReplyEventTypeMessage,
		Message:          "",
		Keywords:         nil,
		Now:              mustParseTime("2024-06-01T10:00:00Z"),
		ScheduleType:     ptrScheduleType(auto_reply.WebhookTriggerScheduleTypeDaily),
		ScheduleSettings: settings,
	}
	result := svc.ValidateTrigger(context.Background(), input)
	if !result.Triggered || result.Type != auto_reply.TriggerTypeSchedule {
		t.Errorf("should trigger by schedule, got %+v", result)
	}
}

func TestAutoReplyService_CRUD(t *testing.T) {
	t.Parallel()
	// 使用記憶體 repo
	repo := auto_replyMemoryRepoMock()
	ctx := context.Background()

	// Create
	ar := &auto_reply.AutoReply{
		OrganizationID: 1,
		Name:           "TestAutoReply",
		Status:         auto_reply.AutoReplyStatusActive,
	}
	err := repo.Create(ctx, ar)
	if err != nil {
		t.Fatalf("create failed: %v", err)
	}
	if ar.ID == 0 {
		t.Errorf("expected ID to be set after create")
	}

	// GetByID
	got, err := repo.GetByID(ctx, ar.ID)
	if err != nil || got == nil || got.Name != ar.Name {
		t.Errorf("get by id failed: %v, got=%+v", err, got)
	}

	// Update
	ar.Name = "UpdatedName"
	err = repo.Update(ctx, ar)
	if err != nil {
		t.Errorf("update failed: %v", err)
	}
	got, _ = repo.GetByID(ctx, ar.ID)
	if got.Name != "UpdatedName" {
		t.Errorf("update not persisted, got=%+v", got)
	}

	// ListByOrganization
	ars, err := repo.ListByOrganization(ctx, 1)
	if err != nil || len(ars) == 0 {
		t.Errorf("list by org failed: %v, got=%+v", err, ars)
	}

	// Delete
	err = repo.Delete(ctx, ar.ID)
	if err != nil {
		t.Errorf("delete failed: %v", err)
	}
	_, err = repo.GetByID(ctx, ar.ID)
	if err == nil {
		t.Errorf("expected error after delete, got nil")
	}
}

func TestAutoReplyService_RepoNotFound(t *testing.T) {
	t.Parallel()
	repo := auto_replyMemoryRepoMock()
	ctx := context.Background()

	_, err := repo.GetByID(ctx, 999)
	if err == nil {
		t.Errorf("expected not found error")
	}
	err = repo.Delete(ctx, 999)
	if err == nil {
		t.Errorf("expected not found error on delete")
	}
}

func TestAutoReplyService_ValidateTrigger_KeywordMatch(t *testing.T) {
	t.Parallel()
	svc := NewAutoReplyService(AutoReplyServiceParam{})
	input := auto_reply.ValidateTriggerInput{
		Channel:   auto_reply.ChannelFacebook,
		EventType: auto_reply.AutoReplyEventTypeMessage,
		Message:   "  HeLLo  ",
		Keywords:  []string{"hello"},
		Now:       time.Now(),
	}
	result := svc.ValidateTrigger(context.Background(), input)
	if !result.Triggered || result.Type != auto_reply.TriggerTypeKeyword {
		t.Errorf("should trigger by keyword, got %+v", result)
	}
}

func TestAutoReplyService_ValidateTrigger_KeywordNoMatch(t *testing.T) {
	t.Parallel()
	svc := NewAutoReplyService(AutoReplyServiceParam{})
	input := auto_reply.ValidateTriggerInput{
		Channel:   auto_reply.ChannelInstagram,
		EventType: auto_reply.AutoReplyEventTypeMessage,
		Message:   "hello world",
		Keywords:  []string{"hello"},
		Now:       time.Now(),
	}
	result := svc.ValidateTrigger(context.Background(), input)
	if result.Triggered {
		t.Errorf("should not trigger for partial match, got %+v", result)
	}
}

func TestAutoReplyService_ValidateTrigger_MultiKeyword(t *testing.T) {
	t.Parallel()
	svc := NewAutoReplyService(AutoReplyServiceParam{})
	input := auto_reply.ValidateTriggerInput{
		Channel:   auto_reply.ChannelLINE,
		EventType: auto_reply.AutoReplyEventTypeMessage,
		Message:   "HI",
		Keywords:  []string{"hello", "hi"},
		Now:       time.Now(),
	}
	result := svc.ValidateTrigger(context.Background(), input)
	if !result.Triggered || result.Type != auto_reply.TriggerTypeKeyword || result.MatchedKeyword != "hi" {
		t.Errorf("should trigger by any keyword, got %+v", result)
	}
}

func TestAutoReplyService_ValidateTrigger_ScheduleDaily(t *testing.T) {
	t.Parallel()
	svc := NewAutoReplyService(AutoReplyServiceParam{})
	dd := &auto_reply.DailySchedule{StartTime: "09:00", EndTime: "18:00"}
	settings := &auto_reply.WebhookTriggerScheduleSettings{Schedules: []auto_reply.WebhookTriggerSchedule{dd}}
	input := auto_reply.ValidateTriggerInput{
		Channel:          auto_reply.ChannelLINE,
		EventType:        auto_reply.AutoReplyEventTypeMessage,
		Message:          "",
		Keywords:         nil,
		Now:              mustParseTime("2024-06-01T10:00:00Z"),
		ScheduleType:     ptrScheduleType(auto_reply.WebhookTriggerScheduleTypeDaily),
		ScheduleSettings: settings,
	}
	result := svc.ValidateTrigger(context.Background(), input)
	if !result.Triggered || result.Type != auto_reply.TriggerTypeSchedule {
		t.Errorf("should trigger by daily schedule, got %+v", result)
	}
}

func TestAutoReplyService_ValidateTrigger_KeywordPriorityOverSchedule(t *testing.T) {
	t.Parallel()
	svc := NewAutoReplyService(AutoReplyServiceParam{})
	dd := &auto_reply.DailySchedule{StartTime: "09:00", EndTime: "18:00"}
	settings := &auto_reply.WebhookTriggerScheduleSettings{Schedules: []auto_reply.WebhookTriggerSchedule{dd}}
	input := auto_reply.ValidateTriggerInput{
		Channel:          auto_reply.ChannelLINE,
		EventType:        auto_reply.AutoReplyEventTypeMessage,
		Message:          "hello",
		Keywords:         []string{"hello"},
		Now:              mustParseTime("2024-06-01T10:00:00Z"),
		ScheduleType:     ptrScheduleType(auto_reply.WebhookTriggerScheduleTypeDaily),
		ScheduleSettings: settings,
	}
	result := svc.ValidateTrigger(context.Background(), input)
	if !result.Triggered || result.Type != auto_reply.TriggerTypeKeyword {
		t.Errorf("keyword should have priority, got %+v", result)
	}
}

func TestAutoReplyService_ValidateTrigger_NotMessageEvent(t *testing.T) {
	t.Parallel()
	svc := NewAutoReplyService(AutoReplyServiceParam{})
	input := auto_reply.ValidateTriggerInput{
		Channel:   auto_reply.ChannelLINE,
		EventType: auto_reply.AutoReplyEventTypePostback,
		Message:   "hello",
		Keywords:  []string{"hello"},
		Now:       time.Now(),
	}
	result := svc.ValidateTrigger(context.Background(), input)
	if result.Triggered {
		t.Errorf("should not trigger for non-message event, got %+v", result)
	}
}

// PRD Story 1: 關鍵字回覆邏輯
// Case 1-1: 完整相符（各種大小寫）→ 觸發
func TestAutoReplyService_ValidateTrigger_KeywordMatch_PRD1_1(t *testing.T) {
	t.Parallel()
	svc := NewAutoReplyService(AutoReplyServiceParam{})
	input := auto_reply.ValidateTriggerInput{
		Channel:   auto_reply.ChannelFacebook,
		EventType: auto_reply.AutoReplyEventTypeMessage,
		Message:   "  HeLLo  ",
		Keywords:  []string{"hello"},
		Now:       time.Now(),
	}
	result := svc.ValidateTrigger(context.Background(), input)
	if !result.Triggered || result.Type != auto_reply.TriggerTypeKeyword {
		t.Errorf("[PRD1-1] should trigger by keyword, got %+v", result)
	}
}

// Case 1-2: 前後有空格 → 去除後觸發
func TestAutoReplyService_ValidateTrigger_KeywordTrim_PRD1_2(t *testing.T) {
	t.Parallel()
	svc := NewAutoReplyService(AutoReplyServiceParam{})
	input := auto_reply.ValidateTriggerInput{
		Channel:   auto_reply.ChannelLINE,
		EventType: auto_reply.AutoReplyEventTypeMessage,
		Message:   "  hello  ",
		Keywords:  []string{"hello"},
		Now:       time.Now(),
	}
	result := svc.ValidateTrigger(context.Background(), input)
	if !result.Triggered {
		t.Errorf("[PRD1-2] should trigger by trimmed keyword, got %+v", result)
	}
}

// Case 1-3: 訊息包含關鍵字但有其他字 → 不觸發
func TestAutoReplyService_ValidateTrigger_KeywordPartial_PRD1_3(t *testing.T) {
	t.Parallel()
	svc := NewAutoReplyService(AutoReplyServiceParam{})
	input := auto_reply.ValidateTriggerInput{
		Channel:   auto_reply.ChannelInstagram,
		EventType: auto_reply.AutoReplyEventTypeMessage,
		Message:   "hello world",
		Keywords:  []string{"hello"},
		Now:       time.Now(),
	}
	result := svc.ValidateTrigger(context.Background(), input)
	if result.Triggered {
		t.Errorf("[PRD1-3] should not trigger for partial match, got %+v", result)
	}
}

// Case 1-4: 部分匹配或近似 → 不觸發
func TestAutoReplyService_ValidateTrigger_KeywordFuzzy_PRD1_4(t *testing.T) {
	t.Parallel()
	svc := NewAutoReplyService(AutoReplyServiceParam{})
	input := auto_reply.ValidateTriggerInput{
		Channel:   auto_reply.ChannelLINE,
		EventType: auto_reply.AutoReplyEventTypeMessage,
		Message:   "hell",
		Keywords:  []string{"hello"},
		Now:       time.Now(),
	}
	result := svc.ValidateTrigger(context.Background(), input)
	if result.Triggered {
		t.Errorf("[PRD1-4] should not trigger for fuzzy match, got %+v", result)
	}
}

// PRD Story 2: 多關鍵字支援
// Case 2-1: 任一關鍵字相符即觸發
func TestAutoReplyService_ValidateTrigger_MultiKeyword_PRD2_1(t *testing.T) {
	t.Parallel()
	svc := NewAutoReplyService(AutoReplyServiceParam{})
	input := auto_reply.ValidateTriggerInput{
		Channel:   auto_reply.ChannelLINE,
		EventType: auto_reply.AutoReplyEventTypeMessage,
		Message:   "HI",
		Keywords:  []string{"hello", "hi"},
		Now:       time.Now(),
	}
	result := svc.ValidateTrigger(context.Background(), input)
	if !result.Triggered || result.Type != auto_reply.TriggerTypeKeyword || result.MatchedKeyword != "hi" {
		t.Errorf("[PRD2-1] should trigger by any keyword, got %+v", result)
	}
}

// Case 2-2: 不同大小寫 → 觸發
func TestAutoReplyService_ValidateTrigger_MultiKeywordCase_PRD2_2(t *testing.T) {
	t.Parallel()
	svc := NewAutoReplyService(AutoReplyServiceParam{})
	input := auto_reply.ValidateTriggerInput{
		Channel:   auto_reply.ChannelLINE,
		EventType: auto_reply.AutoReplyEventTypeMessage,
		Message:   "HELLO",
		Keywords:  []string{"hello", "hi"},
		Now:       time.Now(),
	}
	result := svc.ValidateTrigger(context.Background(), input)
	if !result.Triggered {
		t.Errorf("[PRD2-2] should trigger by case-insensitive keyword, got %+v", result)
	}
}

// Case 2-3: 無任何關鍵字匹配 → 不觸發
func TestAutoReplyService_ValidateTrigger_MultiKeywordNoMatch_PRD2_3(t *testing.T) {
	t.Parallel()
	svc := NewAutoReplyService(AutoReplyServiceParam{})
	input := auto_reply.ValidateTriggerInput{
		Channel:   auto_reply.ChannelLINE,
		EventType: auto_reply.AutoReplyEventTypeMessage,
		Message:   "bye",
		Keywords:  []string{"hello", "hi"},
		Now:       time.Now(),
	}
	result := svc.ValidateTrigger(context.Background(), input)
	if result.Triggered {
		t.Errorf("[PRD2-3] should not trigger if no keyword matches, got %+v", result)
	}
}

// PRD Story 3: 一般時間排程邏輯
// Case 3-1: 每日排程內 → 觸發
func TestAutoReplyService_ValidateTrigger_ScheduleDaily_PRD3_1(t *testing.T) {
	t.Parallel()
	svc := NewAutoReplyService(AutoReplyServiceParam{})
	dd := &auto_reply.DailySchedule{StartTime: "09:00", EndTime: "18:00"}
	settings := &auto_reply.WebhookTriggerScheduleSettings{Schedules: []auto_reply.WebhookTriggerSchedule{dd}}
	input := auto_reply.ValidateTriggerInput{
		Channel:          auto_reply.ChannelLINE,
		EventType:        auto_reply.AutoReplyEventTypeMessage,
		Message:          "",
		Keywords:         nil,
		Now:              mustParseTime("2024-06-01T10:00:00Z"),
		ScheduleType:     ptrScheduleType(auto_reply.WebhookTriggerScheduleTypeDaily),
		ScheduleSettings: settings,
	}
	result := svc.ValidateTrigger(context.Background(), input)
	if !result.Triggered || result.Type != auto_reply.TriggerTypeSchedule {
		t.Errorf("[PRD3-1] should trigger by daily schedule, got %+v", result)
	}
}

// Case 3-2: 每月特定日期時間 → 觸發
func TestAutoReplyService_ValidateTrigger_ScheduleMonthly_PRD3_2(t *testing.T) {
	t.Parallel()
	svc := NewAutoReplyService(AutoReplyServiceParam{})
	mm := &auto_reply.MonthlySchedule{Day: 1, StartTime: "09:00", EndTime: "18:00"}
	settings := &auto_reply.WebhookTriggerScheduleSettings{Schedules: []auto_reply.WebhookTriggerSchedule{mm}}
	input := auto_reply.ValidateTriggerInput{
		Channel:          auto_reply.ChannelLINE,
		EventType:        auto_reply.AutoReplyEventTypeMessage,
		Message:          "",
		Keywords:         nil,
		Now:              mustParseTime("2024-06-01T10:00:00Z"),
		ScheduleType:     ptrScheduleType(auto_reply.WebhookTriggerScheduleTypeMonthly),
		ScheduleSettings: settings,
	}
	result := svc.ValidateTrigger(context.Background(), input)
	if !result.Triggered || result.Type != auto_reply.TriggerTypeSchedule {
		t.Errorf("[PRD3-2] should trigger by monthly schedule, got %+v", result)
	}
}

// Case 3-3: 營業時段內／外 → 根據設定觸發或不觸發（真實情境）
func TestAutoReplyService_ValidateTrigger_BusinessHour_Real_PRD3_3(t *testing.T) {
	t.Parallel()
	svc := NewAutoReplyService(AutoReplyServiceParam{})
	bh := &auto_reply.BusinessHourSchedule{
		DaysOfWeek: []time.Weekday{time.Monday, time.Tuesday, time.Wednesday, time.Thursday, time.Friday},
		Periods: []auto_reply.TimePeriod{
			{Start: "09:00", End: "12:00"},
			{Start: "13:00", End: "18:00"},
		},
	}
	settings := &auto_reply.WebhookTriggerScheduleSettings{Schedules: []auto_reply.WebhookTriggerSchedule{bh}}

	// 週一 10:00 → 在 Mon~Fri 09:00~12:00 內，應觸發
	tm := time.Date(2024, 6, 3, 10, 0, 0, 0, time.Local) // 2024-06-03 是週一
	input := auto_reply.ValidateTriggerInput{
		Channel:          auto_reply.ChannelLINE,
		EventType:        auto_reply.AutoReplyEventTypeMessage,
		Message:          "",
		Keywords:         nil,
		Now:              tm,
		ScheduleType:     ptrScheduleType(auto_reply.WebhookTriggerScheduleTypeBusinessHour),
		ScheduleSettings: settings,
	}
	result := svc.ValidateTrigger(context.Background(), input)
	if !result.Triggered {
		t.Errorf("[PRD3-3-real] should trigger in business hour (Mon 10:00), got %+v", result)
	}

	// 週日 10:00 → 不在 Mon~Fri，應不觸發
	sunday := time.Date(2024, 6, 2, 10, 0, 0, 0, time.Local) // 2024-06-02 是週日
	input.Now = sunday
	result = svc.ValidateTrigger(context.Background(), input)
	if result.Triggered {
		t.Errorf("[PRD3-3-real] should NOT trigger on Sunday, got %+v", result)
	}

	// 週一 08:00 → 不在時段內，應不觸發
	input.Now = time.Date(2024, 6, 3, 8, 0, 0, 0, time.Local)
	result = svc.ValidateTrigger(context.Background(), input)
	if result.Triggered {
		t.Errorf("[PRD3-3-real] should NOT trigger before business hour, got %+v", result)
	}

	// 週一 13:30 → 在 13:00~18:00 內，應觸發
	input.Now = time.Date(2024, 6, 3, 13, 30, 0, 0, time.Local)
	result = svc.ValidateTrigger(context.Background(), input)
	if !result.Triggered {
		t.Errorf("[PRD3-3-real] should trigger in business hour (Mon 13:30), got %+v", result)
	}
}

// PRD3-3: 跨夜時段與時區測試
func TestAutoReplyService_ValidateTrigger_BusinessHour_Overnight_TimeZone_PRD3_3(t *testing.T) {
	t.Parallel()
	svc := NewAutoReplyService(AutoReplyServiceParam{})
	bh := &auto_reply.BusinessHourSchedule{
		DaysOfWeek: []time.Weekday{time.Monday, time.Tuesday, time.Wednesday, time.Thursday, time.Friday, time.Saturday, time.Sunday},
		Periods: []auto_reply.TimePeriod{
			{Start: "22:00", End: "06:00"}, // 跨夜
		},
	}
	settings := &auto_reply.WebhookTriggerScheduleSettings{Schedules: []auto_reply.WebhookTriggerSchedule{bh}}
	loc, _ := time.LoadLocation("Asia/Tokyo")

	// 週五 23:00（在跨夜時段內）
	tm := time.Date(2024, 6, 7, 23, 0, 0, 0, loc) // 2024-06-07 是週五
	input := auto_reply.ValidateTriggerInput{
		Channel:          auto_reply.ChannelLINE,
		EventType:        auto_reply.AutoReplyEventTypeMessage,
		Message:          "",
		Keywords:         nil,
		Now:              tm,
		Location:         loc,
		ScheduleType:     ptrScheduleType(auto_reply.WebhookTriggerScheduleTypeBusinessHour),
		ScheduleSettings: settings,
	}
	result := svc.ValidateTrigger(context.Background(), input)
	if !result.Triggered {
		t.Errorf("[PRD3-3-overnight] should trigger in overnight business hour (Fri 23:00 JST), got %+v", result)
	}

	// 週六 05:00（在跨夜時段內）
	input.Now = time.Date(2024, 6, 8, 5, 0, 0, 0, loc)
	result = svc.ValidateTrigger(context.Background(), input)
	if !result.Triggered {
		t.Errorf("[PRD3-3-overnight] should trigger in overnight business hour (Sat 05:00 JST), got %+v", result)
	}

	// 週六 07:00（不在跨夜時段內）
	input.Now = time.Date(2024, 6, 8, 7, 0, 0, 0, loc)
	result = svc.ValidateTrigger(context.Background(), input)
	if result.Triggered {
		t.Errorf("[PRD3-3-overnight] should NOT trigger after overnight business hour (Sat 07:00 JST), got %+v", result)
	}

	// 驗證時區 Asia/Tokyo
	utc := time.Date(2024, 6, 7, 14, 0, 0, 0, time.UTC) // 23:00 JST = 14:00 UTC
	input.Now = utc
	input.Location = loc
	result = svc.ValidateTrigger(context.Background(), input)
	if !result.Triggered {
		t.Errorf("[PRD3-3-timezone] should trigger in business hour with Asia/Tokyo timezone, got %+v", result)
	}
}

// PRD Story 4: 優先權邏輯（關鍵字優先）
// Case 4-1: 同時符合關鍵字與排程 → 只觸發關鍵字
func TestAutoReplyService_ValidateTrigger_KeywordPriority_PRD4_1(t *testing.T) {
	t.Parallel()
	svc := NewAutoReplyService(AutoReplyServiceParam{})
	dd := &auto_reply.DailySchedule{StartTime: "09:00", EndTime: "18:00"}
	settings := &auto_reply.WebhookTriggerScheduleSettings{Schedules: []auto_reply.WebhookTriggerSchedule{dd}}
	input := auto_reply.ValidateTriggerInput{
		Channel:          auto_reply.ChannelLINE,
		EventType:        auto_reply.AutoReplyEventTypeMessage,
		Message:          "hello",
		Keywords:         []string{"hello"},
		Now:              mustParseTime("2024-06-01T10:00:00Z"),
		ScheduleType:     ptrScheduleType(auto_reply.WebhookTriggerScheduleTypeDaily),
		ScheduleSettings: settings,
	}
	result := svc.ValidateTrigger(context.Background(), input)
	if !result.Triggered || result.Type != auto_reply.TriggerTypeKeyword {
		t.Errorf("[PRD4-1] keyword should have priority, got %+v", result)
	}
}

// Case 4-2: 僅符合排程 → 觸發排程
func TestAutoReplyService_ValidateTrigger_ScheduleOnly_PRD4_2(t *testing.T) {
	t.Parallel()
	svc := NewAutoReplyService(AutoReplyServiceParam{})
	dd := &auto_reply.DailySchedule{StartTime: "09:00", EndTime: "18:00"}
	settings := &auto_reply.WebhookTriggerScheduleSettings{Schedules: []auto_reply.WebhookTriggerSchedule{dd}}
	input := auto_reply.ValidateTriggerInput{
		Channel:          auto_reply.ChannelLINE,
		EventType:        auto_reply.AutoReplyEventTypeMessage,
		Message:          "",
		Keywords:         nil,
		Now:              mustParseTime("2024-06-01T10:00:00Z"),
		ScheduleType:     ptrScheduleType(auto_reply.WebhookTriggerScheduleTypeDaily),
		ScheduleSettings: settings,
	}
	result := svc.ValidateTrigger(context.Background(), input)
	if !result.Triggered || result.Type != auto_reply.TriggerTypeSchedule {
		t.Errorf("[PRD4-2] should trigger by schedule only, got %+v", result)
	}
}

// Case 4-3: 關鍵字在排程外 → 還是觸發關鍵字
func TestAutoReplyService_ValidateTrigger_KeywordOutOfSchedule_PRD4_3(t *testing.T) {
	t.Parallel()
	svc := NewAutoReplyService(AutoReplyServiceParam{})
	// 時間不在排程內，但有關鍵字
	dd := &auto_reply.DailySchedule{StartTime: "09:00", EndTime: "18:00"}
	settings := &auto_reply.WebhookTriggerScheduleSettings{Schedules: []auto_reply.WebhookTriggerSchedule{dd}}
	input := auto_reply.ValidateTriggerInput{
		Channel:          auto_reply.ChannelLINE,
		EventType:        auto_reply.AutoReplyEventTypeMessage,
		Message:          "hello",
		Keywords:         []string{"hello"},
		Now:              mustParseTime("2024-06-01T20:00:00Z"), // 不在排程內
		ScheduleType:     ptrScheduleType(auto_reply.WebhookTriggerScheduleTypeDaily),
		ScheduleSettings: settings,
	}
	result := svc.ValidateTrigger(context.Background(), input)
	if !result.Triggered || result.Type != auto_reply.TriggerTypeKeyword {
		t.Errorf("[PRD4-3] keyword should trigger even out of schedule, got %+v", result)
	}
}

// PRD Story 5: 訊息內容處理
// Case 5-1: 有設定關鍵字且精準匹配 → 關鍵字回覆
func TestAutoReplyService_ValidateTrigger_KeywordContent_PRD5_1(t *testing.T) {
	t.Parallel()
	svc := NewAutoReplyService(AutoReplyServiceParam{})
	input := auto_reply.ValidateTriggerInput{
		Channel:   auto_reply.ChannelLINE,
		EventType: auto_reply.AutoReplyEventTypeMessage,
		Message:   "hello",
		Keywords:  []string{"hello"},
		Now:       time.Now(),
	}
	result := svc.ValidateTrigger(context.Background(), input)
	if !result.Triggered || result.Type != auto_reply.TriggerTypeKeyword {
		t.Errorf("[PRD5-1] should trigger by keyword content, got %+v", result)
	}
}

// Case 5-2: 無任何關鍵字匹配 → 無關鍵字回覆
func TestAutoReplyService_ValidateTrigger_NoKeyword_PRD5_2(t *testing.T) {
	t.Parallel()
	svc := NewAutoReplyService(AutoReplyServiceParam{})
	input := auto_reply.ValidateTriggerInput{
		Channel:   auto_reply.ChannelLINE,
		EventType: auto_reply.AutoReplyEventTypeMessage,
		Message:   "bye",
		Keywords:  []string{"hello"},
		Now:       time.Now(),
	}
	result := svc.ValidateTrigger(context.Background(), input)
	if result.Triggered {
		t.Errorf("[PRD5-2] should not trigger if no keyword matches, got %+v", result)
	}
}

// Case 5-3: 時間排程內 → 一般回覆
func TestAutoReplyService_ValidateTrigger_ScheduleContent_PRD5_3(t *testing.T) {
	t.Parallel()
	svc := NewAutoReplyService(AutoReplyServiceParam{})
	dd := &auto_reply.DailySchedule{StartTime: "09:00", EndTime: "18:00"}
	settings := &auto_reply.WebhookTriggerScheduleSettings{Schedules: []auto_reply.WebhookTriggerSchedule{dd}}
	input := auto_reply.ValidateTriggerInput{
		Channel:          auto_reply.ChannelLINE,
		EventType:        auto_reply.AutoReplyEventTypeMessage,
		Message:          "",
		Keywords:         nil,
		Now:              mustParseTime("2024-06-01T10:00:00Z"),
		ScheduleType:     ptrScheduleType(auto_reply.WebhookTriggerScheduleTypeDaily),
		ScheduleSettings: settings,
	}
	result := svc.ValidateTrigger(context.Background(), input)
	if !result.Triggered || result.Type != auto_reply.TriggerTypeSchedule {
		t.Errorf("[PRD5-3] should trigger by schedule content, got %+v", result)
	}
}

// PRD: [B-P1-18-Test7]
// Story 6: IG Story 關鍵字邏輯 - 關鍵字相符但不是回覆指定 IG Story，不應觸發
func TestAutoReplyService_ValidateTrigger_IGStoryKeyword_NotStoryReply_PRD_B_P1_18_Test7(t *testing.T) {
	t.Parallel()
	svc := NewAutoReplyService(AutoReplyServiceParam{})
	input := auto_reply.ValidateTriggerInput{
		Channel:         auto_reply.ChannelInstagram,
		EventType:       auto_reply.AutoReplyEventTypeMessage,
		Message:         "hello",
		IGStoryIDs:      []string{"story999"}, // 不在指定 story 內
		IGStoryTargetID: "story123",           // 設定的 story id
		IGStoryKeywords: []string{"hello"},
		Now:             time.Now(),
	}
	result := svc.ValidateTrigger(context.Background(), input)
	if result.Triggered {
		t.Errorf("[B-P1-18-Test7] should NOT trigger when not replying to the selected story, got %+v", result)
	}
}

// PRD: [B-P1-18-Test8a], [IG-Story-Keyword-Test1], [IG-Story-Keyword-Test2], [IG-Story-Keyword-Test3]
// Story 6: IG Story 關鍵字邏輯
func TestAutoReplyService_ValidateTrigger_IGStoryKeyword(t *testing.T) {
	svc := NewAutoReplyService(AutoReplyServiceParam{})
	// 正確 story id 且關鍵字相符
	input := auto_reply.ValidateTriggerInput{
		Channel:         auto_reply.ChannelInstagram,
		EventType:       auto_reply.AutoReplyEventTypeMessage,
		Message:         "hello",
		IGStoryIDs:      []string{"story123"},
		IGStoryTargetID: "story123",
		IGStoryKeywords: []string{"hello", "hi"},
		Now:             time.Now(),
	}
	result := svc.ValidateTrigger(context.Background(), input)
	if !result.Triggered || result.Type != auto_reply.TriggerTypeIGStoryKeyword {
		t.Errorf("[Story6] should trigger IG Story keyword, got %+v", result)
	}
	// 錯誤 story id
	input.IGStoryIDs = []string{"story999"}
	result = svc.ValidateTrigger(context.Background(), input)
	if result.Triggered {
		t.Errorf("[Story6] should not trigger for wrong story id, got %+v", result)
	}
	// 沒帶 ig_story_id
	input.IGStoryIDs = nil
	result = svc.ValidateTrigger(context.Background(), input)
	if result.Triggered {
		t.Errorf("[Story6] should not trigger if no ig_story_id, got %+v", result)
	}
}

// PRD: [B-P1-18-Test8b], [IG-Story-General-Test1], [IG-Story-General-Test2], [IG-Story-General-Test3]
// Story 7: IG Story 一般時間邏輯
func TestAutoReplyService_ValidateTrigger_IGStorySchedule(t *testing.T) {
	svc := NewAutoReplyService(AutoReplyServiceParam{})
	dd := &auto_reply.DailySchedule{StartTime: "09:00", EndTime: "18:00"}
	settings := &auto_reply.WebhookTriggerScheduleSettings{Schedules: []auto_reply.WebhookTriggerSchedule{dd}}
	input := auto_reply.ValidateTriggerInput{
		Channel:                 auto_reply.ChannelInstagram,
		EventType:               auto_reply.AutoReplyEventTypeMessage,
		Message:                 "",
		IGStoryIDs:              []string{"story123"},
		IGStoryTargetID:         "story123",
		IGStoryScheduleType:     ptrScheduleType(auto_reply.WebhookTriggerScheduleTypeDaily),
		IGStoryScheduleSettings: settings,
		Now:                     mustParseTime("2024-06-01T10:00:00Z"),
	}
	result := svc.ValidateTrigger(context.Background(), input)
	if !result.Triggered || result.Type != auto_reply.TriggerTypeIGStorySchedule {
		t.Errorf("[Story7] should trigger IG Story schedule, got %+v", result)
	}
	// 時間外
	input.Now = mustParseTime("2024-06-01T20:00:00Z")
	result = svc.ValidateTrigger(context.Background(), input)
	if result.Triggered {
		t.Errorf("[Story7] should not trigger out of schedule, got %+v", result)
	}
	// 錯誤 story id
	input.IGStoryIDs = []string{"story999"}
	input.Now = mustParseTime("2024-06-01T10:00:00Z")
	result = svc.ValidateTrigger(context.Background(), input)
	if result.Triggered {
		t.Errorf("[Story7] should not trigger for wrong story id, got %+v", result)
	}
}

// PRD: [B-P1-18-Test9], [IG-Story-Priority-Test1], [IG-Story-Priority-Test2]
// Story 8: IG Story 優先級
func TestAutoReplyService_ValidateTrigger_IGStoryPriority(t *testing.T) {
	svc := NewAutoReplyService(AutoReplyServiceParam{})
	// 同時符合 IG Story 關鍵字與一般關鍵字
	input := auto_reply.ValidateTriggerInput{
		Channel:         auto_reply.ChannelInstagram,
		EventType:       auto_reply.AutoReplyEventTypeMessage,
		Message:         "hello",
		Keywords:        []string{"hello"},
		IGStoryIDs:      []string{"story123"},
		IGStoryTargetID: "story123",
		IGStoryKeywords: []string{"hello"},
		Now:             time.Now(),
	}
	result := svc.ValidateTrigger(context.Background(), input)
	if !result.Triggered || result.Type != auto_reply.TriggerTypeIGStoryKeyword {
		t.Errorf("[Story8] IG Story keyword should have priority, got %+v", result)
	}
	// 同時符合 IG Story 時間與一般時間
	dd := &auto_reply.DailySchedule{StartTime: "09:00", EndTime: "18:00"}
	settings := &auto_reply.WebhookTriggerScheduleSettings{Schedules: []auto_reply.WebhookTriggerSchedule{dd}}
	input = auto_reply.ValidateTriggerInput{
		Channel:                 auto_reply.ChannelInstagram,
		EventType:               auto_reply.AutoReplyEventTypeMessage,
		Message:                 "",
		ScheduleType:            ptrScheduleType(auto_reply.WebhookTriggerScheduleTypeDaily),
		ScheduleSettings:        settings,
		IGStoryIDs:              []string{"story123"},
		IGStoryTargetID:         "story123",
		IGStoryScheduleType:     ptrScheduleType(auto_reply.WebhookTriggerScheduleTypeDaily),
		IGStoryScheduleSettings: settings,
		Now:                     mustParseTime("2024-06-01T10:00:00Z"),
	}
	result = svc.ValidateTrigger(context.Background(), input)
	if !result.Triggered || result.Type != auto_reply.TriggerTypeIGStorySchedule {
		t.Errorf("[Story8] IG Story schedule should have priority, got %+v", result)
	}
}

// PRD: [IG-Story-Multiple-Keywords-Test1], [IG-Story-Multiple-Keywords-Test2]
// Story 9: IG Story 多關鍵字支援
func TestAutoReplyService_ValidateTrigger_IGStoryMultiKeyword(t *testing.T) {
	svc := NewAutoReplyService(AutoReplyServiceParam{})
	input := auto_reply.ValidateTriggerInput{
		Channel:         auto_reply.ChannelInstagram,
		EventType:       auto_reply.AutoReplyEventTypeMessage,
		Message:         "hi",
		IGStoryIDs:      []string{"story123"},
		IGStoryTargetID: "story123",
		IGStoryKeywords: []string{"hello", "hi", "test"},
		Now:             time.Now(),
	}
	result := svc.ValidateTrigger(context.Background(), input)
	if !result.Triggered || result.Type != auto_reply.TriggerTypeIGStoryKeyword || result.MatchedKeyword != "hi" {
		t.Errorf("[Story9] should trigger by any IG Story keyword, got %+v", result)
	}
	// 關鍵字相符但錯誤 story id
	input.IGStoryIDs = []string{"story999"}
	result = svc.ValidateTrigger(context.Background(), input)
	if result.Triggered {
		t.Errorf("[Story9] should not trigger for wrong story id, got %+v", result)
	}
}

// PRD: [Complete-Priority-Test1], [Complete-Priority-Test2], [Complete-Priority-Test3], [Complete-Priority-Test4]
// Story 10: 完整優先權系統
func TestAutoReplyService_ValidateTrigger_IGStoryPrioritySystem(t *testing.T) {
	svc := NewAutoReplyService(AutoReplyServiceParam{})
	// 1. IG Story 關鍵字 > IG Story 時間 > 一般關鍵字 > 一般時間
	dd := &auto_reply.DailySchedule{StartTime: "09:00", EndTime: "18:00"}
	settings := &auto_reply.WebhookTriggerScheduleSettings{Schedules: []auto_reply.WebhookTriggerSchedule{dd}}
	input := auto_reply.ValidateTriggerInput{
		Channel:                 auto_reply.ChannelInstagram,
		EventType:               auto_reply.AutoReplyEventTypeMessage,
		Message:                 "hello",
		Keywords:                []string{"hello"},
		ScheduleType:            ptrScheduleType(auto_reply.WebhookTriggerScheduleTypeDaily),
		ScheduleSettings:        settings,
		IGStoryIDs:              []string{"story123"},
		IGStoryTargetID:         "story123",
		IGStoryKeywords:         []string{"hello"},
		IGStoryScheduleType:     ptrScheduleType(auto_reply.WebhookTriggerScheduleTypeDaily),
		IGStoryScheduleSettings: settings,
		Now:                     mustParseTime("2024-06-01T10:00:00Z"),
	}
	result := svc.ValidateTrigger(context.Background(), input)
	if !result.Triggered || result.Type != auto_reply.TriggerTypeIGStoryKeyword {
		t.Errorf("[Story10] IG Story keyword should have highest priority, got %+v", result)
	}
	// 2. IG Story 時間 > 一般關鍵字 > 一般時間
	input.Message = ""
	input.IGStoryKeywords = nil
	result = svc.ValidateTrigger(context.Background(), input)
	if !result.Triggered || result.Type != auto_reply.TriggerTypeIGStorySchedule {
		t.Errorf("[Story10] IG Story schedule should have 2nd priority, got %+v", result)
	}
	// 3. 一般關鍵字 > 一般時間
	input.IGStoryIDs = nil
	input.IGStoryTargetID = ""
	input.IGStoryScheduleType = nil
	input.IGStoryScheduleSettings = nil
	input.Keywords = []string{"hello"}
	input.Message = "hello"
	result = svc.ValidateTrigger(context.Background(), input)
	if !result.Triggered || result.Type != auto_reply.TriggerTypeKeyword {
		t.Errorf("[Story10] general keyword should have 3rd priority, got %+v", result)
	}
	// 4. 一般時間
	input.Keywords = nil
	input.Message = ""
	result = svc.ValidateTrigger(context.Background(), input)
	if !result.Triggered || result.Type != auto_reply.TriggerTypeSchedule {
		t.Errorf("[Story10] general schedule should have 4th priority, got %+v", result)
	}
}

// PRD: [IG-Story-Exclusion-Test1], [IG-Story-Exclusion-Test2], [IG-Story-Exclusion-Test3]
// Story 11: IG Story 排他邏輯
func TestAutoReplyService_ValidateTrigger_IGStoryExclusive(t *testing.T) {
	svc := NewAutoReplyService(AutoReplyServiceParam{})
	// 僅有 IG Story 關鍵字設定，對普通訊息不觸發
	input := auto_reply.ValidateTriggerInput{
		Channel:         auto_reply.ChannelInstagram,
		EventType:       auto_reply.AutoReplyEventTypeMessage,
		Message:         "hello",
		IGStoryIDs:      nil,
		IGStoryTargetID: "story123",
		IGStoryKeywords: []string{"hello"},
		Now:             time.Now(),
	}
	result := svc.ValidateTrigger(context.Background(), input)
	if result.Triggered {
		t.Errorf("[Story11] IG Story keyword should not trigger for normal message, got %+v", result)
	}
	// 僅有一般關鍵字設定，對普通訊息仍觸發
	input = auto_reply.ValidateTriggerInput{
		Channel:   auto_reply.ChannelInstagram,
		EventType: auto_reply.AutoReplyEventTypeMessage,
		Message:   "hello",
		Keywords:  []string{"hello"},
		Now:       time.Now(),
	}
	result = svc.ValidateTrigger(context.Background(), input)
	if !result.Triggered || result.Type != auto_reply.TriggerTypeKeyword {
		t.Errorf("[Story11] general keyword should trigger for normal message, got %+v", result)
	}
	// 同時有 IG Story 與一般關鍵字設定，普通訊息僅觸發一般設定
	input = auto_reply.ValidateTriggerInput{
		Channel:         auto_reply.ChannelInstagram,
		EventType:       auto_reply.AutoReplyEventTypeMessage,
		Message:         "hello",
		Keywords:        []string{"hello"},
		IGStoryIDs:      nil,
		IGStoryTargetID: "story123",
		IGStoryKeywords: []string{"hello"},
		Now:             time.Now(),
	}
	result = svc.ValidateTrigger(context.Background(), input)
	if !result.Triggered || result.Type != auto_reply.TriggerTypeKeyword {
		t.Errorf("[Story11] general keyword should trigger for normal message, got %+v", result)
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

func ptrScheduleType(t auto_reply.WebhookTriggerScheduleType) *auto_reply.WebhookTriggerScheduleType {
	return &t
}

func auto_replyMemoryRepoMock() *auto_replyMemoryRepositoryAdapter {
	return &auto_replyMemoryRepositoryAdapter{repo: repository.NewAutoReplyMemoryRepository()}
}

type auto_replyMemoryRepositoryAdapter struct {
	repo *repository.AutoReplyMemoryRepository
}

func (a *auto_replyMemoryRepositoryAdapter) Create(ctx context.Context, ar *auto_reply.AutoReply) error {
	return a.repo.Create(ctx, ar)
}
func (a *auto_replyMemoryRepositoryAdapter) Update(ctx context.Context, ar *auto_reply.AutoReply) error {
	return a.repo.Update(ctx, ar)
}
func (a *auto_replyMemoryRepositoryAdapter) Delete(ctx context.Context, id int) error {
	return a.repo.Delete(ctx, id)
}
func (a *auto_replyMemoryRepositoryAdapter) GetByID(ctx context.Context, id int) (*auto_reply.AutoReply, error) {
	return a.repo.GetByID(ctx, id)
}
func (a *auto_replyMemoryRepositoryAdapter) ListByOrganization(ctx context.Context, orgID int) ([]*auto_reply.AutoReply, error) {
	return a.repo.ListByOrganization(ctx, orgID)
}
