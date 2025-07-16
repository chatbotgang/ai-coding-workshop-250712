package auto_reply

import (
	"strings"
	"time"
)

// Default timezone for auto-reply evaluation (follows legacy system default)
const DefaultTimezone = "Asia/Taipei"

// AutoReply represents an omnichannel rule that associates several WebhookTriggerSetting instances.
// It defines the high-level auto-reply configuration for an organization.
type AutoReply struct {
	ID                      int                             `json:"id"`
	OrganizationID          int                             `json:"organization_id"`
	Name                    string                          `json:"name"`
	Status                  AutoReplyStatus                 `json:"status"`
	EventType               AutoReplyEventType              `json:"event_type"`
	Priority                int                             `json:"priority"`
	Keywords                []string                        `json:"keywords,omitempty"`
	TriggerScheduleType     *WebhookTriggerScheduleType     `json:"trigger_schedule_type,omitempty"`
	TriggerScheduleSettings *WebhookTriggerScheduleSettings `json:"trigger_schedule_settings,omitempty"`
	Timezone                string                          `json:"timezone"`
	IGStorySettings         *IGStorySettings                `json:"ig_story_settings,omitempty"`
	CreatedAt               time.Time                       `json:"created_at"`
	UpdatedAt               time.Time                       `json:"updated_at"`
}

// IGStorySettings represents Instagram Story-specific configuration for auto-reply rules.
type IGStorySettings struct {
	StoryIDs []string `json:"story_ids"`
}

// GetTimezone returns the configured timezone or default if not set
func (ar *AutoReply) GetTimezone() string {
	if ar.Timezone == "" {
		return DefaultTimezone
	}
	return ar.Timezone
}

// IsIGStoryRule returns true if this auto-reply is specific to Instagram Stories
func (ar *AutoReply) IsIGStoryRule() bool {
	return ar.EventType == AutoReplyEventTypeIGStoryKeyword || ar.EventType == AutoReplyEventTypeIGStoryGeneral
}

// HasIGStorySettings returns true if this auto-reply has IG Story settings configured
func (ar *AutoReply) HasIGStorySettings() bool {
	return ar.IGStorySettings != nil && len(ar.IGStorySettings.StoryIDs) > 0
}

// AutoReplyStatus represents the status of an auto-reply rule.
type AutoReplyStatus string

const (
	AutoReplyStatusActive   AutoReplyStatus = "active"
	AutoReplyStatusInactive AutoReplyStatus = "inactive"
	AutoReplyStatusArchived AutoReplyStatus = "archived"
)

// AutoReplyEventType represents the type of event that triggers the auto-reply.
type AutoReplyEventType string

const (
	AutoReplyEventTypeMessage        AutoReplyEventType = "message"
	AutoReplyEventTypePostback       AutoReplyEventType = "postback"
	AutoReplyEventTypeFollow         AutoReplyEventType = "follow"
	AutoReplyEventTypeBeacon         AutoReplyEventType = "beacon"
	AutoReplyEventTypeTime           AutoReplyEventType = "time"
	AutoReplyEventTypeKeyword        AutoReplyEventType = "keyword"
	AutoReplyEventTypeDefault        AutoReplyEventType = "default"
	AutoReplyEventTypeIGStoryKeyword AutoReplyEventType = "ig_story_keyword"
	AutoReplyEventTypeIGStoryGeneral AutoReplyEventType = "ig_story_general"
)

// ValidateTrigger validates whether an incoming webhook event should trigger the given auto-reply.
// It evaluates triggers based on 4-level priority system:
// Priority 1: IG Story Keyword (highest) - matches keyword AND story ID
// Priority 2: IG Story General - matches schedule AND story ID  
// Priority 3: General Keyword - matches keyword (no story requirement)
// Priority 4: General Time-based (lowest) - matches schedule (no story requirement)
// Returns true if the event matches the auto-reply conditions, false otherwise.
func ValidateTrigger(autoReply AutoReply, event WebhookEvent) bool {
	// Only handle active auto-replies
	if autoReply.Status != AutoReplyStatusActive {
		return false
	}

	// Only handle MESSAGE events for now
	if event.Type != "message" || event.Message == nil {
		return false
	}

	// Priority 1: IG Story Keyword triggers (highest priority)
	if autoReply.EventType == AutoReplyEventTypeIGStoryKeyword {
		return matchesIGStoryKeyword(autoReply, event)
	}

	// Priority 2: IG Story General triggers
	if autoReply.EventType == AutoReplyEventTypeIGStoryGeneral {
		return matchesIGStoryGeneral(autoReply, event)
	}

	// Priority 3: General Keyword triggers
	if autoReply.EventType == AutoReplyEventTypeKeyword && len(autoReply.Keywords) > 0 {
		return matchesKeyword(autoReply.Keywords, event.Message.Text)
	}

	// Priority 4: General Time-based triggers (lowest priority)
	if autoReply.EventType == AutoReplyEventTypeTime {
		return matchesTimeSchedule(autoReply, event.Timestamp)
	}

	return false
}

