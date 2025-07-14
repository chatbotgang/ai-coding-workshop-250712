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
	AutoReplyEventTypeMessage  AutoReplyEventType = "message"
	AutoReplyEventTypePostback AutoReplyEventType = "postback"
	AutoReplyEventTypeFollow   AutoReplyEventType = "follow"
	AutoReplyEventTypeBeacon   AutoReplyEventType = "beacon"
	AutoReplyEventTypeTime     AutoReplyEventType = "time"
	AutoReplyEventTypeKeyword  AutoReplyEventType = "keyword"
	AutoReplyEventTypeDefault  AutoReplyEventType = "default"
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

// AutoReplyChannelSettingAggregate represents all trigger settings and business context for a bot/channel.
type AutoReplyChannelSettingAggregate struct {
	BotID           int
	TriggerSettings []*AutoReplyTriggerSetting
	BusinessHours   []BusinessHour
	Timezone        string // e.g., "Asia/Taipei"
}

// ValidateTrigger validates the incoming event and returns the first matching trigger setting based on priority.
func (agg *AutoReplyChannelSettingAggregate) ValidateTrigger(event WebhookEvent) (*AutoReplyTriggerSetting, error) {
	// 1. Collect all active keyword triggers
	var keywordTriggers []*AutoReplyTriggerSetting
	for _, t := range agg.TriggerSettings {
		if t.IsActive() && t.IsKeywordTrigger() {
			keywordTriggers = append(keywordTriggers, t)
		}
	}
	// Sort keyword triggers by Priority (desc)
	sort.Slice(keywordTriggers, func(i, j int) bool {
		return keywordTriggers[i].Priority > keywordTriggers[j].Priority
	})
	// Check keyword triggers
	if event.MessageText != nil {
		for _, t := range keywordTriggers {
			if t.IsKeywordMatch(*event.MessageText) {
				return t, nil
			}
		}
	}

	// 2. Collect all active general time triggers
	var generalTriggers []*AutoReplyTriggerSetting
	for _, t := range agg.TriggerSettings {
		if t.IsActive() && t.IsGeneralTimeTrigger() {
			generalTriggers = append(generalTriggers, t)
		}
	}
	// Sort general triggers by schedule type priority, then by Priority (desc)
	sort.Slice(generalTriggers, func(i, j int) bool {
		priI := scheduleTypePriority(generalTriggers[i].TriggerScheduleType)
		priJ := scheduleTypePriority(generalTriggers[j].TriggerScheduleType)
		if priI != priJ {
			return priI < priJ // lower value = higher priority
		}
		return generalTriggers[i].Priority > generalTriggers[j].Priority
	})
	// TODO: implement schedule matching logic for each general trigger
	// for _, t := range generalTriggers {
	//   if isScheduleMatch(t, event.Timestamp, agg.BusinessHours, agg.Timezone) {
	//     return t, nil
	//   }
	// }

	// 3. No match found
	return nil, nil
}

// scheduleTypePriority returns the priority order for schedule types (lower = higher priority)
func scheduleTypePriority(scheduleType *WebhookTriggerScheduleType) int {
	if scheduleType == nil {
		return 99 // lowest priority if not set
	}
	switch *scheduleType {
	case WebhookTriggerScheduleTypeMonthly:
		return 1
	case WebhookTriggerScheduleTypeBusinessHour:
		return 2
	case WebhookTriggerScheduleTypeNonBusinessHour:
		return 3
	case WebhookTriggerScheduleTypeDaily:
		return 4
	default:
		return 99
	}
}

// BusinessHour is an alias for organization.BusinessHour for convenience.
type BusinessHour = organization.BusinessHour

// WebhookEvent represents a unified webhook event for trigger validation.
type WebhookEvent struct {
	EventType   string    // "message" (only type we handle for now)
	MessageText *string   // For keyword matching
	Timestamp   time.Time // For time-based triggers
	ChannelType string    // e.g., "LINE", "FB", "IG"
}
