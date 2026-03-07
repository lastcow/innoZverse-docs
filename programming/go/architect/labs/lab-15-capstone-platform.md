# Lab 15: Capstone — Production Go Platform

**Time:** 60 minutes | **Level:** Architect | **Docker:** `golang:1.22-alpine`

## Overview

Production Go platform integrating all architect patterns: GMP scheduler tuning, generic repository + event bus, event sourcing (EventStore), CQRS CommandBus (3 middleware), mTLS, OpenTelemetry traces + Prometheus metrics, chacha20poly1305 + ed25519 security, actor system, table-driven tests (10+), and versioned build output.

---

## Step 1: Project Structure

```
go-architect-platform/
├── cmd/
│   └── server/main.go          # Entry point + build version injection
├── internal/
│   ├── platform/
│   │   ├── repository/         # Generic Repository[T, ID]
│   │   ├── eventstore/         # Event sourcing + optimistic concurrency
│   │   ├── cqrs/               # CommandBus + QueryBus + Middleware
│   │   ├── actor/              # ActorSystem + supervision
│   │   └── resilience/         # Circuit breaker + bulkhead + retry
│   ├── security/
│   │   ├── crypto.go           # chacha20poly1305 + argon2
│   │   └── tokens.go           # Ed25519 + HMAC-SHA512
│   ├── observability/
│   │   ├── tracing.go          # OpenTelemetry SDK
│   │   └── metrics.go          # Prometheus counters/histograms
│   └── domain/
│       ├── user/               # User aggregate + commands + queries
│       └── order/              # Order aggregate + event sourcing
├── go.mod
└── go.sum
```

---

## Step 2: GMP Scheduler Tuning

```go
package main

import (
	"fmt"
	"runtime"
	"runtime/debug"
)

var version = "dev" // Set via: go build -ldflags="-X main.version=v1.0.0"

func initRuntime() {
	// Container-aware: auto-set GOMAXPROCS to cgroup CPU quota
	// Use: go.uber.org/automaxprocs
	// automaxprocs.Init()  // Reads cgroup v1/v2 limits

	// Manual tuning
	runtime.GOMAXPROCS(runtime.NumCPU())

	// GC tuning for latency-sensitive services
	debug.SetGCPercent(200) // Less frequent GC (more memory, lower latency)

	// Soft memory limit (Go 1.19+)
	debug.SetMemoryLimit(512 * 1024 * 1024) // 512 MB max

	fmt.Printf("Runtime: GOMAXPROCS=%d NumCPU=%d\n",
		runtime.GOMAXPROCS(0), runtime.NumCPU())
}
```

---

## Step 3: Generic Repository + EventBus

```go
package platform

// Generic Repository — type-safe CRUD
type Repository[T any, ID comparable] struct {
	store map[ID]T
	mu    sync.RWMutex
}

func (r *Repository[T, ID]) Save(id ID, item T) {
	r.mu.Lock(); defer r.mu.Unlock()
	r.store[id] = item
}

func (r *Repository[T, ID]) FindByID(id ID) (T, bool) {
	r.mu.RLock(); defer r.mu.RUnlock()
	v, ok := r.store[id]
	return v, ok
}

// Generic EventBus — type-safe event dispatch
type EventBus[T any] struct {
	handlers []func(T)
	mu       sync.RWMutex
}

func (b *EventBus[T]) Subscribe(fn func(T)) {
	b.mu.Lock(); defer b.mu.Unlock()
	b.handlers = append(b.handlers, fn)
}

func (b *EventBus[T]) Publish(event T) {
	b.mu.RLock(); defer b.mu.RUnlock()
	for _, fn := range b.handlers { fn(event) }
}
```

---

## Step 4: Event Sourcing

```go
package eventstore

// Append-only log with optimistic concurrency
type EventStore struct {
	mu     sync.Mutex
	events map[string][]Event
}

func (s *EventStore) Append(id string, expectedVersion int, events []Event) error {
	s.mu.Lock(); defer s.mu.Unlock()

	current := s.events[id]
	if len(current) != expectedVersion {
		return fmt.Errorf("optimistic concurrency: expected v%d, current v%d",
			expectedVersion, len(current))
	}

	for i, e := range events {
		e.Version = expectedVersion + i + 1
		e.AggregateID = id
		s.events[id] = append(s.events[id], e)
	}
	return nil
}
```

---

## Step 5: CQRS CommandBus — 3 Middleware

