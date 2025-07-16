package auto_reply

import (
	"encoding/json"
	"fmt"
	"strings"
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
type BusinessHourSchedule struct{}

func (b *BusinessHourSchedule) GetScheduleType() WebhookTriggerScheduleType {
	return WebhookTriggerScheduleTypeBusinessHour
}

func (b *BusinessHourSchedule) GetScheduleSettings() json.RawMessage {
	return nil
}

// NonBusinessHourSchedule represents a non-business hour trigger schedule.
type NonBusinessHourSchedule struct{}

func (n *NonBusinessHourSchedule) GetScheduleType() WebhookTriggerScheduleType {
	return WebhookTriggerScheduleTypeNonBusinessHour
}

func (n *NonBusinessHourSchedule) GetScheduleSettings() json.RawMessage {
	return nil
}

// normalizeKeyword normalizes a keyword for matching by converting to lowercase and trimming spaces
func normalizeKeyword(keyword string) string {
	return strings.ToLower(strings.TrimSpace(keyword))
}

// matchesKeyword checks if the message content matches any of the provided keywords
// following the PRD requirements: case-insensitive, trim spaces, exact match only
func matchesKeyword(messageContent string, keywords []string) bool {
	if len(keywords) == 0 {
		return false
	}
	
	normalizedMessage := normalizeKeyword(messageContent)
	if normalizedMessage == "" {
		return false
	}
	
	for _, keyword := range keywords {
		normalizedKeyword := normalizeKeyword(keyword)
		if normalizedKeyword != "" && normalizedMessage == normalizedKeyword {
			return true
		}
	}
	
	return false
}

// isKeywordTrigger checks if a WebhookTriggerSetting is a keyword-based trigger
func isKeywordTrigger(setting *WebhookTriggerSetting) bool {
	return setting.EventType == EventTypeMessage || 
		   setting.EventType == EventTypePostback || 
		   setting.EventType == EventTypeBeacon ||
		   setting.EventType == EventTypeMessageEditor ||
		   setting.EventType == EventTypePostbackEditor
}

// isTimeTrigger checks if a WebhookTriggerSetting is a time-based trigger
func isTimeTrigger(setting *WebhookTriggerSetting) bool {
	return setting.EventType == EventTypeTime
}

// extractKeywords extracts keywords from a WebhookTriggerSetting
// For now, we'll use the TriggerCode field as a single keyword
// TODO: This will need to be updated to integrate with AutoReply.Keywords when available
func extractKeywords(setting *WebhookTriggerSetting) []string {
	if setting.TriggerCode != nil && *setting.TriggerCode != "" {
		return []string{*setting.TriggerCode}
	}
	return []string{}
}

// evaluateKeywordTrigger checks if a keyword trigger matches the message content
func evaluateKeywordTrigger(setting *WebhookTriggerSetting, messageContent string) bool {
	if !isKeywordTrigger(setting) {
		return false
	}
	
	keywords := extractKeywords(setting)
	return matchesKeyword(messageContent, keywords)
}

// parseTimeString parses a time string in "HH:MM" format
func parseTimeString(timeStr string) (int, int, error) {
	parts := strings.Split(timeStr, ":")
	if len(parts) != 2 {
		return 0, 0, fmt.Errorf("invalid time format: %s", timeStr)
	}
	
	parsedTime, err := time.Parse("15:04", timeStr)
	if err != nil {
		return 0, 0, fmt.Errorf("invalid time format: %s", timeStr)
	}
	
	return parsedTime.Hour(), parsedTime.Minute(), nil
}

// isInTimeRange checks if eventTime falls within the specified time range
func isInTimeRange(eventTime time.Time, startTime, endTime string) (bool, error) {
	startHour, startMin, err := parseTimeString(startTime)
	if err != nil {
		return false, fmt.Errorf("invalid start time: %w", err)
	}
	
	endHour, endMin, err := parseTimeString(endTime)
	if err != nil {
		return false, fmt.Errorf("invalid end time: %w", err)
	}
	
	eventHour := eventTime.Hour()
	eventMin := eventTime.Minute()
	
	// Handle midnight crossing (e.g., 22:00 to 06:00)
	if startHour > endHour || (startHour == endHour && startMin > endMin) {
		// Range crosses midnight
		return (eventHour > startHour || (eventHour == startHour && eventMin >= startMin)) ||
			   (eventHour < endHour || (eventHour == endHour && eventMin < endMin)), nil
	}
	
	// Normal range (e.g., 09:00 to 17:00)
	return (eventHour > startHour || (eventHour == startHour && eventMin >= startMin)) &&
		   (eventHour < endHour || (eventHour == endHour && eventMin < endMin)), nil
}

// evaluateDailySchedule checks if eventTime matches a daily schedule
func evaluateDailySchedule(scheduleSettings json.RawMessage, eventTime time.Time) (bool, error) {
	if scheduleSettings == nil {
		return false, fmt.Errorf("daily schedule settings cannot be nil")
	}
	
	var schedules []DailySchedule
	if err := json.Unmarshal(scheduleSettings, &schedules); err != nil {
		return false, fmt.Errorf("failed to parse daily schedule: %w", err)
	}
	
	for _, schedule := range schedules {
		matches, err := isInTimeRange(eventTime, schedule.StartTime, schedule.EndTime)
		if err != nil {
			return false, fmt.Errorf("failed to evaluate daily schedule: %w", err)
		}
		if matches {
			return true, nil
		}
	}
	
	return false, nil
}

// evaluateMonthlySchedule checks if eventTime matches a monthly schedule
func evaluateMonthlySchedule(scheduleSettings json.RawMessage, eventTime time.Time) (bool, error) {
	if scheduleSettings == nil {
		return false, fmt.Errorf("monthly schedule settings cannot be nil")
	}
	
	var schedules []MonthlySchedule
	if err := json.Unmarshal(scheduleSettings, &schedules); err != nil {
		return false, fmt.Errorf("failed to parse monthly schedule: %w", err)
	}
	
	currentDay := eventTime.Day()
	
	for _, schedule := range schedules {
		if schedule.Day == currentDay {
			matches, err := isInTimeRange(eventTime, schedule.StartTime, schedule.EndTime)
			if err != nil {
				return false, fmt.Errorf("failed to evaluate monthly schedule: %w", err)
			}
			if matches {
				return true, nil
			}
		}
	}
	
	return false, nil
}

// evaluateBusinessHourSchedule checks if eventTime is within business hours
// TODO: This needs to be integrated with organization.BusinessHour model
func evaluateBusinessHourSchedule(eventTime time.Time, organizationID int) (bool, error) {
	// TODO: Fetch business hours from organization
	// For now, return false as we need to implement the business hour fetching logic
	return false, fmt.Errorf("business hour evaluation not yet implemented")
}

// evaluateNonBusinessHourSchedule checks if eventTime is outside business hours
func evaluateNonBusinessHourSchedule(eventTime time.Time, organizationID int) (bool, error) {
	inBusinessHours, err := evaluateBusinessHourSchedule(eventTime, organizationID)
	if err != nil {
		return false, err
	}
	return !inBusinessHours, nil
}

// evaluateTimeBasedTrigger checks if a time-based trigger matches the event time
func evaluateTimeBasedTrigger(setting *WebhookTriggerSetting, eventTime time.Time, organizationID int) (bool, error) {
	if !isTimeTrigger(setting) {
		return false, nil
	}
	
	if setting.TriggerScheduleType == nil {
		return false, fmt.Errorf("time trigger must have schedule type")
	}
	
	switch *setting.TriggerScheduleType {
	case WebhookTriggerScheduleTypeDaily:
		return evaluateDailySchedule(setting.TriggerScheduleSettings, eventTime)
	case WebhookTriggerScheduleTypeMonthly:
		return evaluateMonthlySchedule(setting.TriggerScheduleSettings, eventTime)
	case WebhookTriggerScheduleTypeBusinessHour:
		return evaluateBusinessHourSchedule(eventTime, organizationID)
	case WebhookTriggerScheduleTypeNonBusinessHour:
		return evaluateNonBusinessHourSchedule(eventTime, organizationID)
	default:
		return false, fmt.Errorf("unsupported schedule type: %s", *setting.TriggerScheduleType)
	}
}

// TriggerSettingsFetcher is an interface for fetching trigger settings
type TriggerSettingsFetcher interface {
	FetchWebhookTriggerSettings(botID int, organizationID int) ([]*WebhookTriggerSetting, error)
}

// DefaultTriggerSettingsFetcher is the default implementation
type DefaultTriggerSettingsFetcher struct{}

func (f *DefaultTriggerSettingsFetcher) FetchWebhookTriggerSettings(botID int, organizationID int) ([]*WebhookTriggerSetting, error) {
	// Mock implementation - in real scenario, this would query the database
	// For now, return empty slice to allow testing of the logic structure
	return []*WebhookTriggerSetting{}, nil
}

// Global fetcher instance - can be overridden for testing
var triggerSettingsFetcher TriggerSettingsFetcher = &DefaultTriggerSettingsFetcher{}

// SetTriggerSettingsFetcher allows overriding the fetcher for testing
func SetTriggerSettingsFetcher(fetcher TriggerSettingsFetcher) {
	triggerSettingsFetcher = fetcher
}

// fetchWebhookTriggerSettings fetches active WebhookTriggerSetting records for a bot
func fetchWebhookTriggerSettings(botID int, organizationID int) ([]*WebhookTriggerSetting, error) {
	return triggerSettingsFetcher.FetchWebhookTriggerSettings(botID, organizationID)
}

// ValidateTrigger validates if a message should trigger an auto-reply based on configured rules.
// It implements the priority system: keyword triggers > time-based triggers.
// Returns the matching WebhookTriggerSetting or nil if no match, with error for configuration issues.
func ValidateTrigger(
	messageContent string,
	eventTime time.Time,
	botID int,
	organizationID int,
) (*WebhookTriggerSetting, error) {
	// Input validation
	if messageContent == "" {
		return nil, fmt.Errorf("messageContent cannot be empty")
	}
	if botID <= 0 {
		return nil, fmt.Errorf("botID must be positive")
	}
	if organizationID <= 0 {
		return nil, fmt.Errorf("organizationID must be positive")
	}
	if eventTime.IsZero() {
		return nil, fmt.Errorf("eventTime cannot be zero")
	}

	// Fetch active trigger settings for the bot/organization
	triggerSettings, err := fetchWebhookTriggerSettings(botID, organizationID)
	if err != nil {
		return nil, fmt.Errorf("failed to fetch trigger settings: %w", err)
	}

	// Filter only active settings
	var activeSettings []*WebhookTriggerSetting
	for _, setting := range triggerSettings {
		if setting.IsActive() {
			activeSettings = append(activeSettings, setting)
		}
	}

	// Priority 1: Check keyword triggers first (highest priority)
	for _, setting := range activeSettings {
		if evaluateKeywordTrigger(setting, messageContent) {
			return setting, nil
		}
	}

	// Priority 2: Check time-based triggers (lower priority)
	for _, setting := range activeSettings {
		matches, err := evaluateTimeBasedTrigger(setting, eventTime, organizationID)
		if err != nil {
			return nil, fmt.Errorf("failed to evaluate time-based trigger: %w", err)
		}
		if matches {
			return setting, nil
		}
	}

	// No matching trigger found
	return nil, nil
}
