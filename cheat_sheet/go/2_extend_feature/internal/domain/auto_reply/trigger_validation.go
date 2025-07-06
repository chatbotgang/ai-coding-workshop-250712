package auto_reply

import (
	"encoding/json"
	"sort"
	"strings"
	"time"

	"github.com/chatbotgang/workshop/internal/domain/organization"
)

// WebhookEvent represents a generic webhook event for trigger validation
type WebhookEvent struct {
	EventType   string               `json:"event_type"`            // "message" (only type we handle for now)
	MessageText *string              `json:"message_text"`          // For keyword matching
	Timestamp   time.Time            `json:"timestamp"`             // For time-based triggers
	ChannelType organization.BotType `json:"channel_type"`          // LINE, FB, IG
	IGStoryID   *string              `json:"ig_story_id,omitempty"` // IG Story ID for story-specific triggers
}

// AutoReplyTriggerSetting represents the merged domain model of AutoReply and WebhookTriggerSetting
// This provides easy access to both trigger configuration and priority information
type AutoReplyTriggerSetting struct {
	// AutoReply fields
	AutoReplyID        int                `json:"auto_reply_id"`
	AutoReplyName      string             `json:"auto_reply_name"`
	AutoReplyStatus    AutoReplyStatus    `json:"auto_reply_status"`
	AutoReplyEventType AutoReplyEventType `json:"auto_reply_event_type"`
	AutoReplyPriority  int                `json:"auto_reply_priority"` // Key field for sorting
	Keywords           []string           `json:"keywords,omitempty"`

	// WebhookTriggerSetting fields
	WebhookTriggerID        int                         `json:"webhook_trigger_id"`
	BotID                   int                         `json:"bot_id"`
	Enable                  bool                        `json:"enable"`
	WebhookTriggerName      string                      `json:"webhook_trigger_name"`
	EventType               WebhookTriggerEventType     `json:"event_type"`
	TriggerCode             *string                     `json:"trigger_code,omitempty"`
	TriggerScheduleType     *WebhookTriggerScheduleType `json:"trigger_schedule_type,omitempty"`
	TriggerScheduleSettings json.RawMessage             `json:"trigger_schedule_settings,omitempty"`
	IGStoryIDs              []string                    `json:"ig_story_ids,omitempty"` // IG Story IDs for story-specific triggers
	Archived                bool                        `json:"archived"`

	// Timestamps
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
}

// IsActive returns true if both AutoReply and WebhookTriggerSetting are active
func (arts *AutoReplyTriggerSetting) IsActive() bool {
	return arts.AutoReplyStatus == AutoReplyStatusActive &&
		arts.Enable &&
		!arts.Archived
}

// IsKeywordTrigger returns true if this is a keyword-based trigger (not IG Story-specific)
func (arts *AutoReplyTriggerSetting) IsKeywordTrigger() bool {
	// Must have keywords and NOT be IG Story-specific
	hasKeywords := len(arts.Keywords) > 0 || (arts.TriggerCode != nil && *arts.TriggerCode != "")
	return hasKeywords && len(arts.IGStoryIDs) == 0
}

// IsGeneralTimeTrigger returns true if this is a general time-based trigger (not IG Story-specific)
func (arts *AutoReplyTriggerSetting) IsGeneralTimeTrigger() bool {
	return arts.EventType == EventTypeTime && arts.TriggerScheduleType != nil && len(arts.IGStoryIDs) == 0
}

// IsIGStoryKeywordTrigger returns true if this is an IG Story-specific keyword trigger
func (arts *AutoReplyTriggerSetting) IsIGStoryKeywordTrigger() bool {
	// Must have keywords AND be IG Story-specific
	hasKeywords := len(arts.Keywords) > 0 || (arts.TriggerCode != nil && *arts.TriggerCode != "")
	return hasKeywords && len(arts.IGStoryIDs) > 0
}

// IsIGStoryGeneralTrigger returns true if this is an IG Story-specific general time trigger
func (arts *AutoReplyTriggerSetting) IsIGStoryGeneralTrigger() bool {
	return arts.EventType == EventTypeTime && arts.TriggerScheduleType != nil && len(arts.IGStoryIDs) > 0
}

