# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI coding workshop repository for Crescendo Lab demonstrating agentic coding practices through a **simplified yet real product feature**: **Omnichannel Auto-Reply**.

The case study involves rewriting a LINE-only auto-reply system to support multi-channel (LINE, Facebook Messenger, Instagram DMs) with priority-based keyword and time-based triggers.

## Development Commands

### Python Development (python_src/)

```bash
# Initialize development environment (includes pyenv, poetry setup)
cd python_src/
make init

# Run tests
make test

# Format code (black, isort, pyright)
make fmt

# Run application
make run
```

### Go Development (go_src/)

```bash
# Setup
cd go_src/
go mod download

# Run tests
make test

# Verbose tests with coverage
make test-verbose

# Lint code
make lint

# Build application
make build

# Run application
make run
```

## Architecture

### Domain-Driven Design Structure

Both Go and Python implementations follow the same domain structure:

```
internal/
├── domain/
│   ├── auto_reply/          # Core auto-reply business logic
│   │   ├── auto_reply.go/.py     # AutoReply domain model
│   │   └── webhook_trigger.go/.py  # Webhook trigger logic
│   ├── common/              # Shared domain utilities
│   │   ├── error.go/.py     # Error handling
│   │   ├── error_code.go/.py # Error codes
│   │   └── requestid.go/.py  # Request ID utilities
│   └── organization/        # Organization domain models
│       ├── bot.go/.py       # Bot configuration
│       ├── business_hour.go/.py # Business hours
│       └── organization.go/.py  # Organization model
```

### Key Domain Models

- **AutoReply**: Omnichannel rule defining high-level auto-reply configuration
- **WebhookTrigger**: Handles trigger validation and priority logic
- **Organization/Bot**: Channel and organization management
- **BusinessHour**: Time-based scheduling support

### Priority System

The system implements a 2-level priority hierarchy:
1. **Priority 1**: Keyword-based triggers (exact match, case-insensitive, trimmed)
2. **Priority 2**: Time-based/General triggers (lowest priority)

### Test Strategy

- **Unit Tests**: Focus on trigger validation logic in `internal/domain/auto_reply/`
- **Integration Tests**: Test complete webhook event processing
- **Coverage**: All domain logic has comprehensive test coverage with real-world scenarios

## Key Implementation Details

### Keyword Matching Logic
- Case-insensitive exact matching
- Leading/trailing whitespace trimming
- Multiple keywords per rule support
- No partial matching (exact match only)

### Event Processing
- Supports MESSAGE events only for keyword triggers
- TIME events for scheduled triggers
- Multi-channel webhook event normalization

### Working Directories
- `go_src/` - Primary Go workspace for development
- `python_src/` - Primary Python workspace for development  
- `cheat_sheet/` - Reference implementations and solutions
- `legacy/` - Original LINE-only implementation for context
- `spec/` - Product requirements and specifications

## Testing Approach

Use the existing test files as examples:
- Go: `internal/domain/common/error_test.go`, `internal/domain/common/requestid_test.go`
- Python: `tests/domain/auto_reply/test_trigger_validation.py`, `tests/domain/common/`

When adding new tests, follow the pattern of testing both success and failure scenarios with comprehensive edge cases.