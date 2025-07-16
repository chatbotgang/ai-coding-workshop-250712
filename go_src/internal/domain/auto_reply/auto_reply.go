package auto_reply

import (
	"time"
)

// AutoReply represents an omnichannel rule that associates several WebhookTriggerSetting instances.
// It defines the high-level auto-reply configuration for an organization.
type AutoReply struct {
	ID                      int                             `json:"id"`
	OrganizationID          int                             `json:"organization_id"`
	Name                    string                          `json:"name"`
	Status                  AutoReplyStatus                 `json:"status"`
	EventType               AutoReplyEventType              `json:"event_type"`
	Priority                AutoReplyPriority               `json:"priority"`
	Keywords                []string                        `json:"keywords,omitempty"`
	IGStoryIDs              []string                        `json:"ig_story_ids,omitempty"`         // Instagram Story IDs for IG Story-specific triggers
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

// AutoReplyPriority represents the 4-level priority system for auto-reply triggers.
type AutoReplyPriority int

const (
	// Priority 1: IG Story Keyword (highest priority)
	AutoReplyPriorityIGStoryKeyword AutoReplyPriority = 1
	// Priority 2: IG Story General
	AutoReplyPriorityIGStoryGeneral AutoReplyPriority = 2
	// Priority 3: General Keyword
	AutoReplyPriorityGeneralKeyword AutoReplyPriority = 3
	// Priority 4: General Time-based (lowest priority)
	AutoReplyPriorityGeneralTime AutoReplyPriority = 4
)

// IsActive returns true if the auto-reply rule is active.
func (a *AutoReply) IsActive() bool {
	return a.Status == AutoReplyStatusActive
}

// IsKeywordTrigger returns true if this is a keyword-based trigger.
func (a *AutoReply) IsKeywordTrigger() bool {
	return len(a.Keywords) > 0
}

// IsTimeTrigger returns true if this is a time-based trigger.
func (a *AutoReply) IsTimeTrigger() bool {
	return a.TriggerScheduleType != nil
}

// IsIGStorySpecific returns true if this trigger is specific to Instagram Stories.
func (a *AutoReply) IsIGStorySpecific() bool {
	return len(a.IGStoryIDs) > 0
}

// GetPriorityLevel returns the priority level based on trigger type and context.
func (a *AutoReply) GetPriorityLevel() AutoReplyPriority {
	if a.IsIGStorySpecific() {
		if a.IsKeywordTrigger() {
			return AutoReplyPriorityIGStoryKeyword
		}
		return AutoReplyPriorityIGStoryGeneral
	}
	
	if a.IsKeywordTrigger() {
		return AutoReplyPriorityGeneralKeyword
	}
	
	return AutoReplyPriorityGeneralTime
}

// MatchesIGStory returns true if the given story ID matches this rule's IG story configuration.
func (a *AutoReply) MatchesIGStory(storyID string) bool {
	if !a.IsIGStorySpecific() || storyID == "" {
		return false
	}
	
	for _, id := range a.IGStoryIDs {
		if id == storyID {
			return true
		}
	}
	return false
}
