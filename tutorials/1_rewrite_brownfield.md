# Rewrite Brownfield Features with AI

Build omnichannel auto-reply trigger logic with agentic coding.

## Background

We are implementing a new auto-reply system on top of the existing LINE auto-reply, based on the [PRD](./../spec/prd-part1.md).

### The Challenge: **Real-World Development Complexity**
However, there are several challenges that mirror **typical brownfield development**:
1. **Incomplete Context**: The new PRD focuses on illustrating feature changes. It doesn't cover existing feature behavior, such as internal priority within general time-based settings and how the current system architecture looks.
2. **Legacy Coupling**: The current LINE auto-reply is highly coupled with the LINE webhook processing flow, making it difficult to extend to an omnichannel architecture.

**Sound familiar?** This is exactly what engineers face daily - unclear requirements and tightly-coupled legacy systems.

### Our Strategic Approach: **Context, Control, Critique in Action**
Therefore, our strategic development approach demonstrates the **3 C's**:

1. **Context**: Collect knowledge base (KB) to gain high-level architecture design knowledge from the legacy codebase and tribal knowledge.
2. **Control**: Combine PRD and KB as comprehensive context, and leverage it to guide AI in building new auto-reply flows from scratch.
3. **Critique**: Switch between the new and old architecture and flows using a feature flag in production to ensure compatibility and release reliability.

**This tutorial shows you how to navigate ambiguity systematically - the same process you'll use on real projects!**


## Tutorials

### 0. Pre-read given materials

In this section, we focus on implementing core trigger match logic only. Both [PRD](./../spec/prd-part1.md) and [KB](./../legacy/kb/) are prepared. Please review all materials carefully before jumping into solution design and development.

### 1. Design interface of trigger validator and generate task plan with AI

Before jumping into implementation, we always discuss feature scope and key designs (domain models and function interfaces) with AI first.
By using the provided prompt ([dev_with_kb.prompt.md](./../.ai/prompt/dev_with_kb.prompt.md)), AI will ask you several questions to clarify scope and unclear hidden assumptions. **Answer based on your best understanding** - you'll refine through the development process.

Go Example:
```
@dev_with_kb.prompt.md 
@auto_reply.md 
@auto_reply.go 
@prd-part1.md
@webhook_trigger.go 

I would like to develop feature 1 - LINE/FB/IG Auto-Reply (Keyword + General) in the given PRD.
Before jumping into implementation, please review the given materials clearly and ask questions, one at a time.

Before implementing any function, I would like to design the interface (input and output) of functions first.
```


Python Example:
```
@dev_with_kb.prompt.md 
@auto_reply.md 
@auto_reply.py 
@prd-part1.md
@webhook_trigger.py

I would like to develop feature 1 - LINE/FB/IG Auto-Reply (Keyword + General) in the given PRD.
Before jumping into implementation, please review the given materials clearly and ask questions, one at a time.

Before implementing any function, I would like to design the interface (input and output) of functions first.
```

#### What to Expect (This is Normal!)
😕 **You WILL feel confused** when AI asks questions about the product spec - this is realistic!  
🤔 **You WON'T know the "correct" answers** - neither do most engineers on day 1 of a new feature!  
💪 **Your job**: Make reasonable decisions with incomplete information  
📋 **Real skill**: Learning to guide AI through ambiguity - the same skill you need daily in production

#### Decision-Making Under Uncertainty
When AI asks questions, assess your confidence level:
- 🟢 **High confidence (80%+)**: Answer directly based on your understanding
- 🟡 **Medium confidence (50-80%)**: "I think X based on the PRD, but let's validate as we build..."
- 🔴 **Low confidence (<50%)**: "I'm not sure, let's try Y and iterate if needed"

**Remember**: Your decisions don't need to be perfect - they need to be reasonable starting points for iteration.

Note: If AI's questions feel completely overwhelming and you need some structured guidance to get started, the [FAQ](#faq) provides common question-answer pairs from previous workshops.