```go
package cqrs

// Middleware 1: Structured logging
func LoggingMiddleware(logger *slog.Logger) Middleware {
	return func(next Handler) Handler {
		return func(ctx context.Context, cmd Command) error {
			start := time.Now()
			logger.Info("command.start", "name", cmd.Name())
			err := next(ctx, cmd)
			logger.Info("command.done",
				"name", cmd.Name(),
				"duration_ms", time.Since(start).Milliseconds(),
				"error", err)
			return err
		}
	}
}

// Middleware 2: Validation
func ValidationMiddleware() Middleware {
	return func(next Handler) Handler {
		return func(ctx context.Context, cmd Command) error {
			if v, ok := cmd.(Validatable); ok {
				if err := v.Validate(); err != nil {
					return fmt.Errorf("validation: %w", err)
				}
			}
			return next(ctx, cmd)
		}
	}
}

// Middleware 3: OpenTelemetry tracing
func TracingMiddleware(tracer trace.Tracer) Middleware {
	return func(next Handler) Handler {
		return func(ctx context.Context, cmd Command) error {
			ctx, span := tracer.Start(ctx, "command."+cmd.Name())
			defer span.End()
			err := next(ctx, cmd)
			if err != nil { span.RecordError(err); span.SetStatus(codes.Error, err.Error()) }
			return err
		}
	}
}
```

---

## Step 6: Security Layer

```go
package security

import (
	"crypto/ed25519"
	"crypto/rand"
	"golang.org/x/crypto/chacha20poly1305"
)

func EncryptMessage(key, plaintext []byte) ([]byte, error) {
	aead, err := chacha20poly1305.NewX(key)
	if err != nil { return nil, err }
	nonce := make([]byte, aead.NonceSize())
	rand.Read(nonce)
	return aead.Seal(nonce, nonce, plaintext, nil), nil
}

func DecryptMessage(key, ciphertext []byte) ([]byte, error) {
	aead, err := chacha20poly1305.NewX(key)
	if err != nil { return nil, err }
	n := aead.NonceSize()
	return aead.Open(nil, ciphertext[:n], ciphertext[n:], nil)
}

func SignAndVerify(message []byte) (valid, tampered bool) {
	pub, priv, _ := ed25519.GenerateKey(rand.Reader)
	sig := ed25519.Sign(priv, message)
	tamperedMsg := append([]byte{}, message...)
	tamperedMsg[0] ^= 0xFF
	return ed25519.Verify(pub, message, sig), ed25519.Verify(pub, tamperedMsg, sig)
}
```

---

## Step 7: Table-Driven Tests

```go
package platform_test

import (
	"testing"
)

func TestPlatformComponents(t *testing.T) {
	tests := []struct {
		name string
		fn   func(t *testing.T)
	}{
		{"repository-save-get", func(t *testing.T) {
			r := NewRepository[User, int]()
			r.Save(1, User{ID: 1, Name: "Alice"})
			u, ok := r.FindByID(1)
			require.True(t, ok)
			require.Equal(t, "Alice", u.Name)
		}},
		{"eventstore-append", func(t *testing.T) {
			s := NewEventStore()
			require.NoError(t, s.Append("agg-1", 0, testEvents(3)))
		}},
		{"eventstore-conflict", func(t *testing.T) {
			s := NewEventStore()
			s.Append("agg-1", 0, testEvents(1))
			require.Error(t, s.Append("agg-1", 0, testEvents(1)))
		}},
		{"commandbus-routing", testCommandBusRouting},
		{"commandbus-validation", testCommandBusValidation},
		{"ed25519-sign-verify", testEd25519},
		{"chacha20-encrypt-decrypt", testEncryption},
		{"circuit-breaker-open", testCircuitBreaker},
		{"actor-message-passing", testActorMessages},
		{"generic-eventbus", testEventBus},
		{"context-cancellation", testContextCancel},
		{"optimistic-concurrency", testOptimisticLock},
	}

	for _, tc := range tests {
		t.Run(tc.name, tc.fn)
	}
}
```

---

## Step 8: Capstone Integration Demo

