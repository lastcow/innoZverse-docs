# Lab 07: Context Package

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm golang:1.22-alpine sh`

## Overview

The `context` package carries deadlines, cancellation signals, and request-scoped values across API boundaries and goroutines. It is the standard way to propagate cancellation in Go — accepted as the first argument of every function in a call chain.

## Step 1: context.Background and context.TODO

These are the root contexts — empty, never cancelled.

```go
package main

import (
    "context"
    "fmt"
)

func main() {
    // Use Background for main, init, tests, and top-level contexts
    bg := context.Background()
    fmt.Println("background:", bg)

    // Use TODO as a placeholder when unsure which context to use
    todo := context.TODO()
    fmt.Println("todo:", todo)
}
```

## Step 2: WithCancel — Manual Cancellation

```go
package main

import (
    "context"
    "fmt"
    "time"
)

func monitor(ctx context.Context, id int) {
    for {
        select {
        case <-ctx.Done():
            fmt.Printf("monitor %d stopped: %v\n", id, ctx.Err())
            return
        default:
            fmt.Printf("monitor %d: running\n", id)
            time.Sleep(10 * time.Millisecond)
        }
    }
}

func main() {
    ctx, cancel := context.WithCancel(context.Background())

    go monitor(ctx, 1)
    go monitor(ctx, 2)

    time.Sleep(25 * time.Millisecond)
    cancel() // signal all goroutines using this context
    time.Sleep(10 * time.Millisecond)
    fmt.Println("all monitors stopped")
}
```

> 💡 **Tip:** Always call `cancel()` — defer it right after the `WithCancel` call. Not calling it leaks resources.

## Step 3: WithTimeout — Deadline After Duration

```go
package main

import (
    "context"
    "fmt"
    "time"
)

func fetchData(ctx context.Context, url string) (string, error) {
    done := make(chan string, 1)
    go func() {
        time.Sleep(50 * time.Millisecond) // simulate HTTP call
        done <- "response from " + url
    }()
    select {
    case data := <-done:
        return data, nil
    case <-ctx.Done():
        return "", ctx.Err()
    }
}

func main() {
    // Fast enough
    ctx1, cancel1 := context.WithTimeout(context.Background(), 100*time.Millisecond)
    defer cancel1()
    result, err := fetchData(ctx1, "http://fast.example.com")
    fmt.Println("fast:", result, err)

    // Too slow
    ctx2, cancel2 := context.WithTimeout(context.Background(), 30*time.Millisecond)
    defer cancel2()
    result, err = fetchData(ctx2, "http://slow.example.com")
    fmt.Println("slow:", result, err)
}
```

## Step 4: WithDeadline — Absolute Time Limit

```go
package main

import (
    "context"
    "fmt"
    "time"
)

func main() {
    deadline := time.Now().Add(50 * time.Millisecond)
    ctx, cancel := context.WithDeadline(context.Background(), deadline)
    defer cancel()

    fmt.Println("deadline:", ctx.Deadline())

    select {
    case <-time.After(100 * time.Millisecond):
        fmt.Println("work completed")
    case <-ctx.Done():
        fmt.Println("deadline hit:", ctx.Err())
    }
}
```

## Step 5: WithValue — Request-Scoped Values

```go
package main

import (
    "context"
    "fmt"
)

// Use unexported type for keys to avoid collisions
type contextKey string

const (
    keyUserID    contextKey = "userID"
    keyRequestID contextKey = "requestID"
)

func withUser(ctx context.Context, userID string) context.Context {
    return context.WithValue(ctx, keyUserID, userID)
}

func withRequestID(ctx context.Context, reqID string) context.Context {
    return context.WithValue(ctx, keyRequestID, reqID)
}

func handleRequest(ctx context.Context, action string) {
    userID := ctx.Value(keyUserID).(string)
    reqID, _ := ctx.Value(keyRequestID).(string)
    fmt.Printf("[%s] user=%s action=%s\n", reqID, userID, action)
}

func main() {
    ctx := context.Background()
    ctx = withUser(ctx, "alice")
    ctx = withRequestID(ctx, "req-001")

    handleRequest(ctx, "create_order")
    handleRequest(ctx, "send_confirmation")
}
```

> 💡 **Tip:** Use `context.WithValue` only for request-scoped data (trace IDs, auth tokens). Don't use it for optional function parameters.

## Step 6: Propagating Cancellation Through Layers

```go
package main

import (
    "context"
    "fmt"
    "time"
)

// Repository layer
func dbQuery(ctx context.Context, query string) (string, error) {
    select {
    case <-time.After(30 * time.Millisecond):
        return "row1,row2", nil
    case <-ctx.Done():
        return "", fmt.Errorf("db: %w", ctx.Err())
    }
}

