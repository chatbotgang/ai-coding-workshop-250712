"""Tests for keyword matching functionality.

These tests verify PRD requirements for keyword matching:
- [B-P0-7-Test2]: Exact keyword matching with various cases
- [B-P0-7-Test3]: Keyword with leading/trailing spaces
- [B-P0-7-Test4]: Message contains keyword but with other text (should not match)
- [B-P0-7-Test5]: Partial match or close variation (should not match)
- [Multiple-Keywords-Test1]: Multiple keywords triggering
- [Multiple-Keywords-Test2]: Multiple keywords with different casing
- [Multiple-Keywords-Test3]: Message doesn't match any keywords
"""

import pytest
from internal.domain.auto_reply.keyword_matcher import match_keywords


class TestKeywordMatcher:
    """Test cases for keyword matching function."""
    
    def test_prd_b_p0_7_test2_exact_keyword_various_cases(self):
        """[PRD B-P0-7-Test2] Test exact keyword matching with various cases.
        
        Expected Result: Auto-reply triggered when message exactly matches keyword, regardless of case.
        """
        keywords = ["hello"]
        
        # Case insensitive matching
        assert match_keywords(keywords, "hello") is True
        assert match_keywords(keywords, "HELLO") is True  
        assert match_keywords(keywords, "Hello") is True
        assert match_keywords(keywords, "HeLLo") is True
    
    def test_prd_b_p0_7_test3_keyword_with_leading_trailing_spaces(self):
        """[PRD B-P0-7-Test3] Test keyword with leading/trailing spaces.
        
        Expected Result: Leading and trailing spaces trimmed, auto-reply triggered if core keyword matches.
        """
        keywords = ["hello"]
        
        # Spaces should be trimmed
        assert match_keywords(keywords, " hello ") is True
        assert match_keywords(keywords, "  hello  ") is True
        assert match_keywords(keywords, "\thello\t") is True
        assert match_keywords(keywords, "\nhello\n") is True
        
        # Combined with case insensitive
        assert match_keywords(keywords, " HELLO ") is True
        assert match_keywords(keywords, "  Hello  ") is True
    
    def test_prd_b_p0_7_test4_message_contains_keyword_plus_other_text(self):
        """[PRD B-P0-7-Test4] Test message containing keyword plus other text.
        
        Expected Result: Auto-reply is NOT triggered as match must be exact.
        """
        keywords = ["hello"]
        
        # Should NOT match when keyword is part of larger text
        assert match_keywords(keywords, "hello world") is False
        assert match_keywords(keywords, "say hello") is False
        assert match_keywords(keywords, "hello there friend") is False
        assert match_keywords(keywords, "well hello") is False
        assert match_keywords(keywords, "hello!") is False
        assert match_keywords(keywords, "hello.") is False
    
    def test_prd_b_p0_7_test5_partial_match_or_close_variation(self):
        """[PRD B-P0-7-Test5] Test partial match or close variation.
        
        Expected Result: Auto-reply is NOT triggered.
        """
        keywords = ["hello"]
        
        # Partial matches should NOT work
        assert match_keywords(keywords, "hell") is False
        assert match_keywords(keywords, "hel") is False
        assert match_keywords(keywords, "ello") is False
        
        # Close variations should NOT work
        assert match_keywords(keywords, "helo") is False
        assert match_keywords(keywords, "helllo") is False
        assert match_keywords(keywords, "heello") is False
        assert match_keywords(keywords, "hellp") is False
    
    def test_prd_multiple_keywords_test1_multiple_keywords_triggering(self):
        """[PRD Multiple-Keywords-Test1] Test multiple keywords triggering.
        
        Expected Result: Auto-reply triggered when any configured keyword matches exactly.
        """
        keywords = ["hello", "hi", "hey"]
        
        # Each keyword should match
        assert match_keywords(keywords, "hello") is True
        assert match_keywords(keywords, "hi") is True  
        assert match_keywords(keywords, "hey") is True
        
        # Non-matching text should not trigger
        assert match_keywords(keywords, "goodbye") is False
        assert match_keywords(keywords, "greetings") is False
    
    def test_prd_multiple_keywords_test2_different_casing(self):
        """[PRD Multiple-Keywords-Test2] Test multiple keywords with different casing.
        
        Expected Result: Auto-reply triggered due to case-insensitive matching.
        """
        keywords = ["hello", "hi", "hey"]
        
        # Case insensitive matching for multiple keywords
        assert match_keywords(keywords, "HELLO") is True
        assert match_keywords(keywords, "HI") is True
        assert match_keywords(keywords, "HEY") is True
        assert match_keywords(keywords, "Hello") is True
        assert match_keywords(keywords, "Hi") is True
        assert match_keywords(keywords, "Hey") is True
    
    def test_prd_multiple_keywords_test3_no_match_any_keywords(self):
        """[PRD Multiple-Keywords-Test3] Test message that doesn't match any keywords.
        
        Expected Result: Auto-reply is NOT triggered.
        """
        keywords = ["hello", "hi", "hey"]
        
        # None of these should match
        assert match_keywords(keywords, "goodbye") is False
        assert match_keywords(keywords, "welcome") is False
        assert match_keywords(keywords, "greetings") is False
        assert match_keywords(keywords, "yo") is False
        assert match_keywords(keywords, "sup") is False
        
        # Partial matches should not work
        assert match_keywords(keywords, "hello world") is False
        assert match_keywords(keywords, "hi there") is False
        assert match_keywords(keywords, "hey buddy") is False
    
    def test_empty_or_none_keywords(self):
        """Test edge cases with empty or None keywords."""
        # None keywords should return False
        assert match_keywords(None, "hello") is False
        assert match_keywords(None, "any message") is False
        
        # Empty keywords list should return False
        assert match_keywords([], "hello") is False
        assert match_keywords([], "any message") is False
    
    def test_empty_message_content(self):
        """Test edge cases with empty message content."""
        keywords = ["hello", "hi"]
        
        # Empty message should not match
        assert match_keywords(keywords, "") is False
        assert match_keywords(keywords, "   ") is False  # Only spaces
        assert match_keywords(keywords, "\t\n") is False  # Only whitespace
    
    def test_whitespace_only_keyword(self):
        """Test edge case with whitespace-only keyword."""
        keywords = ["hello", "  ", "hi"]  # Middle keyword is just spaces
        
        # Should still work for valid keywords
        assert match_keywords(keywords, "hello") is True
        assert match_keywords(keywords, "hi") is True
        
        # Empty message (after trim) should not match whitespace keyword
        assert match_keywords(keywords, "  ") is False