// AutoReplyChannelSettingAggregate holds all trigger settings for a specific bot/channel
// and manages the validation logic with business rules
type AutoReplyChannelSettingAggregate struct {
	BotID           int                         `json:"bot_id"`
	TriggerSettings []AutoReplyTriggerSetting   `json:"trigger_settings"` // Updated to use merged model
	BusinessHours   []organization.BusinessHour `json:"business_hours"`
	Timezone        string                      `json:"timezone"` // e.g., "Asia/Taipei"
}

// ValidateTrigger validates a webhook event against configured trigger settings
// Returns the highest priority matching trigger setting, or nil if no match
// Priority order for Feature 2 (4-level priority system):
//  1. IG Story Keyword (Priority 1 - highest)
//  2. IG Story General (Priority 2)
//  3. General Keyword (Priority 3)
//  4. General Time-based (Priority 4 - lowest)
//
// Within each level: sorted by auto-reply's priority field (higher number = higher priority)
// For general time triggers: schedule type priority (monthly -> business hour -> non-business hour -> daily)
//
//	then by auto-reply's priority field within the same schedule type
func (a *AutoReplyChannelSettingAggregate) ValidateTrigger(event WebhookEvent) (*AutoReplyTriggerSetting, error) {
	// Only handle MESSAGE events
	if event.EventType != "message" {
		return nil, nil
	}

	// Priority 1: Check IG Story keyword triggers first (highest priority)
	igStoryKeywordMatch, err := a.validateIGStoryKeywordTrigger(event)
	if err != nil {
		return nil, err
	}
	if igStoryKeywordMatch != nil {
		return igStoryKeywordMatch, nil
	}

	// Priority 2: Check IG Story general triggers
	igStoryGeneralMatch, err := a.validateIGStoryGeneralTrigger(event)
	if err != nil {
		return nil, err
	}
	if igStoryGeneralMatch != nil {
		return igStoryGeneralMatch, nil
	}

	// Priority 3: Check general keyword triggers
	keywordMatch, err := a.validateKeywordTrigger(event)
	if err != nil {
		return nil, err
	}
	if keywordMatch != nil {
		return keywordMatch, nil
	}

	// Priority 4: Check general time triggers (lowest priority)
	generalTimeMatch, err := a.validateGeneralTimeTrigger(event)
	if err != nil {
		return nil, err
	}
	if generalTimeMatch != nil {
		return generalTimeMatch, nil
	}

	// No matching triggers found
	return nil, nil
}

// validateKeywordTrigger checks if the event matches any keyword trigger settings
func (a *AutoReplyChannelSettingAggregate) validateKeywordTrigger(event WebhookEvent) (*AutoReplyTriggerSetting, error) {
	if event.MessageText == nil {
		return nil, nil // No message text to match against
	}

	normalizedMessage := normalizeKeyword(*event.MessageText)
	var matchingSettings []AutoReplyTriggerSetting

	// Find all keyword triggers that match the message
	for _, setting := range a.TriggerSettings {
		if !setting.IsActive() {
			continue
		}

		if setting.IsKeywordTrigger() {
			// Check if any of the keywords match
			for _, keyword := range setting.Keywords {
				normalizedKeyword := normalizeKeyword(keyword)
				if normalizedMessage == normalizedKeyword {
					matchingSettings = append(matchingSettings, setting)
					break // Found a match, no need to check other keywords for this setting
				}
			}

			// Also check TriggerCode for backward compatibility
			if setting.TriggerCode != nil && *setting.TriggerCode != "" {
				normalizedTriggerCode := normalizeKeyword(*setting.TriggerCode)
				if normalizedMessage == normalizedTriggerCode {
					matchingSettings = append(matchingSettings, setting)
				}
			}
		}
	}

	if len(matchingSettings) == 0 {
		return nil, nil // No matching keyword triggers
	}

	// Sort by priority and return the highest priority match
	sortedSettings := a.sortKeywordTriggersByPriority(matchingSettings)
	return &sortedSettings[0], nil
}

