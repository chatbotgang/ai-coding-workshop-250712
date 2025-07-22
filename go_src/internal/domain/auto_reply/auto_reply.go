package auto_reply

import (
	"sort"
	"strings"
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

// AutoReplyTriggerSetting combines AutoReply and WebhookTriggerSetting for trigger validation and priority sorting.
type AutoReplyTriggerSetting struct {
	AutoReplyID             int
	WebhookTriggerSettingID int
	BotID                   int
	ChannelType             string // organization.BotType as string
	Enable                  bool
	Status                  AutoReplyStatus
	EventType               AutoReplyEventType
	Keywords                []string
	Priority                int
	TriggerScheduleType     *WebhookTriggerScheduleType
	TriggerScheduleSettings *WebhookTriggerScheduleSettings
	// IG Story specific fields
	StoryIDs  []string // If set, this rule is IG Story specific
	CreatedAt time.Time
	UpdatedAt time.Time
}

// AutoReplyChannelSettingAggregate holds all trigger settings for a specific bot/channel.
type AutoReplyChannelSettingAggregate struct {
	BotID           int
	ChannelType     string // organization.BotType as string
	TriggerSettings []*AutoReplyTriggerSetting
	Timezone        string // e.g., "Asia/Taipei"
}

// WebhookEvent represents the incoming event for trigger validation.
type WebhookEvent struct {
	EventType   string    // "message" (only type we handle)
	MessageText *string   // For keyword matching
	Timestamp   time.Time // For time-based triggers
	ChannelType string    // organization.BotType as string
	IGStoryID   *string   // For IG Story context, nil if not a story reply
}

// normalizeKeyword trims spaces and lowercases the keyword
func normalizeKeyword(s string) string {
	return strings.ToLower(strings.TrimSpace(s))
}

// isKeywordMatch returns true if message matches any keyword (case-insensitive, trimmed, exact match)
func isKeywordMatch(keywords []string, message string) bool {
	msgNorm := normalizeKeyword(message)
	for _, kw := range keywords {
		if msgNorm == normalizeKeyword(kw) {
			return true
		}
	}
	return false
}

// isTimeMatch checks if the event timestamp matches the trigger's schedule (daily, monthly, business hour)
func isTimeMatch(scheduleType *WebhookTriggerScheduleType, scheduleSettings *WebhookTriggerScheduleSettings, eventTime time.Time) bool {
	if scheduleType == nil || scheduleSettings == nil {
		return false
	}

	switch *scheduleType {
	case WebhookTriggerScheduleTypeDaily:
		for _, s := range scheduleSettings.Schedules {
			if daily, ok := s.(*DailySchedule); ok {
				start, err1 := time.Parse("15:04", daily.StartTime)
				end, err2 := time.Parse("15:04", daily.EndTime)
				if err1 != nil || err2 != nil {
					continue
				}
				eventHM := eventTime.Format("15:04")
				eventT, _ := time.Parse("15:04", eventHM)
				if start.Before(end) {
					if (eventT.Equal(start) || eventT.After(start)) && eventT.Before(end) {
						return true
					}
				} else if start.After(end) {
					if eventT.Equal(start) || eventT.After(start) || eventT.Before(end) {
						return true
					}
				} else if start.Equal(end) {
					return true
				}
			}
		}
	case WebhookTriggerScheduleTypeMonthly:
		for _, s := range scheduleSettings.Schedules {
			if monthly, ok := s.(*MonthlySchedule); ok {
				if eventTime.Day() != monthly.Day {
					continue
				}
				start, err1 := time.Parse("15:04", monthly.StartTime)
				end, err2 := time.Parse("15:04", monthly.EndTime)
				if err1 != nil || err2 != nil {
					continue
				}
				eventHM := eventTime.Format("15:04")
				eventT, _ := time.Parse("15:04", eventHM)
				if start.Before(end) {
					if (eventT.Equal(start) || eventT.After(start)) && eventT.Before(end) {
						return true
					}
				} else if start.After(end) {
					if eventT.Equal(start) || eventT.After(start) || eventT.Before(end) {
						return true
					}
				} else if start.Equal(end) {
					return true
				}
			}
		}
	case WebhookTriggerScheduleTypeBusinessHour:
		return true // stub, 可擴充
	case WebhookTriggerScheduleTypeNonBusinessHour:
		return true // stub, 可擴充
	}
	return false
}

// ValidateTrigger returns the first matching trigger setting based on the 4-level priority system, or nil if no match.
func (a *AutoReplyChannelSettingAggregate) ValidateTrigger(event WebhookEvent) (*AutoReplyTriggerSetting, error) {
	// Priority 1: IG Story Keyword
	var igStoryKeywordTriggers []*AutoReplyTriggerSetting
	// Priority 2: IG Story General
	var igStoryGeneralTriggers []*AutoReplyTriggerSetting
	// Priority 3: General Keyword
	var generalKeywordTriggers []*AutoReplyTriggerSetting
	// Priority 4: General Time-based
	var generalTimeTriggers []*AutoReplyTriggerSetting

	for _, t := range a.TriggerSettings {
		if !t.Enable || t.Status != AutoReplyStatusActive {
			continue
		}
		isIGStory := len(t.StoryIDs) > 0
		isKeyword := len(t.Keywords) > 0
		isTime := t.TriggerScheduleType != nil && t.TriggerScheduleSettings != nil

		if isIGStory && isKeyword {
			igStoryKeywordTriggers = append(igStoryKeywordTriggers, t)
		} else if isIGStory && isTime {
			igStoryGeneralTriggers = append(igStoryGeneralTriggers, t)
		} else if !isIGStory && isKeyword {
			generalKeywordTriggers = append(generalKeywordTriggers, t)
		} else if !isIGStory && isTime {
			generalTimeTriggers = append(generalTimeTriggers, t)
		}
	}

	sort.Slice(igStoryKeywordTriggers, func(i, j int) bool {
		return igStoryKeywordTriggers[i].Priority > igStoryKeywordTriggers[j].Priority
	})
	sort.Slice(igStoryGeneralTriggers, func(i, j int) bool {
		return igStoryGeneralTriggers[i].Priority > igStoryGeneralTriggers[j].Priority
	})
	sort.Slice(generalKeywordTriggers, func(i, j int) bool {
		return generalKeywordTriggers[i].Priority > generalKeywordTriggers[j].Priority
	})
	sort.Slice(generalTimeTriggers, func(i, j int) bool {
		return generalTimeTriggers[i].Priority > generalTimeTriggers[j].Priority
	})

	// Priority 1: IG Story Keyword
	if event.EventType == "message" && event.MessageText != nil && event.IGStoryID != nil {
		for _, t := range igStoryKeywordTriggers {
			if containsString(t.StoryIDs, *event.IGStoryID) && isKeywordMatch(t.Keywords, *event.MessageText) {
				return t, nil
			}
		}
	}
	// Priority 2: IG Story General
	if event.EventType == "message" && event.IGStoryID != nil {
		// 時區處理
		eventTime := event.Timestamp
		if a.Timezone != "" {
			if loc, err := time.LoadLocation(a.Timezone); err == nil {
				eventTime = eventTime.In(loc)
			}
		}
		for _, t := range igStoryGeneralTriggers {
			if containsString(t.StoryIDs, *event.IGStoryID) && isTimeMatch(t.TriggerScheduleType, t.TriggerScheduleSettings, eventTime) {
				return t, nil
			}
		}
	}
	// Priority 3: General Keyword (only if NOT IG Story context)
	if event.EventType == "message" && event.MessageText != nil && event.IGStoryID == nil {
		for _, t := range generalKeywordTriggers {
			if isKeywordMatch(t.Keywords, *event.MessageText) {
				return t, nil
			}
		}
	}
	// Priority 4: General Time-based (only if NOT IG Story context)
	if event.EventType == "message" && event.IGStoryID == nil {
		// 時區處理
		eventTime := event.Timestamp
		if a.Timezone != "" {
			if loc, err := time.LoadLocation(a.Timezone); err == nil {
				eventTime = eventTime.In(loc)
			}
		}
		for _, t := range generalTimeTriggers {
			if isTimeMatch(t.TriggerScheduleType, t.TriggerScheduleSettings, eventTime) {
				return t, nil
			}
		}
	}
	return nil, nil
}

// containsString returns true if target is in arr
func containsString(arr []string, target string) bool {
	for _, s := range arr {
		if s == target {
			return true
		}
	}
	return false
}
