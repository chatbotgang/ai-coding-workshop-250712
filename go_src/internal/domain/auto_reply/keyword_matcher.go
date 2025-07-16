package auto_reply

import (
	"strings"
)

// KeywordMatcher handles keyword matching logic with normalization rules.
type KeywordMatcher struct{}

// NewKeywordMatcher creates a new KeywordMatcher instance.
func NewKeywordMatcher() *KeywordMatcher {
	return &KeywordMatcher{}
}

// MatchesKeywords checks if the message text matches any of the provided keywords.
// Implements exact match with case-insensitive and trim normalization as per PRD:
// - Case insensitive: "hello" matches "HELLO" 
// - Trim spaces: "hello" matches " hello "
// - Exact match only: "hello" does NOT match "hello world"
// - Multiple keywords: ["hello", "hi"] matches "hi"
func (km *KeywordMatcher) MatchesKeywords(messageText string, keywords []string) bool {
	if messageText == "" || len(keywords) == 0 {
		return false
	}

	normalizedMessage := km.normalizeText(messageText)

	for _, keyword := range keywords {
		if keyword == "" {
			continue
		}
		
		normalizedKeyword := km.normalizeText(keyword)
		if normalizedMessage == normalizedKeyword {
			return true
		}
	}

	return false
}

// MatchesKeyword checks if the message text matches a single keyword.
func (km *KeywordMatcher) MatchesKeyword(messageText string, keyword string) bool {
	return km.MatchesKeywords(messageText, []string{keyword})
}

// normalizeText applies normalization rules for keyword matching:
// 1. Trim leading and trailing whitespace
// 2. Convert to lowercase for case-insensitive matching
func (km *KeywordMatcher) normalizeText(text string) string {
	return strings.ToLower(strings.TrimSpace(text))
}

// ValidateKeywords checks if the provided keywords are valid.
// Returns an error if any keyword is invalid.
func (km *KeywordMatcher) ValidateKeywords(keywords []string) error {
	for _, keyword := range keywords {
		if err := km.ValidateKeyword(keyword); err != nil {
			return err
		}
	}
	return nil
}

// ValidateKeyword checks if a single keyword is valid.
func (km *KeywordMatcher) ValidateKeyword(keyword string) error {
	normalized := km.normalizeText(keyword)
	if normalized == "" {
		return &KeywordValidationError{
			Keyword: keyword,
			Reason:  "keyword cannot be empty after normalization",
		}
	}
	return nil
}

// KeywordValidationError represents an error in keyword validation.
type KeywordValidationError struct {
	Keyword string
	Reason  string
}

func (e *KeywordValidationError) Error() string {
	return "keyword validation failed for '" + e.Keyword + "': " + e.Reason
}

// GetNormalizedKeywords returns the normalized versions of the provided keywords.
// Useful for storage and debugging.
func (km *KeywordMatcher) GetNormalizedKeywords(keywords []string) []string {
	normalized := make([]string, 0, len(keywords))
	for _, keyword := range keywords {
		if norm := km.normalizeText(keyword); norm != "" {
			normalized = append(normalized, norm)
		}
	}
	return normalized
}