// normalizeKeyword normalizes keyword for matching (case insensitive, trim spaces)
func normalizeKeyword(keyword string) string {
	// Trim leading and trailing spaces, then convert to lowercase
	return strings.ToLower(strings.TrimSpace(keyword))
}

// validateIGStoryKeywordTrigger checks if the event matches any IG Story keyword trigger settings
func (a *AutoReplyChannelSettingAggregate) validateIGStoryKeywordTrigger(event WebhookEvent) (*AutoReplyTriggerSetting, error) {
	// Must have both message text and IG Story ID
	if event.MessageText == nil || event.IGStoryID == nil {
		return nil, nil
	}

	normalizedMessage := normalizeKeyword(*event.MessageText)
	var matchingSettings []AutoReplyTriggerSetting

	// Find all IG Story keyword triggers that match the message and story ID
	for _, setting := range a.TriggerSettings {
		if !setting.IsActive() {
			continue
		}

		if setting.IsIGStoryKeywordTrigger() {
			// Check if the story ID matches
			if !a.matchesStoryID(*event.IGStoryID, setting.IGStoryIDs) {
				continue
			}

			// Check if any of the keywords match
			for _, keyword := range setting.Keywords {
				normalizedKeyword := normalizeKeyword(keyword)
				if normalizedMessage == normalizedKeyword {
					matchingSettings = append(matchingSettings, setting)
					break // Found a match, no need to check other keywords for this setting
				}
			}

			// Also check TriggerCode for backward compatibility
			if setting.TriggerCode != nil && *setting.TriggerCode != "" {
				normalizedTriggerCode := normalizeKeyword(*setting.TriggerCode)
				if normalizedMessage == normalizedTriggerCode {
					matchingSettings = append(matchingSettings, setting)
				}
			}
		}
	}

	if len(matchingSettings) == 0 {
		return nil, nil // No matching IG Story keyword triggers
	}

	// Sort by priority and return the highest priority match
	sortedSettings := a.sortKeywordTriggersByPriority(matchingSettings)
	return &sortedSettings[0], nil
}

// matchesStoryID checks if the incoming story ID matches any of the configured story IDs
func (a *AutoReplyChannelSettingAggregate) matchesStoryID(incomingStoryID string, configuredStoryIDs []string) bool {
	for _, configuredID := range configuredStoryIDs {
		if incomingStoryID == configuredID {
			return true
		}
	}
	return false
}

// validateGeneralTimeTrigger checks if the event matches any general time-based trigger settings
func (a *AutoReplyChannelSettingAggregate) validateGeneralTimeTrigger(event WebhookEvent) (*AutoReplyTriggerSetting, error) {
	var matchingSettings []AutoReplyTriggerSetting

	// Find all general time triggers that match the current time
	for _, setting := range a.TriggerSettings {
		if !setting.IsActive() {
			continue
		}

		if setting.IsGeneralTimeTrigger() {
			// Check if the current time matches the trigger schedule
			isMatch, err := a.isWithinSchedule(event.Timestamp, setting.TriggerScheduleType, setting.TriggerScheduleSettings)
			if err != nil {
				return nil, err
			}

			if isMatch {
				matchingSettings = append(matchingSettings, setting)
			}
		}
	}

	if len(matchingSettings) == 0 {
		return nil, nil // No matching general time triggers
	}

	// Sort by priority and return the highest priority match
	sortedSettings := a.sortGeneralTriggersByPriority(matchingSettings)
	return &sortedSettings[0], nil
}

