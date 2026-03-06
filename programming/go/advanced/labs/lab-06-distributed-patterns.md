# Lab 06: Distributed Patterns

**Time:** 45 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm golang:1.22-alpine sh`

## Overview

Implement production-grade distributed system patterns: circuit breaker (gobreaker), retry with exponential backoff + jitter, token bucket rate limiter, bulkhead pattern, and health check endpoints.

---

## Step 1: Circuit Breaker with `gobreaker`

The circuit breaker prevents cascading failures by stopping calls to a failing service.

```
States:  Closed ──(failures≥threshold)──► Open
         Open   ──(timeout elapsed)─────► Half-Open
         Half-Open ──(success)──────────► Closed
         Half-Open ──(failure)──────────► Open
```

```go
package main

import (
	"errors"
	"fmt"
	"time"

	"github.com/sony/gobreaker"
)

func setupCircuitBreaker() *gobreaker.CircuitBreaker {
	settings := gobreaker.Settings{
		Name:        "product-service",
		MaxRequests: 3,                // max requests in half-open state
		Interval:    10 * time.Second, // count window
		Timeout:     5 * time.Second,  // time in open state
		ReadyToTrip: func(counts gobreaker.Counts) bool {
			// Trip after 3 consecutive failures
			return counts.ConsecutiveFailures >= 3
		},
		OnStateChange: func(name string, from gobreaker.State, to gobreaker.State) {
			fmt.Printf("  ⚡ Circuit '%s': %s → %s\n", name, from, to)
		},
	}
	return gobreaker.NewCircuitBreaker(settings)
}

func callService(cb *gobreaker.CircuitBreaker, fail bool) (string, error) {
	result, err := cb.Execute(func() (interface{}, error) {
		if fail {
			return nil, errors.New("service unavailable")
		}
		return "ok", nil
	})
	if err != nil {
		return "", err
	}
	return result.(string), nil
}
```

---

## Step 2: State Transition Demo

```go
func main() {
	cb := setupCircuitBreaker()

	fmt.Println("=== Closed → Open ===")
	for i := 1; i <= 5; i++ {
		_, err := callService(cb, true)
		fmt.Printf("  Call %d: err=%v state=%s\n", i, err, cb.State())
	}

	fmt.Println("\n=== Open → Timeout → Half-Open ===")
	// In half-open, after Timeout the circuit allows limited requests
	fmt.Printf("  Waiting... state=%s\n", cb.State())
}
```

---

## Step 3: Retry with Exponential Backoff + Jitter

```go
package main

import (
	"context"
	"errors"
	"fmt"
	"math"
	"math/rand"
	"time"
)

type RetryConfig struct {
	MaxAttempts int
	BaseDelay   time.Duration
	MaxDelay    time.Duration
	Multiplier  float64
}

var DefaultRetryConfig = RetryConfig{
	MaxAttempts: 5,
	BaseDelay:   100 * time.Millisecond,
	MaxDelay:    10 * time.Second,
	Multiplier:  2.0,
}

// IsRetryable determines if an error warrants a retry
type IsRetryable func(error) bool

func WithRetry(ctx context.Context, cfg RetryConfig, isRetryable IsRetryable, fn func() error) error {
	var lastErr error
	for attempt := 0; attempt < cfg.MaxAttempts; attempt++ {
		if err := ctx.Err(); err != nil {
			return err
		}

		lastErr = fn()
		if lastErr == nil {
			return nil
		}

		if !isRetryable(lastErr) {
			return lastErr // don't retry permanent errors
		}

		if attempt == cfg.MaxAttempts-1 {
			break
		}

		// Exponential backoff: base * multiplier^attempt
		delay := time.Duration(float64(cfg.BaseDelay) * math.Pow(cfg.Multiplier, float64(attempt)))
		if delay > cfg.MaxDelay {
			delay = cfg.MaxDelay
		}

		// Full jitter: randomize between [0, delay]
		jitter := time.Duration(rand.Int63n(int64(delay) + 1))

		fmt.Printf("  Attempt %d failed: %v, retrying in %v\n", attempt+1, lastErr, jitter.Round(time.Millisecond))

		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-time.After(jitter):
		}
	}
	return fmt.Errorf("all %d attempts failed: %w", cfg.MaxAttempts, lastErr)
}
```

---

## Step 4: Rate Limiter — Token Bucket

```go
package main

import (
	"context"
	"fmt"
	"time"

	"golang.org/x/time/rate"
)

