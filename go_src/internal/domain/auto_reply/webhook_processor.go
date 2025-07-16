package auto_reply

import (
	"fmt"
	"time"
)

// WebhookProcessor handles the complete webhook event processing pipeline.
// It orchestrates all components to determine if and which auto-reply should be triggered.
type WebhookProcessor struct {
	triggerValidator *TriggerValidator
	priorityManager  *PriorityManager
}

// NewWebhookProcessor creates a new WebhookProcessor instance.
func NewWebhookProcessor() *WebhookProcessor {
	return &WebhookProcessor{
		triggerValidator: NewTriggerValidator(),
		priorityManager:  NewPriorityManager(),
	}
}

// ProcessWebhookEvent processes a webhook event against all auto-reply rules.
// This is the main entry point for webhook event processing.
func (wp *WebhookProcessor) ProcessWebhookEvent(
	event *WebhookEvent,
	autoReplies []*AutoReply,
	businessHours []*BusinessHour,
	timezone *time.Location,
) *WebhookProcessResult {
	// Input validation
	if event == nil {
		return &WebhookProcessResult{
			Success: false,
			Error:   "webhook event is nil",
		}
	}

	if len(autoReplies) == 0 {
		return &WebhookProcessResult{
			Success:    true,
			HasMatch:   false,
			Reason:     "no auto-reply rules configured",
			Event:      event,
			TotalRules: 0,
		}
	}

	// Set default timezone if not provided
	if timezone == nil {
		timezone = time.UTC
	}

	// Filter active auto-replies only
	activeReplies := wp.filterActiveAutoReplies(autoReplies)
	if len(activeReplies) == 0 {
		return &WebhookProcessResult{
			Success:    true,
			HasMatch:   false,
			Reason:     "no active auto-reply rules",
			Event:      event,
			TotalRules: len(autoReplies),
		}
	}

	// Validate all triggers with priority management
	validationResult, allValidTriggers := wp.triggerValidator.ValidateWithPriorityManagement(
		activeReplies,
		event,
		businessHours,
		timezone,
	)

	// Build comprehensive result
	result := &WebhookProcessResult{
		Success:           true,
		HasMatch:          validationResult.Matches,
		Event:             event,
		TotalRules:        len(autoReplies),
		ActiveRules:       len(activeReplies),
		EvaluatedTriggers: len(allValidTriggers),
		Timezone:          timezone.String(),
	}

	if validationResult.Matches {
		result.MatchedAutoReply = validationResult.AutoReply
		result.Priority = validationResult.Priority
		result.MatchType = string(validationResult.MatchType)
		result.Reason = validationResult.Reason
		result.AllValidTriggers = allValidTriggers
	} else {
		result.Reason = validationResult.Reason
	}

	return result
}

// ProcessWebhookEventSimple provides a simplified interface for basic webhook processing.
// This method is useful when you don't need business hours or timezone handling.
func (wp *WebhookProcessor) ProcessWebhookEventSimple(
	event *WebhookEvent,
	autoReplies []*AutoReply,
) *WebhookProcessResult {
	return wp.ProcessWebhookEvent(event, autoReplies, nil, nil)
}

// ValidateAutoReplyConfiguration validates the auto-reply configuration for potential issues.
func (wp *WebhookProcessor) ValidateAutoReplyConfiguration(autoReplies []*AutoReply) *ConfigurationValidationResult {
	if len(autoReplies) == 0 {
		return &ConfigurationValidationResult{
			Valid: true,
			Message: "no auto-reply rules to validate",
		}
	}

	// Get priority analysis
	analysis := wp.triggerValidator.GetPriorityAnalysis(autoReplies)
	warnings, _ := analysis["warnings"].([]PriorityWarning)

	result := &ConfigurationValidationResult{
		Valid:        len(warnings) == 0,
		TotalRules:   len(autoReplies),
		ActiveRules:  wp.countActiveRules(autoReplies),
		Warnings:     warnings,
		PriorityAnalysis: analysis,
	}

	if len(warnings) > 0 {
		result.Message = fmt.Sprintf("found %d configuration warnings", len(warnings))
	} else {
		result.Message = "configuration is valid"
	}

	return result
}

// CreateWebhookEvent creates a normalized WebhookEvent from platform-specific data.
// This is a utility method to help with event normalization.
func (wp *WebhookProcessor) CreateWebhookEvent(
	eventID string,
	eventType WebhookEventType,
	channelType BotType,
	botID int,
	userID string,
	messageText string,
	igStoryID *string,
	timestamp time.Time,
	extra map[string]any,
) *WebhookEvent {
	return &WebhookEvent{
		ID:          eventID,
		EventType:   eventType,
		ChannelType: channelType,
		BotID:       botID,
		UserID:      userID,
		MessageText: messageText,
		IGStoryID:   igStoryID,
		Timestamp:   timestamp,
		Extra:       extra,
	}
}

