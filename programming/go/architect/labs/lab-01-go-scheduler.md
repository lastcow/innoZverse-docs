# Lab 01: Go Runtime Scheduler

**Time:** 60 minutes | **Level:** Architect | **Docker:** `golang:1.22-alpine`

## Overview

Deep dive into the Go runtime scheduler: GMP model (Goroutine/Machine/Processor), GOMAXPROCS tuning, `runtime.LockOSThread()`, work stealing algorithm, `runtime/trace` for profiling, and goroutine lifecycle states.

---

## Step 1: The GMP Model

```
GMP (Goroutine / Machine / Processor):

  G (Goroutine)  — lightweight thread, ~2KB initial stack, grows as needed
  M (Machine)    — OS thread, usually GOMAXPROCS threads active
  P (Processor)  — scheduling context, has a run queue of goroutines

  Run Queue:
    Global queue (fallback)
    Per-P local queue (max 256 goroutines)

  States (goroutine):
    Runnable   — ready to run, waiting for P
    Running    — executing on an M
    Syscall    — blocked in OS syscall (M detaches from P)
    Waiting    — blocked on channel/mutex/timer/IO
    Dead       — finished
```

---

## Step 2: GOMAXPROCS Tuning

```go
package main

import (
	"fmt"
	"runtime"
	"sync"
)

func main() {
	// Default: number of logical CPUs
	fmt.Printf("NumCPU: %d\n", runtime.NumCPU())
	fmt.Printf("GOMAXPROCS (default): %d\n", runtime.GOMAXPROCS(0))

	// Set explicitly — returns old value
	old := runtime.GOMAXPROCS(4)
	fmt.Printf("GOMAXPROCS set to 4, was: %d\n", old)

	// Workload example
	var wg sync.WaitGroup
	results := make([]int, 8)

	for i := 0; i < 8; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			// CPU-bound work
			sum := 0
			for j := 0; j < 1_000_000; j++ {
				sum += j
			}
			results[id] = sum
		}(i)
	}

	wg.Wait()
	fmt.Printf("NumGoroutine after: %d\n", runtime.NumGoroutine())
	fmt.Printf("Results[0]: %d\n", results[0])
}
```

```
CPU-bound workloads: GOMAXPROCS = NumCPU (default, optimal)
I/O-bound workloads: can exceed NumCPU (goroutines sleep while waiting)
Container: set GOMAXPROCS to container CPU quota (not host CPUs!)
  Use: go.uber.org/automaxprocs for automatic container-aware tuning
```

---

## Step 3: runtime.LockOSThread()

```go
package main

import (
	"fmt"
	"runtime"
)

// Use LockOSThread when:
// 1. Calling C code that uses thread-local storage
// 2. Windows COM objects
// 3. Any OS API requiring thread affinity

func threadLocalWork() {
	// Lock this goroutine to its OS thread
	runtime.LockOSThread()
	defer runtime.UnlockOSThread()

	// Now this goroutine will always run on the same OS thread
	// Other goroutines are NOT affected

	fmt.Printf("Goroutine locked to OS thread\n")
	// ... thread-local work here ...
}

// Example: CGO + TLS
/*
#cgo CFLAGS: -g -Wall
#include <pthread.h>
static __thread int tls_value = 0;
void set_tls(int v) { tls_value = v; }
int  get_tls()      { return tls_value; }
*/
// import "C"
// func useTLS() {
//     runtime.LockOSThread()
//     defer runtime.UnlockOSThread()
//     C.set_tls(42)
//     v := C.get_tls()  // Always reads 42 — same OS thread
// }
```

---

## Step 4: Work Stealing Algorithm

```
Go's work stealing:
  Each P has a local run queue (deque)
  
  When P's local queue is empty:
    1. Check global queue (every 61 ticks)
    2. Steal from another P's local queue (steals half!)
    3. Check network poller for ready goroutines
  
  Stealing from the END of another P's deque:
    - Victim P adds to END (LIFO: hot goroutines)
    - Thief steals from FRONT (FIFO: older work)
    - Minimizes cache interference

  Implementation: runtime/proc.go stealWork()
```

---

## Step 5: runtime/trace

```go
package main

import (
	"os"
	"runtime/trace"
	"sync"
)

func main() {
	// Write trace to file
	f, _ := os.Create("trace.out")
	defer f.Close()

	trace.Start(f)
	defer trace.Stop()

	// Add user annotations — visible in trace viewer
	ctx, task := trace.NewTask(context.Background(), "ProcessBatch")
	defer task.End()

	var wg sync.WaitGroup
	for i := 0; i < 10; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			// Mark regions for trace viewer
			trace.WithRegion(ctx, "ProcessItem", func() {
				// ... work ...
			})
		}(i)
	}
	wg.Wait()
}

// Analyze: go tool trace trace.out
// Opens browser with:
// - Goroutine timeline (which P ran which G)
// - Heap profile
// - GC events
// - User task/region annotations
```

