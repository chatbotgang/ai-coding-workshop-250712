package auto_reply

import (
	"sort"
)

// PriorityManager handles the 4-level priority system for auto-reply triggers.
// Priority levels (from highest to lowest):
// 1. IG Story Keyword
// 2. IG Story General  
// 3. General Keyword
// 4. General Time-based
type PriorityManager struct{}

// NewPriorityManager creates a new PriorityManager instance.
func NewPriorityManager() *PriorityManager {
	return &PriorityManager{}
}

// TriggerWithPriority represents an auto-reply with its calculated priority.
type TriggerWithPriority struct {
	AutoReply *AutoReply
	Priority  AutoReplyPriority
	Context   string // Description of why this priority was assigned
}

// CalculatePriority calculates the priority for a given auto-reply and event context.
func (pm *PriorityManager) CalculatePriority(autoReply *AutoReply, event *WebhookEvent) *TriggerWithPriority {
	if autoReply == nil {
		return nil
	}

	var priority AutoReplyPriority
	var context string

	// Check IG Story context first (highest priority levels)
	if autoReply.IsIGStorySpecific() {
		if event != nil && event.IsIGStoryReply() && autoReply.MatchesIGStory(*event.IGStoryID) {
			if autoReply.IsKeywordTrigger() {
				priority = AutoReplyPriorityIGStoryKeyword
				context = "IG Story + Keyword match"
			} else {
				priority = AutoReplyPriorityIGStoryGeneral
				context = "IG Story + General/Time match"
			}
		} else {
			// IG Story specific but context doesn't match - should not trigger
			return nil
		}
	} else {
		// General triggers (lower priority levels)
		if autoReply.IsKeywordTrigger() {
			priority = AutoReplyPriorityGeneralKeyword
			context = "General Keyword match"
		} else {
			priority = AutoReplyPriorityGeneralTime
			context = "General Time-based match"
		}
	}

	return &TriggerWithPriority{
		AutoReply: autoReply,
		Priority:  priority,
		Context:   context,
	}
}

// SortByPriority sorts triggers by priority (highest priority first).
func (pm *PriorityManager) SortByPriority(triggers []*TriggerWithPriority) []*TriggerWithPriority {
	if len(triggers) <= 1 {
		return triggers
	}

	sorted := make([]*TriggerWithPriority, len(triggers))
	copy(sorted, triggers)

	sort.Slice(sorted, func(i, j int) bool {
		return sorted[i].Priority < sorted[j].Priority // Lower number = higher priority
	})

	return sorted
}

// GetHighestPriorityTrigger returns the highest priority trigger from a list.
func (pm *PriorityManager) GetHighestPriorityTrigger(triggers []*TriggerWithPriority) *TriggerWithPriority {
	if len(triggers) == 0 {
		return nil
	}

	sorted := pm.SortByPriority(triggers)
	return sorted[0]
}

// FilterByPriorityLevel filters triggers by a specific priority level.
func (pm *PriorityManager) FilterByPriorityLevel(triggers []*TriggerWithPriority, level AutoReplyPriority) []*TriggerWithPriority {
	var filtered []*TriggerWithPriority
	
	for _, trigger := range triggers {
		if trigger.Priority == level {
			filtered = append(filtered, trigger)
		}
	}
	
	return filtered
}

// GroupByPriorityLevel groups triggers by their priority levels.
func (pm *PriorityManager) GroupByPriorityLevel(triggers []*TriggerWithPriority) map[AutoReplyPriority][]*TriggerWithPriority {
	groups := make(map[AutoReplyPriority][]*TriggerWithPriority)
	
	for _, trigger := range triggers {
		groups[trigger.Priority] = append(groups[trigger.Priority], trigger)
	}
	
	return groups
}

// ValidatePriorityConfiguration validates that auto-reply configurations don't conflict.
// Returns warnings for potential issues.
func (pm *PriorityManager) ValidatePriorityConfiguration(autoReplies []*AutoReply) []PriorityWarning {
	var warnings []PriorityWarning

	// Group by keywords to detect conflicts
	keywordMap := make(map[string][]*AutoReply)
	
	for _, ar := range autoReplies {
		if !ar.IsActive() {
			continue
		}
		
		for _, keyword := range ar.Keywords {
			keywordMap[keyword] = append(keywordMap[keyword], ar)
		}
	}

	// Check for keyword conflicts
	for keyword, triggers := range keywordMap {
		if len(triggers) > 1 {
			// Check if there are conflicting triggers (same keyword, different priorities)
			priorities := make(map[AutoReplyPriority]bool)
			for _, trigger := range triggers {
				priorities[trigger.GetPriorityLevel()] = true
			}
			
			if len(priorities) > 1 {
				warnings = append(warnings, PriorityWarning{
					Type:     "keyword_conflict",
					Message:  "Keyword '" + keyword + "' used in multiple triggers with different priorities",
					Keyword:  keyword,
					Triggers: triggers,
				})
			}
		}
	}

	return warnings
}

// PriorityWarning represents a potential issue with priority configuration.
type PriorityWarning struct {
	Type     string
	Message  string
	Keyword  string
	Triggers []*AutoReply
}

// GetPriorityDescription returns a human-readable description of the priority level.
func (pm *PriorityManager) GetPriorityDescription(priority AutoReplyPriority) string {
	switch priority {
	case AutoReplyPriorityIGStoryKeyword:
		return "IG Story Keyword (Highest Priority)"
	case AutoReplyPriorityIGStoryGeneral:
		return "IG Story General"
	case AutoReplyPriorityGeneralKeyword:
		return "General Keyword"
	case AutoReplyPriorityGeneralTime:
		return "General Time-based (Lowest Priority)"
	default:
		return "Unknown Priority"
	}
}

// IsHigherPriority returns true if priority1 is higher than priority2.
func (pm *PriorityManager) IsHigherPriority(priority1, priority2 AutoReplyPriority) bool {
	return priority1 < priority2 // Lower number = higher priority
}

// GetAllPriorityLevels returns all priority levels in order (highest to lowest).
func (pm *PriorityManager) GetAllPriorityLevels() []AutoReplyPriority {
	return []AutoReplyPriority{
		AutoReplyPriorityIGStoryKeyword,
		AutoReplyPriorityIGStoryGeneral,
		AutoReplyPriorityGeneralKeyword,
		AutoReplyPriorityGeneralTime,
	}
}