# Auto-Reply (Webhook Trigger)

---

## 1. **Feature Overview**
- **Feature Name:** Auto-Reply (Webhook Trigger)
- **Purpose:**
  - Enables automated, rule-based responses to user or system events (messages, postbacks, follows, beacons, scheduled times) across multiple platforms (LINE, Facebook, Instagram).
  - Supports marketing, support, and engagement automation via configurable triggers and reply messages.
- **Main Use Cases:**
  - Keyword-based auto-reply
  - Scheduled/time-based auto-reply
  - Event-based auto-reply (follow, beacon, postback)
  - Multi-platform messaging (LINE/FB/IG)
  - Tagging members
  - Performance reporting

---

## 2. **Multi-Platform Support** ⭐ NEW

### 2.1. **Supported Platforms**
- **LINE**: Full feature support (legacy system)
- **Facebook Messenger**: MESSAGE events with keyword and time-based triggers
- **Instagram Direct Messages**: MESSAGE events with keyword and time-based triggers

### 2.2. **Unified Trigger Validation**

The new `validate_trigger()` function provides a unified interface for trigger validation across all supported platforms.

**Location:** `python_src/internal/domain/auto_reply/auto_reply.py`

```python
def validate_trigger(
    event: WebhookEvent,
    auto_reply_rules: List[AutoReply],
    current_time: Optional[datetime] = None
) -> Optional[TriggerValidationResult]
```

#### 2.2.1. **Key Features**
- **Platform Agnostic**: Handles LINE, Facebook, and Instagram events through unified `WebhookEvent` interface
- **Priority System**: Keyword triggers (Priority 1) > General time-based triggers (Priority 2)
- **Exact Match Logic**: Implements precise keyword matching as per PRD requirements
- **Schedule Support**: Full support for all schedule types (DAILY, MONTHLY, BUSINESS_HOUR, etc.)
- **Testable**: Supports `current_time` parameter for deterministic testing

#### 2.2.2. **Event Types Supported**
- **MessageEvent**: Text messages from any platform
- **Future**: PostbackEvent, FollowEvent, BeaconEvent (extensible design)

#### 2.2.3. **Trigger Validation Results**
```python
class TriggerValidationResult(BaseModel):
    matched_rule: AutoReply
    trigger_type: TriggerType  # "keyword" | "general_time"
    confidence_score: float    # 1.0 for keyword, 0.8 for time-based
    matched_keyword: Optional[str]
    reply_content: str
    should_send_reply: bool
```

### 2.3. **Platform-Specific Event Models**

#### 2.3.1. **Unified Event Interface**
```python
class WebhookEvent(BaseModel, ABC):
    event_id: str
    channel_type: ChannelType  # LINE | FACEBOOK | INSTAGRAM
    user_id: str
    timestamp: datetime
    
    @abstractmethod
    def get_event_type(self) -> str:
        pass
```

#### 2.3.2. **Message Event Implementation**
```python
class MessageEvent(WebhookEvent):
    content: str
    message_id: str
    
    def get_event_type(self) -> str:
        return "message"
```

### 2.4. **Keyword Matching Logic** ⭐ ENHANCED

#### 2.4.1. **PRD-Compliant Exact Matching**
- **Case Insensitive**: "HELLO" matches "hello"
- **Trim Spaces**: " hello " matches "hello"
- **Exact Match Only**: "hello world" does NOT match "hello"
- **Multiple Keywords**: ["hello", "hi", "hey"] - any one can trigger

#### 2.4.2. **Implementation Details**
```python
def _validate_keyword_triggers(context, active_rules):
    normalized_content = context.event_content.strip().lower()
    
    for rule in keyword_rules:
        for keyword in rule.keywords:
            normalized_keyword = keyword.strip().lower()
            if normalized_content == normalized_keyword:  # Exact match
                return TriggerValidationResult(...)
```

### 2.5. **Time-Based Trigger Enhancements**

