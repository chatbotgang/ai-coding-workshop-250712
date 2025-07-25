# AI Workshop: PRD (User Stories & Test Cases)

## Product Feature Overview

### Feature Summary
The **FB/IG Auto-Reply Feature** enables automated responses for Facebook Messenger and Instagram direct messages, including replies triggered by IG Story interactions.
This spec focuses on implementing the core trigger logic that determines when auto-replies should be sent.

### Key Capabilities
- **Multi-Channel Support**: LINE, Facebook Messenger, Instagram DMs
- **Trigger Types**: Keyword-based, General (Time-based), IG Story-specific
  - Keyword triggers → match exact keywords in message content
  - General triggers → match based on schedule/timing
  - IG Story triggers → match based on story ID context
- **Priority System**: 4-level hierarchy ensuring most specific triggers take precedence
  - Priority 1: IG Story Keyword (highest)
  - Priority 2: IG Story General
  - Priority 3: General Keyword
  - Priority 4: General Time-based (lowest)
- **Keyword Normalization**
  - Stored: "hello" → Incoming: "HELLO" → Match: True (case insensitive)
  - Stored: "hello" → Incoming: " hello " → Match: True (trim spaces)
  - Stored: "hello" → Incoming: "hello world" → Match: False (exact match)
  - Multiple keywords: ["hello", "hi"] → Incoming: "hi" → Match: True
- **Event Handling**: MESSAGE events only

### Business Value
- **Operational Efficiency**: Automate responses across multiple channels from one platform
- **Lead Nurturing**: Provide immediate responses to customer inquiries
- **Multi-Channel Expansion**: Support beyond LINE to Facebook and Instagram ecosystems

---

## Auto-Reply Trigger Logic Implementation

**Scope**: Implement `validate_trigger()` function with priority system  
**Excluded**: Constraint validation, reply validation, message sending, welcome message logic

---

## Feature 2: IG Story-Specific Auto-Reply

### Story 6: IG Story Keyword Logic

- [ ] [P1] As a Marketer, I want to create Keyword Replies specifically for replies to Instagram Stories, so that I can provide contextually relevant responses to story interactions. [B-P1-18-Keyword]
    - [ ] **[BE]** [B-P1-18-Test7]: Create a specific IG Story Keyword Reply rule. Test sending a message that matches the keyword but is NOT a reply to one of the selected stories.
        - Expected Result: The auto-reply is NOT triggered.
    - [ ] **[BE]** [B-P1-18-Test8a]: Create a specific IG Story Keyword Reply rule. Test sending a message that is a reply to one of the selected stories and matches the keyword.
        - Expected Result: The auto-reply IS triggered.
    - [ ] **[BE]** [IG-Story-Keyword-Test1]: Create an IG Story Keyword Reply rule for story "story123" with keyword "hello". Send a message with keyword "hello" and ig_story_id "story123".
        - Expected Result: The IG story keyword reply is triggered.
    - [ ] **[BE]** [IG-Story-Keyword-Test2]: Create an IG Story Keyword Reply rule for story "story123" with keyword "hello". Send a message with keyword "hello" and ig_story_id "story456".
        - Expected Result: The IG story keyword reply is NOT triggered (wrong story).
    - [ ] **[BE]** [IG-Story-Keyword-Test3]: Create an IG Story Keyword Reply rule for story "story123" with keyword "hello". Send a message with keyword "hello" but no ig_story_id.
        - Expected Result: The IG story keyword reply is NOT triggered (no story context).

### Story 7: IG Story General Logic

- [ ] [P1] As a Marketer, I want to create General Replies specifically for replies to Instagram Stories, so that I can provide time-based responses to story interactions. [B-P1-18-General]
    - [ ] **[BE]** [B-P1-18-Test8b]: Create a specific IG Story General Reply rule. Test sending a message that is a reply to one of the selected stories and is within the schedule.
        - Expected Result: The auto-reply IS triggered.
    - [ ] **[BE]** [IG-Story-General-Test1]: Create an IG Story General Reply rule for story "story123" with daily 9-17 schedule. Send a message at 14:00 with ig_story_id "story123".
        - Expected Result: The IG story general reply is triggered.
    - [ ] **[BE]** [IG-Story-General-Test2]: Create an IG Story General Reply rule for story "story123" with daily 9-17 schedule. Send a message at 20:00 with ig_story_id "story123".
        - Expected Result: The IG story general reply is NOT triggered (outside schedule).
    - [ ] **[BE]** [IG-Story-General-Test3]: Create an IG Story General Reply rule for story "story123" with daily 9-17 schedule. Send a message at 14:00 with ig_story_id "story456".
        - Expected Result: The IG story general reply is NOT triggered (wrong story).

