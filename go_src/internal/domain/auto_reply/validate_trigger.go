package auto_reply

import (
	"strings"
	"time"
)

// ChannelType 支援多通道
// LINE, Facebook Messenger, Instagram DMs
// 可擴充

type ChannelType string

const (
	ChannelLINE      ChannelType = "line"
	ChannelFacebook  ChannelType = "facebook"
	ChannelInstagram ChannelType = "instagram"
)

// TriggerType 觸發類型

type TriggerType int

const (
	TriggerTypeNone TriggerType = iota
	TriggerTypeKeyword
	TriggerTypeSchedule
	// 新增 IG Story 觸發型別
	TriggerTypeIGStoryKeyword
	TriggerTypeIGStorySchedule
)

// TriggerResult 表示觸發結果

type TriggerResult struct {
	Triggered      bool
	Type           TriggerType
	MatchedKeyword string // 若為關鍵字觸發，記錄匹配的關鍵字
}

// ValidateTriggerInput 驗證觸發的輸入

type ValidateTriggerInput struct {
	Channel          ChannelType
	EventType        AutoReplyEventType // 僅處理 MESSAGE 事件
	Message          string
	Keywords         []string // 多關鍵字
	Now              time.Time
	Location         *time.Location // 新增：時區
	ScheduleType     *WebhookTriggerScheduleType
	ScheduleSettings *WebhookTriggerScheduleSettings
	// IG Story 相關
	IGStoryIDs              []string // 支援多個 IG Story ID
	IGStoryTargetID         string   // 觸發規則指定的 story id
	IGStoryKeywords         []string // IG Story 關鍵字
	IGStoryScheduleType     *WebhookTriggerScheduleType
	IGStoryScheduleSettings *WebhookTriggerScheduleSettings
}

// validateTrigger 決定是否觸發自動回覆，回傳觸發結果
func ValidateTrigger(input ValidateTriggerInput) TriggerResult {
	// 僅處理 MESSAGE 事件
	if input.EventType != AutoReplyEventTypeMessage {
		return TriggerResult{Triggered: false, Type: TriggerTypeNone}
	}

	// 1. IG Story 關鍵字（最高）
	if len(input.IGStoryIDs) > 0 && input.IGStoryTargetID != "" && contains(input.IGStoryIDs, input.IGStoryTargetID) && len(input.IGStoryKeywords) > 0 {
		msgNorm := normalizeKeyword(input.Message)
		for _, kw := range input.IGStoryKeywords {
			if msgNorm == normalizeKeyword(kw) {
				return TriggerResult{Triggered: true, Type: TriggerTypeIGStoryKeyword, MatchedKeyword: kw}
			}
		}
	}

	// 2. IG Story 一般時間
	if len(input.IGStoryIDs) > 0 && input.IGStoryTargetID != "" && contains(input.IGStoryIDs, input.IGStoryTargetID) && input.IGStoryScheduleType != nil && input.IGStoryScheduleSettings != nil {
		if isInSchedule(input.Now, input.Location, *input.IGStoryScheduleType, input.IGStoryScheduleSettings) {
			return TriggerResult{Triggered: true, Type: TriggerTypeIGStorySchedule}
		}
	}

	// 3. 一般關鍵字
	if len(input.Keywords) > 0 {
		msgNorm := normalizeKeyword(input.Message)
		for _, kw := range input.Keywords {
			if msgNorm == normalizeKeyword(kw) {
				return TriggerResult{Triggered: true, Type: TriggerTypeKeyword, MatchedKeyword: kw}
			}
		}
	}

	// 4. 一般時間排程
	if input.ScheduleType != nil && input.ScheduleSettings != nil {
		if isInSchedule(input.Now, input.Location, *input.ScheduleType, input.ScheduleSettings) {
			return TriggerResult{Triggered: true, Type: TriggerTypeSchedule}
		}
	}

	return TriggerResult{Triggered: false, Type: TriggerTypeNone}
}

// normalizeKeyword 正規化：小寫、去除前後空白
func normalizeKeyword(s string) string {
	return strings.ToLower(strings.TrimSpace(s))
}

// isInSchedule 判斷當前時間是否在排程內
func isInSchedule(now time.Time, loc *time.Location, scheduleType WebhookTriggerScheduleType, settings *WebhookTriggerScheduleSettings) bool {
	if loc == nil {
		loc = time.Local
	}
	now = now.In(loc)
	for _, sch := range settings.Schedules {
		switch scheduleType {
		case WebhookTriggerScheduleTypeDaily:
			if daily, ok := sch.(*DailySchedule); ok {
				nowStr := now.Format("15:04")
				if isNowInTimeRangeStr(nowStr, daily.StartTime, daily.EndTime) {
					return true
				}
			}
		case WebhookTriggerScheduleTypeMonthly:
			if monthly, ok := sch.(*MonthlySchedule); ok {
				nowStr := now.Format("15:04")
				if now.Day() == monthly.Day && isNowInTimeRangeStr(nowStr, monthly.StartTime, monthly.EndTime) {
					return true
				}
			}
		case WebhookTriggerScheduleTypeBusinessHour:
			if bh, ok := sch.(*BusinessHourSchedule); ok {
				if isNowInBusinessHour(now, bh) {
					return true
				}
			}
		case WebhookTriggerScheduleTypeNonBusinessHour:
			if bh, ok := sch.(*BusinessHourSchedule); ok {
				if !isNowInBusinessHour(now, bh) {
					return true
				}
			}
		case WebhookTriggerScheduleTypeDateRange:
			if dr, ok := sch.(*DateRangeSchedule); ok {
				start, err1 := time.Parse("2006-01-02", dr.StartDate)
				end, err2 := time.Parse("2006-01-02", dr.EndDate)
				if err1 == nil && err2 == nil && now.After(start) && now.Before(end) {
					return true
				}
			}
		}
	}
	return false
}

// isNowInBusinessHour 判斷 now 是否在營業時段
func isNowInBusinessHour(now time.Time, bh *BusinessHourSchedule) bool {
	weekday := now.Weekday()
	inDay := false
	for _, d := range bh.DaysOfWeek {
		if d == weekday {
			inDay = true
			break
		}
	}
	if !inDay {
		return false
	}
	nowStr := now.Format("15:04")
	for _, p := range bh.Periods {
		if isNowInTimeRangeStr(nowStr, p.Start, p.End) {
			return true
		}
	}
	return false
}

// isNowInTimeRangeStr 判斷 nowStr 是否在 start-end 時間區間內（格式 HH:mm），支援跨夜
func isNowInTimeRangeStr(now, start, end string) bool {
	layout := "15:04"
	nowT, err1 := time.Parse(layout, now)
	startT, err2 := time.Parse(layout, start)
	endT, err3 := time.Parse(layout, end)
	if err1 != nil || err2 != nil || err3 != nil {
		return false
	}
	if startT.Before(endT) || startT.Equal(endT) {
		return !nowT.Before(startT) && !nowT.After(endT)
	}
	// 跨夜：22:00~06:00
	return !nowT.Before(startT) || !nowT.After(endT)
}

// contains 判斷 slice 中是否有指定值
func contains(ids []string, target string) bool {
	for _, id := range ids {
		if id == target {
			return true
		}
	}
	return false
}
