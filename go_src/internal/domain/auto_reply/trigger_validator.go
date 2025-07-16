package auto_reply

import (
	"time"
)

// TriggerValidator handles the validation logic for auto-reply triggers.
type TriggerValidator struct {
	keywordMatcher    *KeywordMatcher
	scheduleValidator *ScheduleValidator
	priorityManager   *PriorityManager
}

// NewTriggerValidator creates a new TriggerValidator instance.
func NewTriggerValidator() *TriggerValidator {
	return &TriggerValidator{
		keywordMatcher:    NewKeywordMatcher(),
		scheduleValidator: NewScheduleValidator(),
		priorityManager:   NewPriorityManager(),
	}
}

// TriggerValidationResult represents the result of trigger validation.
type TriggerValidationResult struct {
	Matches    bool                `json:"matches"`
	Priority   AutoReplyPriority   `json:"priority"`
	AutoReply  *AutoReply          `json:"auto_reply,omitempty"`
	Reason     string              `json:"reason,omitempty"`
	MatchType  TriggerMatchType    `json:"match_type"`
}

// TriggerMatchType represents the type of trigger that matched.
type TriggerMatchType string

const (
	TriggerMatchTypeIGStoryKeyword TriggerMatchType = "ig_story_keyword"
	TriggerMatchTypeIGStoryGeneral TriggerMatchType = "ig_story_general"
	TriggerMatchTypeGeneralKeyword TriggerMatchType = "general_keyword"
	TriggerMatchTypeGeneralTime    TriggerMatchType = "general_time"
	TriggerMatchTypeNone           TriggerMatchType = "none"
)

// BusinessHour represents business hour configuration for schedule validation.
type BusinessHour struct {
	Weekday   int
	StartTime time.Time
	EndTime   time.Time
}

// ValidateTrigger validates if the given auto-reply rule should trigger for the webhook event.
// This implements the core trigger validation logic excluding time-based validation.
func (tv *TriggerValidator) ValidateTrigger(autoReply *AutoReply, event *WebhookEvent) *TriggerValidationResult {
	if autoReply == nil || event == nil {
		return &TriggerValidationResult{
			Matches:   false,
			Reason:    "auto_reply or event is nil",
			MatchType: TriggerMatchTypeNone,
		}
	}

	// Check if auto-reply is active
	if !autoReply.IsActive() {
		return &TriggerValidationResult{
			Matches:   false,
			Reason:    "auto_reply is not active",
			MatchType: TriggerMatchTypeNone,
		}
	}

	// Only MESSAGE events support triggers (as per PRD)
	if !event.IsMessageEvent() {
		return &TriggerValidationResult{
			Matches:   false,
			Reason:    "only MESSAGE events support triggers",
			MatchType: TriggerMatchTypeNone,
		}
	}

	// Validate IG Story context matching
	if autoReply.IsIGStorySpecific() {
		return tv.validateIGStoryTrigger(autoReply, event)
	}

	// Validate general triggers
	return tv.validateGeneralTrigger(autoReply, event)
}

// validateIGStoryTrigger validates IG Story-specific triggers.
func (tv *TriggerValidator) validateIGStoryTrigger(autoReply *AutoReply, event *WebhookEvent) *TriggerValidationResult {
	// Must be an Instagram channel
	if event.ChannelType != BotTypeInstagram {
		return &TriggerValidationResult{
			Matches:   false,
			Reason:    "IG story trigger requires Instagram channel",
			MatchType: TriggerMatchTypeNone,
		}
	}

	// Must be a reply to a story
	if !event.IsIGStoryReply() {
		return &TriggerValidationResult{
			Matches:   false,
			Reason:    "IG story trigger requires story context",
			MatchType: TriggerMatchTypeNone,
		}
	}

	// Must match the specified story ID
	if !autoReply.MatchesIGStory(*event.IGStoryID) {
		return &TriggerValidationResult{
			Matches:   false,
			Reason:    "story ID does not match configured story IDs",
			MatchType: TriggerMatchTypeNone,
		}
	}

	// Check if it's a keyword trigger
	if autoReply.IsKeywordTrigger() {
		if tv.keywordMatcher.MatchesKeywords(event.MessageText, autoReply.Keywords) {
			return &TriggerValidationResult{
				Matches:   true,
				Priority:  AutoReplyPriorityIGStoryKeyword,
				AutoReply: autoReply,
				MatchType: TriggerMatchTypeIGStoryKeyword,
			}
		}
		return &TriggerValidationResult{
			Matches:   false,
			Reason:    "message does not match IG story keywords",
			MatchType: TriggerMatchTypeNone,
		}
	}

	// IG Story General trigger (time-based validation will be handled separately)
	return &TriggerValidationResult{
		Matches:   true,
		Priority:  AutoReplyPriorityIGStoryGeneral,
		AutoReply: autoReply,
		MatchType: TriggerMatchTypeIGStoryGeneral,
	}
}

