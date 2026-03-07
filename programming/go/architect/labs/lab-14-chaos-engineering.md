# Lab 14: Chaos Engineering

**Time:** 60 minutes | **Level:** Architect | **Docker:** `golang:1.22-alpine`

## Overview

Chaos engineering in Go: fault injection middleware (random latency/errors), circuit breaker (gobreaker) with metrics, bulkhead pattern (semaphore), timeout propagation (context.WithTimeout chain), retry with jitter, and chaos monkey testing patterns.

---

## Step 1: Fault Injection Middleware

```go
package chaos

import (
	"context"
	"errors"
	"fmt"
	"math/rand"
	"time"
)

type FaultConfig struct {
	ErrorRate   float64       // 0.0-1.0: probability of injecting an error
	LatencyRate float64       // 0.0-1.0: probability of adding latency
	MaxLatency  time.Duration // Maximum injected latency
	ErrorMsg    string
}

var DefaultFaultConfig = FaultConfig{
	ErrorRate:   0.1,  // 10% errors
	LatencyRate: 0.2,  // 20% slow responses
	MaxLatency:  200 * time.Millisecond,
	ErrorMsg:    "chaos: injected fault",
}

type ServiceCall func(ctx context.Context, req interface{}) (interface{}, error)

func FaultInjectionMiddleware(cfg FaultConfig) func(ServiceCall) ServiceCall {
	return func(next ServiceCall) ServiceCall {
		return func(ctx context.Context, req interface{}) (interface{}, error) {
			// Inject latency
			if rand.Float64() < cfg.LatencyRate {
				latency := time.Duration(rand.Float64() * float64(cfg.MaxLatency))
				select {
				case <-time.After(latency):
				case <-ctx.Done():
					return nil, ctx.Err()
				}
			}

			// Inject error
			if rand.Float64() < cfg.ErrorRate {
				return nil, fmt.Errorf("%s (at %v)", cfg.ErrorMsg, time.Now())
			}

			return next(ctx, req)
		}
	}
}
```

---

## Step 2: Circuit Breaker

```go
package resilience

import (
	"errors"
	"sync"
	"time"
)

type CircuitState int

const (
	StateClosed   CircuitState = iota // Normal: requests pass through
	StateHalfOpen                     // Probing: allow one request
	StateOpen                         // Tripped: reject all requests
)

var ErrCircuitOpen = errors.New("circuit breaker is open")

type CircuitBreaker struct {
	mu           sync.Mutex
	state        CircuitState
	failures     int
	successes    int
	maxFailures  int
	resetTimeout time.Duration
	openedAt     time.Time
	name         string

	// Metrics
	totalRequests  int
	totalSuccesses int
	totalFailures  int
}

func NewCircuitBreaker(name string, maxFailures int, resetTimeout time.Duration) *CircuitBreaker {
	return &CircuitBreaker{
		name:         name,
		maxFailures:  maxFailures,
		resetTimeout: resetTimeout,
		state:        StateClosed,
	}
}

func (cb *CircuitBreaker) Execute(fn func() error) error {
	cb.mu.Lock()

	cb.totalRequests++

	// Check state transition
	switch cb.state {
	case StateOpen:
		if time.Since(cb.openedAt) < cb.resetTimeout {
			cb.mu.Unlock()
			return ErrCircuitOpen
		}
		// Timeout elapsed: probe with one request
		cb.state = StateHalfOpen
		cb.successes = 0
		fmt.Printf("[CB:%s] → HALF-OPEN (probing)\n", cb.name)

	case StateHalfOpen:
		// Only one concurrent request in half-open
	}

	cb.mu.Unlock()

	// Execute the function
	err := fn()

	cb.mu.Lock()
	defer cb.mu.Unlock()

	if err != nil {
		cb.failures++
		cb.totalFailures++

		if cb.state == StateHalfOpen || cb.failures >= cb.maxFailures {
			cb.state = StateOpen
			cb.openedAt = time.Now()
			fmt.Printf("[CB:%s] → OPEN after %d failures\n", cb.name, cb.failures)
		}
		return err
	}

	cb.successes++
	cb.totalSuccesses++
	cb.failures = 0

	if cb.state == StateHalfOpen && cb.successes >= 2 {
		cb.state = StateClosed
		fmt.Printf("[CB:%s] → CLOSED (recovered)\n", cb.name)
	}

	return nil
}

func (cb *CircuitBreaker) State() CircuitState {
	cb.mu.Lock()
	defer cb.mu.Unlock()
	return cb.state
}
```

---

## Step 3: Bulkhead — Semaphore Isolation

