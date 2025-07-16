"""Keyword matching functionality for auto-reply triggers."""


def match_keywords(keywords: list[str] | None, message_content: str) -> bool:
    """Check if message content matches any of the provided keywords.
    
    Args:
        keywords: List of keywords to match against, or None
        message_content: The message content to check
        
    Returns:
        True if message matches any keyword (exact match, case insensitive, spaces trimmed)
        False if no keywords provided or no match found
        
    Keyword matching rules (per PRD):
    - Case insensitive: "hello" matches "HELLO"
    - Trim spaces: "hello" matches " hello "  
    - Exact match: "hello" does NOT match "hello world"
    - Multiple keywords: ["hello", "hi"] - any match returns True
    """
    if not keywords:
        return False
    
    # Normalize message content: trim spaces and convert to lowercase
    normalized_content = message_content.strip().lower()
    
    # Check if any keyword matches exactly
    return any(keyword.lower() == normalized_content for keyword in keywords)