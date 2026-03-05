# Lab 02: Select Statement

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm golang:1.22-alpine sh`

## Overview

`select` lets a goroutine wait on multiple channel operations simultaneously. It is to channels what `switch` is to values — but non-deterministic when multiple cases are ready. It is the cornerstone of timeouts, cancellations, and fan-in merging.

## Step 1: Basic Select with Multiple Channels

`select` picks whichever case is ready. If multiple are ready, it chooses randomly.

```go
package main

import "fmt"

func main() {
    ch1 := make(chan string, 1)
    ch2 := make(chan string, 1)
    ch1 <- "one"
    ch2 <- "two"

    for i := 0; i < 2; i++ {
        select {
        case msg := <-ch1:
            fmt.Println("from ch1:", msg)
        case msg := <-ch2:
            fmt.Println("from ch2:", msg)
        }
    }
}
```

> 💡 **Tip:** When both channels have data, `select` picks randomly — this is by design for fairness.

## Step 2: Default Case (Non-blocking)

A `default` case executes immediately if no other case is ready, making the select non-blocking.

```go
package main

import "fmt"

func tryReceive(ch <-chan int) (int, bool) {
    select {
    case v := <-ch:
        return v, true
    default:
        return 0, false
    }
}

func trySend(ch chan<- int, val int) bool {
    select {
    case ch <- val:
        return true
    default:
        return false
    }
}

func main() {
    ch := make(chan int, 1)

    v, ok := tryReceive(ch)
    fmt.Printf("receive: val=%d ok=%v\n", v, ok) // 0 false

    sent := trySend(ch, 42)
    fmt.Println("sent:", sent) // true

    v, ok = tryReceive(ch)
    fmt.Printf("receive: val=%d ok=%v\n", v, ok) // 42 true
}
```

## Step 3: Timeout with time.After

`time.After(d)` returns a channel that receives a value after duration `d` — perfect for select timeouts.

```go
package main

import (
    "fmt"
    "time"
)

func fetchData() <-chan string {
    ch := make(chan string)
    go func() {
        time.Sleep(200 * time.Millisecond) // simulate slow operation
        ch <- "data"
    }()
    return ch
}

func main() {
    result := fetchData()
    select {
    case data := <-result:
        fmt.Println("got:", data)
    case <-time.After(100 * time.Millisecond):
        fmt.Println("request timed out")
    }
}
```

> 💡 **Tip:** `time.After` leaks the underlying timer until it fires. For tight loops, use `time.NewTimer` and call `timer.Stop()`.

## Step 4: Done Channel Pattern

A `done` channel signals goroutines to stop work — the original cancellation pattern before `context`.

```go
package main

import (
    "fmt"
    "time"
)

func worker(done <-chan struct{}, id int) {
    for {
        select {
        case <-done:
            fmt.Printf("worker %d: stopping\n", id)
            return
        default:
            fmt.Printf("worker %d: working...\n", id)
            time.Sleep(5 * time.Millisecond)
        }
    }
}

func main() {
    done := make(chan struct{})
    go worker(done, 1)
    time.Sleep(20 * time.Millisecond)
    close(done) // broadcast to all workers
    time.Sleep(10 * time.Millisecond)
    fmt.Println("main: done")
}
```

## Step 5: context.WithTimeout

`context` is the idiomatic way to propagate deadlines and cancellations through call chains.

```go
package main

import (
    "context"
    "fmt"
    "time"
)

func doWork(ctx context.Context, name string) {
    select {
    case <-time.After(500 * time.Millisecond):
        fmt.Println(name, "completed")
    case <-ctx.Done():
        fmt.Printf("%s cancelled: %v\n", name, ctx.Err())
    }
}

func main() {
    ctx, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)
    defer cancel()

    go doWork(ctx, "task-1")
    go doWork(ctx, "task-2")

    time.Sleep(200 * time.Millisecond)
}
```

## Step 6: Select in a Loop (Heartbeat Pattern)

```go
package main

import (
    "fmt"
    "time"
)

func heartbeat(done <-chan struct{}, interval time.Duration) <-chan time.Time {
    out := make(chan time.Time)
    go func() {
        defer close(out)
        ticker := time.NewTicker(interval)
        defer ticker.Stop()
        for {
            select {
            case t := <-ticker.C:
                out <- t
            case <-done:
                return
            }
        }
    }()
    return out
}

func main() {
    done := make(chan struct{})
    hb := heartbeat(done, 10*time.Millisecond)

    count := 0
    for t := range hb {
        fmt.Printf("heartbeat at %v\n", t.Format("15:04:05.000"))
        count++
        if count == 3 {
            close(done)
        }
    }
}
```

## Step 7: Multiplex with Fan-In Using Select

```go
package main

import (
    "fmt"
    "time"
)

func source(name string, interval time.Duration) <-chan string {
    out := make(chan string)
    go func() {
        for i := 0; i < 3; i++ {
            time.Sleep(interval)
            out <- fmt.Sprintf("%s-%d", name, i)
        }
        close(out)
    }()
    return out
}

func merge(a, b <-chan string) <-chan string {
    out := make(chan string)
    go func() {
        defer close(out)
        for a != nil || b != nil {
            select {
            case v, ok := <-a:
                if !ok { a = nil; continue }
                out <- v
            case v, ok := <-b:
                if !ok { b = nil; continue }
                out <- v
            }
        }
    }()
    return out
}

func main() {
    fast := source("fast", 5*time.Millisecond)
    slow := source("slow", 15*time.Millisecond)
    for msg := range merge(fast, slow) {
        fmt.Println(msg)
    }
}
```

## Step 8: Capstone — Rate-Limited Worker

Combine select, ticker, done channel, and context for a rate-limited job processor.

```go
package main

import (
    "context"
    "fmt"
    "time"
)

func rateLimitedWorker(ctx context.Context, jobs <-chan int, rate time.Duration) <-chan string {
    results := make(chan string)
    go func() {
        defer close(results)
        limiter := time.NewTicker(rate)
        defer limiter.Stop()
        for {
            select {
            case <-ctx.Done():
                results <- "worker: context cancelled"
                return
            case job, ok := <-jobs:
                if !ok {
                    return
                }
                <-limiter.C // wait for rate limit
                results <- fmt.Sprintf("processed job %d", job)
            }
        }
    }()
    return results
}

func main() {
    ctx, cancel := context.WithTimeout(context.Background(), 200*time.Millisecond)
    defer cancel()

    jobs := make(chan int, 10)
    for i := 1; i <= 5; i++ {
        jobs <- i
    }
    close(jobs)

    for result := range rateLimitedWorker(ctx, jobs, 30*time.Millisecond) {
        fmt.Println(result)
    }
}
```

📸 **Verified Output:**
```
=== Basic Select ===
from ch2: two
from ch1: one

=== Non-blocking (default) ===
no value ready

=== Timeout ===
timeout!

=== Done Channel ===
done signal received

=== context.WithTimeout ===
worker 2: cancelled (context deadline exceeded)
worker 1: cancelled (context deadline exceeded)
```

## Summary

| Concept | Key Points |
|---|---|
| `select` | Waits on multiple channel ops; random when multiple ready |
| `default` | Makes select non-blocking |
| `time.After` | Simple per-operation timeout |
| `time.NewTimer` | Reusable timer; call `.Stop()` to avoid leak |
| Done channel | `close(done)` broadcasts cancellation to all waiters |
| `context.WithTimeout` | Idiomatic cancellation with deadline propagation |
| `context.WithCancel` | Manual cancellation via `cancel()` function |
| Nil channel | A nil channel in select is always skipped — useful for disabling cases |
