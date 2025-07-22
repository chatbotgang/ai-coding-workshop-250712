# Personal Rules for AI

Build short, concrete rules that make AI fit your development habits and prevent common issues.

> **Note**: This feature is absolutely the same as Cursor Memory. Personal rules in Cursor IDE are implemented through the memory system, which stores your preferences and applies them consistently across all chat sessions. Whether you call it "personal rules," "memory," or "workspace rules," the underlying functionality is identical - it's Cursor's way of remembering and enforcing your development preferences automatically.

## Background

Even the most advanced AI can miss important preferences when rules are too verbose or buried in documentation. Personal rules with highest priority ensure AI consistently follows your specific development habits and avoids recurring mistakes.

The key challenges with AI rules include:
1. **Rule Fatigue**: Long rules get ignored or partially followed
2. **Priority Confusion**: Important preferences get lost among general guidelines
3. **Context Loss**: AI forgets specific habits during long conversations
4. **Repetitive Issues**: Same mistakes keep happening despite corrections

Therefore, our strategic approach for personal rules is:
1. Create short, concrete rules with highest priority declaration
2. Focus on recurring issues and strong personal preferences
3. Use forced confirmation patterns for critical workflows
4. Test and refine rules based on actual AI behavior

## Tutorials

### 1. Copy the example rules to target place

Copy the following example rules to your AI assistant rules file:

**For Cursor** (`.cursor/rules/personal.mdc`):

```markdown
---
alwaysApply: true
---

## This instruction applies to all files in the repository.
## This instruction has the highest priority over other instructions.

- Never run migration commands like `python manage.py migrate`.
- The only way of running test is `pytest {test_file}`.
- Use `git --no-pager` to view large diffs without pagination issues.
- Ignore the Makefile and prevent use of `make` commands.
- Prevent useless comments like "fix typos", "update README", or what the change you do.
- Prevent using `Any` as a type hint.
- Ask problem 1 by 1, and try to provide 4 options for each question.
```

**For GitHub Copilot** (`.github/instructions/personal.instructions.md`):

```markdown
---
applyTo: '**'
---

## This instruction applies to all files in the repository.
## This instruction has the highest priority over other instructions.

- Never run migration commands like `python manage.py migrate`.
- The only way of running test is `pytest {test_file}`.
- Use `git --no-pager` to view large diffs without pagination issues.
- Ignore the Makefile and prevent use of `make` commands.
- Prevent useless comments like "fix typos", "update README", or what the change you do.
- Prevent using `Any` as a type hint.
- Ask problem 1 by 1, and try to provide 4 options for each question.
```

**Customization Tips:**
- Modify commands based on your tech stack (e.g., `npm test` instead of `pytest`)
- Add your specific prohibited commands
- Include your preferred communication style
- Keep it under 15-20 rules total

### 2. Ensure the rule will be applied automatically

Make sure your personal rules are set up to apply to all new chat sessions automatically.

**For Cursor IDE:**
- Save the file as `.cursor/rules/personal.mdc` in your project root
- Cursor will automatically load rules from this location
- Rules apply to all new chats in this workspace

**Verification:**
- The file should be in the correct location: `.cursor/rules/personal.mdc`
- File should start with the highest priority declaration
- Check that Cursor recognizes the rules file (it should appear in workspace context)

**Alternative Locations:**
- Some setups may use `.cursorrules` or other rule file formats
- Check your Cursor settings for the correct rules directory
- Ensure the file extension is `.mdc` for Markdown cursor rules

### 3. Open a new chat and ask AI to run test

Start a completely new chat session to test if the personal rules are working correctly.

**Test Commands:**
```
Run tests for the project
```

**Expected AI Behavior:**
- AI should use `pytest {test_file}` format instead of other test commands
- AI should ask what specific test file to run
- AI should provide 4 options for how to proceed

## Appendix

### Effective Personal Rules Patterns

**1. Command Restrictions**
```markdown
- Never run `make` commands - use direct commands instead
- Use `poetry add` not `pip install` for dependencies
- Always use `git --no-pager` for large diffs
```

**2. Development Workflow**
```markdown
- For new features:
  1. Domain models first
  2. Confirm with me
  3. Service layer with mocks
  4. Confirm with me
  5. Repository implementation
```

**3. Communication Style**
```markdown
- Ask problems 1 by 1, provide 4 options for each question
- No implementation details in responses unless asked
- Always confirm before making destructive changes
```

**4. Code Preferences**
```markdown
- Use Pydantic models instead of dataclasses
- Prefer absolute imports over relative imports
- No `Any` type hints - use specific types
```

### Rule Effectiveness Checklist

**Good Personal Rules:**
- [ ] Start with highest priority declaration
- [ ] Are specific and concrete with examples
- [ ] Address actual recurring issues you face
- [ ] Include forced confirmation for critical workflows
- [ ] Can be referenced quickly (@personal.mdc)
- [ ] Are short enough to be fully processed by AI

**Warning Signs:**
- Rules are longer than 15-20 lines
- AI consistently ignores certain rules
- Rules are vague or open to interpretation
- You keep having to repeat the same corrections