### 2. Ask AI to implement trigger validator based on PRD + KB

Example:
```
All good now.
Implement the function based on the plan, PRD, and KB.
```

#### Validation Mindset (You Don't Need Domain Expertise!)
When AI delivers code, instead of asking "Is this correct?" (which requires deep domain knowledge), ask these **process-focused** questions:

✅ **"Does this match my understanding from Step 1?"** - Compare with the interface design you agreed on  
✅ **"Can I trace through the logic?"** - Follow the code flow even without knowing all business rules  
✅ **"Does the structure make sense?"** - Are functions well-organized and named clearly?  

**Remember**: Your job isn't to be a domain expert overnight - it's to be a thoughtful engineering partner to AI.

Note: If you want to compare the result with a reference solution, check the [cheat sheet](#cheat-sheet) - but do this AFTER forming your own assessment.

### 3. Ask AI to write tests to validate functionality based on given test cases

All critical happy path and edge use cases are provided in the PRD. Ask your AI agent to write corresponding tests to ensure all use cases are covered.

```
Validate the function by tests. The tests should be written based on test cases in PRD and add the test case number.
```

```
Run the tests for validating functionality.
```

#### Building Confidence Through Testing
This is where you gain confidence in your implementation! Tests are your **feedback loop** - they tell you if your decisions in Steps 1-2 were reasonable.

#### What Makes Good Tests
✅ **Traceable to Requirements**: Each test should map back to a specific use case in the PRD  
✅ **Clear Pass/Fail**: You should be able to tell immediately if something works  
✅ **Edge Case Coverage**: Test both happy paths and boundary conditions  
✅ **Readable Names**: Test names should tell you what behavior is being verified


### 4. Refactor and iterate based on test results

This is where you see if your uncertainty navigation in Steps 1-2 led to a working solution. **Don't worry if things need adjustment** - this is the normal TDD cycle!

```
Based on the test results, let's refine the implementation to handle [specific failing test case].
```

**Remember**: This back-and-forth between assumptions, implementation, and validation is the core AI agentic development skill you're learning!

#### Refactoring Mindset
Instead of thinking "I got it wrong," think:
- **"I learned something new from the test results"**
- **"Now I can make a more informed decision"**
- **"This is exactly how real development works"**

### 5. Update feature changes to KB

Now you'll document what you learned through the uncertainty navigation process. This KB update captures both the **technical decisions** and the **reasoning behind them**.

#### What to Include in KB Updates
✅ **Interface decisions you made** and why  
✅ **Key assumptions** that turned out to be correct/incorrect  
✅ **Testing insights** that refined your understanding  
✅ **Implementation patterns** that emerged  

This isn't just documentation - it's **context for future AI collaboration** on related features.

```
@kb_management.prompt.md @auto_reply.md 
update kb 
```

#### Reflection Questions
- What would you tell someone starting this feature tomorrow?
- Which of your initial assumptions were most/least accurate?

Note: AI may create a new KB due to architecture changes - that's normal! Fresh KB better captures evolved design patterns.

## Appendix

### Cheat sheet
- [go](./../cheat_sheet/go/1_rewrite_brownfield/)
- [python](./../cheat_sheet/python/1_rewrite_brownfield/)

### FAQ

Here are some frequently asked questions that AI may ask in step 1:

**Q1: What is the scope of Feature 1 that we're implementing?**

Ans: Feature 1 focuses on LINE/FB/IG Auto-Reply with Keyword + General triggers. We're implementing the core trigger validation logic that determines when auto-replies should be sent. The scope includes keyword-based triggers (exact match with case insensitive + trim spaces) and general time-based triggers (daily, monthly, business hours, non-business hours). We're NOT implementing constraint validation, reply validation, message sending, or welcome message logic in this phase.

**Q2: What is the main interface design approach we chose?**

Ans: We chose approach (B) - a method on the AutoReplyChannelSettingAggregate struct that encapsulates the validation logic:

```go
func (a *AutoReplyChannelSettingAggregate) ValidateTrigger(event WebhookEvent) (*AutoReplyTriggerSetting, error)
```

```python
def validate_trigger(
    trigger_settings: list[WebhookTriggerSetting],
    message_event: WebhookEvent,
    business_hour_checker: BusinessHourChecker | None = None,
    organization_id: int | None = None,
    bot_timezone: str | None = None,
    organization_timezone: str | None = None,
):
    ...
```

This aggregate holds all trigger settings for a specific bot/channel and manages the validation logic with business rules.

**Q3: What webhook events do we handle and what's the input structure?**

Ans: We only handle MESSAGE events for now. The input structure is:
```go
type WebhookEvent struct {
    EventType   string               // "message" (only type we handle)
    MessageText *string              // For keyword matching
    Timestamp   time.Time            // For time-based triggers
    ChannelType organization.BotType // LINE, FB, IG (using existing BotType)
}
```
```python
class WebhookEvent(BaseModel, ABC):
    """Abstract base class for webhook events."""

    event_id: str = Field(..., description="Unique event identifier")
    channel_type: ChannelType = Field(..., description="Channel where event originated")
    user_id: str = Field(..., description="User identifier from the channel")
    timestamp: datetime = Field(..., description="Event timestamp")

class MessageEvent(WebhookEvent):
    """Message webhook event."""

    content: str = Field(..., description="Message content/text")
    message_id: str = Field(..., description="Unique message identifier")
```
We don't need to worry about IGStoryID at this moment.

**Q4: What does the AutoReplyChannelSettingAggregate contain?**

Ans: The aggregate contains:
- BotID: Channel identifier
- TriggerSettings: All auto-reply trigger settings for the bot
- BusinessHours: Business hour configuration (using organization.BusinessHour)
- Timezone: Timezone for time-based calculations (e.g., "Asia/Taipei")

**Q5: What is the priority system for trigger validation?**

Ans: We have a two-level priority system:
- Trigger Type Priority: Keyword triggers (higher) → General time-based triggers (lower)
- Within Keyword Triggers: Sorted by AutoReply's priority field (higher number = higher priority, e.g., priority 10 > priority 5)
- Within General Time Triggers:
  - First by schedule type: Monthly → Business Hour → Non-Business Hour → Daily
  - Then by AutoReply's priority field within the same schedule type (higher number = higher priority)
- The key correction is that higher priority number = higher priority (not lower number = higher priority as initially assumed). This means:
  - Priority 10 beats Priority 5
  - Priority 100 beats Priority 50
  - When sorting, we'll sort in descending order by priority number to get the highest priority first

**Q6: What is the validation method's return behavior?**

Ans: The ValidateTrigger method returns the first matching trigger setting based on priority, or nil if no match. It follows the "first match wins" principle - only the highest priority matching trigger is returned, not all matching triggers.

**Q7: Why did we create a new domain model?**

Ans: We created AutoReplyTriggerSetting - a merged domain model that combines AutoReply and WebhookTriggerSetting into a single entity. This provides easy access to both trigger configuration and the crucial priority information needed for the two-level sorting system, avoiding the need for complex lookups during validation.

**Q8: What are the key features of the AutoReplyTriggerSetting model?**

Ans: The model includes:
- AutoReply fields: ID, Name, Status, EventType, Priority (key for sorting), Keywords
- WebhookTriggerSetting fields: ID, BotID, Enable, EventType, TriggerCode, ScheduleType, etc.
- Helper methods: IsActive(), IsKeywordTrigger(), IsGeneralTimeTrigger()
- Priority field: AutoReplyPriority is the key field used for sorting within trigger types

**Q9: How does keyword matching work?**

Ans: Keyword matching follows these rules:
- Case insensitive: "hello" matches "HELLO"
- Trim spaces: "hello" matches " hello "
- Exact match: "hello" does NOT match "hello world"
- Multiple keywords: ["hello", "hi"] - incoming "hi" matches
- Normalization: Keywords are normalized before comparison using normalizeKeyword() function