// matchesIGStoryKeyword checks if the event matches IG Story keyword trigger conditions.
// It validates both keyword matching AND story ID matching for IG Story-specific rules.
func matchesIGStoryKeyword(autoReply AutoReply, event WebhookEvent) bool {
	// Must have IG Story settings configured
	if !autoReply.HasIGStorySettings() {
		return false
	}

	// Must have story ID in the event
	if event.IGStoryID == "" {
		return false
	}

	// Check if the event's story ID matches any configured story IDs
	if !matchesStoryID(autoReply.IGStorySettings.StoryIDs, event.IGStoryID) {
		return false
	}

	// Check if the message text matches any configured keywords
	if len(autoReply.Keywords) == 0 {
		return false
	}

	return matchesKeyword(autoReply.Keywords, event.Message.Text)
}

// matchesIGStoryGeneral checks if the event matches IG Story general trigger conditions.
// It validates both schedule matching AND story ID matching for IG Story-specific rules.
func matchesIGStoryGeneral(autoReply AutoReply, event WebhookEvent) bool {
	// Must have IG Story settings configured
	if !autoReply.HasIGStorySettings() {
		return false
	}

	// Must have story ID in the event
	if event.IGStoryID == "" {
		return false
	}

	// Check if the event's story ID matches any configured story IDs
	if !matchesStoryID(autoReply.IGStorySettings.StoryIDs, event.IGStoryID) {
		return false
	}

	// Check if the event timestamp matches the configured schedule
	return matchesTimeSchedule(autoReply, event.Timestamp)
}

// matchesStoryID checks if the event's story ID matches any of the configured story IDs.
func matchesStoryID(configuredStoryIDs []string, eventStoryID string) bool {
	if eventStoryID == "" {
		return false
	}

	for _, storyID := range configuredStoryIDs {
		if storyID == eventStoryID {
			return true
		}
	}

	return false
}

// matchesKeyword checks if the message text matches any of the configured keywords.
// Keywords are matched case-insensitively with leading/trailing spaces trimmed.
// The match must be exact (no partial matches).
func matchesKeyword(keywords []string, messageText string) bool {
	if messageText == "" {
		return false
	}

	// Normalize the incoming message text
	normalizedMessage := strings.ToLower(strings.TrimSpace(messageText))

	// Check against each keyword
	for _, keyword := range keywords {
		if keyword == "" {
			continue
		}
		
		// Normalize the keyword for comparison
		normalizedKeyword := strings.ToLower(strings.TrimSpace(keyword))
		
		// Exact match required
		if normalizedMessage == normalizedKeyword {
			return true
		}
	}

	return false
}

// convertToTargetTimezone converts a timestamp to the target timezone for schedule evaluation
func convertToTargetTimezone(timestamp time.Time, targetTimezone string) (time.Time, error) {
	if targetTimezone == "" {
		targetTimezone = DefaultTimezone
	}
	
	location, err := time.LoadLocation(targetTimezone)
	if err != nil {
		return timestamp, err
	}
	
	return timestamp.In(location), nil
}

