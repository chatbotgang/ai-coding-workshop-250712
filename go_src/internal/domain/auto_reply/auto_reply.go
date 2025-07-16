package auto_reply

import (
	"strings"
	"time"

	"sort"

	"github.com/chatbotgang/workshop/internal/domain/organization"
)

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
	CreatedAt               time.Time                       `json:"created_at"`
	UpdatedAt               time.Time                       `json:"updated_at"`
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
	AutoReplyEventTypeMessage          AutoReplyEventType = "message"
	AutoReplyEventTypePostback         AutoReplyEventType = "postback"
	AutoReplyEventTypeFollow           AutoReplyEventType = "follow"
	AutoReplyEventTypeBeacon           AutoReplyEventType = "beacon"
	AutoReplyEventTypeTime             AutoReplyEventType = "time"
	AutoReplyEventTypeKeyword          AutoReplyEventType = "keyword"
	AutoReplyEventTypeDefault          AutoReplyEventType = "default"
	AutoReplyEventTypeIGStoryKeyword   AutoReplyEventType = "ig_story_keyword"
	AutoReplyEventTypeIGStoryGeneral   AutoReplyEventType = "ig_story_general"
)

// AutoReplyTriggerSetting is a merged domain model for trigger validation logic.
type AutoReplyTriggerSetting struct {
	// From AutoReply
	AutoReplyID             int
	OrganizationID          int
	Name                    string
	Status                  AutoReplyStatus
	EventType               AutoReplyEventType
	Priority                int
	Keywords                []string
	TriggerScheduleType     *WebhookTriggerScheduleType
	TriggerScheduleSettings *WebhookTriggerScheduleSettings
	CreatedAt               time.Time
	UpdatedAt               time.Time

	// From WebhookTriggerSetting
	WebhookTriggerSettingID int
	BotID                   int
	Enable                  bool
	WebhookEventType        WebhookTriggerEventType
	TriggerCode             *string
	WebhookScheduleType     *WebhookTriggerScheduleType
	WebhookScheduleSettings *WebhookTriggerScheduleSettings
	Archived                bool
	Extra                   map[string]interface{}
	
	// IG Story specific fields
	IGStoryIDs              []string // List of IG Story IDs this trigger applies to
}

// IsActive returns true if the trigger is enabled and not archived/inactive.
func (t *AutoReplyTriggerSetting) IsActive() bool {
	return t.Enable && !t.Archived && t.Status == AutoReplyStatusActive
}

// IsKeywordTrigger returns true if this is a keyword-based trigger.
func (t *AutoReplyTriggerSetting) IsKeywordTrigger() bool {
	return t.EventType == AutoReplyEventTypeKeyword
}

// IsGeneralTimeTrigger returns true if this is a general time-based trigger.
func (t *AutoReplyTriggerSetting) IsGeneralTimeTrigger() bool {
	return t.EventType == AutoReplyEventTypeTime
}

// IsIGStoryKeywordTrigger returns true if this is an IG Story keyword-based trigger.
func (t *AutoReplyTriggerSetting) IsIGStoryKeywordTrigger() bool {
	return t.EventType == AutoReplyEventTypeIGStoryKeyword
}

// IsIGStoryGeneralTrigger returns true if this is an IG Story general time-based trigger.
func (t *AutoReplyTriggerSetting) IsIGStoryGeneralTrigger() bool {
	return t.EventType == AutoReplyEventTypeIGStoryGeneral
}

// normalizeKeyword trims spaces and lowercases the keyword for comparison.
func normalizeKeyword(s string) string {
	return strings.ToLower(strings.TrimSpace(s))
}

// IsKeywordMatch checks if the message exactly matches any of the trigger's keywords (case-insensitive, trim spaces).
func (t *AutoReplyTriggerSetting) IsKeywordMatch(message string) bool {
	if len(t.Keywords) == 0 {
		return false
	}
	msgNorm := normalizeKeyword(message)
	for _, kw := range t.Keywords {
		if msgNorm == normalizeKeyword(kw) {
			return true
		}
	}
	return false
}

// IsIGStoryMatch checks if the event's IG Story ID matches any of the trigger's IG Story IDs.
func (t *AutoReplyTriggerSetting) IsIGStoryMatch(igStoryID *string) bool {
	if igStoryID == nil {
		return false
	}
	if len(t.IGStoryIDs) == 0 {
		return false
	}
	for _, storyID := range t.IGStoryIDs {
		if storyID == *igStoryID {
			return true
		}
	}
	return false
}