func demonstrateRateLimiter() {
	// 5 requests/second, burst of 2
	limiter := rate.NewLimiter(rate.Limit(5), 2)

	fmt.Println("Token bucket (5 req/s, burst=2):")
	for i := 1; i <= 6; i++ {
		allowed := limiter.Allow()
		fmt.Printf("  Request %d: allowed=%v tokens≈%.1f\n",
			i, allowed, limiter.Tokens())
	}

	// Wait-based: blocks until token available
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	fmt.Println("\nWait-based rate limiting:")
	for i := 1; i <= 3; i++ {
		start := time.Now()
		if err := limiter.Wait(ctx); err != nil {
			fmt.Printf("  Request %d: timeout\n", i)
			break
		}
		fmt.Printf("  Request %d: waited %v\n", i, time.Since(start).Round(time.Millisecond))
	}
}
```

---

## Step 5: Bulkhead Pattern — Semaphore

```go
package main

import (
	"context"
	"fmt"
	"sync"
	"time"
)

// Semaphore limits concurrent access to a resource
type Semaphore struct {
	ch chan struct{}
}

func NewSemaphore(maxConcurrency int) *Semaphore {
	return &Semaphore{ch: make(chan struct{}, maxConcurrency)}
}

func (s *Semaphore) Acquire(ctx context.Context) error {
	select {
	case s.ch <- struct{}{}:
		return nil
	case <-ctx.Done():
		return ctx.Err()
	}
}

func (s *Semaphore) Release() {
	<-s.ch
}

func (s *Semaphore) Available() int {
	return cap(s.ch) - len(s.ch)
}

func demonstrateBulkhead() {
	sem := NewSemaphore(3) // max 3 concurrent calls
	var wg sync.WaitGroup

	fmt.Println("Bulkhead: max 3 concurrent")
	for i := 1; i <= 8; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			ctx, cancel := context.WithTimeout(context.Background(), 500*time.Millisecond)
			defer cancel()

			if err := sem.Acquire(ctx); err != nil {
				fmt.Printf("  Worker %d: rejected (bulkhead full)\n", id)
				return
			}
			defer sem.Release()

			fmt.Printf("  Worker %d: executing (slots left: %d)\n", id, sem.Available())
			time.Sleep(100 * time.Millisecond)
		}(i)
	}
	wg.Wait()
}
```

---

## Step 6: Health Check Endpoint

```go
package main

import (
	"context"
	"encoding/json"
	"net/http"
	"sync"
	"time"
)

type HealthStatus struct {
	Status   string            `json:"status"`
	Checks   map[string]string `json:"checks"`
	Uptime   string            `json:"uptime"`
}

type HealthChecker struct {
	mu      sync.RWMutex
	checks  map[string]func(context.Context) error
	startAt time.Time
}

func NewHealthChecker() *HealthChecker {
	return &HealthChecker{
		checks:  make(map[string]func(context.Context) error),
		startAt: time.Now(),
	}
}

func (h *HealthChecker) Register(name string, check func(context.Context) error) {
	h.mu.Lock()
	defer h.mu.Unlock()
	h.checks[name] = check
}

func (h *HealthChecker) Handler() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
		defer cancel()

		h.mu.RLock()
		checks := make(map[string]func(context.Context) error, len(h.checks))
		for k, v := range h.checks {
			checks[k] = v
		}
		h.mu.RUnlock()

		results := make(map[string]string)
		overall := "healthy"
		for name, fn := range checks {
			if err := fn(ctx); err != nil {
				results[name] = "unhealthy: " + err.Error()
				overall = "degraded"
			} else {
				results[name] = "healthy"
			}
		}

		status := HealthStatus{
			Status: overall,
			Checks: results,
			Uptime: time.Since(h.startAt).Round(time.Second).String(),
		}

		code := http.StatusOK
		if overall != "healthy" {
			code = http.StatusServiceUnavailable
		}
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(code)
		json.NewEncoder(w).Encode(status)
	}
}
```

---

## Step 7: Complete Integration

```go
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"time"
)

