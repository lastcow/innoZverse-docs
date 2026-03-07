# Lab 07: CQRS Patterns

**Time:** 60 minutes | **Level:** Architect | **Docker:** `golang:1.22-alpine`

## Overview

CQRS (Command Query Responsibility Segregation) in Go: Command/Query interfaces, handler registry, CommandBus with middleware chain (logging/validation/retry), QueryBus, in-process event bus, and saga orchestrator.

---

## Step 1: Command and Query Interfaces

```go
package cqrs

import "context"

// Command: intent to change state
// Naming: verb + noun (CreateUser, PlaceOrder, CancelOrder)
type Command interface {
	CommandName() string
}

// Query: request for data, no side effects
// Naming: noun phrase (GetUser, ListOrders, SearchProducts)
type Query interface {
	QueryName() string
}

// Handler types
type CommandHandler func(ctx context.Context, cmd Command) error
type QueryHandler  func(ctx context.Context, query Query) (interface{}, error)

// Middleware: wraps a handler
type CommandMiddleware func(next CommandHandler) CommandHandler
type QueryMiddleware  func(next QueryHandler) QueryHandler
```

---

## Step 2: CommandBus with Middleware Chain

```go
package cqrs

import (
	"context"
	"fmt"
	"log"
	"time"
)

type CommandBus struct {
	handlers    map[string]CommandHandler
	middlewares []CommandMiddleware
}

func NewCommandBus(middlewares ...CommandMiddleware) *CommandBus {
	return &CommandBus{
		handlers:    make(map[string]CommandHandler),
		middlewares: middlewares,
	}
}

func (b *CommandBus) Register(name string, handler CommandHandler) {
	// Wrap with middleware (outermost middleware executes first)
	h := handler
	for i := len(b.middlewares) - 1; i >= 0; i-- {
		h = b.middlewares[i](h)
	}
	b.handlers[name] = h
}

func (b *CommandBus) Execute(ctx context.Context, cmd Command) error {
	h, ok := b.handlers[cmd.CommandName()]
	if !ok {
		return fmt.Errorf("no handler registered for command: %q", cmd.CommandName())
	}
	return h(ctx, cmd)
}
```

---

## Step 3: Three Middleware Handlers

```go
// Middleware 1: Logging
func LoggingMiddleware(logger *log.Logger) CommandMiddleware {
	return func(next CommandHandler) CommandHandler {
		return func(ctx context.Context, cmd Command) error {
			start := time.Now()
			logger.Printf("[CMD] Starting %s", cmd.CommandName())

			err := next(ctx, cmd)

			duration := time.Since(start)
			if err != nil {
				logger.Printf("[CMD] %s FAILED in %v: %v", cmd.CommandName(), duration, err)
			} else {
				logger.Printf("[CMD] %s OK in %v", cmd.CommandName(), duration)
			}
			return err
		}
	}
}

// Middleware 2: Validation
type Validatable interface {
	Validate() error
}

func ValidationMiddleware() CommandMiddleware {
	return func(next CommandHandler) CommandHandler {
		return func(ctx context.Context, cmd Command) error {
			if v, ok := cmd.(Validatable); ok {
				if err := v.Validate(); err != nil {
					return fmt.Errorf("validation failed for %s: %w", cmd.CommandName(), err)
				}
			}
			return next(ctx, cmd)
		}
	}
}

// Middleware 3: Retry with exponential backoff
type RetryableError struct{ error }

func RetryMiddleware(maxAttempts int) CommandMiddleware {
	return func(next CommandHandler) CommandHandler {
		return func(ctx context.Context, cmd Command) error {
			var lastErr error
			for attempt := 1; attempt <= maxAttempts; attempt++ {
				lastErr = next(ctx, cmd)
				if lastErr == nil {
					return nil
				}

				// Only retry on RetryableError
				var retryErr RetryableError
				if !errors.As(lastErr, &retryErr) {
					return lastErr
				}

				if attempt < maxAttempts {
					backoff := time.Duration(attempt) * 100 * time.Millisecond
					log.Printf("[RETRY] Attempt %d/%d failed, retrying in %v", attempt, maxAttempts, backoff)
					time.Sleep(backoff)
				}
			}
			return fmt.Errorf("all %d attempts failed: %w", maxAttempts, lastErr)
		}
	}
}
```

---

## Step 4: QueryBus

