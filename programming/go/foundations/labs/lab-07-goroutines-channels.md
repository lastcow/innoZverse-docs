# Lab 07: Goroutines & Channels

## Objective
Write concurrent Go programs using goroutines and channels: fan-out/fan-in, worker pools, select statements, and channel directions.

## Time
35 minutes

## Prerequisites
- Lab 01–06

## Tools
- Docker image: `zchencow/innozverse-go:latest`

---

## Lab Instructions

### Step 1: Goroutines

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import (
    "fmt"
    "sync"
    "time"
)

func sayHello(id int, wg *sync.WaitGroup) {
    defer wg.Done()
    fmt.Printf("Goroutine %d: Hello!\n", id)
}

func countDown(from int) {
    for i := from; i >= 0; i-- {
        fmt.Printf("T-%d\n", i)
        time.Sleep(10 * time.Millisecond)
    }
}

func main() {
    // Launch goroutines and wait for all to finish
    var wg sync.WaitGroup

    for i := 1; i <= 5; i++ {
        wg.Add(1)
        go sayHello(i, &wg)
    }
    wg.Wait()
    fmt.Println("All goroutines done")

    // Goroutines are lightweight — spawn thousands easily
    fmt.Println("\nCounting down...")
    var wg2 sync.WaitGroup
    wg2.Add(1)
    go func() {
        defer wg2.Done()
        countDown(3)
    }()
    wg2.Wait()
    fmt.Println("Launch!")
}
EOF
```

> 💡 **Goroutines cost ~2KB of stack** (vs ~1MB for OS threads) and the runtime multiplexes them across CPU cores. You can have millions of goroutines simultaneously. `sync.WaitGroup` is the standard way to wait for a group to finish — `Add(1)` before launching, `Done()` in the goroutine (always via `defer`), `Wait()` to block.

**📸 Verified Output:**
```
Goroutine 3: Hello!
Goroutine 1: Hello!
Goroutine 2: Hello!
Goroutine 4: Hello!
Goroutine 5: Hello!
All goroutines done

Counting down...
T-3
T-2
T-1
T-0
Launch!
```

---

### Step 2: Channels

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import (
    "fmt"
    "math/rand"
)

func producer(ch chan<- int, count int) {
    for i := 0; i < count; i++ {
        ch <- rand.Intn(100)
    }
    close(ch) // signal no more values
}

func squarer(in <-chan int, out chan<- int) {
    for n := range in { // range on channel receives until closed
        out <- n * n
    }
    close(out)
}

func main() {
    // Unbuffered channel — send/receive synchronize
    nums := make(chan int)
    squares := make(chan int)

    go producer(nums, 5)
    go squarer(nums, squares)

    for sq := range squares {
        fmt.Printf("square: %d\n", sq)
    }

    // Buffered channel — send doesn't block until buffer full
    buf := make(chan string, 3)
    buf <- "first"
    buf <- "second"
    buf <- "third"
    // buf <- "fourth" would block (buffer full)

    fmt.Println(<-buf)
    fmt.Println(<-buf)
    fmt.Println(<-buf)

    // Channel directions in function signatures
    // chan<- T: send-only   <-chan T: receive-only
    ping := make(chan string, 1)
    pong := make(chan string, 1)

    go func(in <-chan string, out chan<- string) {
        msg := <-in
        out <- msg + " PONG"
    }(ping, pong)

    ping <- "PING"
    fmt.Println(<-pong)
}
EOF
```

> 💡 **Close a channel when the sender is done** — receivers can use `range ch` to consume all values and stop automatically when the channel closes. Only the *sender* should close a channel, never the receiver. Sending to a closed channel panics. Receiving from a closed channel returns the zero value immediately.

**📸 Verified Output:**
```
square: 441
square: 6724
square: 1225
square: 961
square: 784
first
second
third
PING PONG
```

---

### Step 3: Select Statement

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import (
    "fmt"
    "time"
)

func ticker(interval time.Duration, stop <-chan struct{}) <-chan time.Time {
    out := make(chan time.Time)
    go func() {
        defer close(out)
        t := time.NewTicker(interval)
        defer t.Stop()
        for {
            select {
            case tick := <-t.C:
                out <- tick
            case <-stop:
                return
            }
        }
    }()
    return out
}

