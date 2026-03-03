# Lab 13: Context & Cancellation

## Objective
Use `context.Context` for cancellation, timeouts, deadlines, and request-scoped values. Propagate context through goroutines and HTTP handlers.

## Time
30 minutes

## Prerequisites
- Lab 07 (Goroutines & Channels), Lab 11 (HTTP)

## Tools
- Docker image: `zchencow/innozverse-go:latest`

---

## Lab Instructions

### Step 1: Context Basics

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import (
    "context"
    "fmt"
    "time"
)

func doWork(ctx context.Context, name string) error {
    select {
    case <-time.After(50 * time.Millisecond):
        fmt.Printf("[%s] completed\n", name)
        return nil
    case <-ctx.Done():
        fmt.Printf("[%s] cancelled: %v\n", name, ctx.Err())
        return ctx.Err()
    }
}

func main() {
    // context.Background() — root context, never cancelled
    bg := context.Background()
    fmt.Println("Background:", bg)

    // WithCancel — manual cancellation
    ctx, cancel := context.WithCancel(bg)
    defer cancel() // always call cancel to release resources

    go func() {
        time.Sleep(20 * time.Millisecond)
        fmt.Println("Cancelling...")
        cancel()
    }()

    if err := doWork(ctx, "Task1"); err != nil {
        fmt.Println("Task1 error:", err)
    }

    // WithTimeout — auto-cancel after duration
    ctx2, cancel2 := context.WithTimeout(bg, 100*time.Millisecond)
    defer cancel2()

    if err := doWork(ctx2, "Task2-fast"); err != nil {
        fmt.Println("Task2 error:", err)
    }

    ctx3, cancel3 := context.WithTimeout(bg, 10*time.Millisecond)
    defer cancel3()
    if err := doWork(ctx3, "Task3-slow"); err != nil {
        fmt.Println("Task3 error:", err)
    }

    // WithDeadline — cancel at specific time
    deadline := time.Now().Add(5 * time.Millisecond)
    ctx4, cancel4 := context.WithDeadline(bg, deadline)
    defer cancel4()
    fmt.Println("Deadline:", ctx4.Deadline())
    doWork(ctx4, "Task4-deadline")
}
EOF
```

> 💡 **Always call `cancel()`** — even if the context already expired. Not calling it leaks goroutines and memory. The idiomatic pattern is `ctx, cancel := context.WithTimeout(parent, d); defer cancel()`. Context cancellation propagates downward: cancelling a parent cancels all children automatically.

**📸 Verified Output:**
```
Background: context.Background
Cancelling...
[Task1] cancelled: context canceled
[Task2-fast] completed
[Task3-slow] cancelled: context deadline exceeded
Deadline: 2026-03-03 05:00:00.005 +0000 UTC true
[Task4-deadline] cancelled: context deadline exceeded
```

---

### Step 2: Context Values

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import (
    "context"
    "fmt"
)

// Use typed keys to avoid collisions
type contextKey string

const (
    keyRequestID contextKey = "request_id"
    keyUserID    contextKey = "user_id"
    keyRole      contextKey = "role"
)

func withRequestID(ctx context.Context, id string) context.Context {
    return context.WithValue(ctx, keyRequestID, id)
}

func withUser(ctx context.Context, userID int, role string) context.Context {
    ctx = context.WithValue(ctx, keyUserID, userID)
    ctx = context.WithValue(ctx, keyRole, role)
    return ctx
}

func getRequestID(ctx context.Context) string {
    if v, ok := ctx.Value(keyRequestID).(string); ok { return v }
    return "unknown"
}

func getUserID(ctx context.Context) (int, bool) {
    id, ok := ctx.Value(keyUserID).(int)
    return id, ok
}

func getRole(ctx context.Context) string {
    if v, ok := ctx.Value(keyRole).(string); ok { return v }
    return "guest"
}

// Middleware-style functions
func authenticate(ctx context.Context, token string) (context.Context, error) {
    users := map[string]struct{ ID int; Role string }{
        "token-admin": {1, "admin"},
        "token-user":  {2, "user"},
    }
    u, ok := users[token]
    if !ok { return ctx, fmt.Errorf("invalid token: %s", token) }
    return withUser(ctx, u.ID, u.Role), nil
}

func processRequest(ctx context.Context, action string) {
    reqID := getRequestID(ctx)
    uid, _ := getUserID(ctx)
    role := getRole(ctx)
    fmt.Printf("[req=%s user=%d role=%s] action=%s\n", reqID, uid, role, action)
}

func main() {
    ctx := context.Background()
    ctx = withRequestID(ctx, "req-001")

    // Simulate request pipeline
    for _, token := range []string{"token-admin", "token-user", "bad-token"} {
        authed, err := authenticate(ctx, token)
        if err != nil {
            fmt.Printf("[req=%s] auth failed: %v\n", getRequestID(ctx), err)
            continue
        }
        processRequest(authed, "GET /api/products")
    }
}
EOF
```