#### 2.5.1. **Schedule Types with Full Implementation**
- **DAILY**: Multiple time ranges, midnight crossing support
- **MONTHLY**: Specific days with time ranges
- **BUSINESS_HOUR**: Monday-Friday 9AM-5PM (configurable)
- **NON_BUSINESS_HOUR**: Outside business hours
- **DATE_RANGE**: Seasonal campaigns and limited-time offers

#### 2.5.2. **Priority System for Time Triggers**
1. **MONTHLY** (Highest Priority)
2. **BUSINESS_HOUR**
3. **NON_BUSINESS_HOUR**
4. **DAILY** (Lowest Priority)

#### 2.5.3. **Midnight Crossing Support**
```python
# Example: Night shift coverage 22:00 to 06:00
{
  "trigger_schedule_type": "daily",
  "trigger_schedule_settings": [
    {
      "start_time": "22:00",
      "end_time": "06:00"  # Next day
    }
  ]
}
```

---

## 3. **Test Coverage & Validation** ⭐ NEW

### 3.1. **PRD Test Case Implementation**
All test cases from the PRD have been implemented and validated:

#### 3.1.1. **Story 1: Keyword Reply Logic**
- ✅ **[B-P0-7-Test2]**: Exact keyword match with various cases
- ✅ **[B-P0-7-Test3]**: Keywords with leading/trailing spaces
- ✅ **[B-P0-7-Test4]**: Messages with keyword + other text (no match)
- ✅ **[B-P0-7-Test5]**: Partial matches or variations (no match)

#### 3.1.2. **Story 2: Multiple Keywords Support**
- ✅ **[Multiple-Keywords-Test1]**: Multiple keywords triggering
- ✅ **[Multiple-Keywords-Test2]**: Case insensitive multiple keywords
- ✅ **[Multiple-Keywords-Test3]**: No match for multiple keywords

#### 3.1.3. **Story 3: General Time-based Logic**
- ✅ **[B-P0-6-Test3]**: Daily schedule within time window
- ✅ **[B-P0-6-Test5]**: Business hours schedule

#### 3.1.4. **Story 4: Priority Logic**
- ✅ **[Priority-Test1]**: Keyword over general (same time)
- ✅ **[Priority-Test2]**: General only (no keyword match)
- ✅ **[Priority-Test3]**: Keyword outside general time

#### 3.1.5. **Story 5: Message Content Handling**
- ✅ **[Message-Content-Test1]**: Keyword match triggering
- ✅ **[Message-Content-Test2]**: No keyword match
- ✅ **[Message-Content-Test3]**: General trigger regardless of content

### 3.2. **Test Location**
**File:** `python_src/tests/domain/auto_reply/test_auto_reply.py`
**Class:** `TestValidateTrigger`
**Coverage:** 20 test cases, 100% pass rate

### 3.3. **Running Tests**
```bash
cd python_src
python -m pytest tests/domain/auto_reply/test_auto_reply.py::TestValidateTrigger -v
```

---

## 4. **Enhanced Reply Content Generation** ⭐ NEW

### 4.1. **Intelligent Reply Generation**
The new system includes smart reply content generation based on trigger type and context:

```python
def _generate_reply_content(rule, trigger_type, matched_keyword=None):
    if trigger_type == TriggerType.KEYWORD:
        # Predefined keyword responses
        return keyword_responses.get(matched_keyword, fallback_response)
    
    elif trigger_type == TriggerType.GENERAL_TIME:
        # Time-aware responses
        current_hour = datetime.now().hour
        if 5 <= current_hour < 12:
            return "Good morning! Thank you for your message..."
        # ... other time-based responses
```

### 4.2. **Supported Reply Types**
- **Keyword-Specific**: Tailored responses for each keyword
- **Time-Aware**: Different responses based on time of day
- **Fallback**: Generic responses for unmapped keywords
- **Rule-Based**: Custom responses based on rule configuration

