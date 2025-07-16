package auto_reply

import (
	"encoding/json"
	"time"
)

// WebhookTriggerEventType represents the type of WebhookTriggerSetting
type WebhookTriggerEventType int

const (
	EventTypeMessage        WebhookTriggerEventType = 1
	EventTypePostback       WebhookTriggerEventType = 2
	EventTypeFollow         WebhookTriggerEventType = 3
	EventTypeBeacon         WebhookTriggerEventType = 4
	EventTypeTime           WebhookTriggerEventType = 100
	EventTypeMessageEditor  WebhookTriggerEventType = 101
	EventTypePostbackEditor WebhookTriggerEventType = 102
)

// WebhookTriggerSetting represents the channel-level configuration for webhook triggers (Auto-Reply).
type WebhookTriggerSetting struct {
	ID                      int                         `json:"id"`
	AutoReplyID             int                         `json:"auto_reply_id"`
	BotID                   int                         `json:"bot_id"`
	Enable                  bool                        `json:"enable"`
	Name                    string                      `json:"name"` // Will be deprecated
	EventType               WebhookTriggerEventType     `json:"event_type"`
	TriggerCode             *string                     `json:"trigger_code,omitempty"`              // Will be deprecated
	TriggerScheduleType     *WebhookTriggerScheduleType `json:"trigger_schedule_type,omitempty"`     // Will be deprecated
	TriggerScheduleSettings json.RawMessage             `json:"trigger_schedule_settings,omitempty"` // Will be deprecated
	CreatedAt               time.Time                   `json:"created_at"`
	UpdatedAt               time.Time                   `json:"updated_at"`
	Archived                bool                        `json:"archived"`
	Extra                   json.RawMessage             `json:"extra,omitempty"`
}

func (wts *WebhookTriggerSetting) IsActive() bool {
	return wts.Enable && !wts.Archived
}

// WebhookTriggerScheduleType represents the type of trigger schedule for webhook trigger.
type WebhookTriggerScheduleType string

const (
	WebhookTriggerScheduleTypeDaily           WebhookTriggerScheduleType = "daily"
	WebhookTriggerScheduleTypeBusinessHour    WebhookTriggerScheduleType = "business_hour"
	WebhookTriggerScheduleTypeNonBusinessHour WebhookTriggerScheduleType = "non_business_hour"
	WebhookTriggerScheduleTypeMonthly         WebhookTriggerScheduleType = "monthly"
	WebhookTriggerScheduleTypeDateRange       WebhookTriggerScheduleType = "date_range"
)

// WebhookTriggerScheduleSettings represents the settings for the trigger schedule.
type WebhookTriggerScheduleSettings struct {
	Schedules []WebhookTriggerSchedule `json:"schedules"`
}

type WebhookTriggerSchedule interface {
	GetScheduleType() WebhookTriggerScheduleType
	GetScheduleSettings() json.RawMessage
}

// DailySchedule represents a daily trigger schedule.
type DailySchedule struct {
	StartTime string `json:"start_time"`
	EndTime   string `json:"end_time"`
}

func (d *DailySchedule) GetScheduleType() WebhookTriggerScheduleType {
	return WebhookTriggerScheduleTypeDaily
}

func (d *DailySchedule) GetScheduleSettings() json.RawMessage {
	settings, err := json.Marshal(d)
	if err != nil {
		return nil
	}
	return settings
}

// MonthlySchedule represents a monthly trigger schedule.
type MonthlySchedule struct {
	Day       int    `json:"day"`
	StartTime string `json:"start_time"`
	EndTime   string `json:"end_time"`
}

func (m *MonthlySchedule) GetScheduleType() WebhookTriggerScheduleType {
	return WebhookTriggerScheduleTypeMonthly
}

func (m *MonthlySchedule) GetScheduleSettings() json.RawMessage {
	settings, err := json.Marshal(m)
	if err != nil {
		return nil
	}
	return settings
}

// DateRangeSchedule represents a date range trigger schedule.
type DateRangeSchedule struct {
	StartDate string `json:"start_date"`
	EndDate   string `json:"end_date"`
}

func (d *DateRangeSchedule) GetScheduleType() WebhookTriggerScheduleType {
	return WebhookTriggerScheduleTypeDateRange
}

func (d *DateRangeSchedule) GetScheduleSettings() json.RawMessage {
	settings, err := json.Marshal(d)
	if err != nil {
		return nil
	}
	return settings
}

// BusinessHourSchedule represents a business hour trigger schedule.
type BusinessHourSchedule struct {
	DaysOfWeek []time.Weekday `json:"days_of_week"`
	Periods    []TimePeriod   `json:"periods"`
}

type TimePeriod struct {
	Start string `json:"start"` // "09:00"
	End   string `json:"end"`   // "18:00"
}

func (b *BusinessHourSchedule) GetScheduleType() WebhookTriggerScheduleType {
	return WebhookTriggerScheduleTypeBusinessHour
}
func (b *BusinessHourSchedule) GetScheduleSettings() json.RawMessage {
	settings, err := json.Marshal(b)
	if err != nil {
		return nil
	}
	return settings
}

// NonBusinessHourSchedule represents a non-business hour trigger schedule.
type NonBusinessHourSchedule struct{}

func (n *NonBusinessHourSchedule) GetScheduleType() WebhookTriggerScheduleType {
	return WebhookTriggerScheduleTypeNonBusinessHour
}

func (n *NonBusinessHourSchedule) GetScheduleSettings() json.RawMessage {
	return nil
}