func main() {
    // select: wait on multiple channels simultaneously
    ch1 := make(chan string, 1)
    ch2 := make(chan string, 1)

    ch1 <- "one"
    ch2 <- "two"

    // Non-deterministic which case fires first
    for i := 0; i < 2; i++ {
        select {
        case msg := <-ch1:
            fmt.Println("from ch1:", msg)
        case msg := <-ch2:
            fmt.Println("from ch2:", msg)
        }
    }

    // Timeout pattern
    slow := make(chan string)
    go func() {
        time.Sleep(5 * time.Millisecond)
        slow <- "response"
    }()

    select {
    case msg := <-slow:
        fmt.Println("Got:", msg)
    case <-time.After(100 * time.Millisecond):
        fmt.Println("Timeout!")
    }

    // Default case — non-blocking select
    ready := make(chan bool, 1)
    select {
    case <-ready:
        fmt.Println("Ready!")
    default:
        fmt.Println("Not ready (default)")
    }

    // Done signal via channel
    stop := make(chan struct{})
    ticks := ticker(10*time.Millisecond, stop)
    count := 0
    for range ticks {
        count++
        if count >= 3 { close(stop); break }
    }
    fmt.Println("Ticks received:", count)
}
EOF
```

> 💡 **`select` is the heart of Go concurrency**. It waits for whichever channel is ready first. `time.After(d)` returns a channel that receives after duration `d` — perfect for timeouts. The `default` case makes `select` non-blocking. `select {}` (empty select) blocks forever — useful as a `sleep(forever)`.

**📸 Verified Output:**
```
from ch1: one
from ch2: two
Got: response
Not ready (default)
Ticks received: 3
```

---

### Step 4: Fan-out / Fan-in

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import (
    "fmt"
    "sync"
    "time"
)

// Fan-out: one channel → multiple workers
func fanOut[T, U any](input <-chan T, workers int, fn func(T) U) <-chan U {
    out := make(chan U, workers)
    var wg sync.WaitGroup
    for i := 0; i < workers; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            for v := range input { out <- fn(v) }
        }()
    }
    go func() { wg.Wait(); close(out) }()
    return out
}

// Fan-in: merge multiple channels into one
func fanIn[T any](channels ...<-chan T) <-chan T {
    out := make(chan T)
    var wg sync.WaitGroup
    for _, ch := range channels {
        wg.Add(1)
        ch := ch
        go func() {
            defer wg.Done()
            for v := range ch { out <- v }
        }()
    }
    go func() { wg.Wait(); close(out) }()
    return out
}

// Pipeline stages
func generate(nums ...int) <-chan int {
    out := make(chan int)
    go func() {
        for _, n := range nums { out <- n }
        close(out)
    }()
    return out
}

func sq(in <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        for n := range in { out <- n * n }
        close(out)
    }()
    return out
}

func main() {
    // Pipeline
    src := generate(2, 3, 4, 5, 6, 7, 8)
    squared := sq(src)
    squaredAgain := sq(squared)
    for n := range squaredAgain {
        fmt.Printf("n^4: %d\n", n)
    }

    // Fan-out: parallel processing
    jobs := make(chan int, 10)
    for i := 1; i <= 8; i++ { jobs <- i }
    close(jobs)

    // 3 workers process jobs concurrently
    results := fanOut(jobs, 3, func(n int) string {
        time.Sleep(time.Duration(n) * time.Millisecond)
        return fmt.Sprintf("job%d→%d", n, n*n)
    })

    var collected []string
    for r := range results { collected = append(collected, r) }
    fmt.Printf("Processed %d jobs\n", len(collected))
}
EOF
```

**📸 Verified Output:**
```
n^4: 16
n^4: 81
n^4: 256
n^4: 625
n^4: 1296
n^4: 2401
n^4: 4096
Processed 8 jobs
```

---

### Steps 5–8: Worker Pool, Done Channel, Mutex vs Channel, Capstone

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import (
    "fmt"
    "sync"
    "sync/atomic"
)

// Step 5: Worker pool
type Job struct{ ID int; Payload int }
type Result struct{ JobID int; Value int }

func workerPool(numWorkers int, jobs <-chan Job) <-chan Result {
    results := make(chan Result, numWorkers)
    var wg sync.WaitGroup
    for w := 0; w < numWorkers; w++ {
        wg.Add(1)
        go func(workerID int) {
            defer wg.Done()
            for job := range jobs {
                // Simulate work
                result := job.Payload * job.Payload
                results <- Result{job.ID, result}
            }
        }(w)
    }
    go func() { wg.Wait(); close(results) }()
    return results
}

