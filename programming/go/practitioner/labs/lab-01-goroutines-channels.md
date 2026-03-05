# Lab 01: Goroutines & Channels

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm golang:1.22-alpine sh`

## Overview

Goroutines are Go's lightweight concurrency primitives — cheaper than OS threads and scheduled by the Go runtime. Channels are typed conduits for communication between goroutines, enforcing the Go philosophy: *"Do not communicate by sharing memory; instead, share memory by communicating."*

## Step 1: Goroutine Lifecycle

A goroutine starts with the `go` keyword and runs concurrently. Use a channel or `sync.WaitGroup` to wait for it.

```go
// lifecycle.go
package main

import (
    "fmt"
    "time"
)

func worker(id int, done chan<- struct{}) {
    fmt.Printf("worker %d: starting\n", id)
    time.Sleep(10 * time.Millisecond)
    fmt.Printf("worker %d: done\n", id)
    done <- struct{}{}
}

func main() {
    done := make(chan struct{})
    go worker(1, done)
    <-done // block until worker finishes
    fmt.Println("main: all workers done")
}
```

> 💡 **Tip:** Without synchronisation, `main()` exits and kills all goroutines. Always wait for goroutines you care about.

## Step 2: Unbuffered vs Buffered Channels

```go
package main

import "fmt"

func main() {
    // Unbuffered: sender blocks until receiver is ready
    unb := make(chan int)
    go func() { unb <- 42 }()
    fmt.Println("unbuffered received:", <-unb)

    // Buffered: sender only blocks when buffer is full
    buf := make(chan int, 3)
    buf <- 1
    buf <- 2
    buf <- 3
    // No goroutine needed — buffer absorbs all three
    fmt.Println("buffered:", <-buf, <-buf, <-buf)
}
```

> 💡 **Tip:** Buffered channels decouple producer and consumer speed but can hide deadlocks — size them carefully.

## Step 3: Channel Directions

Restricting channel direction in function signatures prevents misuse at compile time.

```go
package main

import "fmt"

func send(out chan<- string, val string) { // send-only
    out <- val
}

func receive(in <-chan string) string { // receive-only
    return <-in
}

func main() {
    ch := make(chan string, 1)
    send(ch, "hello")
    fmt.Println(receive(ch))
}
```

## Step 4: Range Over Channel & close()

`range` over a channel reads until it is closed.

```go
package main

import "fmt"

func generate(nums ...int) <-chan int {
    out := make(chan int)
    go func() {
        for _, n := range nums {
            out <- n
        }
        close(out) // MUST close to end range
    }()
    return out
}

func main() {
    for n := range generate(2, 3, 5, 7, 11) {
        fmt.Print(n, " ")
    }
    fmt.Println()
}
```

> 💡 **Tip:** Only the **sender** should close a channel. Closing a nil or already-closed channel panics.

## Step 5: Fan-Out Pattern

Distribute work from one channel to multiple workers.

```go
package main

import (
    "fmt"
    "sync"
)

func fanOut(in <-chan int, workers int) []<-chan int {
    outs := make([]<-chan int, workers)
    for i := 0; i < workers; i++ {
        out := make(chan int)
        outs[i] = out
        go func(o chan<- int) {
            for v := range in {
                o <- v * v // square the input
            }
            close(o)
        }(out)
    }
    return outs
}
```

## Step 6: Fan-In Pattern

Merge multiple channels into one.

```go
func fanIn(channels ...<-chan int) <-chan int {
    var wg sync.WaitGroup
    merged := make(chan int)

    output := func(c <-chan int) {
        defer wg.Done()
        for v := range c {
            merged <- v
        }
    }

    wg.Add(len(channels))
    for _, c := range channels {
        go output(c)
    }

    go func() {
        wg.Wait()
        close(merged)
    }()
    return merged
}
```

## Step 7: Putting It All Together

```go
package main

import (
    "fmt"
    "sort"
    "sync"
)

func producer(nums ...int) <-chan int {
    out := make(chan int)
    go func() {
        for _, n := range nums {
            out <- n
        }
        close(out)
    }()
    return out
}

func fanOut(in <-chan int, workers int) []<-chan int {
    outs := make([]<-chan int, workers)
    for i := 0; i < workers; i++ {
        out := make(chan int)
        outs[i] = out
        go func(o chan<- int) {
            for v := range in {
                o <- v * v
            }
            close(o)
        }(out)
    }
    return outs
}

func fanIn(channels ...<-chan int) <-chan int {
    var wg sync.WaitGroup
    merged := make(chan int)
    wg.Add(len(channels))
    for _, c := range channels {
        go func(ch <-chan int) {
            defer wg.Done()
            for v := range ch {
                merged <- v
            }
        }(c)
    }
    go func() { wg.Wait(); close(merged) }()
    return merged
}

func main() {
    src := producer(1, 2, 3, 4, 5, 6)
    workers := fanOut(src, 3)
    results := fanIn(workers...)

    var squares []int
    for r := range results {
        squares = append(squares, r)
    }
    sort.Ints(squares)
    fmt.Println("squares:", squares)
}
```

## Step 8: Capstone — Pipeline

Build a three-stage pipeline: generate → square → filter (keep evens).

```go
package main

import "fmt"

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

func filterEven(in <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        for n := range in {
            if n%2 == 0 { out <- n }
        }
        close(out)
    }()
    return out
}

func main() {
    nums   := generate(1, 2, 3, 4, 5, 6, 7, 8)
    sq     := square(nums)
    evens  := filterEven(sq)

    for v := range evens {
        fmt.Print(v, " ")
    }
    fmt.Println()
}
```

📸 **Verified Output:**
```
4 16 36 64
```

## Summary

| Concept | Key Points |
|---|---|
| Goroutine | `go func()` — lightweight, runtime-scheduled |
| Unbuffered channel | Synchronous handoff — both parties must be ready |
| Buffered channel | `make(chan T, n)` — async up to n items |
| Channel direction | `chan<- T` send-only, `<-chan T` receive-only |
| `close()` + `range` | Signal completion; only sender closes |
| Fan-out | Distribute one source to many workers |
| Fan-in | Merge many sources to one consumer |
| Pipeline | Chain stages via channels for composable data flow |