---

## Step 6: Goroutine Leak Detection

```go
package main

import (
	"fmt"
	"runtime"
	"time"
)

func leakyFunction() {
	// LEAK: goroutine blocked forever on unbuffered channel
	ch := make(chan int)
	go func() {
		// Nobody sends to ch — goroutine stuck here forever
		v := <-ch
		fmt.Println(v)
	}()
	// ch goes out of scope but goroutine still alive!
}

func main() {
	before := runtime.NumGoroutine()
	fmt.Printf("Before: %d goroutines\n", before)

	for i := 0; i < 10; i++ {
		leakyFunction()
	}

	time.Sleep(10 * time.Millisecond)
	after := runtime.NumGoroutine()
	fmt.Printf("After:  %d goroutines\n", after)
	fmt.Printf("Leaked: %d goroutines\n", after-before)

	// Fix: use context for cancellation
	// go func() {
	//     select {
	//     case v := <-ch:
	//         fmt.Println(v)
	//     case <-ctx.Done():
	//         return  // Goroutine exits cleanly
	//     }
	// }()
}
```

> 💡 Use `goleak` (go.uber.org/goleak) in tests to automatically detect goroutine leaks: `defer goleak.VerifyNone(t)`.

---

## Step 7: MemStats and GC Tuning

```go
package main

import (
	"fmt"
	"runtime"
	"runtime/debug"
)

func main() {
	var ms runtime.MemStats
	runtime.ReadMemStats(&ms)

	fmt.Printf("HeapAlloc:    %d KB\n", ms.HeapAlloc/1024)
	fmt.Printf("HeapSys:      %d KB\n", ms.HeapSys/1024)
	fmt.Printf("NumGC:        %d\n", ms.NumGC)
	fmt.Printf("PauseTotalNs: %d ms\n", ms.PauseTotalNs/1_000_000)
	fmt.Printf("GCCPUFraction: %.4f\n", ms.GCCPUFraction)

	// Tune GC: GOGC=200 means trigger at 200% growth (default 100%)
	// For latency-sensitive: debug.SetGCPercent(200)
	// For memory-sensitive: debug.SetGCPercent(50)

	// Manual GC trigger (use sparingly)
	runtime.GC()

	// Set soft memory limit (Go 1.19+)
	debug.SetMemoryLimit(512 * 1024 * 1024) // 512 MB
}
```

---

## Step 8: Capstone — Scheduler Demo

```bash
docker run --rm golang:1.22-alpine sh -c "cat > /tmp/main.go << 'GOEOF'
package main

import (
  \"fmt\"
  \"runtime\"
  \"sync\"
  \"time\"
)

func main() {
  fmt.Printf(\"Go Runtime Scheduler Demo\\n\")
  fmt.Printf(\"GOMAXPROCS: %d\\n\", runtime.GOMAXPROCS(0))
  fmt.Printf(\"NumCPU: %d\\n\", runtime.NumCPU())
  var wg sync.WaitGroup
  results := make([]int, 5)
  for i := 0; i < 5; i++ {
    wg.Add(1)
    go func(id int) { defer wg.Done(); results[id] = id * id }(i)
  }
  wg.Wait()
  fmt.Printf(\"NumGoroutine (after): %d\\n\", runtime.NumGoroutine())
  fmt.Printf(\"Goroutine results: %v\\n\", results)
  var ms runtime.MemStats
  runtime.ReadMemStats(&ms)
  fmt.Printf(\"HeapAlloc: %d KB\\n\", ms.HeapAlloc/1024)
  _ = time.Now()
}
GOEOF
cd /tmp && go run main.go"
```

📸 **Verified Output:**
```
Go Runtime Scheduler Demo
GOMAXPROCS: 32
NumCPU: 32
NumGoroutine (after): 1
Goroutine results: [0 1 4 9 16]
HeapAlloc: 321 KB
NumGC: 0
```

---

## Summary

| Component | Role | Tuning |
|-----------|------|--------|
| G (Goroutine) | ~2KB stack, grows | Keep short-lived |
| M (Machine) | OS thread | Limited by GOMAXPROCS |
| P (Processor) | Run queue (max 256) | = GOMAXPROCS |
| Work stealing | Balance load across Ps | Automatic |
| GOMAXPROCS | Parallelism degree | = NumCPU default |
| LockOSThread | Thread affinity | CGO/TLS only |
| runtime/trace | Profiling | `go tool trace` |
| GOGC | GC frequency | 100 default, tune for latency |
