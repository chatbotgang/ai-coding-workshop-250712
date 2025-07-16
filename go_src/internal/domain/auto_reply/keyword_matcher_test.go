package auto_reply

import (
	"testing"
)

func TestKeywordMatcher_MatchesKeywords(t *testing.T) {
	matcher := NewKeywordMatcher()

	tests := []struct {
		name         string
		messageText  string
		keywords     []string
		shouldMatch  bool
		description  string
	}{
		// PRD Test Cases from Story 1: Keyword Reply Logic
		{
			name:        "exact_match_case_insensitive",
			messageText: "HELLO",
			keywords:    []string{"hello"},
			shouldMatch: true,
			description: "B-P0-7-Test2: exact keyword match regardless of case",
		},
		{
			name:        "exact_match_with_spaces",
			messageText: " hello ",
			keywords:    []string{"hello"},
			shouldMatch: true,
			description: "B-P0-7-Test3: leading and trailing spaces are trimmed",
		},
		{
			name:        "partial_match_should_fail",
			messageText: "hello world",
			keywords:    []string{"hello"},
			shouldMatch: false,
			description: "B-P0-7-Test4: partial match should NOT trigger",
		},
		{
			name:        "close_variation_should_fail",
			messageText: "helo",
			keywords:    []string{"hello"},
			shouldMatch: false,
			description: "B-P0-7-Test5: close variation should NOT trigger",
		},
		
		// PRD Test Cases from Story 2: Multiple Keywords Support  
		{
			name:        "multiple_keywords_first_match",
			messageText: "hello",
			keywords:    []string{"hello", "hi", "hey"},
			shouldMatch: true,
			description: "Multiple-Keywords-Test1: match first keyword",
		},
		{
			name:        "multiple_keywords_middle_match",
			messageText: "hi",
			keywords:    []string{"hello", "hi", "hey"},
			shouldMatch: true,
			description: "Multiple-Keywords-Test1: match middle keyword",
		},
		{
			name:        "multiple_keywords_case_insensitive",
			messageText: "HI",
			keywords:    []string{"hello", "hi", "hey"},
			shouldMatch: true,
			description: "Multiple-Keywords-Test2: case insensitive with multiple keywords",
		},
		{
			name:        "multiple_keywords_no_match",
			messageText: "goodbye",
			keywords:    []string{"hello", "hi", "hey"},
			shouldMatch: false,
			description: "Multiple-Keywords-Test3: no match with multiple keywords",
		},

		// Edge Cases
		{
			name:        "empty_message",
			messageText: "",
			keywords:    []string{"hello"},
			shouldMatch: false,
			description: "empty message should not match",
		},
		{
			name:        "empty_keywords",
			messageText: "hello",
			keywords:    []string{},
			shouldMatch: false,
			description: "empty keywords should not match",
		},
		{
			name:        "empty_keyword_in_list",
			messageText: "hello",
			keywords:    []string{"", "hello"},
			shouldMatch: true,
			description: "should ignore empty keywords and match valid ones",
		},
		{
			name:        "whitespace_only_message",
			messageText: "   ",
			keywords:    []string{"hello"},
			shouldMatch: false,
			description: "whitespace-only message should not match",
		},
		{
			name:        "special_characters",
			messageText: "hello!",
			keywords:    []string{"hello!"},
			shouldMatch: true,
			description: "special characters should be matched exactly",
		},
		{
			name:        "unicode_characters",
			messageText: "こんにちは",
			keywords:    []string{"こんにちは"},
			shouldMatch: true,
			description: "unicode characters should be matched",
		},
		{
			name:        "mixed_case_keyword",
			messageText: "Hello",
			keywords:    []string{"HELLO"},
			shouldMatch: true,
			description: "mixed case should match case-insensitively",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := matcher.MatchesKeywords(tt.messageText, tt.keywords)
			if result != tt.shouldMatch {
				t.Errorf("MatchesKeywords() = %v, want %v. Description: %s", result, tt.shouldMatch, tt.description)
			}
		})
	}
}