// AutoReplyChannelSettingAggregate represents all trigger settings and business context for a bot/channel.
type AutoReplyChannelSettingAggregate struct {
	BotID           int
	TriggerSettings []*AutoReplyTriggerSetting
	BusinessHours   []BusinessHour
	Timezone        string // e.g., "Asia/Taipei"
}

// ValidateTrigger validates the incoming event and returns the first matching trigger setting based on priority.
func (agg *AutoReplyChannelSettingAggregate) ValidateTrigger(event WebhookEvent) (*AutoReplyTriggerSetting, error) {
	// 4-stage priority system:
	// Priority 1: IG Story Keyword
	// Priority 2: IG Story General
	// Priority 3: General Keyword
	// Priority 4: General Time-based
	
	// Priority 1: IG Story Keyword triggers
	if event.MessageText != nil {
		igStoryKeywordTriggers := agg.collectIGStoryKeywordTriggers()
		for _, t := range igStoryKeywordTriggers {
			if t.IsIGStoryMatch(event.IGStoryID) && t.IsKeywordMatch(*event.MessageText) {
				return t, nil
			}
		}
	}
	
	// Priority 2: IG Story General triggers  
	igStoryGeneralTriggers := agg.collectIGStoryGeneralTriggers()
	for _, t := range igStoryGeneralTriggers {
		if t.IsIGStoryMatch(event.IGStoryID) && isScheduleMatch(t, event.Timestamp, agg.BusinessHours, agg.Timezone) {
			return t, nil
		}
	}
	
	// Priority 3: General Keyword triggers (only if no IG Story ID)
	if event.MessageText != nil {
		generalKeywordTriggers := agg.collectGeneralKeywordTriggers()
		for _, t := range generalKeywordTriggers {
			if t.IsKeywordMatch(*event.MessageText) {
				return t, nil
			}
			// Check for partial/close match to prevent fallback
			if agg.hasPartialMatch(t, *event.MessageText) {
				return nil, nil
			}
		}
	}
	
	// Priority 4: General Time-based triggers (only if no IG Story ID)
	generalTimeTriggers := agg.collectGeneralTimeTriggers()
	for _, t := range generalTimeTriggers {
		if isScheduleMatch(t, event.Timestamp, agg.BusinessHours, agg.Timezone) {
			return t, nil
		}
	}
	
	// No match found
	return nil, nil
}

// collectIGStoryKeywordTriggers collects all active IG Story keyword triggers sorted by priority.
func (agg *AutoReplyChannelSettingAggregate) collectIGStoryKeywordTriggers() []*AutoReplyTriggerSetting {
	var triggers []*AutoReplyTriggerSetting
	for _, t := range agg.TriggerSettings {
		if t.IsActive() && t.IsIGStoryKeywordTrigger() {
			triggers = append(triggers, t)
		}
	}
	// Sort by Priority (desc)
	sort.Slice(triggers, func(i, j int) bool {
		return triggers[i].Priority > triggers[j].Priority
	})
	return triggers
}

// collectIGStoryGeneralTriggers collects all active IG Story general triggers sorted by priority.
func (agg *AutoReplyChannelSettingAggregate) collectIGStoryGeneralTriggers() []*AutoReplyTriggerSetting {
	var triggers []*AutoReplyTriggerSetting
	for _, t := range agg.TriggerSettings {
		if t.IsActive() && t.IsIGStoryGeneralTrigger() {
			triggers = append(triggers, t)
		}
	}
	// Sort by Priority (desc)
	sort.Slice(triggers, func(i, j int) bool {
		return triggers[i].Priority > triggers[j].Priority
	})
	return triggers
}

// collectGeneralKeywordTriggers collects all active general keyword triggers sorted by priority.
func (agg *AutoReplyChannelSettingAggregate) collectGeneralKeywordTriggers() []*AutoReplyTriggerSetting {
	var triggers []*AutoReplyTriggerSetting
	for _, t := range agg.TriggerSettings {
		if t.IsActive() && t.IsKeywordTrigger() {
			triggers = append(triggers, t)
		}
	}
	// Sort by Priority (desc)
	sort.Slice(triggers, func(i, j int) bool {
		return triggers[i].Priority > triggers[j].Priority
	})
	return triggers
}