// validateGeneralTrigger validates general (non-IG Story) triggers.
func (tv *TriggerValidator) validateGeneralTrigger(autoReply *AutoReply, event *WebhookEvent) *TriggerValidationResult {
	// Check if it's a keyword trigger
	if autoReply.IsKeywordTrigger() {
		if tv.keywordMatcher.MatchesKeywords(event.MessageText, autoReply.Keywords) {
			return &TriggerValidationResult{
				Matches:   true,
				Priority:  AutoReplyPriorityGeneralKeyword,
				AutoReply: autoReply,
				MatchType: TriggerMatchTypeGeneralKeyword,
			}
		}
		return &TriggerValidationResult{
			Matches:   false,
			Reason:    "message does not match general keywords",
			MatchType: TriggerMatchTypeNone,
		}
	}

	// General time-based trigger (time validation will be handled separately)
	return &TriggerValidationResult{
		Matches:   true,
		Priority:  AutoReplyPriorityGeneralTime,
		AutoReply: autoReply,
		MatchType: TriggerMatchTypeGeneralTime,
	}
}

// ValidateMultipleTriggers validates multiple auto-reply rules and returns the highest priority match.
// Implements the priority system: IG Story Keyword > IG Story General > General Keyword > General Time.
func (tv *TriggerValidator) ValidateMultipleTriggers(autoReplies []*AutoReply, event *WebhookEvent) *TriggerValidationResult {
	if len(autoReplies) == 0 {
		return &TriggerValidationResult{
			Matches:   false,
			Reason:    "no auto_replies provided",
			MatchType: TriggerMatchTypeNone,
		}
	}

	var bestMatch *TriggerValidationResult
	
	for _, autoReply := range autoReplies {
		result := tv.ValidateTrigger(autoReply, event)
		
		if !result.Matches {
			continue
		}
		
		// First match or higher priority match
		if bestMatch == nil || result.Priority < bestMatch.Priority {
			bestMatch = result
		}
	}

	if bestMatch == nil {
		return &TriggerValidationResult{
			Matches:   false,
			Reason:    "no triggers matched",
			MatchType: TriggerMatchTypeNone,
		}
	}

	return bestMatch
}

// ValidateCompleteTrigger validates both keyword/context and schedule constraints for a trigger.
// This is the main entry point for comprehensive trigger validation.
func (tv *TriggerValidator) ValidateCompleteTrigger(
	autoReply *AutoReply,
	event *WebhookEvent,
	businessHours []*BusinessHour,
	timezone *time.Location,
) *TriggerValidationResult {
	// First validate basic trigger logic (keyword/context)
	basicResult := tv.ValidateTrigger(autoReply, event)
	if !basicResult.Matches {
		return basicResult
	}

	// If this is a time-based trigger, validate schedule
	if autoReply.IsTimeTrigger() {
		scheduleResult := tv.scheduleValidator.ValidateSchedule(
			autoReply,
			event.Timestamp,
			businessHours,
			timezone,
		)
		
		if !scheduleResult.IsMatch {
			return &TriggerValidationResult{
				Matches:   false,
				Priority:  basicResult.Priority,
				AutoReply: basicResult.AutoReply,
				Reason:    "schedule validation failed: " + scheduleResult.Reason,
				MatchType: basicResult.MatchType,
			}
		}
	}

	// Both basic and schedule validation passed
	return basicResult
}