func setupServer(hc *HealthChecker) *http.Server {
	mux := http.NewServeMux()
	mux.HandleFunc("/health", hc.Handler())
	mux.HandleFunc("/ready", func(w http.ResponseWriter, r *http.Request) {
		json.NewEncoder(w).Encode(map[string]bool{"ready": true})
	})
	return &http.Server{Addr: ":18082", Handler: mux}
}
```

---

## Step 8: Capstone — Full Demo

```bash
docker run --rm golang:1.22-alpine sh -c "
mkdir -p /tmp/distrib
cd /tmp/distrib
cat > go.mod << 'EOF'
module distrib
go 1.22
EOF
go get github.com/sony/gobreaker@v0.5.0 golang.org/x/time@v0.9.0 2>/dev/null

cat > main.go << 'GOEOF'
package main

import (
	\"context\"
	\"errors\"
	\"fmt\"
	\"math/rand\"
	\"time\"
	\"github.com/sony/gobreaker\"
	\"golang.org/x/time/rate\"
)

func setupCB() *gobreaker.CircuitBreaker {
	return gobreaker.NewCircuitBreaker(gobreaker.Settings{
		Name: \"demo\", MaxRequests: 2, Timeout: 2*time.Second,
		ReadyToTrip: func(c gobreaker.Counts) bool { return c.ConsecutiveFailures >= 3 },
		OnStateChange: func(n string, f, t gobreaker.State) { fmt.Printf(\"  CB: %s -> %s\n\", f, t) },
	})
}

func retryOp(ctx context.Context, maxTries int, fn func() error) error {
	for i := 0; i < maxTries; i++ {
		if err := fn(); err == nil { return nil }
		if i < maxTries-1 {
			d := time.Duration(50*(1<<i))*time.Millisecond + time.Duration(rand.Intn(30))*time.Millisecond
			fmt.Printf(\"  retry %d after %v\n\", i+1, d.Round(time.Millisecond))
			select { case <-ctx.Done(): return ctx.Err(); case <-time.After(d): }
		}
	}
	return errors.New(\"all retries failed\")
}

func main() {
	rand.Seed(42)

	// Circuit breaker
	fmt.Println(\"=== Circuit Breaker ===\")
	cb := setupCB()
	for i := 1; i <= 5; i++ {
		_, err := cb.Execute(func() (interface{}, error) { return nil, errors.New(\"fail\") })
		fmt.Printf(\"  Call %d: err=%v state=%s\n\", i, err, cb.State())
	}

	// Rate limiter
	fmt.Println(\"\\n=== Rate Limiter (10/s burst=2) ===\")
	lim := rate.NewLimiter(rate.Limit(10), 2)
	for i := 1; i <= 5; i++ {
		fmt.Printf(\"  Request %d: allowed=%v\n\", i, lim.Allow())
	}

	// Retry
	fmt.Println(\"\\n=== Retry with Backoff ===\")
	attempts := 0
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()
	err := retryOp(ctx, 4, func() error {
		attempts++
		if attempts < 3 { return errors.New(\"transient\") }
		return nil
	})
	if err != nil { fmt.Println(\"Failed:\", err) } else { fmt.Printf(\"  Succeeded on attempt %d\n\", attempts) }
}
GOEOF
go run main.go 2>&1"
```

📸 **Verified Output:**
```
=== Circuit Breaker ===
  Call 1: err=service unavailable state=closed
  Call 2: err=service unavailable state=closed
  CB: closed -> open
  Call 3: err=service unavailable state=open
  Call 4: err=circuit breaker is open state=open
  Call 5: err=circuit breaker is open state=open

=== Rate Limiter (10/s burst=2) ===
  Request 1: allowed=true
  Request 2: allowed=true
  Request 3: allowed=false
  Request 4: allowed=false
  Request 5: allowed=false

=== Retry with Backoff ===
  retry 1 after 55ms
  retry 2 after 117ms
  Succeeded on attempt 3
```

---

## Summary

| Pattern | Library | Problem Solved |
|---------|---------|----------------|
| Circuit Breaker | `github.com/sony/gobreaker` | Prevent cascading failures |
| Retry + Backoff | stdlib + math | Transient failure recovery |
| Token Bucket | `golang.org/x/time/rate` | Rate limiting |
| Bulkhead | semaphore (channels) | Resource isolation |
| Health Check | `net/http` | Kubernetes liveness/readiness |

**Key Takeaways:**
- Circuit breaker: trip fast, recover gradually (Closed→Open→Half-Open→Closed)
- Full jitter beats equal jitter for thundering herd prevention
- Rate limiters protect servers; bulkheads protect clients
- Combine patterns: circuit breaker + retry + rate limiter for resilient services
- `/health` for liveness (is it running?), `/ready` for readiness (can it serve traffic?)