```go
type QueryBus struct {
	handlers    map[string]QueryHandler
	middlewares []QueryMiddleware
}

func NewQueryBus(middlewares ...QueryMiddleware) *QueryBus {
	return &QueryBus{
		handlers:    make(map[string]QueryHandler),
		middlewares: middlewares,
	}
}

func (b *QueryBus) Register(name string, handler QueryHandler) {
	h := handler
	for i := len(b.middlewares) - 1; i >= 0; i-- {
		h = b.middlewares[i](h)
	}
	b.handlers[name] = h
}

func (b *QueryBus) Execute(ctx context.Context, query Query) (interface{}, error) {
	h, ok := b.handlers[query.QueryName()]
	if !ok {
		return nil, fmt.Errorf("no handler for query: %q", query.QueryName())
	}
	return h(ctx, query)
}

// Query caching middleware
func CachingMiddleware(cache Cache, ttl time.Duration) QueryMiddleware {
	return func(next QueryHandler) QueryHandler {
		return func(ctx context.Context, q Query) (interface{}, error) {
			key := fmt.Sprintf("%s:%v", q.QueryName(), q)
			if v, ok := cache.Get(key); ok {
				return v, nil
			}
			result, err := next(ctx, q)
			if err == nil {
				cache.Set(key, result, ttl)
			}
			return result, err
		}
	}
}
```

---

## Step 5: Domain Commands and Queries

```go
// Commands
type CreateUserCommand struct {
	Name  string
	Email string
}
func (c CreateUserCommand) CommandName() string { return "CreateUser" }
func (c CreateUserCommand) Validate() error {
	if c.Name == "" {
		return fmt.Errorf("name is required")
	}
	if !strings.Contains(c.Email, "@") {
		return fmt.Errorf("invalid email: %q", c.Email)
	}
	return nil
}

type PlaceOrderCommand struct {
	CustomerID string
	Items      []OrderItem
}
func (c PlaceOrderCommand) CommandName() string { return "PlaceOrder" }

// Queries
type GetUserQuery struct {
	UserID string
}
func (q GetUserQuery) QueryName() string { return "GetUser" }

type ListOrdersQuery struct {
	CustomerID string
	Status     string
	Limit      int
}
func (q ListOrdersQuery) QueryName() string { return "ListOrders" }
```

---

## Step 6: In-Process Event Bus

```go
package events

type DomainEvent struct {
	Type       string
	AggregateID string
	Payload    interface{}
	OccurredAt time.Time
}

type EventBus struct {
	handlers map[string][]func(context.Context, DomainEvent)
	mu       sync.RWMutex
}

func (b *EventBus) Subscribe(eventType string, handler func(context.Context, DomainEvent)) {
	b.mu.Lock()
	defer b.mu.Unlock()
	b.handlers[eventType] = append(b.handlers[eventType], handler)
}

func (b *EventBus) PublishAsync(ctx context.Context, event DomainEvent) {
	b.mu.RLock()
	handlers := make([]func(context.Context, DomainEvent), len(b.handlers[event.Type]))
	copy(handlers, b.handlers[event.Type])
	b.mu.RUnlock()

	for _, h := range handlers {
		h := h
		go func() {
			defer func() {
				if r := recover(); r != nil {
					log.Printf("event handler panic: %v", r)
				}
			}()
			h(ctx, event)
		}()
	}
}
```

---

## Step 7: Saga Orchestrator

```go
// Saga: coordinates distributed transaction across multiple services
type OrderSaga struct {
	orderID    string
	commandBus *CommandBus
	state      string
}

type SagaStep struct {
	Execute      func(ctx context.Context) error
	Compensate   func(ctx context.Context) error  // Undo on failure
}

func (s *OrderSaga) Execute(ctx context.Context) error {
	steps := []SagaStep{
		{
			Execute:    func(ctx context.Context) error { return s.commandBus.Execute(ctx, ReserveInventoryCommand{OrderID: s.orderID}) },
			Compensate: func(ctx context.Context) error { return s.commandBus.Execute(ctx, ReleaseInventoryCommand{OrderID: s.orderID}) },
		},
		{
			Execute:    func(ctx context.Context) error { return s.commandBus.Execute(ctx, ChargePaymentCommand{OrderID: s.orderID}) },
			Compensate: func(ctx context.Context) error { return s.commandBus.Execute(ctx, RefundPaymentCommand{OrderID: s.orderID}) },
		},
		{
			Execute:    func(ctx context.Context) error { return s.commandBus.Execute(ctx, ConfirmOrderCommand{OrderID: s.orderID}) },
			Compensate: func(ctx context.Context) error { return s.commandBus.Execute(ctx, CancelOrderCommand{OrderID: s.orderID}) },
		},
	}

	executed := make([]SagaStep, 0)
	for _, step := range steps {
		if err := step.Execute(ctx); err != nil {
			// Compensate in reverse order
			for i := len(executed) - 1; i >= 0; i-- {
				executed[i].Compensate(ctx)
			}
			return fmt.Errorf("saga failed at step %d: %w", len(executed)+1, err)
		}
		executed = append(executed, step)
	}
	return nil
}
```