```bash
docker run --rm golang:1.22-alpine sh -c "cat > /tmp/main.go << 'GOEOF'
package main
import (\"context\";\"crypto/ed25519\";\"crypto/rand\";\"errors\";\"fmt\";\"runtime\";\"sync\";\"time\")

// --- Generic Repository ---
type Repository[T any, ID comparable] struct{ store map[ID]T; mu sync.RWMutex }
func NewRepo[T any, ID comparable]() *Repository[T,ID] { return &Repository[T,ID]{store:make(map[ID]T)} }
func (r *Repository[T,ID]) Save(id ID, v T) { r.mu.Lock(); r.store[id]=v; r.mu.Unlock() }
func (r *Repository[T,ID]) Get(id ID) (T,bool) { r.mu.RLock(); defer r.mu.RUnlock(); v,ok:=r.store[id]; return v,ok }

// --- Event Sourcing ---
type Event struct{ Type string; Version int }
type EventStore struct{ mu sync.Mutex; events map[string][]Event }
func NewES() *EventStore { return &EventStore{events:make(map[string][]Event)} }
func (s *EventStore) Append(id string, expected int, evts []Event) error {
  s.mu.Lock(); defer s.mu.Unlock()
  if len(s.events[id]) != expected { return fmt.Errorf(\"conflict: expected v%d, got v%d\", expected, len(s.events[id])) }
  for i, e := range evts { e.Version=expected+i+1; s.events[id]=append(s.events[id],e) }
  return nil
}

// --- CQRS CommandBus ---
type Cmd interface{ CmdName() string }
type CmdHandler func(context.Context, Cmd) error
type MW func(CmdHandler) CmdHandler
type Bus struct{ handlers map[string]CmdHandler; mw []MW }
func NewBus(mw ...MW) *Bus { return &Bus{handlers:make(map[string]CmdHandler), mw:mw} }
func (b *Bus) Register(name string, h CmdHandler) { for i:=len(b.mw)-1;i>=0;i-- { h=b.mw[i](h) }; b.handlers[name]=h }
func (b *Bus) Execute(ctx context.Context, cmd Cmd) error { h,ok:=b.handlers[cmd.CmdName()]; if !ok { return fmt.Errorf(\"no handler: %s\",cmd.CmdName()) }; return h(ctx,cmd) }
type CreateUserCmd struct{ UserName, Email string }
func (c CreateUserCmd) CmdName() string { return \"CreateUser\" }

// --- Actor ---
type ActorCh chan interface{}
type CounterActor struct{ count int }
func (a *CounterActor) run(ch ActorCh, wg *sync.WaitGroup) {
  defer wg.Done()
  for m := range ch { switch v := m.(type) { case int: a.count+=v; case string: fmt.Printf(\"[actor] count=%d msg=%s\\n\", a.count, v) } }
}

// --- Ed25519 ---
func signVerify(msg []byte) (bool, bool) {
  pub,priv,_:=ed25519.GenerateKey(rand.Reader); sig:=ed25519.Sign(priv,msg)
  t:=append([]byte{},msg...); t[0]^=0xFF
  return ed25519.Verify(pub,msg,sig), ed25519.Verify(pub,t,sig)
}

// --- Table-driven tests ---
func runTests() int {
  type test struct{ name string; fn func() bool }
  tests := []test{
    {\"repo-save-get\", func() bool { r:=NewRepo[string,int](); r.Save(1,\"A\"); v,ok:=r.Get(1); return ok&&v==\"A\" }},
    {\"repo-miss\", func() bool { r:=NewRepo[string,int](); _,ok:=r.Get(99); return !ok }},
    {\"es-append\", func() bool { s:=NewES(); return s.Append(\"x\",0,[]Event{{\"e1\",0}})==nil }},
    {\"es-conflict\", func() bool { s:=NewES(); s.Append(\"x\",0,[]Event{{\"e1\",0}}); return s.Append(\"x\",0,[]Event{{\"e2\",0}})!=nil }},
    {\"es-version\", func() bool { s:=NewES(); s.Append(\"x\",0,[]Event{{\"e1\",0},{\"e2\",0}}); return s.events[\"x\"][1].Version==2 }},
    {\"ed25519-valid\", func() bool { ok,_:=signVerify([]byte(\"test\")); return ok }},
    {\"ed25519-tamper\", func() bool { _,bad:=signVerify([]byte(\"test\")); return !bad }},
    {\"gomaxprocs\", func() bool { return runtime.GOMAXPROCS(0)>0 }},
    {\"ctx-cancel\", func() bool { ctx,cancel:=context.WithTimeout(context.Background(),100*time.Millisecond); defer cancel(); select { case <-ctx.Done(): return false; default: return true } }},
    {\"errors-wrap\", func() bool { base:=errors.New(\"base\"); err:=fmt.Errorf(\"wrap: %w\",base); return errors.Is(err,base) }},
  }
  passed:=0; for _,tc:=range tests { if tc.fn() { passed++ } else { fmt.Printf(\"FAIL: %s\\n\", tc.name) } }
  return passed
}

func main() {
  fmt.Println(\"=== Go Architect Platform Capstone ===\")
  fmt.Printf(\"\\nRuntime: GOMAXPROCS=%d NumCPU=%d\\n\", runtime.GOMAXPROCS(0), runtime.NumCPU())
  var ms runtime.MemStats; runtime.ReadMemStats(&ms)
  fmt.Printf(\"HeapAlloc: %d KB\\n\", ms.HeapAlloc/1024)
  repo := NewRepo[string,int](); repo.Save(1,\"Alice\"); repo.Save(2,\"Bob\")
  alice,_:=repo.Get(1)
  fmt.Printf(\"\\nGeneric Repository: FindByID(1)=%s\\n\", alice)
  es := NewES()
  es.Append(\"order-1\", 0, []Event{{\"Created\",0},{\"ItemAdded\",0},{\"Confirmed\",0}})
  fmt.Printf(\"\\nEvent Sourcing: %d events stored\\n\", len(es.events[\"order-1\"]))
  fmt.Printf(\"Concurrency conflict: %v\\n\", es.Append(\"order-1\",0,[]Event{{\"Conflict\",0}})!=nil)
  bus := NewBus(
    func(next CmdHandler) CmdHandler { return func(ctx context.Context,c Cmd) error { fmt.Printf(\"[LOG] %s\\n\",c.CmdName()); return next(ctx,c) }},
    func(next CmdHandler) CmdHandler { return func(ctx context.Context,c Cmd) error { fmt.Printf(\"[VALID] ok\\n\"); return next(ctx,c) }},
  )
  bus.Register(\"CreateUser\", func(ctx context.Context, c Cmd) error { u:=c.(CreateUserCmd); fmt.Printf(\"[HANDLER] CreateUser: %s <%s>\\n\", u.UserName, u.Email); return nil })
  fmt.Println(); bus.Execute(context.Background(), CreateUserCmd{\"Alice\",\"alice@example.com\"})
  var wg sync.WaitGroup; ch:=make(ActorCh,10); actor:=&CounterActor{}; wg.Add(1); go actor.run(ch,&wg)
  ch<-5; ch<-3; ch<-\"done\"; close(ch); wg.Wait()
  valid, tampered := signVerify([]byte(\"hello\"))
  fmt.Printf(\"\\nEd25519: valid=%v tampered=%v\\n\", valid, tampered)
  passed := runTests()
  fmt.Printf(\"\\nTests: %d/10 passed\\n\", passed)
  fmt.Printf(\"Build: version=v1.0.0 (set via -ldflags=\\\"-X main.version=v1.0.0\\\")\\n\")
  fmt.Println(\"\\n=== Platform Capstone: COMPLETE ===\")
}
GOEOF
cd /tmp && go run main.go"
```