// matchesTimeSchedule checks if the event timestamp matches the configured time-based schedule.
// Implements priority order: MONTHLY > BUSINESS_HOUR > NON_BUSINESS_HOUR > DAILY
// All time comparisons are done in the AutoReply's configured timezone.
func matchesTimeSchedule(autoReply AutoReply, timestamp time.Time) bool {
	if autoReply.TriggerScheduleType == nil || autoReply.TriggerScheduleSettings == nil {
		return false
	}

	// Convert timestamp to the auto-reply's configured timezone
	convertedTimestamp, err := convertToTargetTimezone(timestamp, autoReply.GetTimezone())
	if err != nil {
		// If timezone conversion fails, fallback to original timestamp
		convertedTimestamp = timestamp
	}

	scheduleType := *autoReply.TriggerScheduleType
	
	switch scheduleType {
	case WebhookTriggerScheduleTypeMonthly:
		return matchesMonthlySchedule(*autoReply.TriggerScheduleSettings, convertedTimestamp)
	case WebhookTriggerScheduleTypeBusinessHour:
		return matchesBusinessHourSchedule(convertedTimestamp)
	case WebhookTriggerScheduleTypeNonBusinessHour:
		return matchesNonBusinessHourSchedule(convertedTimestamp)
	case WebhookTriggerScheduleTypeDaily:
		return matchesDailySchedule(*autoReply.TriggerScheduleSettings, convertedTimestamp)
	default:
		return false
	}
}

// matchesMonthlySchedule checks if the timestamp matches a monthly schedule
func matchesMonthlySchedule(settings WebhookTriggerScheduleSettings, timestamp time.Time) bool {
	for _, schedule := range settings.Schedules {
		if monthlySchedule, ok := schedule.(*MonthlySchedule); ok {
			if matchesMonthlyRule(monthlySchedule, timestamp) {
				return true
			}
		}
	}
	return false
}

// matchesMonthlyRule checks if timestamp matches a specific monthly schedule rule
func matchesMonthlyRule(schedule *MonthlySchedule, timestamp time.Time) bool {
	// Check if the day matches
	if timestamp.Day() != schedule.Day {
		return false
	}
	
	// Check if the time is within the start and end time
	return isTimeInRange(schedule.StartTime, schedule.EndTime, timestamp)
}

// matchesDailySchedule checks if the timestamp matches a daily schedule
func matchesDailySchedule(settings WebhookTriggerScheduleSettings, timestamp time.Time) bool {
	for _, schedule := range settings.Schedules {
		if dailySchedule, ok := schedule.(*DailySchedule); ok {
			if matchesDailyRule(dailySchedule, timestamp) {
				return true
			}
		}
	}
	return false
}

// matchesDailyRule checks if timestamp matches a specific daily schedule rule
func matchesDailyRule(schedule *DailySchedule, timestamp time.Time) bool {
	return isTimeInRange(schedule.StartTime, schedule.EndTime, timestamp)
}

// matchesBusinessHourSchedule checks if the timestamp is within business hours
// TODO: This needs to be implemented with actual business hour data from organization
func matchesBusinessHourSchedule(timestamp time.Time) bool {
	// TODO: Implement business hour matching logic
	// This would require accessing organization business hour data
	return false
}

// matchesNonBusinessHourSchedule checks if the timestamp is outside business hours
// TODO: This needs to be implemented with actual business hour data from organization
func matchesNonBusinessHourSchedule(timestamp time.Time) bool {
	// TODO: Implement non-business hour matching logic
	// This would require accessing organization business hour data
	return false
}

// isTimeInRange checks if a timestamp's time component is within a time range
// Supports midnight crossing (e.g., 22:00 to 06:00)
func isTimeInRange(startTime, endTime string, timestamp time.Time) bool {
	start, err := time.Parse("15:04", startTime)
	if err != nil {
		return false
	}
	
	end, err := time.Parse("15:04", endTime)
	if err != nil {
		return false
	}
	
	// Get the time component of the timestamp
	currentTime := time.Date(0, 1, 1, timestamp.Hour(), timestamp.Minute(), timestamp.Second(), timestamp.Nanosecond(), timestamp.Location())
	
	// Normalize start and end times to the same date
	startNormalized := time.Date(0, 1, 1, start.Hour(), start.Minute(), 0, 0, timestamp.Location())
	endNormalized := time.Date(0, 1, 1, end.Hour(), end.Minute(), 59, 999999999, timestamp.Location())
	
	// Handle midnight crossing (e.g., 22:00 to 06:00)
	if startNormalized.After(endNormalized) {
		// Time range crosses midnight
		return currentTime.After(startNormalized) || currentTime.Before(endNormalized)
	}
	
	// Normal time range (e.g., 09:00 to 17:00)
	return currentTime.After(startNormalized) && currentTime.Before(endNormalized)
}
