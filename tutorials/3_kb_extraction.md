# KB Extraction with AI

Extract critical system knowledge from brownfield codebase with agentic coding.

## Background

We have demonstrated the power of Knowledge Base (KB) in previous sections - how it enables AI to understand complex legacy systems and build new features with minimal guesswork. Now it's time to practice how to extract KB from your own codebase.

The key challenges in KB extraction include:
1. **Hidden Assumptions**: Legacy codebases often contain implicit business rules and architectural decisions that are not documented.
2. **Tribal Knowledge**: Critical system knowledge often exists only in developers' minds, not in code or documentation.
3. **Complex Interconnections**: Understanding how different features interact and depend on each other requires deep system knowledge.

Therefore, our strategic approach for KB extraction is:
1. Work in small teams to leverage collective knowledge and cross-validate findings.
2. Use AI-powered extraction prompts to systematically capture all aspects of a feature.
3. Answer all clarifying questions during extraction to ensure no hidden assumptions remain.
4. Create comprehensive, navigable documentation that enables both humans and AI to work with the feature safely.

## Tutorials

### 0. Pre-read given materials

In this section, we focus on extracting comprehensive knowledge from a critical feature in your codebase. The KB extraction prompt ([kb_extraction.prompt.md](./../.ai/prompt/kb_extraction.prompt.md)) is prepared to guide you through systematic knowledge capture. Please review the prompt carefully to understand the extraction framework before starting.

### 1. Form teams and select target feature

**Team Formation:**
- Form groups of 2-3 people
- Ensure each team has diverse knowledge of the codebase
- Mix senior and junior developers for knowledge transfer

**Feature Selection Criteria:**
Choose a critical feature that meets these criteria:
- **Business Critical**: Core to your product's value proposition
- **Complex**: Has multiple workflows, integrations, or edge cases
- **Well-Understood**: At least one team member has deep knowledge of the feature
- **Poorly Documented**: Limited or outdated documentation exists

Example features to consider:
- User authentication and authorization system
- Payment processing workflow
- Notification/messaging system
- Data synchronization between services
- Reporting and analytics pipeline

### 2. Extract KB using AI-powered prompt

Use the provided KB extraction prompt to systematically capture feature knowledge.

Example:
```
@kb_extraction.prompt.md
@/path/to/your/feature/code
@existing_docs_if_any.md

I want to extract comprehensive knowledge about our [FEATURE_NAME] feature from the codebase.

This feature is critical because [BUSINESS_IMPORTANCE].
Current documentation is [CURRENT_STATE - e.g., "minimal", "outdated", "scattered"].

Please analyze the provided code and extract knowledge following the KB extraction framework.
```

**Key Guidelines:**
- **Answer ALL Questions**: When AI asks clarifying questions, provide detailed answers
- **No Guessing**: If you're unsure about something, explicitly state "unclear" or "needs investigation"
- **Cross-Validate**: Team members should verify each other's answers
- **Include Examples**: Provide concrete examples, payloads, and code snippets when possible

### 3. Collaborative review and refinement

**Review Process:**
1. **Individual Review**: Each team member reviews the extracted KB independently
2. **Team Discussion**: Discuss findings, fill gaps, and resolve conflicts
3. **Stakeholder Validation**: If possible, validate with product owners or other teams
4. **Iterative Refinement**: Refine the KB based on feedback

**Quality Checklist:**
- [ ] All 11 sections of the KB framework are addressed
- [ ] Code references are accurate and clickable
- [ ] Mermaid diagrams are included for complex workflows
- [ ] Edge cases and technical traps are documented
- [ ] Integration points with other features are clear
- [ ] Testing gaps are identified


### 4. Validate KB effectiveness

Test the extracted KB by having someone unfamiliar with the feature use it to:
- Understand the feature's purpose and workflows
- Identify extension points for new requirements
- Debug a simulated issue
- Estimate effort for a hypothetical change

**Success Criteria:**
- New team member can understand the feature in < 2 hours
- AI can answer specific questions about the feature using the KB
- KB enables safe modification without extensive code archaeology

## Appendix

### KB Quality Examples

**Good KB Characteristics:**
- **Actionable**: Enables concrete next steps
- **Navigable**: Easy to find relevant information
- **Code-Linked**: Direct references to implementation
- **Assumption-Free**: No hidden or implicit knowledge
- **Diagram-Rich**: Visual representations of complex flows

**Poor KB Characteristics:**
- **Vague**: Generic descriptions without specifics
- **Outdated**: References to old code or deprecated features
- **Incomplete**: Missing critical sections or workflows
- **Assumption-Heavy**: Requires prior knowledge to understand

### Common KB Extraction Pitfalls

**1. Scope Creep**
- **Problem**: Trying to document everything instead of focusing on the selected feature
- **Solution**: Stick to the feature boundaries; reference other KBs for related features

**2. Implementation Over Intent**
- **Problem**: Documenting what the code does instead of why it exists
- **Solution**: Focus on business purpose, user flows, and architectural decisions

**3. Missing Edge Cases**
- **Problem**: Only documenting happy path scenarios
- **Solution**: Actively search for error handling, timeouts, and boundary conditions

**4. Tribal Knowledge Gaps**
- **Problem**: Assuming everyone knows the "obvious" things
- **Solution**: Document everything, especially things that seem obvious

### FAQ

**Q1: How long should KB extraction take?**

Ans: Plan for 4-8 hours of active work spread over 2-3 days. This includes initial extraction (2-3 hours), team review (1-2 hours), refinement (1-2 hours), and documentation (1 hour). Don't rush - quality KB saves significant time later.

**Q2: What if we discover the feature is more complex than expected?**

Ans: This is common and valuable! Consider breaking it into multiple KBs (e.g., "User Auth - Core Flow" and "User Auth - Advanced Features") or adjust scope to focus on the most critical workflows first.

**Q3: How do we handle features that span multiple services?**

Ans: Create a primary KB for the main feature and reference integration points with other services. Include sequence diagrams showing cross-service interactions. Consider creating separate integration-focused KBs for complex multi-service workflows.

**Q4: What if team members disagree on how something works?**

Ans: This reveals important knowledge gaps! Document the disagreement, investigate together by tracing through the code, and test the behavior if possible. These discoveries often uncover the most valuable insights.

**Q5: Can we use this process for new features?**

Ans: Absolutely! For new features, the KB becomes design documentation. Work through the 11 sections during design phase to ensure you've considered all aspects before implementation.

**Q6: How do we maintain KB freshness over time?**

Ans: Honestly? KB gets outdated and we take it easy. It happens to everyone. The key is accepting that KB maintenance is imperfect and focusing on what matters most:
- Update KB when you're actually working on the feature (not retroactively)
- If new team members find gaps, fix those specific sections
- Don't stress about keeping everything perfect - outdated KB is still better than no KB
- When KB becomes seriously misleading, that's when you prioritize updates