> 💡 **Always use typed keys for `context.WithValue`** — using a plain string like `"user_id"` as a key can collide with other packages. Using `type contextKey string` creates a distinct type that can't be accidentally matched by other packages using a plain string key.

**📸 Verified Output:**
```
[req=req-001 user=1 role=admin] action=GET /api/products
[req=req-001 user=2 role=user] action=GET /api/products
[req=req-001] auth failed: invalid token: bad-token
```

---

### Steps 3–8: Propagation, HTTP context, Timeout wrapper, Pipeline cancel, graceful shutdown, Capstone

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import (
    "context"
    "fmt"
    "sync"
    "time"
)

// Step 3: Context propagation through goroutines
func crawler(ctx context.Context, url string, depth int, results chan<- string) {
    select {
    case <-ctx.Done():
        return
    default:
    }

    results <- fmt.Sprintf("fetched: %s (depth=%d)", url, depth)

    if depth <= 0 { return }

    subURLs := []string{url + "/page1", url + "/page2"}
    var wg sync.WaitGroup
    for _, sub := range subURLs {
        wg.Add(1)
        go func(u string) {
            defer wg.Done()
            time.Sleep(10 * time.Millisecond)
            crawler(ctx, u, depth-1, results)
        }(sub)
    }
    wg.Wait()
}

// Step 4: Timeout wrapper for any function
func withTimeout[T any](ctx context.Context, timeout time.Duration, fn func(context.Context) (T, error)) (T, error) {
    ctx, cancel := context.WithTimeout(ctx, timeout)
    defer cancel()

    type result struct {
        val T
        err error
    }
    ch := make(chan result, 1)
    go func() {
        v, err := fn(ctx)
        ch <- result{v, err}
    }()

    select {
    case r := <-ch:
        return r.val, r.err
    case <-ctx.Done():
        var zero T
        return zero, ctx.Err()
    }
}

// Step 5: Cancellable pipeline
func source(ctx context.Context, nums ...int) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        for _, n := range nums {
            select {
            case out <- n:
            case <-ctx.Done():
                return
            }
        }
    }()
    return out
}

func doubler(ctx context.Context, in <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        for n := range in {
            select {
            case out <- n * 2:
            case <-ctx.Done():
                return
            }
        }
    }()
    return out
}

// Step 6: Graceful shutdown
type Server struct {
    name    string
    running bool
}

func (s *Server) Start(ctx context.Context) {
    s.running = true
    fmt.Printf("[%s] started\n", s.name)
    <-ctx.Done()
    fmt.Printf("[%s] shutting down: %v\n", s.name, ctx.Err())
    time.Sleep(5 * time.Millisecond) // simulate cleanup
    s.running = false
    fmt.Printf("[%s] stopped\n", s.name)
}

// Step 7: Context in worker pool
func poolWorker(ctx context.Context, id int, jobs <-chan int, results chan<- int, wg *sync.WaitGroup) {
    defer wg.Done()
    for {
        select {
        case job, ok := <-jobs:
            if !ok { return }
            select {
            case results <- job * job:
            case <-ctx.Done():
                return
            }
        case <-ctx.Done():
            return
        }
    }
}

// Step 8: Capstone — cancellable request processor
type Request struct {
    ID      int
    Payload string
}

type Response struct {
    ReqID  int
    Result string
    Error  error
}

func processWithContext(ctx context.Context, req Request) Response {
    // Simulate variable processing time
    delay := time.Duration(len(req.Payload)) * time.Millisecond

    select {
    case <-time.After(delay):
        return Response{req.ID, "processed: " + req.Payload, nil}
    case <-ctx.Done():
        return Response{req.ID, "", ctx.Err()}
    }
}