---

## 5. **Migration from Legacy System**

### 5.1. **Legacy vs New Implementation**
| Aspect | Legacy (LINE only) | New (Multi-platform) |
|--------|--------------------|-----------------------|
| **Platforms** | LINE only | LINE + Facebook + Instagram |
| **Event Handling** | Platform-specific | Unified `WebhookEvent` interface |
| **Keyword Matching** | Partial matching | Exact matching (PRD compliant) |
| **Schedule Support** | Basic implementation | Full schedule types with priority |
| **Testing** | Limited coverage | Comprehensive PRD-based tests |
| **Reply Generation** | Static responses | Intelligent, context-aware |

### 5.2. **Backward Compatibility**
- Legacy `keyword_auto_reply()` and `general_auto_reply()` functions maintained
- New `validate_trigger()` function can be adopted incrementally
- Existing LINE webhook handlers continue to work

### 5.3. **Migration Path**
1. **Phase 1**: Deploy new models and functions alongside legacy
2. **Phase 2**: Update webhook handlers to use `validate_trigger()`
3. **Phase 3**: Add Facebook and Instagram webhook endpoints
4. **Phase 4**: Deprecate legacy functions

---

## 6. **Architecture Decisions & Design Patterns**

### 6.1. **Domain-Driven Design**
- **Domain Models**: Clear separation of concerns
- **Event Abstraction**: Platform-agnostic event handling
- **Value Objects**: Immutable trigger results
- **Repositories**: Data access abstraction

### 6.2. **Strategy Pattern**
- **Platform Handlers**: Different strategies for each platform
- **Schedule Validators**: Different validation strategies for each schedule type
- **Reply Generators**: Different generation strategies for each trigger type

### 6.3. **Factory Pattern**
- **Event Factory**: Creates appropriate event objects from raw webhooks
- **Schedule Factory**: Creates schedule validators based on type
- **Reply Factory**: Creates appropriate reply content based on context

---

## 7. **Performance Considerations**

### 7.1. **Optimization Strategies**
- **Early Exit**: Priority system allows early termination
- **Caching**: Rule caching to avoid repeated database queries
- **Lazy Evaluation**: Schedule validation only when needed
- **Batch Processing**: Multiple rules processed efficiently

### 7.2. **Scalability Features**
- **Platform Independence**: New platforms can be added easily
- **Rule Prioritization**: Efficient rule matching
- **Schedule Optimization**: TODO: Advanced data structures for large rule sets
- **Memory Efficiency**: Minimal object creation in hot paths

---

# Auto-Reply (Legacy System)

> **⚠️ LEGACY SYSTEM NOTICE**  
> This document describes the **legacy LINE-only auto-reply system**. A new **unified multi-channel architecture** is being implemented for LINE/Facebook/Instagram with IG Story-specific features.  
> 
> **For new development:** See [Auto-Reply New Architecture KB](./auto_reply_250716.md)  
> **Current status:** Legacy system in maintenance mode, new system handles multi-platform with IG Story support  
> **Future plan:** Merge documentation when new system reaches full production maturity

---

## Migration & Documentation Plan

### **Current Status:**
- **Legacy System:** LINE-only auto-reply, production-stable (this document)
- **Unified System:** Multi-channel with IG Story features, backend complete, UI in development
- **Documentation Strategy:** Separate KBs during transition, merge when unified system reaches full maturity

### **Future Merge Criteria:**
Documentation will be consolidated when:
- [ ] IG Story UI implementation complete
- [ ] Instagram webhook integration deployed to production  
- [ ] Production stability proven (3+ months)
- [ ] Feature parity validated across all platforms
- [ ] Legacy migration technical plan finalized

### **Development Guidelines:**
- **Legacy System:** Maintenance mode only, no new features
- **New Development:** Use new system ([Auto-Reply New Architecture KB](./auto_reply_250716.md))

---



