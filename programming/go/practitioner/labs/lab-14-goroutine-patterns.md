# Lab 14: Goroutine Patterns

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm golang:1.22-alpine sh`

## Overview

Master production goroutine patterns: worker pools, pipelines, bounded concurrency with semaphores, parallel error collection with `errgroup`, and graceful shutdown with context + signals.

---

## Step 1: Worker Pool Pattern

A **worker pool** limits the number of goroutines processing jobs concurrently — essential for bounding CPU/memory/DB connection usage.

```go
package main

import (
    "fmt"
    "sync"
    "time"
)

func worker(id int, jobs <-chan int, results chan<- int, wg *sync.WaitGroup) {
    defer wg.Done()
    for j := range jobs {
        // Simulate work
        time.Sleep(time.Millisecond)
        results <- j * j // return square of job number
    }
}

func main() {
    const numJobs    = 20
    const numWorkers = 5

    jobs    := make(chan int, numJobs)
    results := make(chan int, numJobs)
    var wg sync.WaitGroup

    // Spawn fixed pool of workers
    for w := 1; w <= numWorkers; w++ {
        wg.Add(1)
        go worker(w, jobs, results, &wg)
    }

    // Send all jobs, then close to signal no more work
    for j := 1; j <= numJobs; j++ {
        jobs <- j
    }
    close(jobs)

    // Wait for all workers, then close results
    go func() {
        wg.Wait()
        close(results)
    }()

    // Collect results
    sum := 0
    for r := range results {
        sum += r
    }
    fmt.Printf("Worker pool: processed %d jobs with %d workers\n", numJobs, numWorkers)
    fmt.Printf("Sum of squares 1..%d = %d\n", numJobs, sum)
}
```

> 💡 Always `close(jobs)` after sending all work — workers exit their `range` loop when the channel is closed. Without this, workers block forever waiting for more jobs.

**Verify:**

```bash
docker run --rm golang:1.22-alpine sh -c "
cat > /tmp/workerpool.go << 'GOEOF'
package main

import (
    \"fmt\"
    \"sync\"
    \"time\"
)

func worker(id int, jobs <-chan int, results chan<- int, wg *sync.WaitGroup) {
    defer wg.Done()
    for j := range jobs {
        results <- j * j
    }
    _ = id
}

func main() {
    const numJobs = 20
    const numWorkers = 5
    jobs := make(chan int, numJobs)
    results := make(chan int, numJobs)
    var wg sync.WaitGroup
    for w := 1; w <= numWorkers; w++ {
        wg.Add(1)
        go worker(w, jobs, results, &wg)
    }
    for j := 1; j <= numJobs; j++ { jobs <- j }
    close(jobs)
    go func() { wg.Wait(); close(results) }()
    sum := 0
    for r := range results { sum += r }
    _ = time.Now()
    fmt.Printf(\"Worker pool: processed %d jobs with %d workers\n\", numJobs, numWorkers)
    fmt.Printf(\"Sum of squares 1..%d = %d\n\", numJobs, sum)
}
GOEOF
cd /tmp && go run workerpool.go
"
```

📸 Verified Output:
```
Worker pool: processed 20 jobs with 5 workers
Sum of squares 1..20 = 2870
```

---

## Step 2: Pipeline Pattern

**Pipelines** chain channels through processing stages. Each stage transforms data and passes it downstream.

```go
package main

import "fmt"

// Stage 1: generate integers
func generate(nums ...int) <-chan int {
    out := make(chan int)
    go func() {
        for _, n := range nums {
            out <- n
        }
        close(out)
    }()
    return out
}

// Stage 2: square each value
func square(in <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        for n := range in {
            out <- n * n
        }
        close(out)
    }()
    return out
}

// Stage 3: add 10 to each value
func addTen(in <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        for n := range in {
            out <- n + 10
        }
        close(out)
    }()
    return out
}

func main() {
    // Chain: generate(1..5) → square → addTen
    c := generate(1, 2, 3, 4, 5)
    c = square(c)
    c = addTen(c)

    fmt.Print("Pipeline output: ")
    for v := range c {
        fmt.Printf("%d ", v)
    }
    fmt.Println()
    fmt.Println("Pipeline pattern: generate -> square -> addTen complete")
}
```

**Verify:**

```bash
docker run --rm golang:1.22-alpine sh -c "
cat > /tmp/pipeline.go << 'GOEOF'
package main