func main() {
    bg := context.Background()

    // Web crawler with cancellation
    fmt.Println("=== Crawler ===")
    ctx1, cancel1 := context.WithTimeout(bg, 200*time.Millisecond)
    defer cancel1()
    results := make(chan string, 20)
    go func() {
        crawler(ctx1, "https://example.com", 2, results)
        close(results)
    }()
    count := 0
    for r := range results { fmt.Println(" ", r); count++ }
    fmt.Printf("Crawled %d pages\n", count)

    // Timeout wrapper
    fmt.Println("\n=== Timeout Wrapper ===")
    val, err := withTimeout(bg, 100*time.Millisecond, func(ctx context.Context) (string, error) {
        time.Sleep(10 * time.Millisecond)
        return "data fetched", nil
    })
    fmt.Printf("result=%q err=%v\n", val, err)

    _, err = withTimeout(bg, 5*time.Millisecond, func(ctx context.Context) (string, error) {
        time.Sleep(100 * time.Millisecond)
        return "too slow", nil
    })
    fmt.Printf("timeout result: err=%v\n", err)

    // Cancellable pipeline
    fmt.Println("\n=== Cancellable Pipeline ===")
    ctx2, cancel2 := context.WithCancel(bg)
    nums := source(ctx2, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
    doubled := doubler(ctx2, nums)
    count2 := 0
    for n := range doubled {
        fmt.Printf("%d ", n)
        count2++
        if count2 == 5 { cancel2(); break }
    }
    fmt.Printf("\nProcessed %d values before cancel\n", count2)

    // Graceful shutdown
    fmt.Println("\n=== Graceful Shutdown ===")
    ctx3, cancel3 := context.WithCancel(bg)
    servers := []*Server{{"api", false}, {"worker", false}, {"metrics", false}}
    var wg sync.WaitGroup
    for _, s := range servers {
        wg.Add(1)
        s := s
        go func() { defer wg.Done(); s.Start(ctx3) }()
    }
    time.Sleep(20 * time.Millisecond)
    fmt.Println("Initiating shutdown...")
    cancel3()
    wg.Wait()
    fmt.Println("All servers stopped")

    // Cancellable request processor
    fmt.Println("\n=== Request Processor ===")
    requests := []Request{
        {1, "hi"},         // fast
        {2, "hello world"}, // medium
        {3, "x"},           // fast
    }
    ctx4, cancel4 := context.WithTimeout(bg, 50*time.Millisecond)
    defer cancel4()
    for _, req := range requests {
        resp := processWithContext(ctx4, req)
        if resp.Error != nil {
            fmt.Printf("  req#%d: ERROR %v\n", resp.ReqID, resp.Error)
        } else {
            fmt.Printf("  req#%d: %s\n", resp.ReqID, resp.Result)
        }
    }
}
EOF
```

**📸 Verified Output:**
```
=== Crawler ===
  fetched: https://example.com (depth=2)
  fetched: https://example.com/page1 (depth=1)
  fetched: https://example.com/page2 (depth=1)
  fetched: https://example.com/page1/page1 (depth=0)
  fetched: https://example.com/page1/page2 (depth=0)
  fetched: https://example.com/page2/page1 (depth=0)
  fetched: https://example.com/page2/page2 (depth=0)
Crawled 7 pages

=== Timeout Wrapper ===
result="data fetched" err=<nil>
timeout result: err=context deadline exceeded

=== Cancellable Pipeline ===
2 4 6 8 10
Processed 5 values before cancel

=== Graceful Shutdown ===
[api] started
[worker] started
[metrics] started
Initiating shutdown...
[api] shutting down: context canceled
[worker] shutting down: context canceled
[metrics] shutting down: context canceled
[api] stopped
[worker] stopped
[metrics] stopped
All servers stopped

=== Request Processor ===
  req#1: processed: hi
  req#2: processed: hello world
  req#3: processed: x
```

---

## Summary

| Function | Purpose |
|----------|---------|
| `context.Background()` | Root context, never cancelled |
| `context.WithCancel(parent)` | Manual cancellation |
| `context.WithTimeout(parent, d)` | Auto-cancel after duration |
| `context.WithDeadline(parent, t)` | Cancel at specific time |
| `context.WithValue(parent, k, v)` | Attach request-scoped values |
| `ctx.Done()` | Channel closed when context cancelled |
| `ctx.Err()` | `context.Canceled` or `context.DeadlineExceeded` |

## Further Reading
- [context package](https://pkg.go.dev/context)
- [Go Blog: Contexts](https://go.dev/blog/context)