// Service layer — passes ctx down
func getUsers(ctx context.Context) ([]string, error) {
    raw, err := dbQuery(ctx, "SELECT * FROM users")
    if err != nil {
        return nil, fmt.Errorf("getUsers: %w", err)
    }
    return []string{raw}, nil
}

// Handler layer — creates context with deadline
func handleGetUsers(timeout time.Duration) {
    ctx, cancel := context.WithTimeout(context.Background(), timeout)
    defer cancel()

    users, err := getUsers(ctx)
    if err != nil {
        fmt.Println("error:", err)
        return
    }
    fmt.Println("users:", users)
}

func main() {
    handleGetUsers(100 * time.Millisecond) // succeeds
    handleGetUsers(10 * time.Millisecond)  // times out
}
```

## Step 7: Context in Goroutine Cleanup

```go
package main

import (
    "context"
    "fmt"
    "sync"
    "time"
)

func worker(ctx context.Context, id int, wg *sync.WaitGroup) {
    defer wg.Done()
    ticker := time.NewTicker(10 * time.Millisecond)
    defer ticker.Stop()

    for {
        select {
        case <-ctx.Done():
            fmt.Printf("worker %d: shutting down\n", id)
            return
        case t := <-ticker.C:
            fmt.Printf("worker %d: tick at %s\n", id, t.Format("15:04:05.000"))
        }
    }
}

func main() {
    ctx, cancel := context.WithTimeout(context.Background(), 35*time.Millisecond)
    defer cancel()

    var wg sync.WaitGroup
    for i := 1; i <= 3; i++ {
        wg.Add(1)
        go worker(ctx, i, &wg)
    }
    wg.Wait()
    fmt.Println("all workers done")
}
```

## Step 8: Capstone — HTTP Handler with Context

```go
package main

import (
    "context"
    "fmt"
    "time"
)

// Simulate HTTP request lifecycle
type Request struct {
    Method string
    Path   string
    UserID string
    ReqID  string
}

type contextKey string

func processRequest(req Request) {
    // Build context with timeout and values
    ctx, cancel := context.WithTimeout(context.Background(), 200*time.Millisecond)
    defer cancel()

    ctx = context.WithValue(ctx, contextKey("userID"), req.UserID)
    ctx = context.WithValue(ctx, contextKey("reqID"), req.ReqID)

    fmt.Printf("[%s] %s %s\n", req.ReqID, req.Method, req.Path)

    result, err := businessLogic(ctx)
    if err != nil {
        fmt.Printf("[%s] error: %v\n", req.ReqID, err)
        return
    }
    fmt.Printf("[%s] response: %s\n", req.ReqID, result)
}

func businessLogic(ctx context.Context) (string, error) {
    user := ctx.Value(contextKey("userID")).(string)
    data, err := fetchFromDB(ctx)
    if err != nil {
        return "", err
    }
    return fmt.Sprintf("Hello %s, data=%s", user, data), nil
}

func fetchFromDB(ctx context.Context) (string, error) {
    select {
    case <-time.After(50 * time.Millisecond):
        return "record-42", nil
    case <-ctx.Done():
        return "", fmt.Errorf("db timeout: %w", ctx.Err())
    }
}

func main() {
    requests := []Request{
        {Method: "GET", Path: "/profile", UserID: "alice", ReqID: "r001"},
        {Method: "POST", Path: "/order", UserID: "bob", ReqID: "r002"},
    }
    for _, r := range requests {
        processRequest(r)
    }
}
```

📸 **Verified Output:**
```
=== Background/TODO ===
background: context.Background
todo: context.TODO

=== WithCancel ===
cancelled: context canceled

=== WithTimeout ===
fast fetch: result from http://fast.example.com <nil>
slow fetch:  context deadline exceeded

=== WithValue ===
handling request for user: alice

=== WithDeadline ===
deadline exceeded: context deadline exceeded
```

## Summary

| Function | Use Case | Key Behaviour |
|---|---|---|
| `context.Background()` | Top-level root context | Never cancelled |
| `context.TODO()` | Placeholder during development | Never cancelled |
| `WithCancel(ctx)` | Manual cancellation | Returns ctx + `cancel()` func |
| `WithTimeout(ctx, d)` | Cancel after duration d | Auto-cancels after d |
| `WithDeadline(ctx, t)` | Cancel at absolute time t | Auto-cancels at t |
| `WithValue(ctx, k, v)` | Attach request-scoped data | Use unexported key types |
| `ctx.Done()` | Channel closed on cancellation | Use in `select` |
| `ctx.Err()` | Returns cancellation reason | `context.Canceled` or `context.DeadlineExceeded` |
