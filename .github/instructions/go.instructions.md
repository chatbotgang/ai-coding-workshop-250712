---
applyTo: '**/*.go'
---
# Go Development Guide in CL

This document provides comprehensive guidance for Go development in Crescendo Lab, covering architecture patterns, coding style, and best practices.

## Table of Contents
- [Architecture Patterns](#architecture-patterns)
- [Package Structure](#package-structure)
- [Code Organization](#code-organization)
- [Naming Conventions](#naming-conventions)
- [Types and Structs](#types-and-structs)
- [Functions and Methods](#functions-and-methods)
- [Error Handling](#error-handling)
- [Concurrency](#concurrency)
- [Testing](#testing)
- [Performance Considerations](#performance-considerations)
- [Logging and Observability](#logging-and-observability)
- [Documentation](#documentation)
- [Project Structure](#project-structure)

## Architecture Patterns

### Clean Architecture

Go project in CL follows a clean architecture pattern with distinct layers:

1. **Domain Layer** (`internal/domain/`)
   - Contains business entities and logic
   - Independent of external frameworks and databases
   - Defines interfaces that are implemented by outer layers

2. **Application Layer** (`internal/app/`)
   - Contains application services that orchestrate domain entities
   - Implements use cases of the system
   - Depends on domain layer, but not on external frameworks

3. **Adapter Layer** (`internal/adapter/`)
   - Implements interfaces defined in the domain layer
   - Connects the application to external systems (databases, message brokers, etc.)
   - Contains concrete implementations of repositories and services

4. **Router Layer** (`internal/router/`)
   - Entry points to the application (HTTP handlers, CLI commands)
   - Depends on application services
   - Translates external requests to internal application calls

### Common Patterns

#### Interface Design
- Define interfaces in the layer that uses them, not in the layer that implements them
- Keep interfaces small and focused on a single responsibility
- Use dependency injection to provide implementations

```go
// In domain layer
type MessageRepository interface {
    WriteMessageBatch(context.Context, []message.Message) common.Error
    GetMessage(ctx context.Context, channelType message.ChannelType, externalMessageID string) (*message.Message, common.Error)
}

// In adapter layer
type messageRepository struct {
    // implementation details
}
```

#### Service Pattern
- Services should be stateless when possible
- Use parameter structs for service constructors with many dependencies
- Services should depend on interfaces, not concrete implementations

```go
type GatewayServiceParam struct {
    MessageRepository   MessageRepository
    ReportRepository    ReportRepository
    // other dependencies
}

func NewGatewayService(ctx context.Context, param GatewayServiceParam) *GatewayService {
    return &GatewayService{
        messageRepository: param.MessageRepository,
        // initialize other dependencies
    }
}
```

#### Repository Pattern
- Repositories abstract data access logic
- They should return domain entities, not data transfer objects
- Use custom error types for domain-specific errors

#### Factory Pattern
- Use factories to create complex domain entities or services
- Hide implementation details behind factory interfaces

```go
type ChannelFactory interface {
    Channel(context.Context, message.ChannelType) (message.Channel, common.Error)
}
```

#### Event-Driven Architecture
- Use event brokers for asynchronous communication between services
- Define clear event interfaces and payloads
- Use event-driven patterns for scalability and loose coupling

## Package Structure
- Package names should be short, concise, and lowercase (e.g., `message`, `gateway`, `common`)
- One package per directory
- Package name should match the directory name
- Use `internal` directory for code that should not be imported by other projects

## Code Organization

### Package Design
- Keep packages focused on a single responsibility
- Avoid circular dependencies between packages
- Organize code by domain concept, not by technical function

### File Organization
- Keep files to a reasonable size (under 500 lines if possible)
- Group related functionality in the same file
- Place interfaces in the same package as the code that uses them
- Use separate files for tests

### Imports
- Group imports into standard library, external packages, and internal packages
- Within each group, imports should be alphabetically sorted
- Use blank lines to separate import groups

```go
import (
    "context"
    "encoding/json"
    "time"

    "github.com/rs/zerolog"
    "github.com/alecthomas/kingpin/v2"

    "github.com/chatbotgang/medley/internal/domain/message"
)
```

## Naming Conventions
- Use `CamelCase` for exported names (public)
- Use `mixedCase` for non-exported names (private)
- Use acronyms consistently (e.g., `ID`, `URL`, `HTTP`)
- Constants should use `PascalCase` with descriptive prefixes
- Interface names should not end with `-er` (e.g., `MessageRepository` not `MessageRepositorier`)

## Types and Structs
- Define types at the top of the file, followed by constants, then variables
- Group related constants together
- Use struct tags for JSON serialization when needed
- For parameter structs, use the suffix `Param` (e.g., `GatewayServiceParam`)

```go
type MessageStatus string

const (
    MessageStatusProcessing MessageStatus = "PROCESSING"
    MessageStatusSent       MessageStatus = "SENT"
    MessageStatusDelivered  MessageStatus = "DELIVERED"
)

type Message struct {
    MessageID   string        `json:"message_id"`
    Status      MessageStatus `json:"status"`
    CreatedAt   time.Time     `json:"created_at"`
}
```

## Functions and Methods
- Use descriptive function names that indicate what the function does
- Receiver variable should be a short, consistent name (e.g., `s` for service)
- Constructor functions should use `New` prefix (e.g., `NewGatewayService`)
- Return errors as the last return value
- Use named return parameters sparingly

```go
func NewGatewayService(ctx context.Context, param GatewayServiceParam) *GatewayService {
    return &GatewayService{
        messageRepository: param.MessageRepository,
        // ...
    }
}

func (s *GatewayService) logger(ctx context.Context) *zerolog.Logger {
    l := zerolog.Ctx(ctx).With().Str("component", "gateway-service").Logger()
    return &l
}
```

## Error Handling

### Error Types
- Use custom error types from `common` package
- Implement the error interface for custom error types
- Use error wrapping to add context to errors
- Check specific error types using errors.Is() and errors.As()

```go
if err != nil {
    return common.NewError(common.ErrorCodeInternal, "failed to process message", err)
}
```

### Error Propagation
- Return errors to the caller rather than handling them internally when appropriate
- Log errors at the appropriate level (usually at the entry point)
- Include relevant context in error messages
- Don't use panic for normal error handling

## Concurrency
- Use contexts for cancellation and timeouts
- Prefer channels and goroutines over mutexes when appropriate
- Always use proper synchronization when sharing data between goroutines
- Use goroutines for concurrent operations, but be mindful of resource usage
- Consider using worker pools for CPU-intensive or I/O-bound tasks

```go
ctx, cancel := context.WithTimeout(parentCtx, 5*time.Second)
defer cancel()

// Use ctx for operations that should be cancelled after timeout
```

### Goroutine Management
- Always ensure goroutines can exit
- Use context for cancellation
- Be careful with infinite loops in goroutines
- Consider using errgroup for managing groups of goroutines

```go
g, ctx := errgroup.WithContext(parentCtx)
for _, task := range tasks {
    task := task // Create a new variable for the closure
    g.Go(func() error {
        return processTask(ctx, task)
    })
}
if err := g.Wait(); err != nil {
    // Handle error
}
```

## Testing

### Test Parallelization Rules

**ALWAYS add `t.Parallel()` to test functions EXCEPT for adapter layer tests**

#### ✅ Use t.Parallel() for:
- **Domain layer tests** (`internal/domain/`) - Pure business logic, no external dependencies
- **Application layer tests** (`internal/app/`) - Service tests with mocked dependencies
- **Router layer tests** (`internal/router/`) - HTTP handler tests with mocked services

```go
func TestDomainFunction(t *testing.T) {
    t.Parallel()  // ✅ Always add for domain tests
    // test implementation
}

func TestAppService(t *testing.T) {
    t.Parallel()  // ✅ Always add for app layer tests
    // test implementation with mocks
}
```

#### ❌ DO NOT use t.Parallel() for:
- **Adapter layer tests** (`internal/adapter/`) - Integration tests coupled with third-party services, databases, or external systems

```go
func TestRedisRepository(t *testing.T) {
    // ❌ DO NOT add t.Parallel() for adapter tests
    if testRedisHost == "" {
        t.Skip("skip integration tests")
    }
    // integration test implementation
}
```

#### Why this rule?
- **Adapter layer** contains integration tests that often:
  - Connect to shared external resources (Redis, databases, APIs)
  - Have resource contention issues when run in parallel
  - May have timing dependencies or cleanup requirements
  - Could interfere with each other when accessing the same external systems

- **Other layers** contain unit tests that:
  - Use mocked dependencies
  - Are isolated and independent
  - Benefit greatly from parallel execution
  - Have no shared state or external dependencies

### Unit Tests
- Write tests for all exported functions and methods
- Use table-driven tests for testing multiple cases
- Mock external dependencies using interfaces
- Keep tests independent and idempotent

```go
func TestSendMessage(t *testing.T) {
    t.Parallel()  // ✅ Add t.Parallel() for unit tests
    tests := []struct {
        name    string
        message message.Message
        expectedError bool
    }{
        // Test cases
    }
    
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            // Test implementation
        })
    }
}
```

### Integration Tests
- Use conditional test skipping for tests that require external credentials or services:
  ```go
  if testLineToken == "" || testLineMemberID == "" {
      t.Skip("skip integration tests")
  }
  ```
- Define test constants at the package level for configuration and test data:
  ```go
  // Test only when the server is changed
  const testLineToken = ""
  const testLineMemberID = ""
  
  // Test message payload templates
  const lineMessageTemplateText = `{ "messages": [ { "type":"text", "text":"Hello, world" } ] }`
  ```
- Structure integration tests using table-driven tests similar to unit tests:
  ```go
  testCases := []struct {
      Name                   string
      Message                message.Message
      Auth                   message.ChannelAuth
      ExpectedStatus         message.MessageStatus
      ExpectedStatusCode     int
      ExpectedError          bool
      ExpectedResolveByRetry bool
  }{
      // Test cases...
  }
  ```
- Include both success and failure test cases with detailed expectations
- Test edge cases and error conditions with specific error expectations
- Verify detailed response properties beyond just error/success:
  ```go
  assert.Equal(t, c.ExpectedStatus, status)
  assert.Equal(t, c.ExpectedStatusCode, channelResponse.StatusCode)
  assert.Equal(t, c.ExpectedResolveByRetry, err.ResolveByRetry())
  ```
- Create helper functions to build test data and requests:
  ```go
  func buildTestLineAuth(token string) message.ChannelAuth {
      return message.ChannelAuth{
          Token: token,
      }
  }
  
  func buildTestLineMessage(recipientID string, messageTemplate string) message.Message {
      return message.Message{
          MessageID:      uuid.NewString(),
          RecipientID:    recipientID,
          ChannelType:    message.ChannelTypeLine,
          // ...other fields
      }
  }
  ```
- Use Docker Compose for integration tests with external dependencies
- Clean up resources after tests
- Use environment variables to configure test behavior
- Consider using testcontainers for ephemeral test dependencies

### Mocking
- Use interface mocks for testing
- Generate mocks using `mockgen` with `//go:generate` directives
- Place mocks in an `automock` subdirectory
- Create structured mock objects for complex services:
  ```go
  type serviceTestMock struct {
      Repository     *automock.MockRepository
      Factory        *automock.MockFactory
      EventBroker    *automock.MockEventBroker
      // Other dependencies
  }
  ```
- Create helper functions to build mock structures:
  ```go
  func buildServiceMock(ctrl *gomock.Controller) serviceTestMock {
      return serviceTestMock{
          Repository:  automock.NewMockRepository(ctrl),
          Factory:     automock.NewMockFactory(ctrl),
          EventBroker: automock.NewMockEventBroker(ctrl),
      }
  }
  ```
- Create helper functions to build services with mocked dependencies:
  ```go
  func buildService(mock serviceTestMock) *Service {
      param := ServiceParam{
          Repository:  mock.Repository,
          Factory:     mock.Factory,
          EventBroker: mock.EventBroker,
      }
      return NewService(context.Background(), param)
  }
  ```
- Use helper functions to build test data:
  ```go
  func buildTestData(size int, status Status, url string) TestData {
      // Build and return test data
  }
  ```
- Use EXPECT() to set up mock expectations with appropriate matchers
- Use gomock.Any() for parameters that don't need specific matching
- Use AnyTimes() for expectations that may be called multiple times
- Add comments for expectations that are intentionally not set (e.g., when testing feature flags)

```go
//go:generate mockgen -destination automock/message_repository.go -package=automock . MessageRepository
``` 

### Test Helpers
- Create reusable helper functions for common test operations
- Place test helpers in the same package as the tests they support
- Use descriptive names for helper functions that indicate their purpose
- Create helpers for building test data with sensible defaults:
  ```go
  func buildTestMessageDelivery(messageBatchSize int, status message.MessageStatus, callBackURL string) message.MessageDelivery {
      // Build and return test data with the specified parameters
  }
  ```
- Create helpers for setting up mock expectations for common scenarios
- Use faker libraries for generating random test data:
  ```go
  import "github.com/bxcodec/faker/v3"
  
  // Use faker to generate random data
  recipientID := faker.URL()
  ```
- Use uuid libraries for generating unique identifiers:
  ```go
  import "github.com/google/uuid"
  
  // Generate a unique ID
  messageID := uuid.NewString()
  ```
- Create helpers that encapsulate complex assertion logic
- Document helper functions with clear comments explaining their purpose and parameters
- Keep helper functions focused on a single responsibility
- Consider parameterizing helpers to make them more flexible

## Performance Considerations

### Memory Management
- Avoid unnecessary memory allocations
- Use pointers judiciously - only when you need to share mutable state
- Consider using sync.Pool for frequently allocated objects
- Be aware of escape analysis and stack vs. heap allocations

### Efficiency
- Use buffered channels when appropriate
- Preallocate slices when you know the size in advance
- Use string concatenation efficiently (strings.Builder for multiple concatenations)
- Profile your code to identify bottlenecks

## Logging and Observability

### Structured Logging
- Use structured logging with `zerolog`
- Include relevant context in log entries
- Use appropriate log levels (debug, info, warn, error)
- Don't log sensitive information
- Create logger helpers that add component information

```go
logger := zerolog.Ctx(ctx).With().
    Str("component", "gateway-service").
    Str("message_id", message.ID).
    Logger()
logger.Info().Msg("Processing message")
```

### Metrics and Tracing
- Instrument code with metrics for important operations
- Use distributed tracing for request flows
- Monitor error rates and latencies
- Use context for propagating trace information

## Documentation

### Code Comments
- All exported functions, types, and constants should have comments
- Comments should start with the name of the thing being described
- Use complete sentences with proper punctuation
- For interfaces, document the behavior, not the implementation
- Focus on why, not just what
- Keep comments up to date with code changes

```go
// MessageStatus is used to indicate the processing status of a MessageDelivery.
type MessageStatus string

// Message represents the message that will be sent to a channel in the system.
// It is an interface to communicate between channels and the system.
type Message struct {
    // ...
}
```

### README and Documentation
- Maintain clear README files for each package
- Document architecture decisions
- Include examples for complex functionality
- Keep documentation close to the code it describes

## Common Pitfalls to Avoid

### Nil Pointer Dereferences
- Check for nil before dereferencing pointers
- Be careful with interface nil checks
- Initialize all fields in structs
- Use pointer receivers consistently

### Race Conditions
- Use proper synchronization (mutex, channels) when sharing data
- Run tests with the race detector (`go test -race`)
- Avoid global mutable state
- Be careful with closures capturing loop variables

### Resource Leaks
- Always close resources (files, connections, etc.)
- Use defer for cleanup operations
- Check for errors when closing resources
- Consider using errgroup for managing multiple resources

```go
file, err := os.Open(filename)
if err != nil {
    return err
}
defer func() {
    if closeErr := file.Close(); closeErr != nil {
        // Log the error
    }
}()
```

## Dependency Injection
- Use parameter structs for services with many dependencies
- Initialize all dependencies in constructors
- Avoid global state and singletons

## Project Structure

### Main Directories

- `cmd/` - Contains the main applications
- `internal/` - Private application and library code
  - `domain/` - Core business logic and entities
    - `organization/` - Organization and channel domain models and business rules
    - `message/` - Message domain models and business rules
    - `common/` - Shared domain logic
  - `app/` - Application services
    - `service/` - Contains various services like gateway, messageworker, callbackworker
  - `adapter/` - External integrations
    - `server/` - External server implementations
    - `repository/` - Data storage implementations
    - `eventbroker/` - Event broker implementations
  - `router/` - Routing logic

- `docs/` - Documentation files

### Configuration
The application uses a combination of environment variables and command-line flags for configuration, with defaults defined in `cmd/app/main.go`.

### Development Workflow
- Use `make test` for running tests
- Use `make mock` to update mock objects
- Use `make run` to start the application locally
- Docker Compose is available for setting up dependent services

### Key Files
- `cmd/app/main.go` - Application entry point and configuration
- `internal/app/application.go` - Core application structure
- `Makefile` - Development commands and workflows