### Story 8: IG Story Priority over General

- [ ] [P1] As a Marketer, I want IG story-specific triggers to have higher priority than general triggers, so that story-specific responses take precedence when both conditions are met. [IG-Story-Priority]
    - [ ] **[BE]** [B-P1-18-Test9]: Create both a story-specific keyword rule and a general keyword rule. Test sending a message that matches both rules (story reply + keyword).
        - Expected Result: Only the story-specific auto-reply is triggered.
    - [ ] **[BE]** [IG-Story-Priority-Test1]: Create both an IG story keyword rule and a general keyword rule for the same keyword. Send a message with the keyword and matching story ID.
        - Expected Result: Only the IG story keyword reply is triggered, not the general keyword reply.
    - [ ] **[BE]** [IG-Story-Priority-Test2]: Create both an IG story general rule and a general time-based rule for the same schedule. Send a message during scheduled time with matching story ID.
        - Expected Result: Only the IG story general reply is triggered, not the general time-based reply.

### Story 9: IG Story Multiple Keywords

- [ ] [P1] As a Marketer, I want to configure multiple keywords for IG story-specific auto-reply rules, so that I can trigger story-specific responses with different trigger words. [IG-Story-Multiple-Keywords]
    - [ ] **[BE]** [IG-Story-Multiple-Keywords-Test1]: Create an IG Story Keyword Reply rule with multiple keywords (e.g., ["hello", "hi"]) for story "story123". Test triggering with each keyword and the correct story ID.
        - Expected Result: The IG story auto-reply is triggered for any of the configured keywords when sent as a reply to the specified story.
    - [ ] **[BE]** [IG-Story-Multiple-Keywords-Test2]: Create an IG Story Keyword Reply rule with multiple keywords for story "story123". Test triggering with one of the keywords but wrong story ID.
        - Expected Result: The IG story auto-reply is NOT triggered.

### Story 10: Complete Priority System

- [ ] [P1] As a system, I want to implement a complete priority system for all trigger types, so that the most specific triggers always take precedence. [Complete-Priority]
    - Note: Priority order: IG story keyword → IG story general → general keyword → general time-based
    - [ ] **[BE]** [Complete-Priority-Test1]: Create all 4 types of rules (IG story keyword, IG story general, general keyword, general time-based). Send a message that could match all rules.
        - Expected Result: Only the IG story keyword reply is triggered (highest priority).
    - [ ] **[BE]** [Complete-Priority-Test2]: Create IG story general, general keyword, and general time-based rules. Send a message during scheduled time with story ID but non-matching keyword.
        - Expected Result: Only the IG story general reply is triggered (priority 2).
    - [ ] **[BE]** [Complete-Priority-Test3]: Create general keyword and general time-based rules. Send a message with matching keyword during scheduled time but no story ID.
        - Expected Result: Only the general keyword reply is triggered (priority 3).
    - [ ] **[BE]** [Complete-Priority-Test4]: Create only general time-based rule. Send a message during scheduled time with no keyword and no story ID.
        - Expected Result: Only the general time-based reply is triggered (priority 4).

### Story 11: IG Story Exclusion Logic

- [ ] [P1] As a system, I want to ensure IG story-specific settings are excluded from general trigger validation, so that story-specific rules don't interfere with general message processing. [IG-Story-Exclusion]
    - [ ] **[BE]** [IG-Story-Exclusion-Test1]: Create an IG story-specific keyword setting with keyword "hello". Send a normal message with keyword "hello" (no IG story ID).
        - Expected Result: The auto-reply is NOT triggered because the setting is IG story-specific.
    - [ ] **[BE]** [IG-Story-Exclusion-Test2]: Create a normal keyword setting without IG story configuration. Send a normal message with matching keyword.
        - Expected Result: The auto-reply IS triggered because the setting is not IG story-specific.
    - [ ] **[BE]** [IG-Story-Exclusion-Test3]: Create both IG story-specific and general keyword settings for the same keyword. Send a message with keyword but no story ID.
        - Expected Result: Only the general keyword setting is triggered, not the IG story-specific one.