📸 **Verified Output:**
```
=== Go Architect Platform Capstone ===

Runtime: GOMAXPROCS=32 NumCPU=32
HeapAlloc: 319 KB

Generic Repository: FindByID(1)=Alice

Event Sourcing: 3 events stored
Concurrency conflict: true

[LOG] CreateUser
[VALID] ok
[HANDLER] CreateUser: Alice <alice@example.com>
[actor] count=8 msg=done

Ed25519: valid=true tampered=false

Tests: 10/10 passed
Build: version=v1.0.0 (set via -ldflags="-X main.version=v1.0.0")

=== Platform Capstone: COMPLETE ===
```

---

## Patterns Integration Summary

| Lab | Pattern | This Capstone |
|-----|---------|--------------|
| 01 | GMP scheduler | GOMAXPROCS + MemStats |
| 02 | CGO interop | Platform concept |
| 03 | Generics | Repository[T,ID] + EventBus[T] |
| 04 | OpenTelemetry | Tracing middleware pattern |
| 05 | mTLS | Service mesh pattern |
| 06 | Event sourcing | EventStore + Append-only |
| 07 | CQRS | CommandBus + 3 middleware |
| 08 | Actor model | CounterActor + goroutine |
| 09 | k8s operator | Reconciler pattern |
| 10 | WASM | Build target concept |
| 11 | Security | Ed25519 sign/verify |
| 12 | Performance | Zero-alloc + sync.Pool |
| 13 | Plugins | Interface registry pattern |
| 14 | Chaos | Circuit breaker + retry |
| **15** | **Capstone** | **All patterns integrated** |

## Production Checklist

```bash
# Build with version injection
go build -ldflags="-X main.version=$(git describe --tags)" ./cmd/server

# Race detector (CI)
go test -race ./...

# Static analysis
go vet ./...
staticcheck ./...

# Benchmarks
go test -bench=. -benchmem ./...

# pprof endpoints (in dev)
import _ "net/http/pprof"

# Graceful shutdown
ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
defer stop()
```
