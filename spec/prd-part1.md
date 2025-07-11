# AI Workshop: PRD (User Stories & Test Cases)

## Product Feature Overview

### Feature Summary
The **FB/IG Auto-Reply Feature** enables automated responses for Facebook Messenger and Instagram direct messages.
This spec focuses on implementing the core trigger logic that determines when auto-replies should be sent.

### Key Capabilities
- **Multi-Channel Support**: LINE, Facebook Messenger, Instagram DMs
- **Trigger Types**: Keyword-based, General (Time-based)
  - Keyword triggers → match exact keywords in message content
  - General triggers → match based on schedule/timing
- **Priority System**: 2-level hierarchy ensuring most specific triggers take precedence
  - Priority 1: General Keyword
  - Priority 2: General Time-based (lowest)
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

## Feature 1: LINE/FB/IG Auto-Reply (Keyword + General)

### Story 1: Keyword Reply Logic

- [ ] [P0] As a Marketer/Customer Service agent, I want to create Keyword Reply auto-replies for LINE/FB/IG DMs with exact match (case insensitive + trim head and tail spaces) triggering, so that I can respond to specific queries based on keywords. [B-P0-7]
    - [ ] **[BE]** [B-P0-7-Test2]: Create a Keyword Reply for a LINE/FB/IG channel with a specific keyword and test triggering it with the exact keyword (various cases).
        - Expected Result: An auto-reply is triggered when a message exactly matches the keyword, regardless of case.
    - [ ] **[BE]** [B-P0-7-Test3]: Test triggering with the keyword surrounded by leading/trailing spaces.
        - Expected Result: Leading and trailing spaces are trimmed, and the auto-reply is triggered if the core keyword matches exactly.
    - [ ] **[BE]** [B-P0-7-Test4]: Test triggering with a message that contains the keyword but also includes other text.
        - Expected Result: The auto-reply is NOT triggered as the match must be exact.
    - [ ] **[BE]** [B-P0-7-Test5]: Test triggering with a message that is a partial match or close variation of the keyword.
        - Expected Result: The auto-reply is NOT triggered.

### Story 2: Multiple Keywords Support

- [ ] [P0] As a Marketer/Customer Service agent, I want to configure multiple keywords for a single auto-reply rule, so that I can trigger the same response with different trigger words. [Multiple-Keywords]
    - [ ] **[BE]** [Multiple-Keywords-Test1]: Create a Keyword Reply rule with multiple keywords (e.g., ["hello", "hi", "hey"]) and test triggering with each keyword.
        - Expected Result: The auto-reply is triggered when any of the configured keywords matches exactly.
    - [ ] **[BE]** [Multiple-Keywords-Test2]: Test triggering with a keyword that matches one of multiple keywords but with different casing.
        - Expected Result: The auto-reply is triggered due to case-insensitive matching.
    - [ ] **[BE]** [Multiple-Keywords-Test3]: Test triggering with a message that doesn't match any of the multiple keywords.
        - Expected Result: The auto-reply is NOT triggered.

### Story 3: General Time-based Logic

- [ ] [P0] As a Marketer/Customer Service agent, I want to create General Reply auto-replies with time/date-based scheduling for LINE/FB/IG DMs, so that I can provide automatic responses during specific hours or dates. [B-P0-6]
    - [ ] **[BE]** [B-P0-6-Test3]: Create a General Reply for a LINE/FB/IG channel with a Daily schedule and test triggering it during the defined time window.
        - Expected Result: An auto-reply is sent when a message is received within the scheduled daily time.
    - [ ] **[BE]** [B-P0-6-Test4]: Create a General Reply for a LINE/FB/IG channel with a Monthly schedule and test triggering it on a scheduled date and time.
        - Expected Result: An auto-reply is sent when a message is received on a scheduled monthly date and time.
    - [ ] **[BE]** [B-P0-6-Test5]: Create a General Reply for a LINE/FB/IG channel based on Business hours and test triggering it during/outside configured reply hours.
        - Expected Result: An auto-reply is sent based on whether the message is received during reply hours or non-reply hours.

### Story 4: Priority Logic (Keyword over General)

- [ ] [P0] As a system, I want keyword replies to have higher priority than general time-based replies, so that specific keyword matches always take precedence over general timing rules. [Priority-Logic]
    - [ ] **[BE]** [Priority-Test1]: Create both a Keyword Reply rule and a General Reply rule for the same channel. Send a message that matches the keyword during the general reply time window.
        - Expected Result: Only the Keyword Reply is triggered, not the General Reply.
    - [ ] **[BE]** [Priority-Test2]: Create both a Keyword Reply rule and a General Reply rule for the same channel. Send a message that doesn't match the keyword during the general reply time window.
        - Expected Result: Only the General Reply is triggered.
    - [ ] **[BE]** [Priority-Test3]: Create both a Keyword Reply rule and a General Reply rule for the same channel. Send a message that matches the keyword outside the general reply time window.
        - Expected Result: Only the Keyword Reply is triggered.

### Story 5: Message Content Handling

- [ ] [P0] As a system, I want to handle message content appropriately for keyword and general triggers, so that the right triggers are evaluated based on message content. [Message-Content]
    - [ ] **[BE]** [Message-Content-Test1]: Create a Keyword Reply rule and test triggering with a message containing the keyword.
        - Expected Result: The keyword reply is triggered when the message contains the exact keyword.
    - [ ] **[BE]** [Message-Content-Test2]: Test sending a message without any keyword to a channel with keyword rules.
        - Expected Result: No keyword reply is triggered when the message has no matching keyword.
    - [ ] **[BE]** [Message-Content-Test3]: Create a General Reply rule and test triggering with any message content during scheduled time.
        - Expected Result: The general reply is triggered regardless of message content when schedule matches.