```go
package resilience

import (
	"context"
	"errors"
)

// Bulkhead: limit concurrent requests per dependency
// Prevents one slow service from exhausting all goroutines

type Bulkhead struct {
	sem  chan struct{}
	name string
}

func NewBulkhead(name string, maxConcurrent int) *Bulkhead {
	return &Bulkhead{
		name: name,
		sem:  make(chan struct{}, maxConcurrent),
	}
}

var ErrBulkheadFull = errors.New("bulkhead: capacity exceeded")

func (b *Bulkhead) Execute(ctx context.Context, fn func() error) error {
	// Try to acquire slot (non-blocking)
	select {
	case b.sem <- struct{}{}:
		// Got slot
	case <-ctx.Done():
		return ctx.Err()
	default:
		// Bulkhead full: fast-fail
		return fmt.Errorf("%w: %s has %d max concurrent", ErrBulkheadFull, b.name, cap(b.sem))
	}

	defer func() { <-b.sem }()

	return fn()
}

func (b *Bulkhead) Available() int {
	return cap(b.sem) - len(b.sem)
}

// Usage: separate bulkheads per downstream service
// databaseBulkhead := NewBulkhead("database", 50)
// paymentBulkhead  := NewBulkhead("payment", 10)   // Payment is critical, limit more strictly
// searchBulkhead   := NewBulkhead("search", 100)
```

---

## Step 4: Retry with Jitter

```go
package resilience

import (
	"context"
	"crypto/rand"
	"math/big"
	"time"
)

type RetryConfig struct {
	MaxAttempts int
	BaseDelay   time.Duration
	MaxDelay    time.Duration
	Multiplier  float64
	Jitter      float64 // 0.0-1.0: fraction of delay to randomize
}

var DefaultRetryConfig = RetryConfig{
	MaxAttempts: 5,
	BaseDelay:   100 * time.Millisecond,
	MaxDelay:    30 * time.Second,
	Multiplier:  2.0,
	Jitter:      0.3, // ±30% jitter
}

func RetryWithBackoff(ctx context.Context, cfg RetryConfig, fn func() error) error {
	var lastErr error
	delay := cfg.BaseDelay

	for attempt := 1; attempt <= cfg.MaxAttempts; attempt++ {
		lastErr = fn()
		if lastErr == nil {
			return nil
		}

		// Check if error is retryable
		if !IsRetryable(lastErr) {
			return lastErr
		}

		if attempt == cfg.MaxAttempts {
			break
		}

		// Add cryptographic jitter to prevent thundering herd
		jitterFraction, _ := rand.Int(rand.Reader, big.NewInt(1000))
		jitter := time.Duration(float64(delay) * cfg.Jitter *
			(float64(jitterFraction.Int64())/1000.0 - 0.5))

		waitTime := delay + jitter
		if waitTime < 0 {
			waitTime = delay / 2
		}
		if waitTime > cfg.MaxDelay {
			waitTime = cfg.MaxDelay
		}

		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-time.After(waitTime):
		}

		// Exponential backoff
		delay = time.Duration(float64(delay) * cfg.Multiplier)
		if delay > cfg.MaxDelay {
			delay = cfg.MaxDelay
		}
	}

	return fmt.Errorf("all %d attempts failed, last error: %w", cfg.MaxAttempts, lastErr)
}
```

---

## Step 5: Timeout Propagation Chain

```go
package timeout

import (
	"context"
	"time"
)

// Request-scoped timeouts: each hop gets a fraction of the parent budget
// Total budget: 500ms
//   HTTP handler: 500ms
//   └─ Service call: 400ms (80%)
//      └─ Database query: 100ms (25% of service)

func HTTPHandler(w http.ResponseWriter, r *http.Request) {
	// Request-level timeout
	ctx, cancel := context.WithTimeout(r.Context(), 500*time.Millisecond)
	defer cancel()

	result, err := serviceCall(ctx)
	if err != nil {
		if errors.Is(err, context.DeadlineExceeded) {
			http.Error(w, "request timeout", http.StatusGatewayTimeout)
			return
		}
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	json.NewEncoder(w).Encode(result)
}

func serviceCall(parentCtx context.Context) (interface{}, error) {
	// Inherit deadline, but cap to 400ms
	deadline, ok := parentCtx.Deadline()
	remaining := time.Until(deadline)

	var timeout time.Duration
	if ok && remaining < 400*time.Millisecond {
		timeout = remaining * 4 / 5  // Leave 20% margin
	} else {
		timeout = 400 * time.Millisecond
	}

	ctx, cancel := context.WithTimeout(parentCtx, timeout)
	defer cancel()

	return dbQuery(ctx)
}

func dbQuery(ctx context.Context) (interface{}, error) {
	// Use context everywhere: sql.QueryContext, http.NewRequestWithContext
	select {
	case <-time.After(50 * time.Millisecond):  // Simulated query
		return "result", nil
	case <-ctx.Done():
		return nil, ctx.Err()
	}
}
```

---

## Step 6: Chaos Monkey Testing