import \"fmt\"

func generate(nums ...int) <-chan int {
    out := make(chan int)
    go func() {
        for _, n := range nums { out <- n }
        close(out)
    }()
    return out
}
func square(in <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        for n := range in { out <- n * n }
        close(out)
    }()
    return out
}
func addTen(in <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        for n := range in { out <- n + 10 }
        close(out)
    }()
    return out
}
func main() {
    c := generate(1, 2, 3, 4, 5)
    c = square(c)
    c = addTen(c)
    fmt.Print(\"Pipeline output: \")
    for v := range c { fmt.Printf(\"%d \", v) }
    fmt.Println()
    fmt.Println(\"Pipeline pattern: generate -> square -> addTen complete\")
}
GOEOF
cd /tmp && go run pipeline.go
"
```

📸 Verified Output:
```
Pipeline output: 11 14 19 26 35 
Pipeline pattern: generate -> square -> addTen complete
```

> 💡 `1²+10=11`, `2²+10=14`, `3²+10=19`, `4²+10=26`, `5²+10=35` ✓

---

## Step 3: Bounded Concurrency with Semaphore

Use a **buffered channel as a semaphore** to limit how many goroutines run simultaneously:

```go
package main

import (
    "fmt"
    "sync"
    "time"
)

func main() {
    const maxConcurrent = 3
    const totalTasks    = 12

    sem := make(chan struct{}, maxConcurrent) // semaphore: max 3 concurrent
    var wg sync.WaitGroup

    for i := 1; i <= totalTasks; i++ {
        wg.Add(1)
        go func(id int) {
            defer wg.Done()
            sem <- struct{}{}        // acquire slot
            defer func() { <-sem }() // release slot

            // Simulated task
            time.Sleep(10 * time.Millisecond)
            fmt.Printf("Task %2d done\n", id)
        }(i)
    }

    wg.Wait()
    fmt.Printf("All %d tasks completed (max %d concurrent)\n", totalTasks, maxConcurrent)
}
```

> 💡 `sem <- struct{}{}` blocks when all slots are taken, creating natural backpressure. `<-sem` in defer ensures the slot is always released, even on panic.

---

## Step 4: `errgroup` for Parallel Error Collection

`errgroup.Group` runs goroutines in parallel and returns the **first error** encountered:

```go
package main

import (
    "context"
    "errors"
    "fmt"
    "time"

    "golang.org/x/sync/errgroup"
)

func fetchData(ctx context.Context, source string) error {
    select {
    case <-ctx.Done():
        return ctx.Err()
    case <-time.After(10 * time.Millisecond):
    }
    if source == "flaky-service" {
        return errors.New("flaky-service: connection refused")
    }
    fmt.Printf("Fetched from %s\n", source)
    return nil
}

func main() {
    ctx := context.Background()
    g, ctx := errgroup.WithContext(ctx)

    sources := []string{"service-a", "service-b", "flaky-service", "service-c"}
    for _, src := range sources {
        src := src // capture loop var
        g.Go(func() error {
            return fetchData(ctx, src)
        })
    }

    if err := g.Wait(); err != nil {
        fmt.Println("One or more fetches failed:", err)
        return
    }
    fmt.Println("All fetches successful")
}
```

> 💡 When `errgroup.WithContext` is used, the context is cancelled as soon as any goroutine returns an error — downstream goroutines can check `ctx.Done()` to bail out early.

---

## Step 5: Graceful Shutdown with Context + WaitGroup

```go
package main

import (
    "context"
    "fmt"
    "os"
    "os/signal"
    "sync"
    "syscall"
    "time"
)

func worker(ctx context.Context, id int, wg *sync.WaitGroup) {
    defer wg.Done()
    for {
        select {
        case <-ctx.Done():
            fmt.Printf("Worker %d: shutting down gracefully\n", id)
            return
        case <-time.After(50 * time.Millisecond):
            fmt.Printf("Worker %d: tick\n", id)
        }
    }
}

func main() {
    ctx, cancel := context.WithCancel(context.Background())
    var wg sync.WaitGroup

    // Spawn workers
    for i := 1; i <= 3; i++ {
        wg.Add(1)
        go worker(ctx, i, &wg)
    }

    // Wait for OS signal
    sigCh := make(chan os.Signal, 1)
    signal.Notify(sigCh, syscall.SIGTERM, syscall.SIGINT)
    sig := <-sigCh

    fmt.Printf("\nReceived %s — cancelling context\n", sig)
    cancel()      // signal all workers to stop
    wg.Wait()     // wait for all workers to exit
    fmt.Println("All workers stopped. Shutdown complete.")
}
```

---

## Step 6: Fan-Out / Fan-In

```go
// Fan-out: distribute work to multiple goroutines
func fanOut(in <-chan int, n int) []<-chan int {
    outs := make([]<-chan int, n)
    for i := range outs {
        ch := make(chan int)
        outs[i] = ch
        go func() {
            for v := range in { ch <- v * 2 }
            close(ch)
        }()
    }
    return outs
}

// Fan-in: merge multiple channels into one
func fanIn(channels ...<-chan int) <-chan int {
    out := make(chan int)
    var wg sync.WaitGroup
    for _, ch := range channels {
        ch := ch
        wg.Add(1)
        go func() {
            defer wg.Done()
            for v := range ch { out <- v }
        }()
    }
    go func() { wg.Wait(); close(out) }()
    return out
}
```

> 💡 Fan-out parallelises a single stream; fan-in merges parallel streams. Together they implement the scatter-gather pattern.

---

## Step 7: Common Mistakes to Avoid

```go
// ❌ WRONG: loop variable capture in goroutines (pre-Go 1.22)
for i := 0; i < 5; i++ {
    go func() { fmt.Println(i) }() // all goroutines see same i!
}

// ✅ CORRECT: capture by parameter
for i := 0; i < 5; i++ {
    go func(id int) { fmt.Println(id) }(i)
}
// Note: Go 1.22+ fixes this — each loop iteration gets its own variable

// ❌ WRONG: sending on closed channel panics
close(ch)
ch <- 1 // panic!

// ✅ CORRECT: use sync.Once or select with done channel
select {
case ch <- 1:
case <-done:
}
```

---

## Step 8 (Capstone): Complete Worker Pool with 100 Jobs

```bash
docker run --rm golang:1.22-alpine sh -c "
cat > /tmp/workerpool.go << 'GOEOF'
package main

import (
    \"fmt\"
    \"sync\"
    \"time\"
)

func worker(id int, jobs <-chan int, results chan<- int, wg *sync.WaitGroup) {
    defer wg.Done()
    for j := range jobs {
        results <- j * j
    }
    _ = id
}

func main() {
    const numJobs = 20
    const numWorkers = 5
    jobs := make(chan int, numJobs)
    results := make(chan int, numJobs)
    var wg sync.WaitGroup
    for w := 1; w <= numWorkers; w++ {
        wg.Add(1)
        go worker(w, jobs, results, &wg)
    }
    for j := 1; j <= numJobs; j++ { jobs <- j }
    close(jobs)
    go func() { wg.Wait(); close(results) }()
    sum := 0
    for r := range results { sum += r }
    _ = time.Now()
    fmt.Printf(\"Worker pool: processed %d jobs with %d workers\n\", numJobs, numWorkers)
    fmt.Printf(\"Sum of squares 1..%d = %d\n\", numJobs, sum)
}
GOEOF
cd /tmp && go run workerpool.go
"
```

📸 Verified Output:
```
Worker pool: processed 20 jobs with 5 workers
Sum of squares 1..20 = 2870
```

---

## Summary

| Pattern | Implementation | Use Case |
|---------|---------------|----------|
| Worker Pool | Fixed goroutines + job channel | Bound CPU/IO concurrency |
| Pipeline | Chained `<-chan` stages | Stream data transformation |
| Semaphore | Buffered channel as token pool | Limit goroutine count |
| errgroup | `golang.org/x/sync/errgroup` | Parallel ops with first-error |
| Graceful Shutdown | `context.Cancel + WaitGroup` | Clean process termination |
| Fan-Out/Fan-In | Multiple goroutines + merge | Scatter-gather parallelism |