// ValidateMultipleCompleteTriggersWithSchedule validates multiple triggers with full schedule validation.
func (tv *TriggerValidator) ValidateMultipleCompleteTriggersWithSchedule(
	autoReplies []*AutoReply,
	event *WebhookEvent,
	businessHours []*BusinessHour,
	timezone *time.Location,
) *TriggerValidationResult {
	if len(autoReplies) == 0 {
		return &TriggerValidationResult{
			Matches:   false,
			Reason:    "no auto_replies provided",
			MatchType: TriggerMatchTypeNone,
		}
	}

	var bestMatch *TriggerValidationResult
	
	for _, autoReply := range autoReplies {
		result := tv.ValidateCompleteTrigger(autoReply, event, businessHours, timezone)
		
		if !result.Matches {
			continue
		}
		
		// First match or higher priority match
		if bestMatch == nil || result.Priority < bestMatch.Priority {
			bestMatch = result
		}
	}

	if bestMatch == nil {
		return &TriggerValidationResult{
			Matches:   false,
			Reason:    "no triggers matched with schedule validation",
			MatchType: TriggerMatchTypeNone,
		}
	}

	return bestMatch
}

// ValidateWithPriorityManagement validates triggers using the priority management system.
// This method provides the most comprehensive validation with detailed priority analysis.
func (tv *TriggerValidator) ValidateWithPriorityManagement(
	autoReplies []*AutoReply,
	event *WebhookEvent,
	businessHours []*BusinessHour,
	timezone *time.Location,
) (*TriggerValidationResult, []*TriggerWithPriority) {
	if len(autoReplies) == 0 {
		return &TriggerValidationResult{
			Matches:   false,
			Reason:    "no auto_replies provided",
			MatchType: TriggerMatchTypeNone,
		}, nil
	}

	var validTriggers []*TriggerWithPriority
	
	// Calculate priority for all triggers and validate them
	for _, autoReply := range autoReplies {
		// Calculate priority context
		triggerWithPriority := tv.priorityManager.CalculatePriority(autoReply, event)
		if triggerWithPriority == nil {
			continue // This trigger doesn't apply to this event context
		}
		
		// Perform complete validation (keyword + schedule)
		validationResult := tv.ValidateCompleteTrigger(autoReply, event, businessHours, timezone)
		if validationResult.Matches {
			validTriggers = append(validTriggers, triggerWithPriority)
		}
	}

	// No valid triggers found
	if len(validTriggers) == 0 {
		return &TriggerValidationResult{
			Matches:   false,
			Reason:    "no triggers matched after complete validation",
			MatchType: TriggerMatchTypeNone,
		}, nil
	}

	// Get the highest priority trigger
	highestPriority := tv.priorityManager.GetHighestPriorityTrigger(validTriggers)
	
	// Convert to TriggerValidationResult
	var matchType TriggerMatchType
	switch highestPriority.Priority {
	case AutoReplyPriorityIGStoryKeyword:
		matchType = TriggerMatchTypeIGStoryKeyword
	case AutoReplyPriorityIGStoryGeneral:
		matchType = TriggerMatchTypeIGStoryGeneral
	case AutoReplyPriorityGeneralKeyword:
		matchType = TriggerMatchTypeGeneralKeyword
	case AutoReplyPriorityGeneralTime:
		matchType = TriggerMatchTypeGeneralTime
	default:
		matchType = TriggerMatchTypeNone
	}

	result := &TriggerValidationResult{
		Matches:   true,
		Priority:  highestPriority.Priority,
		AutoReply: highestPriority.AutoReply,
		MatchType: matchType,
		Reason:    highestPriority.Context,
	}

	return result, validTriggers
}

// GetPriorityAnalysis provides detailed analysis of trigger priorities for debugging/monitoring.
func (tv *TriggerValidator) GetPriorityAnalysis(autoReplies []*AutoReply) map[string]any {
	warnings := tv.priorityManager.ValidatePriorityConfiguration(autoReplies)
	
	priorityGroups := make(map[string][]string)
	for _, autoReply := range autoReplies {
		if !autoReply.IsActive() {
			continue
		}
		
		priority := autoReply.GetPriorityLevel()
		priorityName := tv.priorityManager.GetPriorityDescription(priority)
		priorityGroups[priorityName] = append(priorityGroups[priorityName], autoReply.Name)
	}

	return map[string]any{
		"warnings":        warnings,
		"priority_groups": priorityGroups,
		"total_triggers":  len(autoReplies),
	}
}