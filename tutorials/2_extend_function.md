# Extend Feature with AI

Add IG Story-specific feature to auto-reply with agentic coding.

## Background

Continuing the case study from "Rewrite Brownfield Features with AI," we are now implementing Feature 2: IG Story-Specific Auto-Reply based on the [PRD](./../spec/prd-part2.md).

### The Challenge: **System Evolution Complexity**
This feature extends the existing LINE/FB/IG auto-reply system with Instagram Story-specific triggers that have higher priority than regular triggers. The key challenges mirror **real feature extension work**:

1. **Architectural Growth**: We need to extend the existing 2-level priority system to a 4-level system that includes IG Story triggers at the top.
2. **New Logic Integration**: We need to implement logic to match incoming story IDs against configured story IDs in the trigger settings.
3. **Compatibility Preservation**: The extension must maintain compatibility with existing trigger validation logic **without breaking anything**.

**Recognize this scenario?** This is classic feature evolution - adding complexity while maintaining stability.

### Our Strategic Approach: **Building on Success**
Therefore, our strategic development approach builds on Tutorial 1 success:

1. **Context**: Leverage the existing knowledge base (KB) and architecture from the previous implementation.
2. **Control**: Extend the current trigger validation system to support IG Story-specific matching with clear decision points.
3. **Critique**: Implement the 4-level priority system while maintaining existing functionality through comprehensive testing.

**This tutorial teaches you system evolution with AI - taking working code and safely extending it with new complexity!**

## Tutorials

### 0. Pre-read given materials

In this section, we focus on extending the existing trigger validation system to support IG Story-specific auto-reply. Both [PRD](./../spec/prd-part2.md) and [KB](./../legacy/kb/) are prepared, along with the IG Story specification [ig_story.json](./../spec/ig_story.json). Please review all materials carefully before jumping into solution design and development.

### 1. Discuss feature changes and generate task plan with AI

Before jumping into implementation, we always discuss feature scope and key design changes (domain models and function interfaces) with AI first.
By using the provided prompt ([dev_with_kb.prompt.md](./../.ai/prompt/dev_with_kb.prompt.md)), AI will ask you several questions to clarify scope and unclear hidden assumptions. **Answer based on your Tutorial 1 experience** and new requirements.

Go Example:
```
@dev_with_kb.prompt.md 
@auto_reply.md 
@auto_reply.go 
@prd-part2.md
@webhook_trigger.go
@ig_story.json

I would like to develop feature 2 - IG Story-Specific Auto-Reply in the given PRD.

Before implementing any function, I would like to discuss design first.
```

Python Example:
```
@dev_with_kb.prompt.md 
@auto_reply.md 
@auto_reply.py 
@prd-part2.md
@webhook_trigger.py
@ig_story.json

I would like to develop feature 2 - IG Story-Specific Auto-Reply in the given PRD.

Before implementing any function, I would like to discuss design first.
```

#### Building on Previous Experience
😊 **You have working code** from Tutorial 1 as a foundation  
🔄 **Extension vs. new build** - you're modifying existing logic, not starting from scratch  
📈 **Increased complexity** - 4-level priority system instead of 2-level  

#### Decision-Making for Extensions
When AI asks about extending the existing system:
- 🟢 **High confidence**: Leverage patterns from Tutorial 1 that worked well  
- 🟡 **Medium confidence**: "This is similar to X from Tutorial 1, but with Y difference..."  
- 🔴 **Low confidence**: "I'm not sure how this interacts with our existing logic, let's try Z"  

**Remember**: You're learning how to **evolve** systems with AI - a critical production skill!

Note: If AI's questions feel completely overwhelming and you need some structured guidance to get started, the [FAQ](#faq) provides common question-answer pairs from previous workshops.

### 2. Ask AI to extend trigger validator based on PRD + KB

Example:
```
All good now.
Extend the function based on the plan, PRD, and KB.
```

#### Extension Validation Mindset
When extending existing code, your validation approach builds on Tutorial 1 skills:

✅ **"Does this preserve existing behavior?"** - Your Tutorial 1 tests should still pass  
✅ **"Can I trace the new priority logic?"** - Follow how 4-level priority extends the 2-level system  
✅ **"Do the extensions make structural sense?"** - Are new components following established patterns?  

**Remember**: Your job is to be a thoughtful engineering partner for system evolution, not an IG Story domain expert.

Note: If you want to compare the result with a reference solution, check the [cheat sheet](#cheat-sheet) - but do this AFTER forming your own assessment.

### 3. Ask AI to write tests to validate functionality based on given test cases

All critical happy path and edge use cases are provided in the PRD. Ask your AI agent to write comprehensive tests covering both new and existing behavior.

```
Validate the function by tests. The tests should be written based on test cases in PRD and add the test case number.
Also ensure all existing functionality from Tutorial 1 still works correctly.
```

```
Run the tests for validating functionality.
```

#### Testing Extensions vs. New Features
Testing extensions requires validating **both** new functionality and **backward compatibility**.

#### What Makes Good Extension Tests
✅ **Regression tests**: Ensure existing Tutorial 1 functionality still works  
✅ **Integration tests**: Verify new priority system works with existing triggers  
✅ **New feature tests**: Validate IG Story-specific behavior from the PRD  
✅ **Priority conflict tests**: Ensure 4-level priority resolves correctly

### 4. Refactor and iterate based on test results

Extensions often surface **interaction bugs** that weren't obvious during planning. **Don't worry if things need adjustment** - this is the normal extension development cycle!

```
Based on test results, let's refine the priority system to handle [specific case] while maintaining Tutorial 1 behavior.
```

**Remember**: This balance between new functionality and system stability is the core system evolution skill you're learning!

#### Extension Refactoring Mindset
Instead of asking "Did I break something?" ask:
- **"Is the priority system easy to understand?"**  
- **"Can I trace from a story ID match to the final trigger?"**  
- **"What would I change if I were writing this?"**

### 5. Update feature changes to KB

Your KB update now captures how a **simple system evolved** into a **complex system** - valuable knowledge for future development!

#### What to Include in Extension KB Updates
✅ **How the 4-level priority system works** and why each level exists  
✅ **Integration patterns** that worked well between new and existing code  
✅ **Extension challenges** you discovered and how you resolved them  
✅ **Testing strategies** that caught integration bugs  

This isn't just documentation - it's **context for future system evolution** with AI.

```
@kb_management.prompt.md @auto_reply.md 
update kb 
```

#### Reflection Questions
- How did adding complexity change your understanding of the original system?  
- What extension patterns emerged that could apply to other features?  

Note: AI should enhance the KB from Tutorial 1 with extension patterns - creating comprehensive knowledge for the entire auto-reply system!

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
