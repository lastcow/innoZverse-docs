# Lab 03: Generic Architecture Patterns

**Time:** 60 minutes | **Level:** Architect | **Docker:** `golang:1.22-alpine`

## Overview

Generic architecture in Go: generic repository pattern, Result[T,E] error handling, EventBus[T] for type-safe events, generic Pipeline with Stage[I,O], type constraint composition, and generic middleware chains.

---

## Step 1: Generic Repository Pattern

```go
package main

import (
	"context"
	"fmt"
)

// Constraint: any ID type that supports == comparison
type Repository[T any, ID comparable] struct {
	store map[ID]T
}

func NewRepository[T any, ID comparable]() *Repository[T, ID] {
	return &Repository[T, ID]{store: make(map[ID]T)}
}

func (r *Repository[T, ID]) Save(_ context.Context, id ID, item T) error {
	r.store[id] = item
	return nil
}

func (r *Repository[T, ID]) FindByID(_ context.Context, id ID) (T, bool) {
	item, ok := r.store[id]
	return item, ok
}

func (r *Repository[T, ID]) All(_ context.Context) []T {
	items := make([]T, 0, len(r.store))
	for _, v := range r.store {
		items = append(items, v)
	}
	return items
}

func (r *Repository[T, ID]) Delete(_ context.Context, id ID) bool {
	_, ok := r.store[id]
	delete(r.store, id)
	return ok
}

func (r *Repository[T, ID]) Count() int {
	return len(r.store)
}
```

---

## Step 2: Generic Result Type

```go
// Result[T, E] — explicit error handling without panics
type Result[T any, E error] struct {
	value T
	err   E
	ok    bool
}

func Ok[T any, E error](value T) Result[T, E] {
	return Result[T, E]{value: value, ok: true}
}

func Err[T any, E error](err E) Result[T, E] {
	return Result[T, E]{err: err, ok: false}
}

func (r Result[T, E]) IsOk() bool          { return r.ok }
func (r Result[T, E]) Unwrap() T            { return r.value }
func (r Result[T, E]) UnwrapErr() E         { return r.err }

func (r Result[T, E]) UnwrapOr(defaultVal T) T {
	if r.ok {
		return r.value
	}
	return defaultVal
}

func Map[T, U any, E error](r Result[T, E], fn func(T) U) Result[U, E] {
	if !r.ok {
		return Result[U, E]{err: r.err}
	}
	return Ok[U, E](fn(r.value))
}
```

---

## Step 3: Generic EventBus

```go
// Type-safe event bus — no interface{} casts needed
type EventHandler[T any] func(event T)

type EventBus[T any] struct {
	subscribers []EventHandler[T]
}

func (b *EventBus[T]) Subscribe(handler EventHandler[T]) {
	b.subscribers = append(b.subscribers, handler)
}

func (b *EventBus[T]) Publish(event T) {
	for _, handler := range b.subscribers {
		handler(event)
	}
}

func (b *EventBus[T]) PublishAsync(event T) {
	for _, handler := range b.subscribers {
		h := handler
		go h(event)
	}
}

// Domain events
type UserCreatedEvent struct {
	UserID string
	Email  string
}

type OrderPlacedEvent struct {
	OrderID string
	Amount  float64
}

// Usage: completely separate type-safe buses
var userBus  = &EventBus[UserCreatedEvent]{}
var orderBus = &EventBus[OrderPlacedEvent]{}
// userBus.Publish(OrderPlacedEvent{}) — compile error!
```

---

## Step 4: Generic Pipeline — Stage[I,O]

```go
// Stage[I, O]: transforms input I to output O
type Stage[I, O any] func(ctx context.Context, input I) (O, error)

// Compose two stages
func Compose[A, B, C any](
	first  Stage[A, B],
	second Stage[B, C],
) Stage[A, C] {
	return func(ctx context.Context, input A) (C, error) {
		intermediate, err := first(ctx, input)
		if err != nil {
			var zero C
			return zero, fmt.Errorf("stage 1: %w", err)
		}
		result, err := second(ctx, intermediate)
		if err != nil {
			var zero C
			return zero, fmt.Errorf("stage 2: %w", err)
		}
		return result, nil
	}
}

// Example pipeline: string → parsed → validated → saved
type RawInput   = string
type ParsedData = struct{ Name, Email string }
type ValidData  = struct{ Name, Email string; Valid bool }

var parseStage Stage[RawInput, ParsedData] = func(ctx context.Context, raw string) (ParsedData, error) {
	// Parse CSV: "Alice,alice@example.com"
	parts := strings.Split(raw, ",")
	if len(parts) != 2 {
		return ParsedData{}, fmt.Errorf("invalid format: %q", raw)
	}
	return ParsedData{Name: parts[0], Email: parts[1]}, nil
}

var validateStage Stage[ParsedData, ValidData] = func(ctx context.Context, p ParsedData) (ValidData, error) {
	valid := strings.Contains(p.Email, "@")
	return ValidData{Name: p.Name, Email: p.Email, Valid: valid}, nil
}

var pipeline = Compose(parseStage, validateStage)
```

---

## Step 5: Type Constraint Composition

