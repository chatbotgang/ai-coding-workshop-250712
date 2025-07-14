---
mode: agent
---

# Document Update Guidelines from Chat Context

## Purpose
This prompt guides AI agents on how to properly update documentation based on chat conversations, ensuring accuracy, appropriate scope, and clear separation between different types of documentation.

## Document Types and Scope

### 1. Development Conventions (`.cursor/rules/go.mdc`, `.cursor/rules/python.mdc`)
**Purpose**: Technical patterns, architectural guidelines, and coding standards
**Include**:
- Architectural patterns (Clean Architecture, service patterns)
- Naming conventions for code (classes, methods, models)
- Code organization and structure
- Testing patterns and standards
- Error handling strategies
- Performance optimization guidelines
- Development workflow and methodology

**Avoid**:
- Specific business logic or domain rules
- Implementation details of particular features
- Overly specific examples that might not generalize
- Business domain terminology explanations

### 2. Knowledge Base (`python_src/kb`, `go_src/kb`)
**Purpose**: Business domain knowledge, entities, and their relationships
**Include**:
- Business entities and their definitions
- Entity relationships and dependencies
- Business rules and constraints
- Domain-specific terminology
- Key operations and their business purposes
- Data models and their business significance

**Avoid**:
- Technical implementation details
- Code patterns and conventions
- API endpoint specifications
- Specific validation rules or technical constraints
- Development workflow instructions

## Update Principles

### 1. Accuracy Over Completeness
- Only document patterns that are actually established in the codebase
- Avoid making absolute statements unless they are universally true
- Use qualifying language ("often", "typically", "case-by-case") when appropriate
- Verify claims against existing code before documenting

### 2. Appropriate Abstraction Level
- **Development Conventions**: Focus on reusable patterns and principles
- **Knowledge Base**: Focus on business concepts and domain understanding
- Avoid mixing technical implementation with business domain knowledge

### 3. Flexibility Over Rigidity
- Document patterns as guidelines, not absolute rules
- Acknowledge when practices vary case-by-case
- Avoid overly prescriptive language that might constrain future development
- Provide context for when patterns should or shouldn't be applied

### 4. Avoid Redundancy
- Don't duplicate content between documents
- Reference other documents when appropriate
- Keep each document focused on its specific purpose
- Remove or consolidate overlapping sections

## Common Mistakes to Avoid

### 1. Overgeneralization
❌ "Always wrap data in `{"data": [...]}`"
✅ "Consider consistent response formats for API endpoints"

### 2. Too Specific Examples
❌ Adding detailed sections about specific features (e.g., "Member Search Functionality")
✅ Documenting general patterns that apply across features

### 3. Wrong Document Placement
❌ Putting technical patterns in the knowledge base
❌ Putting business rules in development conventions
✅ Clear separation based on document purpose

### 4. Absolute Statements Without Context
❌ "Domain Models: `{Action}{Domain}{Type}`"
✅ "Domain Models: Case-by-case, can be simple entities or action-specific"

## Update Process

### 0. Initial Planning
- **Update One Document at a Time**: Focus on completing one document fully before moving to the next
- **Seek Clarification**: If you have any confusion or disagreement about what should be updated or how, ask the user for clarification before proceeding
- **Confirm Approach**: When updating multiple documents, confirm the order and approach with the user

### 1. Before Making Changes
- Read the existing document to understand current structure and tone
- Identify which type of document you're updating
- Verify patterns exist in the codebase before documenting them
- Check for potential redundancy with other documents

### 2. While Making Changes
- Maintain consistency with existing formatting and structure
- Use clear, concise language appropriate for the document type
- Provide context and reasoning for patterns when helpful
- Include examples only when they illustrate broader principles

### 3. After Making Changes
- Review for accuracy and completeness
- Ensure no redundancy with other documents
- Verify the document maintains its focused purpose
- Check that examples are representative, not overly specific

## Key Questions to Ask

Before documenting any pattern:
1. **Is this pattern actually established in the codebase?**
2. **Does this belong in this document type?**
3. **Is this too specific to be generally useful?**
4. **Am I making absolute statements that might not always be true?**
5. **Does this duplicate information in another document?**
6. **Would this constraint future development inappropriately?**

## Success Criteria

A well-updated document should:
- ✅ Accurately reflect established patterns in the codebase
- ✅ Maintain appropriate scope for its document type
- ✅ Provide guidance without being overly prescriptive
- ✅ Avoid redundancy with other documents
- ✅ Use clear, professional language
- ✅ Include context and reasoning for recommendations
- ✅ Be useful for future development decisions

## Remember
The goal is to create documentation that helps developers understand and maintain consistency, not to constrain or over-specify implementation details. Focus on capturing the essence of good patterns while maintaining flexibility for future needs.