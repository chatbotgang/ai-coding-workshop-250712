# Knowledge Base Management During Architecture Changes

## Overview

This document provides guidelines for managing Knowledge Base (KB) updates during significant architecture changes, based on lessons learned from the auto-reply unified architecture implementation.

## Decision Framework: When to Create Separate vs. Update Existing KB

### **Create Separate KB When:**
- **Major Architecture Changes** (>50% of system redesigned)
- **Multi-phase Implementation** (backend complete, frontend in progress)
- **Dual System Operation** (legacy + new system coexisting)
- **Cross-platform Expansion** (single platform → multi-platform)
- **New Domain Models** (significant changes to core entities)
- **Implementation Timeline > 3 months**

### **Update Existing KB When:**
- **Minor Feature Additions** (<20% of system changed)
- **Bug Fixes or Performance Improvements**
- **API Endpoint Changes** (same core logic)
- **UI/UX Updates** (no backend changes)
- **Configuration Changes**
- **Implementation Timeline < 1 month**

## Separate KB Approach (Major Changes)

### Phase 1: Create Unified KB
1. **File Naming Convention:**
   ```
   .ai/kb/{feature}_{yymmdd}.md   # New architecture (date of design)
   .ai/kb/{feature}.md            # Legacy system (add deprecation notice)
   ```

2. **Unified KB Structure:**
   ```markdown
   # {Feature} New Architecture ({Date})
   
   ## 1. Architecture Overview
   - Dual system explanation
   - Migration strategy
   - Key differences from legacy
   
   ## 2. Terminology Mapping
   | User-Facing Term | Technical Implementation | API Field | Legacy Term |
   
   ## 3. Major Workflows
   - New unified flow (primary)
   - Legacy flow (maintenance mode)
   
   ## 4. Domain Models & API Contracts
   - New domain models with code examples
   - API request/response examples
   - Service layer architecture
   
   ## 5. Service Layer Architecture
   - Service dependencies
   - Business logic orchestration
   - Integration points
   
   ## 6. Cross-Platform Integration
   - Platform-specific handling
   - Event mapping
   - Message format differences
   
   ## 7. Migration & Compatibility
   - Backward compatibility strategy
   - Data migration approach
   - Performance considerations
   
   ## 8. Testing Strategy
   - Test coverage approach
   - Integration testing
   - Performance testing
   
   ## 9. Development Guidelines
   - Architecture principles
   - Code patterns
   - Best practices
   ```

3. **Legacy KB Updates:**
   ```markdown
   # {Feature} (Legacy System)
   
       > **⚠️ LEGACY SYSTEM NOTICE**  
    > This document describes the **legacy {platform}-only system**. A new **multi-channel architecture** is being implemented.  
    > 
    > **For new development:** See [{Feature} New Architecture KB](./{feature}_{yymmdd}.md)  
    > **Current status:** Legacy system in maintenance mode  
    > **Future plan:** Merge documentation when new system reaches full production maturity
   
   [... existing content ...]
   
   ## Migration & Documentation Plan
   
   ### **Current Status:**
   - **Legacy System:** {Platform}-only, production-stable (this document)
   - **Unified System:** Multi-channel, backend complete, UI in development
   - **Documentation Strategy:** Separate KBs during transition, merge when unified system reaches full maturity
   
   ### **Future Merge Criteria:**
   Documentation will be consolidated when:
   - [ ] Unified system UI implementation complete
   - [ ] {Platform} migration technical plan finalized  
   - [ ] Production stability proven (3+ months)
   - [ ] Feature parity validated
   
   ### **Development Guidelines:**
   - **Legacy System:** Maintenance mode only, no new features
       - **New Development:** Use new system ([{Feature} New Architecture KB](./{feature}_{yymmdd}.md))
   ```

### Phase 2: Maintain Dual Documentation
- **Update new architecture KB** for new development
- **Minimal updates to legacy KB** (bug fixes only)
- **Cross-reference between documents**
- **Track merge criteria progress**

### Phase 3: Consolidation (When Ready)
- **Merge criteria met** (UI complete, migration plan ready, stability proven)
- **Create consolidated KB** combining both systems
- **Archive legacy KB** with historical reference
- **Update all cross-references**