```go
// Build complex constraints from simpler ones
type Ordered interface {
	~int | ~int8 | ~int16 | ~int32 | ~int64 |
		~uint | ~uint8 | ~uint16 | ~uint32 | ~uint64 |
		~float32 | ~float64 | ~string
}

type Number interface {
	~int | ~int8 | ~int16 | ~int32 | ~int64 |
		~uint | ~uint8 | ~uint16 | ~uint32 | ~uint64 |
		~float32 | ~float64
}

// Generic min/max
func Min[T Ordered](a, b T) T {
	if a < b {
		return a
	}
	return b
}

func Max[T Ordered](a, b T) T {
	if a > b {
		return a
	}
	return b
}

// Generic sum
func Sum[T Number](values []T) T {
	var total T
	for _, v := range values {
		total += v
	}
	return total
}

// Generic filter
func Filter[T any](slice []T, pred func(T) bool) []T {
	result := make([]T, 0)
	for _, v := range slice {
		if pred(v) {
			result = append(result, v)
		}
	}
	return result
}

// Generic map
func MapSlice[T, U any](slice []T, fn func(T) U) []U {
	result := make([]U, len(slice))
	for i, v := range slice {
		result[i] = fn(v)
	}
	return result
}
```

---

## Step 6: Generic Middleware Chain

```go
// Generic middleware: wraps Handler[T, R]
type Handler[T, R any] func(ctx context.Context, req T) (R, error)

type Middleware[T, R any] func(Handler[T, R]) Handler[T, R]

// Build a middleware chain
func Chain[T, R any](handler Handler[T, R], middlewares ...Middleware[T, R]) Handler[T, R] {
	for i := len(middlewares) - 1; i >= 0; i-- {
		handler = middlewares[i](handler)
	}
	return handler
}

// Generic logging middleware
func Logging[T, R any](name string) Middleware[T, R] {
	return func(next Handler[T, R]) Handler[T, R] {
		return func(ctx context.Context, req T) (R, error) {
			fmt.Printf("[%s] handling request\n", name)
			result, err := next(ctx, req)
			fmt.Printf("[%s] done, err=%v\n", name, err)
			return result, err
		}
	}
}
```

---

## Step 7: Generic Cache

```go
// Generic TTL cache
type Cache[K comparable, V any] struct {
	mu    sync.RWMutex
	items map[K]cacheItem[V]
	ttl   time.Duration
}

type cacheItem[V any] struct {
	value   V
	expires time.Time
}

func NewCache[K comparable, V any](ttl time.Duration) *Cache[K, V] {
	return &Cache[K, V]{
		items: make(map[K]cacheItem[V]),
		ttl:   ttl,
	}
}

func (c *Cache[K, V]) Set(key K, value V) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.items[key] = cacheItem[V]{value: value, expires: time.Now().Add(c.ttl)}
}

func (c *Cache[K, V]) Get(key K) (V, bool) {
	c.mu.RLock()
	defer c.mu.RUnlock()
	item, ok := c.items[key]
	if !ok || time.Now().After(item.expires) {
		var zero V
		return zero, false
	}
	return item.value, true
}
```

---

## Step 8: Capstone — Generic Repository + EventBus

```bash
docker run --rm golang:1.22-alpine sh -c "cat > /tmp/main.go << 'GOEOF'
package main
import \"fmt\"

type Repository[T any, ID comparable] struct { store map[ID]T }
func NewRepository[T any, ID comparable]() *Repository[T, ID] { return &Repository[T, ID]{store: make(map[ID]T)} }
func (r *Repository[T, ID]) Save(id ID, item T) { r.store[id] = item }
func (r *Repository[T, ID]) FindByID(id ID) (T, bool) { item, ok := r.store[id]; return item, ok }
func (r *Repository[T, ID]) All() []T { items := make([]T, 0, len(r.store)); for _, v := range r.store { items = append(items, v) }; return items }

type EventBus[T any] struct { subscribers []func(T) }
func (b *EventBus[T]) Subscribe(fn func(T)) { b.subscribers = append(b.subscribers, fn) }
func (b *EventBus[T]) Publish(event T) { for _, fn := range b.subscribers { fn(event) } }

type User struct { ID int; Name string }
type UserEvent struct { Type string; User User }

func main() {
	repo := NewRepository[User, int]()
	repo.Save(1, User{1, \"Alice\"})
	repo.Save(2, User{2, \"Bob\"})
	u, ok := repo.FindByID(1)
	fmt.Printf(\"Generic Repository[User, int]\\n\")
	fmt.Printf(\"FindByID(1): %v, found=%v\\n\", u, ok)
	fmt.Printf(\"All(): %v\\n\", repo.All())
	bus := &EventBus[UserEvent]{}
	bus.Subscribe(func(e UserEvent) { fmt.Printf(\"Event[UserEvent]: %s -> %s\\n\", e.Type, e.User.Name) })
	bus.Publish(UserEvent{\"created\", User{3, \"Carol\"}})
}
GOEOF
cd /tmp && go run main.go"
```

📸 **Verified Output:**
```
Generic Repository[User, int]
FindByID(1): {1 Alice}, found=true
All(): [{1 Alice} {2 Bob}]
Event[UserEvent]: created -> Carol
```

---

## Summary

| Pattern | Generic API | Type Safety |
|---------|------------|------------|
| Repository | `Repository[T, ID comparable]` | Full CRUD typed |
| Result type | `Result[T, E error]` | No untyped errors |
| EventBus | `EventBus[T]` | No interface{} cast |
| Pipeline | `Stage[I, O]` + `Compose` | Stage chain typed |
| Constraints | `type Ordered interface{~int\|...}` | Method sets |
| Middleware | `Middleware[T, R]` | Handler signature |
| Cache | `Cache[K comparable, V any]` | Type-safe K/V |