func TestKeywordMatcher_MatchesKeyword(t *testing.T) {
	matcher := NewKeywordMatcher()

	tests := []struct {
		name        string
		messageText string
		keyword     string
		shouldMatch bool
	}{
		{
			name:        "single_keyword_match",
			messageText: "hello",
			keyword:     "hello",
			shouldMatch: true,
		},
		{
			name:        "single_keyword_no_match",
			messageText: "goodbye",
			keyword:     "hello",
			shouldMatch: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := matcher.MatchesKeyword(tt.messageText, tt.keyword)
			if result != tt.shouldMatch {
				t.Errorf("MatchesKeyword() = %v, want %v", result, tt.shouldMatch)
			}
		})
	}
}

func TestKeywordMatcher_ValidateKeywords(t *testing.T) {
	matcher := NewKeywordMatcher()

	tests := []struct {
		name      string
		keywords  []string
		shouldErr bool
	}{
		{
			name:      "valid_keywords",
			keywords:  []string{"hello", "hi", "hey"},
			shouldErr: false,
		},
		{
			name:      "empty_keyword",
			keywords:  []string{"hello", "", "hi"},
			shouldErr: true,
		},
		{
			name:      "whitespace_only_keyword",
			keywords:  []string{"hello", "   ", "hi"},
			shouldErr: true,
		},
		{
			name:      "valid_single_keyword",
			keywords:  []string{"hello"},
			shouldErr: false,
		},
		{
			name:      "empty_list",
			keywords:  []string{},
			shouldErr: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := matcher.ValidateKeywords(tt.keywords)
			if (err != nil) != tt.shouldErr {
				t.Errorf("ValidateKeywords() error = %v, shouldErr %v", err, tt.shouldErr)
			}
		})
	}
}

func TestKeywordMatcher_GetNormalizedKeywords(t *testing.T) {
	matcher := NewKeywordMatcher()

	tests := []struct {
		name     string
		keywords []string
		expected []string
	}{
		{
			name:     "normalize_case_and_spaces",
			keywords: []string{" HELLO ", "Hi", "  hey  "},
			expected: []string{"hello", "hi", "hey"},
		},
		{
			name:     "filter_empty_keywords",
			keywords: []string{"hello", "", "  ", "hi"},
			expected: []string{"hello", "hi"},
		},
		{
			name:     "unicode_normalization",
			keywords: []string{" こんにちは ", "Hello"},
			expected: []string{"こんにちは", "hello"},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := matcher.GetNormalizedKeywords(tt.keywords)
			if len(result) != len(tt.expected) {
				t.Errorf("GetNormalizedKeywords() length = %v, want %v", len(result), len(tt.expected))
				return
			}
			for i, keyword := range result {
				if keyword != tt.expected[i] {
					t.Errorf("GetNormalizedKeywords()[%d] = %v, want %v", i, keyword, tt.expected[i])
				}
			}
		})
	}
}

func TestKeywordMatcher_normalizeText(t *testing.T) {
	matcher := NewKeywordMatcher()

	tests := []struct {
		name     string
		input    string
		expected string
	}{
		{
			name:     "trim_and_lowercase",
			input:    " HELLO ",
			expected: "hello",
		},
		{
			name:     "already_normalized",
			input:    "hello",
			expected: "hello",
		},
		{
			name:     "empty_string",
			input:    "",
			expected: "",
		},
		{
			name:     "whitespace_only",
			input:    "   ",
			expected: "",
		},
		{
			name:     "unicode_text",
			input:    " こんにちは ",
			expected: "こんにちは",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := matcher.normalizeText(tt.input)
			if result != tt.expected {
				t.Errorf("normalizeText() = %v, want %v", result, tt.expected)
			}
		})
	}
}