// validateIGStoryGeneralTrigger checks if the event matches any IG Story general time-based trigger settings
func (a *AutoReplyChannelSettingAggregate) validateIGStoryGeneralTrigger(event WebhookEvent) (*AutoReplyTriggerSetting, error) {
	// Must have IG Story ID
	if event.IGStoryID == nil {
		return nil, nil
	}

	var matchingSettings []AutoReplyTriggerSetting

	// Find all IG Story general time triggers that match the current time and story ID
	for _, setting := range a.TriggerSettings {
		if !setting.IsActive() {
			continue
		}

		if setting.IsIGStoryGeneralTrigger() {
			// Check if the story ID matches
			if !a.matchesStoryID(*event.IGStoryID, setting.IGStoryIDs) {
				continue
			}

			// Check if the current time matches the trigger schedule
			isMatch, err := a.isWithinSchedule(event.Timestamp, setting.TriggerScheduleType, setting.TriggerScheduleSettings)
			if err != nil {
				return nil, err
			}

			if isMatch {
				matchingSettings = append(matchingSettings, setting)
			}
		}
	}

	if len(matchingSettings) == 0 {
		return nil, nil // No matching IG Story general time triggers
	}

	// Sort by priority and return the highest priority match
	sortedSettings := a.sortGeneralTriggersByPriority(matchingSettings)
	return &sortedSettings[0], nil
}

// isWithinSchedule checks if the given timestamp is within the trigger schedule
func (a *AutoReplyChannelSettingAggregate) isWithinSchedule(timestamp time.Time, scheduleType *WebhookTriggerScheduleType, scheduleSettings json.RawMessage) (bool, error) {
	if scheduleType == nil {
		return false, nil
	}

	// Convert timestamp to the configured timezone
	loc, err := time.LoadLocation(a.Timezone)
	if err != nil {
		// Fallback to UTC if timezone is invalid
		loc = time.UTC
	}
	localTime := timestamp.In(loc)

	switch *scheduleType {
	case WebhookTriggerScheduleTypeDaily:
		return a.isWithinDailySchedule(localTime, scheduleSettings)
	case WebhookTriggerScheduleTypeMonthly:
		return a.isWithinMonthlySchedule(localTime, scheduleSettings)
	case WebhookTriggerScheduleTypeBusinessHour:
		return a.isWithinBusinessHours(localTime), nil
	case WebhookTriggerScheduleTypeNonBusinessHour:
		return !a.isWithinBusinessHours(localTime), nil
	default:
		return false, nil
	}
}

// isWithinDailySchedule checks if the time is within daily schedule settings
func (a *AutoReplyChannelSettingAggregate) isWithinDailySchedule(localTime time.Time, scheduleSettings json.RawMessage) (bool, error) {
	if len(scheduleSettings) == 0 {
		return false, nil
	}

	var dailySchedules []struct {
		StartTime string `json:"start_time"`
		EndTime   string `json:"end_time"`
	}

	if err := json.Unmarshal(scheduleSettings, &dailySchedules); err != nil {
		return false, err
	}

	currentTime := localTime.Format("15:04")

	for _, schedule := range dailySchedules {
		if a.isTimeInRange(currentTime, schedule.StartTime, schedule.EndTime) {
			return true, nil
		}
	}

	return false, nil
}

// isWithinMonthlySchedule checks if the time is within monthly schedule settings
func (a *AutoReplyChannelSettingAggregate) isWithinMonthlySchedule(localTime time.Time, scheduleSettings json.RawMessage) (bool, error) {
	if len(scheduleSettings) == 0 {
		return false, nil
	}

	var monthlySchedules []struct {
		Day       int    `json:"day"`
		StartTime string `json:"start_time"`
		EndTime   string `json:"end_time"`
	}

	if err := json.Unmarshal(scheduleSettings, &monthlySchedules); err != nil {
		return false, err
	}

	currentDay := localTime.Day()
	currentTime := localTime.Format("15:04")

	for _, schedule := range monthlySchedules {
		if currentDay == schedule.Day && a.isTimeInRange(currentTime, schedule.StartTime, schedule.EndTime) {
			return true, nil
		}
	}

	return false, nil
}

// isWithinBusinessHours checks if the given timestamp is within business hours
func (a *AutoReplyChannelSettingAggregate) isWithinBusinessHours(timestamp time.Time) bool {
	currentWeekday := int(timestamp.Weekday())
	// Convert Go's Sunday=0 to our Monday=1, Sunday=7 format
	if currentWeekday == 0 {
		currentWeekday = 7
	}

	currentTime := timestamp.Format("15:04")

	for _, businessHour := range a.BusinessHours {
		if int(businessHour.Weekday) == currentWeekday {
			startTime := businessHour.StartTime.Format("15:04")
			endTime := businessHour.EndTime.Format("15:04")
			if a.isTimeInRange(currentTime, startTime, endTime) {
				return true
			}
		}
	}

	return false
}