## Direct Update Approach (Minor Changes)

### When to Use:
- Small feature additions
- Bug fixes
- API changes without architecture impact
- UI updates
- Performance improvements

### Update Process:
1. **Identify affected sections** in existing KB
2. **Update in-place** with clear change markers
3. **Add version/date stamps** for significant updates
4. **Update cross-references** if needed
5. **Test documentation accuracy** against implementation

### Change Markers:
```markdown
## Section Title ⭐ **UPDATED: 2025-01-XX**

**Changes:**
- Added new API endpoint `/api/v2/feature/`
- Updated response format to include `new_field`
- Deprecated `old_field` (will be removed in v3.0)

[... updated content ...]
```

## Best Practices

### Documentation Quality
1. **Accuracy First:** Ensure KB matches actual implementation
2. **User-Centric:** Use terminology that matches user-facing interfaces
3. **Code Examples:** Include real API requests/responses from codebase
4. **Cross-References:** Link to actual implementation files
5. **Test Coverage:** Document which tests cover which features

### Maintenance
1. **Regular Reviews:** Monthly KB accuracy checks during active development
2. **Implementation Sync:** Update KB immediately after major code changes
3. **Stakeholder Input:** Include PM/Design feedback on user-facing terminology
4. **Version Control:** Use git to track KB evolution alongside code

### Communication
1. **Status Updates:** Clear implementation status in KB headers
2. **Migration Timelines:** Document expected consolidation dates
3. **Development Guidelines:** Clear guidance for developers on which system to use
4. **Cross-Team Coordination:** Ensure frontend/backend teams use same KB

## Templates

### Deprecation Notice Template
```markdown
> **⚠️ LEGACY SYSTEM NOTICE**  
> This document describes the **legacy {platform}-only {feature} system**. A new **unified multi-channel architecture** is being implemented for {platforms}.  
> 
 > **For new development:** See [{Feature} New Architecture KB](./{feature}_{yymmdd}.md)  
 > **Current status:** Legacy system in maintenance mode, new system handles {new_platforms}  
 > **Future plan:** Merge documentation when new system reaches full production maturity
```

### Implementation Status Template
```markdown
## Implementation Status Summary

### ✅ **COMPLETED**
- **{Component}**: {Description}
- **{Component}**: {Description}

### 🔄 **IN PROGRESS**
- **{Component}**: {Description}
- **{Component}**: {Description}

### 📋 **REMAINING TASKS**
- **{Component}**: {Description}
- **{Component}**: {Description}

### 📊 **Test Coverage Summary**
**{Layer} Test Coverage: {percentage}% ({count}+ tests)**
- ✅ **{Component}**: {Description}
- ✅ **{Component}**: {Description}
```

## Checklist for KB Updates

### Before Starting
- [ ] Assess scope of changes (major vs. minor)
- [ ] Determine if separate KB is needed
- [ ] Review existing KB structure
- [ ] Identify affected stakeholders

### During Implementation
- [ ] Update KB alongside code changes
- [ ] Verify terminology with PM/Design
- [ ] Include real code examples
- [ ] Test API examples work
- [ ] Cross-reference implementation files

### After Completion
- [ ] Review KB accuracy
- [ ] Update cross-references
- [ ] Notify stakeholders of changes
- [ ] Plan consolidation timeline (if applicable)

## Example: Auto-Reply Architecture Change

**Situation:** LINE-only auto-reply → Unified multi-channel (LINE/FB/IG)

**Decision:** Separate KB approach
- **Reason:** Major architecture change, dual system operation, 6+ month timeline
- **Files Created:** 
  - `.ai/kb/auto_reply_250611.md` (new architecture)
  - Updated `.ai/kb/auto_reply.md` (legacy with deprecation notice)

**Key Success Factors:**
- Clear terminology mapping between legacy and new systems
- Comprehensive API documentation with real examples
- Detailed migration strategy and timeline
- Cross-platform integration documentation
- Test coverage mapping to PRD requirements

**Lessons Learned:**
- Start with separate KB for major changes
- Use real API examples from codebase
- Include implementation status tracking
- Plan consolidation criteria upfront
- Maintain both KBs during transition period 