// collectGeneralTimeTriggers collects all active general time triggers sorted by priority.
func (agg *AutoReplyChannelSettingAggregate) collectGeneralTimeTriggers() []*AutoReplyTriggerSetting {
	var triggers []*AutoReplyTriggerSetting
	for _, t := range agg.TriggerSettings {
		if t.IsActive() && t.IsGeneralTimeTrigger() {
			triggers = append(triggers, t)
		}
	}
	// Sort by schedule type priority, then by Priority (desc)
	sort.Slice(triggers, func(i, j int) bool {
		priI := scheduleTypePriority(triggers[i].TriggerScheduleType)
		priJ := scheduleTypePriority(triggers[j].TriggerScheduleType)
		if priI != priJ {
			return priI < priJ // lower value = higher priority
		}
		return triggers[i].Priority > triggers[j].Priority
	})
	return triggers
}

// hasPartialMatch checks if the message has a partial/close match with the trigger's keywords.
func (agg *AutoReplyChannelSettingAggregate) hasPartialMatch(t *AutoReplyTriggerSetting, message string) bool {
	if len(t.Keywords) == 0 {
		return false
	}
	msgNorm := normalizeKeyword(message)
	for _, kw := range t.Keywords {
		kwNorm := normalizeKeyword(kw)
		// Check if keyword is at the start or end of the message (close variation)
		// or if it appears as a complete word (partial match)
		if strings.Contains(msgNorm, kwNorm) && msgNorm != kwNorm {
			// Check if it's a meaningful partial match:
			// 1. Keyword at start: "hello world"
			// 2. Keyword at end: "say hello"  
			// 3. Close variation: "helloo"
			if strings.HasPrefix(msgNorm, kwNorm) || strings.HasSuffix(msgNorm, kwNorm) {
				return true
			}
			// Check if keyword appears as a complete word
			words := strings.Fields(msgNorm)
			for _, word := range words {
				if word == kwNorm {
					return true
				}
			}
		}
	}
	return false
}

// scheduleTypePriority returns the priority order for schedule types (lower = higher priority)
func scheduleTypePriority(scheduleType *WebhookTriggerScheduleType) int {
	if scheduleType == nil {
		return 99 // lowest priority if not set
	}
	switch *scheduleType {
	case WebhookTriggerScheduleTypeMonthly:
		return 1
	case WebhookTriggerScheduleTypeDaily:
		return 2
	case WebhookTriggerScheduleTypeBusinessHour:
		return 3
	case WebhookTriggerScheduleTypeNonBusinessHour:
		return 4
	default:
		return 99
	}
}