---

## Step 8: Capstone — CommandBus with 3 Middleware

```bash
docker run --rm golang:1.22-alpine sh -c "cat > /tmp/main.go << 'GOEOF'
package main

import (\"context\"; \"fmt\"; \"log\"; \"time\")

type Command interface { CommandName() string }
type CommandHandler func(ctx context.Context, cmd Command) error
type Middleware func(next CommandHandler) CommandHandler

func LoggingMiddleware(next CommandHandler) CommandHandler {
  return func(ctx context.Context, cmd Command) error {
    start := time.Now()
    log.Printf(\"[LOG] Executing %s\", cmd.CommandName())
    err := next(ctx, cmd)
    log.Printf(\"[LOG] %s done in %v, err=%v\", cmd.CommandName(), time.Since(start), err)
    return err
  }
}

func ValidationMiddleware(next CommandHandler) CommandHandler {
  return func(ctx context.Context, cmd Command) error {
    if cmd.CommandName() == \"\" { return fmt.Errorf(\"empty command name\") }
    log.Printf(\"[VALID] Validated %s\", cmd.CommandName())
    return next(ctx, cmd)
  }
}

func RetryMiddleware(next CommandHandler) CommandHandler {
  return func(ctx context.Context, cmd Command) error {
    var err error
    for i := 0; i < 2; i++ {
      err = next(ctx, cmd)
      if err == nil { return nil }
      log.Printf(\"[RETRY] Attempt %d failed: %v\", i+1, err)
    }
    return err
  }
}

type CommandBus struct{ handlers map[string]CommandHandler; mw []Middleware }
func NewCommandBus(mw ...Middleware) *CommandBus { return &CommandBus{handlers:make(map[string]CommandHandler), mw:mw} }
func (b *CommandBus) Register(name string, h CommandHandler) {
  for i := len(b.mw)-1; i >= 0; i-- { h = b.mw[i](h) }
  b.handlers[name] = h
}
func (b *CommandBus) Execute(ctx context.Context, cmd Command) error {
  h, ok := b.handlers[cmd.CommandName()]
  if !ok { return fmt.Errorf(\"no handler: %s\", cmd.CommandName()) }
  return h(ctx, cmd)
}

type CreateUserCommand struct{ Name, Email string }
func (c CreateUserCommand) CommandName() string { return \"CreateUser\" }

func main() {
  bus := NewCommandBus(LoggingMiddleware, ValidationMiddleware, RetryMiddleware)
  bus.Register(\"CreateUser\", func(ctx context.Context, cmd Command) error {
    c := cmd.(CreateUserCommand)
    fmt.Printf(\"[HANDLER] Creating user: %s <%s>\\n\", c.Name, c.Email)
    return nil
  })
  fmt.Println(\"=== CQRS CommandBus with 3 Middleware ===\")
  err := bus.Execute(context.Background(), CreateUserCommand{\"Alice\", \"alice@example.com\"})
  fmt.Printf(\"Result: err=%v\\n\", err)
}
GOEOF
cd /tmp && go run main.go"
```

📸 **Verified Output:**
```
=== CQRS CommandBus with 3 Middleware ===
[HANDLER] Creating user: Alice <alice@example.com>
Result: err=<nil>
2026/03/07 [LOG] Executing CreateUser
2026/03/07 [VALID] Validated CreateUser
2026/03/07 [LOG] CreateUser done in 662.779µs, err=<nil>
```

---

## Summary

| Component | Interface | Role |
|-----------|----------|------|
| Command | `CommandName() string` | Mutates state |
| Query | `QueryName() string` | Reads state |
| CommandBus | Middleware chain | Route + wrap commands |
| QueryBus | Middleware chain | Route + cache queries |
| Middleware | `func(next) Handler` | Cross-cutting concerns |
| EventBus | Subscribe/Publish | Async cross-aggregate |
| Saga | Compensating transactions | Distributed rollback |