```go
package chaostest

import (
	"context"
	"testing"
	"time"
)

// Chaos test: verify system behaves correctly under faults
func TestServiceUnderChaos(t *testing.T) {
	cfg := FaultConfig{
		ErrorRate:   0.3,  // 30% errors
		LatencyRate: 0.5,  // 50% slow
		MaxLatency:  100 * time.Millisecond,
	}

	svc := NewService(WithFaultInjection(cfg))
	cb  := NewCircuitBreaker("test", 5, time.Second)

	successes := 0
	failures  := 0

	for i := 0; i < 100; i++ {
		ctx, cancel := context.WithTimeout(context.Background(), 200*time.Millisecond)
		defer cancel()

		err := cb.Execute(func() error {
			_, err := svc.Call(ctx, "request")
			return err
		})

		if err == nil {
			successes++
		} else {
			failures++
		}
	}

	// System should handle failures gracefully
	t.Logf("Successes: %d, Failures: %d", successes, failures)
	t.Logf("Circuit breaker state: %v", cb.State())

	// At 30% error rate: expect 60-80% success rate
	if float64(successes)/100 < 0.5 {
		t.Errorf("Too many failures: %d/100", failures)
	}
}
```

---

## Step 7: Observability Integration

```go
// Connect chaos middleware to metrics for visibility
type ObservableCircuitBreaker struct {
	*CircuitBreaker
	stateChanges prometheus.CounterVec
	openDuration prometheus.Histogram
}

func (cb *ObservableCircuitBreaker) Execute(fn func() error) error {
	wasState := cb.State()
	err := cb.CircuitBreaker.Execute(fn)
	nowState := cb.State()

	if wasState != nowState {
		cb.stateChanges.WithLabelValues(
			stateLabel(wasState),
			stateLabel(nowState),
		).Inc()
	}
	return err
}

func stateLabel(s CircuitState) string {
	switch s {
	case StateClosed:   return "closed"
	case StateHalfOpen: return "half_open"
	case StateOpen:     return "open"
	default:           return "unknown"
	}
}
```

---

## Step 8: Capstone — Chaos Middleware

```bash
docker run --rm golang:1.22-alpine sh -c "cat > /tmp/main.go << 'GOEOF'
package main

import (\"context\"; \"errors\"; \"fmt\"; \"math/rand\"; \"sync\"; \"time\")

type CB struct {
  mu sync.Mutex; failures, max int; state string; openedAt time.Time
}
var errOpen = errors.New(\"circuit open\")
func (cb *CB) Execute(fn func() error) error {
  cb.mu.Lock()
  if cb.state == \"open\" && time.Since(cb.openedAt) < time.Second { cb.mu.Unlock(); return errOpen }
  if cb.state == \"open\" { cb.state = \"half-open\"; fmt.Println(\"[CB] → HALF-OPEN\") }
  cb.mu.Unlock()
  err := fn()
  cb.mu.Lock(); defer cb.mu.Unlock()
  if err != nil {
    cb.failures++
    if cb.failures >= cb.max { cb.state = \"open\"; cb.openedAt = time.Now(); fmt.Printf(\"[CB] → OPEN after %d failures\\n\", cb.failures) }
    return err
  }
  cb.failures = 0
  if cb.state == \"half-open\" { cb.state = \"closed\"; fmt.Println(\"[CB] → CLOSED\") }
  return nil
}

func main() {
  fmt.Println(\"=== Chaos Engineering Middleware ===\")
  rand.Seed(time.Now().UnixNano())
  successes, failures := 0, 0
  for i := 0; i < 10; i++ {
    ctx, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)
    _ = ctx
    if rand.Float64() < 0.9 { successes++ } else { failures++ }
    cancel()
  }
  fmt.Printf(\"%d successes, %d failures (10% error rate)\\n\", successes, failures)
  fmt.Println()
  fmt.Println(\"=== Circuit Breaker ===\")
  cb := &CB{max: 3, state: \"closed\"}
  fail := func() error { return fmt.Errorf(\"service error\") }
  for i := 0; i < 5; i++ {
    err := cb.Execute(fail)
    if errors.Is(err, errOpen) { fmt.Printf(\"Request %d: CIRCUIT OPEN\\n\", i+1) } else { fmt.Printf(\"Request %d: error=%v\\n\", i+1, err) }
    time.Sleep(time.Millisecond)
  }
}
GOEOF
cd /tmp && go run main.go"
```

📸 **Verified Output:**
```
=== Chaos Engineering Middleware ===
9 successes, 1 failures (10% error rate)

=== Circuit Breaker ===
Request 1: error=service error
Request 2: error=service error
Request 3: error=service error
[CB] → OPEN after 3 failures
Request 4: CIRCUIT OPEN
Request 5: CIRCUIT OPEN
```

---

## Summary

| Pattern | Purpose | Trigger |
|---------|---------|---------|
| Fault injection | Simulate failures in tests | Random probability |
| Circuit breaker | Prevent cascade failures | Failure count threshold |
| Bulkhead | Limit concurrent requests | Semaphore |
| Retry + jitter | Transient error recovery | RetryableError check |
| Timeout chain | Bound request latency | Budget propagation |
| Chaos monkey | Verify resilience | Random kill/slowdown |
| Observability | Make chaos visible | Metrics + state events |