// Step 6: Mutex for shared state
type SafeCounter struct {
    mu    sync.Mutex
    count int
}
func (c *SafeCounter) Inc()      { c.mu.Lock(); defer c.mu.Unlock(); c.count++ }
func (c *SafeCounter) Value() int { c.mu.Lock(); defer c.mu.Unlock(); return c.count }

// Step 7: Atomic for simple counters
type AtomicCounter struct{ n int64 }
func (c *AtomicCounter) Inc()       { atomic.AddInt64(&c.n, 1) }
func (c *AtomicCounter) Value() int64 { return atomic.LoadInt64(&c.n) }

// Step 8: Capstone — concurrent product price fetcher
type PriceResult struct {
    Product string
    Price   float64
    Err     error
}

func fetchPrice(product string) (float64, error) {
    // Simulate API call with mock data
    prices := map[string]float64{
        "Surface Pro":  864.00,
        "Surface Pen":  49.99,
        "Office 365":   99.99,
        "USB-C Hub":    29.99,
        "Surface Book": 1299.00,
    }
    if p, ok := prices[product]; ok {
        return p, nil
    }
    return 0, fmt.Errorf("product %q not found", product)
}

func fetchAllPrices(products []string) []PriceResult {
    results := make([]PriceResult, len(products))
    var wg sync.WaitGroup
    for i, product := range products {
        wg.Add(1)
        go func(idx int, name string) {
            defer wg.Done()
            price, err := fetchPrice(name)
            results[idx] = PriceResult{name, price, err}
        }(i, product)
    }
    wg.Wait()
    return results
}

func main() {
    // Worker pool
    const numJobs    = 10
    const numWorkers = 3
    jobs := make(chan Job, numJobs)
    for i := 1; i <= numJobs; i++ { jobs <- Job{i, i} }
    close(jobs)

    results := workerPool(numWorkers, jobs)
    sum := 0
    for r := range results { sum += r.Value }
    fmt.Printf("Worker pool: %d jobs → sum of squares = %d\n", numJobs, sum)

    // Mutex counter
    var wg sync.WaitGroup
    mc := &SafeCounter{}
    for i := 0; i < 1000; i++ {
        wg.Add(1)
        go func() { defer wg.Done(); mc.Inc() }()
    }
    wg.Wait()
    fmt.Println("SafeCounter:", mc.Value())

    // Atomic counter
    ac := &AtomicCounter{}
    for i := 0; i < 1000; i++ {
        wg.Add(1)
        go func() { defer wg.Done(); ac.Inc() }()
    }
    wg.Wait()
    fmt.Println("AtomicCounter:", ac.Value())

    // Concurrent price fetching
    products := []string{"Surface Pro", "Surface Pen", "Office 365", "Unknown", "USB-C Hub"}
    prices := fetchAllPrices(products)

    fmt.Println("\n=== Price Results ===")
    total := 0.0
    for _, r := range prices {
        if r.Err != nil {
            fmt.Printf("  ❌ %-20s Error: %s\n", r.Product, r.Err)
        } else {
            fmt.Printf("  ✓  %-20s $%.2f\n", r.Product, r.Price)
            total += r.Price
        }
    }
    fmt.Printf("  Total (found): $%.2f\n", total)
}
EOF
```

**📸 Verified Output:**
```
Worker pool: 10 jobs → sum of squares = 385
SafeCounter: 1000
AtomicCounter: 1000

=== Price Results ===
  ✓  Surface Pro          $864.00
  ✓  Surface Pen          $49.99
  ✓  Office 365           $99.99
  ❌ Unknown              Error: product "Unknown" not found
  ✓  USB-C Hub            $29.99
  Total (found): $1043.97
```

---

## Summary

| Concept | Pattern | Use case |
|---------|---------|---------|
| Goroutine | `go fn()` | Concurrent execution |
| WaitGroup | `wg.Add/Done/Wait` | Wait for N goroutines |
| Channel | `make(chan T)` | Communication between goroutines |
| Select | `select { case <-ch }` | Wait on multiple channels |
| Worker pool | N goroutines reading from 1 channel | Parallel task processing |
| Mutex | `mu.Lock/Unlock` | Protect shared mutable state |
| Atomic | `atomic.AddInt64` | Simple counter without mutex |

## Further Reading
- [Go Concurrency Patterns](https://go.dev/blog/pipelines)
- [sync package](https://pkg.go.dev/sync)