// isScheduleMatch checks if the event timestamp matches the trigger's schedule.
func isScheduleMatch(t *AutoReplyTriggerSetting, eventTime time.Time, businessHours []BusinessHour, timezone string) bool {
	if t.TriggerScheduleType == nil {
		return false
	}
	
	// Convert event time to bot's timezone
	var eventTimeInBotTZ time.Time
	if timezone != "" {
		if botLocation, err := time.LoadLocation(timezone); err == nil {
			eventTimeInBotTZ = eventTime.In(botLocation)
		} else {
			// Fallback to UTC if timezone is invalid
			eventTimeInBotTZ = eventTime.UTC()
		}
	} else {
		// Default to UTC if no timezone specified
		eventTimeInBotTZ = eventTime.UTC()
	}
	switch *t.TriggerScheduleType {
	case WebhookTriggerScheduleTypeDaily:
		if t.TriggerScheduleSettings == nil {
			return false
		}
		for _, sched := range t.TriggerScheduleSettings.Schedules {
			if ds, ok := sched.(*DailySchedule); ok {
				start, err1 := time.Parse("15:04", ds.StartTime)
				end, err2 := time.Parse("15:04", ds.EndTime)
				if err1 != nil || err2 != nil {
					continue
				}
				et := eventTimeInBotTZ
				startToday := time.Date(et.Year(), et.Month(), et.Day(), start.Hour(), start.Minute(), 0, 0, et.Location())
				endToday := time.Date(et.Year(), et.Month(), et.Day(), end.Hour(), end.Minute(), 0, 0, et.Location())
				if start.Before(end) {
					// Normal time range: start <= time < end
					if !et.Before(startToday) && et.Before(endToday) {
						return true
					}
				} else { // 跨午夜
					// Cross-midnight: time >= start || time <= end
					if !et.Before(startToday) || !et.After(endToday) {
						return true
					}
				}
			}
		}
	case WebhookTriggerScheduleTypeMonthly:
		if t.TriggerScheduleSettings == nil {
			return false
		}
		for _, sched := range t.TriggerScheduleSettings.Schedules {
			if ms, ok := sched.(*MonthlySchedule); ok {
				if ms.Day != eventTimeInBotTZ.Day() {
					continue
				}
				start, err1 := time.Parse("15:04", ms.StartTime)
				end, err2 := time.Parse("15:04", ms.EndTime)
				if err1 != nil || err2 != nil {
					continue
				}
				et := eventTimeInBotTZ
				startToday := time.Date(et.Year(), et.Month(), et.Day(), start.Hour(), start.Minute(), 0, 0, et.Location())
				endToday := time.Date(et.Year(), et.Month(), et.Day(), end.Hour(), end.Minute(), 0, 0, et.Location())
				if start.Before(end) {
					// Normal time range: start < time < end
					if et.After(startToday) && et.Before(endToday) {
						return true
					}
				} else { // 跨午夜
					// Cross-midnight: time > start || time <= end
					if et.After(startToday) || !et.After(endToday) {
						return true
					}
				}
			}
		}
	case WebhookTriggerScheduleTypeBusinessHour:
		for _, bh := range businessHours {
			// Convert Go weekday to our weekday format
			// Go: Sunday=0, Monday=1, ..., Saturday=6
			// Ours: Monday=1, Tuesday=2, ..., Sunday=7
			goWeekday := int(eventTimeInBotTZ.Weekday())
			ourWeekday := goWeekday
			if goWeekday == 0 { // Sunday in Go
				ourWeekday = 7 // Sunday in our format
			}
			if int(bh.Weekday) != ourWeekday {
				continue
			}
			start := time.Date(eventTimeInBotTZ.Year(), eventTimeInBotTZ.Month(), eventTimeInBotTZ.Day(), bh.StartTime.Hour(), bh.StartTime.Minute(), 0, 0, eventTimeInBotTZ.Location())
			end := time.Date(eventTimeInBotTZ.Year(), eventTimeInBotTZ.Month(), eventTimeInBotTZ.Day(), bh.EndTime.Hour(), bh.EndTime.Minute(), 0, 0, eventTimeInBotTZ.Location())
			if !eventTimeInBotTZ.Before(start) && eventTimeInBotTZ.Before(end) {
				return true
			}
		}
	case WebhookTriggerScheduleTypeNonBusinessHour:
		inBusiness := false
		for _, bh := range businessHours {
			// Convert Go weekday to our weekday format
			// Go: Sunday=0, Monday=1, ..., Saturday=6
			// Ours: Monday=1, Tuesday=2, ..., Sunday=7
			goWeekday := int(eventTimeInBotTZ.Weekday())
			ourWeekday := goWeekday
			if goWeekday == 0 { // Sunday in Go
				ourWeekday = 7 // Sunday in our format
			}
			if int(bh.Weekday) != ourWeekday {
				continue
			}
			start := time.Date(eventTimeInBotTZ.Year(), eventTimeInBotTZ.Month(), eventTimeInBotTZ.Day(), bh.StartTime.Hour(), bh.StartTime.Minute(), 0, 0, eventTimeInBotTZ.Location())
			end := time.Date(eventTimeInBotTZ.Year(), eventTimeInBotTZ.Month(), eventTimeInBotTZ.Day(), bh.EndTime.Hour(), bh.EndTime.Minute(), 0, 0, eventTimeInBotTZ.Location())
			if !eventTimeInBotTZ.Before(start) && eventTimeInBotTZ.Before(end) {
				inBusiness = true
			}
		}
		if !inBusiness {
			return true
		}
	}
	return false
}

// BusinessHour is an alias for organization.BusinessHour for convenience.
type BusinessHour = organization.BusinessHour

// WebhookEvent represents a unified webhook event for trigger validation.
type WebhookEvent struct {
	EventType   string    // "message" (only type we handle for now)
	MessageText *string   // For keyword matching
	Timestamp   time.Time // For time-based triggers
	ChannelType string    // e.g., "LINE", "FB", "IG"
	IGStoryID   *string   // For IG Story-specific triggers
}
