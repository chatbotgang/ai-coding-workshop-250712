# ai-coding-workshop-250712

This is an internal workshop held at Crescendo Lab that demonstrates how to improve product velocity and quality by leveraging AI agentic coding practices.

## AI Coding Practices at CL

At Crescendo Lab:
- We **don't practice vibe coding**. 
- We **provide AI with as much context as possible** to guide them in developing and validating product features efficiently.
- We believe **AI coding capability is driven and scoped by humans** who are skilled in domain and software knowledge, make technical decisions, and have the capability to evaluate AI's coding outputs.
- We learn when to leverage agentic coding and when to code hands-on (with auto-complete) by ourselves.

# Case Study - Extend Line Auto-Reply to Omnichannel Auto-Reply

Auto-Reply (Keyword + General):
<video width="640" height="480" controls>
  <source src="https://drive.google.com/uc?export=download&id=150uIbDx_ZageXc-ofMVt62PUgs_gFq36" type="video/mp4">
  Your browser does not support the video tag.
</video>

Auto-Reply (IG Story-Specific):
<video width="640" height="480" controls>
  <source src="https://drive.google.com/uc?export=download&id=10L-x17h9JHhErp4OtBG0Kc7y8s7QpGny" type="video/mp4">
  Your browser does not support the video tag.
</video>

- Auto-Reply Intro: [CH](https://crescendolab.zendesk.com/hc/zh-tw/articles/48047855114137-%E5%8A%9F%E8%83%BD%E8%AA%AA%E6%98%8E-Omnichannel-%E8%87%AA%E5%8B%95%E5%9B%9E%E6%87%89-%E5%90%AB-FB-IG-LINE), EN
- Auto-Reply Tutorials: [CH](https://crescendolab.zendesk.com/hc/zh-tw/articles/48502467789209-%E8%A8%AD%E5%AE%9A%E6%95%99%E5%AD%B8-Omnichannel-%E8%87%AA%E5%8B%95%E5%9B%9E%E6%87%89), [EN](https://crescendolab.zendesk.com/hc/en-us/articles/39949866982425-Tutorials-NEW-Auto-reply)


## Review given PRD, KB, and domain models

- PRD: [here](./spec/prd.md)
- KB: [here](./legacy/kb/auto_reply.md)
- Domain models
    - go: [here](./go_src/internal/domain/auto_reply/)
    - python: here 

## 1. Rewrite Brownfield Features with AI

Build Omni (LINE/FB) Auto-Reply trigger logic with agentic coding.

### 1.1 Design interface of trigger validator and generate task plan with AI

```
@dev_with_kb.prompt.md 
@auto_reply.md 
@auto_reply.go 
@prd.md
@webhook_trigger.go 

I would like to develop feature 1 - LINE/FB/IG Auto-Reply (Keyword + General) in the given PRD.
Before jumping into implementation, please review the given materials clearly and ask questions, one at a time.

Before implementing any function, I would like to design the interface (input and output) of functions first.
```

**FAQ**

**Q1: What is the scope of Feature 1 that we're implementing?**

Ans: Feature 1 focuses on LINE/FB/IG Auto-Reply with Keyword + General triggers. We're implementing the core trigger validation logic that determines when auto-replies should be sent. The scope includes keyword-based triggers (exact match with case insensitive + trim spaces) and general time-based triggers (daily, monthly, business hours, non-business hours). We're NOT implementing constraint validation, reply validation, message sending, or welcome message logic in this phase.

**Q2: What is the main interface design approach we chose?**

Ans: We chose approach (B) - a method on the AutoReplyChannelSettingAggregate struct that encapsulates the validation logic:

```go
func (a *AutoReplyChannelSettingAggregate) ValidateTrigger(event WebhookEvent) (*AutoReplyTriggerSetting, error)
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


### 1.2 Ask AI to implement trigger validator based on PRD + KB

```
All good now.
Implement the function based on the plan and PRD.
```

### 1.3 Ask AI to write tests to validate functionality based on given test cases

```
Validate the function by tests. The tests should be written based on test cases in PRD and add the test case number.
```

### 1.4 Refactor codeline whatever you want manually or with AI

@jalex: TDD time. Enjoy it.

### 1.5 Update feature changes to KB

```
@kb_management.prompt.md @auto_reply.md 
update kb 
```

AI may create a new KB because of major architecture changes.

## 2. Extend Feature with AI

Continuing to the case study - Rewrite Brownfield Features with AI, add IG Story-specific feature to Auto-Reply with agentic coding.

### 2.1 Discuss feature changes and generate task plan with AI

```
@ig_story.json @prd.md 
@auto_reply_250707.md 
@dev_with_kb.prompt.md
@auto_reply.md  
@/auto_reply 

Continuing the work of FB/IF auto-reply implmentation, let's implement Feature 2: IG Story-Specific Auto-Reply in PRD.

Before jumping into implementation, please review the given materials clearly and ask questions, one at a time.

Before implementing any function, I would like to discuss design first.
```

**FAQ**

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
IG Story Keyword (Priority 1 - highest)
IG Story General (Priority 2)
General Keyword (Priority 3)
General Time-based (Priority 4 - lowest)
Within each level, triggers are sorted by AutoReplyPriority field (higher number = higher priority).

**Q6: How do we validate IG Story triggers?**

Ans: IG Story triggers require two conditions: (1) the standard trigger condition (keyword match or schedule match), and (2) the incoming ig_story_id must match one of the configured ig_story_ids. Both conditions must be met for the trigger to activate.

### 2.2 Ask AI to extend trigger validator based on PRD + KB

```
All good now.
Extend the function based on the plan and PRD.
```

### 2.3 Ask AI to write tests to validate the new functionality based on given test cases

Same as [1.3](#13-ask-ai-to-write-tests-to-validate-functionality-based-on-given-test-cases)

### 2.4 Refactor codeline whatever you want manually or with AI

Same as [1.4](#14-refactor-codeline-whatever-you-want-manually-or-with-ai)

### 2.5 Update feature changes to KB

Same as [1.5](#15-update-feature-changes-to-kb)