// isTimeInRange checks if currentTime is within the range [startTime, endTime)
// Handles midnight crossing (e.g., 22:00 to 06:00)
func (a *AutoReplyChannelSettingAggregate) isTimeInRange(currentTime, startTime, endTime string) bool {
	// Parse times
	current, err := time.Parse("15:04", currentTime)
	if err != nil {
		return false
	}
	start, err := time.Parse("15:04", startTime)
	if err != nil {
		return false
	}
	end, err := time.Parse("15:04", endTime)
	if err != nil {
		return false
	}

	// Check if range crosses midnight
	if start.After(end) {
		// Midnight crossing: start_time <= current_time OR current_time < end_time
		return !current.Before(start) || current.Before(end)
	} else {
		// Normal range: start_time <= current_time < end_time
		return !current.Before(start) && current.Before(end)
	}
}

// sortKeywordTriggersByPriority sorts keyword trigger settings by auto-reply priority
// Higher priority number = higher priority (e.g., priority 10 > priority 5)
func (a *AutoReplyChannelSettingAggregate) sortKeywordTriggersByPriority(settings []AutoReplyTriggerSetting) []AutoReplyTriggerSetting {
	// Make a copy to avoid modifying the original slice
	sortedSettings := make([]AutoReplyTriggerSetting, len(settings))
	copy(sortedSettings, settings)

	// Sort by AutoReplyPriority in descending order (higher number = higher priority)
	sort.Slice(sortedSettings, func(i, j int) bool {
		return sortedSettings[i].AutoReplyPriority > sortedSettings[j].AutoReplyPriority
	})

	return sortedSettings
}

// sortGeneralTriggersByPriority sorts general time trigger settings by:
// 1. Schedule type priority (monthly -> business hour -> non-business hour -> daily)
// 2. Auto-reply priority within the same schedule type (higher number = higher priority)
func (a *AutoReplyChannelSettingAggregate) sortGeneralTriggersByPriority(settings []AutoReplyTriggerSetting) []AutoReplyTriggerSetting {
	// Make a copy to avoid modifying the original slice
	sortedSettings := make([]AutoReplyTriggerSetting, len(settings))
	copy(sortedSettings, settings)

	// Sort by schedule type priority first, then by auto-reply priority
	sort.Slice(sortedSettings, func(i, j int) bool {
		scheduleTypePriorityI := getScheduleTypePriority(sortedSettings[i].TriggerScheduleType)
		scheduleTypePriorityJ := getScheduleTypePriority(sortedSettings[j].TriggerScheduleType)

		// If schedule type priorities are different, sort by schedule type priority
		if scheduleTypePriorityI != scheduleTypePriorityJ {
			return scheduleTypePriorityI < scheduleTypePriorityJ // Lower number = higher priority for schedule type
		}

		// If schedule type priorities are the same, sort by auto-reply priority
		return sortedSettings[i].AutoReplyPriority > sortedSettings[j].AutoReplyPriority // Higher number = higher priority
	})

	return sortedSettings
}

// getScheduleTypePriority returns the priority order for general time trigger schedule types
// Lower number = higher priority
func getScheduleTypePriority(scheduleType *WebhookTriggerScheduleType) int {
	if scheduleType == nil {
		return 999 // Lowest priority for nil schedule type
	}

	switch *scheduleType {
	case WebhookTriggerScheduleTypeMonthly:
		return 1 // Highest priority
	case WebhookTriggerScheduleTypeBusinessHour:
		return 2
	case WebhookTriggerScheduleTypeNonBusinessHour:
		return 3
	case WebhookTriggerScheduleTypeDaily:
		return 4 // Lowest priority
	default:
		return 999 // Unknown schedule type
	}
}
