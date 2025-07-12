# Extend Feature with AI

Add IG Story-specific feature to auto-reply with agentic coding.

## Background

Continuing the case study from "Rewrite Brownfield Features with AI," we are now implementing Feature 2: IG Story-Specific Auto-Reply based on the [PRD](./../spec/prd-part2.md).

This feature extends the existing LINE/FB/IG auto-reply system with Instagram Story-specific triggers that have higher priority than regular triggers. The key challenges include:

1. **Priority System Extension**: We need to extend the existing 2-level priority system to a 4-level system that includes IG Story triggers at the top.
2. **Story ID Matching**: We need to implement logic to match incoming story IDs against configured story IDs in the trigger settings.
3. **Backward Compatibility**: The extension must maintain compatibility with existing trigger validation logic.

Therefore, our strategic development approach is:
1. Leverage the existing knowledge base (KB) and architecture from the previous implementation.
2. Extend the current trigger validation system to support IG Story-specific matching.
3. Implement the 4-level priority system while maintaining existing functionality.

## Tutorials

### 0. Pre-read given materials

In this section, we focus on extending the existing trigger validation system to support IG Story-specific auto-reply. Both [PRD](./../spec/prd-part2.md) and [KB](./../legacy/kb/) are prepared, along with the IG Story specification [ig_story.json](./../spec/ig_story.json). Please review all materials carefully before jumping into solution design and development.

### 1. Discuss feature changes and generate task plan with AI

Before jumping into implementation, we always discuss feature scope and key design changes (domain models and function interfaces) with AI first.
By using the provided prompt ([dev_with_kb.prompt.md](./../.ai/prompt/dev_with_kb.prompt.md)), AI will ask you several questions to clarify scope and unclear hidden assumptions. **Answer all the questions** to ensure no guesswork during development.

Example:
```
@ig_story.json @prd-part2.md 
@auto_reply_250707.md 
@dev_with_kb.prompt.md
@auto_reply.md  
@/auto_reply 

Continuing the work of FB/IG auto-reply implementation, let's implement Feature 2: IG Story-Specific Auto-Reply in PRD.

Before jumping into implementation, please review the given materials clearly and ask questions, one at a time.

Before implementing any function, I would like to discuss design first.
```

Note: If you are not familiar with product scope or context, use the [FAQ](#faq) directly.

### 2. Ask AI to extend trigger validator based on PRD + KB

Example:
```
All good now.
Extend the function based on the plan, PRD, and KB.
```

Note: If you are struggling with how an acceptable solution may look, check the [cheat sheet](#cheat-sheet) for references.

### 3. Ask AI to write tests to validate functionality based on given test cases

All critical happy path and edge use cases are provided in the PRD. Please ask your AI agent to write corresponding tests to ensure all use cases are passed without any tricks.

```
Validate the function by tests. The tests should be written based on test cases in PRD and add the test case number.
```

### 4. Refactor codeline whatever you want manually or with AI

TDD time. Enjoy it.

### 5. Update feature changes to KB

Use the provided prompt ([kb_management.prompt.md](./../.ai/prompt/kb_management.prompt.md)) to ask the AI agent to update the KB based on the new implementation.

```
@kb_management.prompt.md @auto_reply.md 
update kb 
```

Note: AI should add context to the KB created in section 1 - Rewrite Brownfield Features with AI.

## Appendix

### Cheat sheet
- [go](./../cheat_sheet/go/2_extend_feature/)
- [python](./../cheat_sheet/python/2_extend_feature/)

### FAQ

Here are some frequently asked questions that AI may ask in step 1:

**Q1: What is the scope of Feature 2 that we're implementing?**

Ans: Feature 2 focuses on IG Story-Specific Auto-Reply triggers that extend the existing LINE/FB/IG Auto-Reply system. We're implementing IG Story Keyword and IG Story General triggers that have higher priority than regular triggers. The scope includes story ID matching logic and integration with the existing 4-level priority system. We're NOT implementing message sending, constraint validation, or UI components in this phase.

**Q2: How do we identify that a message is a reply to an Instagram Story?**

Ans: The webhook event will include an ig_story_id field that we match against configured story IDs. We don't need to query external APIs or extract metadata - the story ID is provided directly in the webhook payload.

**Q3: How are IG Story IDs configured in the auto-reply settings?**

Ans: IG Story IDs are stored as a simple array field (ig_story_ids: []string) in the WebhookTriggerSetting model. Only IG bot types can have valid IG Story settings. The presence of this array determines if a trigger is IG Story-specific.

**Q4: How do IG Story triggers relate to existing trigger types?**

Ans: We keep existing event types (EventTypeMessage, EventTypeTime) and use the presence of ig_story_ids array to determine if it's an IG Story-specific trigger. IG Story Keyword uses EventTypeMessage + ig_story_ids, while IG Story General uses EventTypeTime + ig_story_ids.

**Q5: What is the complete priority system with IG Story triggers?**

Ans: The 4-level priority system is:
- IG Story Keyword (Priority 1 - highest)
- IG Story General (Priority 2)
- General Keyword (Priority 3)
- General Time-based (Priority 4 - lowest)

Within each level, triggers are sorted by AutoReplyPriority field (higher number = higher priority).

**Q6: How do we validate IG Story triggers?**

Ans: IG Story triggers require two conditions: (1) the standard trigger condition (keyword match or schedule match), and (2) the incoming ig_story_id must match one of the configured ig_story_ids. Both conditions must be met for the trigger to activate.