// GetProcessingStats returns statistics about webhook processing.
func (wp *WebhookProcessor) GetProcessingStats(results []*WebhookProcessResult) *ProcessingStats {
	stats := &ProcessingStats{
		TotalEvents:      len(results),
		SuccessfulEvents: 0,
		MatchedEvents:    0,
		FailedEvents:     0,
		PriorityBreakdown: make(map[AutoReplyPriority]int),
		MatchTypeBreakdown: make(map[string]int),
	}

	for _, result := range results {
		if result.Success {
			stats.SuccessfulEvents++
			if result.HasMatch {
				stats.MatchedEvents++
				stats.PriorityBreakdown[result.Priority]++
				stats.MatchTypeBreakdown[result.MatchType]++
			}
		} else {
			stats.FailedEvents++
		}
	}

	return stats
}

// filterActiveAutoReplies filters out inactive auto-reply rules.
func (wp *WebhookProcessor) filterActiveAutoReplies(autoReplies []*AutoReply) []*AutoReply {
	var active []*AutoReply
	for _, ar := range autoReplies {
		if ar.IsActive() {
			active = append(active, ar)
		}
	}
	return active
}

// countActiveRules counts the number of active auto-reply rules.
func (wp *WebhookProcessor) countActiveRules(autoReplies []*AutoReply) int {
	count := 0
	for _, ar := range autoReplies {
		if ar.IsActive() {
			count++
		}
	}
	return count
}

// WebhookProcessResult represents the result of webhook event processing.
type WebhookProcessResult struct {
	Success             bool                    `json:"success"`
	HasMatch            bool                    `json:"has_match"`
	MatchedAutoReply    *AutoReply              `json:"matched_auto_reply,omitempty"`
	Priority            AutoReplyPriority       `json:"priority,omitempty"`
	MatchType           string                  `json:"match_type,omitempty"`
	Reason              string                  `json:"reason,omitempty"`
	Error               string                  `json:"error,omitempty"`
	Event               *WebhookEvent           `json:"event,omitempty"`
	TotalRules          int                     `json:"total_rules"`
	ActiveRules         int                     `json:"active_rules"`
	EvaluatedTriggers   int                     `json:"evaluated_triggers"`
	AllValidTriggers    []*TriggerWithPriority  `json:"all_valid_triggers,omitempty"`
	Timezone            string                  `json:"timezone,omitempty"`
	ProcessingTimeMs    int64                   `json:"processing_time_ms,omitempty"`
}

// ConfigurationValidationResult represents the result of configuration validation.
type ConfigurationValidationResult struct {
	Valid            bool                   `json:"valid"`
	Message          string                 `json:"message"`
	TotalRules       int                    `json:"total_rules"`
	ActiveRules      int                    `json:"active_rules"`
	Warnings         []PriorityWarning      `json:"warnings,omitempty"`
	PriorityAnalysis map[string]any         `json:"priority_analysis,omitempty"`
}

// ProcessingStats provides statistics about webhook processing performance.
type ProcessingStats struct {
	TotalEvents        int                         `json:"total_events"`
	SuccessfulEvents   int                         `json:"successful_events"`
	MatchedEvents      int                         `json:"matched_events"`
	FailedEvents       int                         `json:"failed_events"`
	PriorityBreakdown  map[AutoReplyPriority]int   `json:"priority_breakdown"`
	MatchTypeBreakdown map[string]int              `json:"match_type_breakdown"`
}

// IsSuccessful returns true if the processing was successful.
func (r *WebhookProcessResult) IsSuccessful() bool {
	return r.Success
}

// ShouldTriggerAutoReply returns true if an auto-reply should be triggered.
func (r *WebhookProcessResult) ShouldTriggerAutoReply() bool {
	return r.Success && r.HasMatch
}

// GetPriorityDescription returns a human-readable description of the matched priority.
func (r *WebhookProcessResult) GetPriorityDescription() string {
	if !r.HasMatch {
		return "No match"
	}
	
	manager := NewPriorityManager()
	return manager.GetPriorityDescription(r.Priority)
}

// GetSummary returns a summary of the processing result.
func (r *WebhookProcessResult) GetSummary() string {
	if !r.Success {
		return fmt.Sprintf("Processing failed: %s", r.Error)
	}
	
	if !r.HasMatch {
		return fmt.Sprintf("No match found: %s", r.Reason)
	}
	
	return fmt.Sprintf("Matched auto-reply '%s' with %s priority", 
		r.MatchedAutoReply.Name, r.GetPriorityDescription())
}