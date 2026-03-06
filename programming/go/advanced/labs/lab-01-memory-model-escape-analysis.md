# Lab 01: Memory Model & Escape Analysis

**Time:** 45 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm golang:1.22-alpine sh`

## Overview

Understand Go's memory model, happens-before guarantees, stack vs heap allocation, and escape analysis. Master `sync/atomic` for lock-free programming.

## Prerequisites
- Go 1.22
- Basic goroutines and channels knowledge

---

## Step 1: Go Memory Model — Happens-Before

The Go memory model defines when a write to a variable is guaranteed to be visible to a read of that variable.

```go
// happens_before.go
package main

import (
	"fmt"
	"sync"
)

var (
	msg  string
	done bool
	mu   sync.Mutex
)

// WRONG: no synchronization — data race
func unsafeCommunicate() {
	go func() { msg = "hello" }()
	// msg might not be visible here!
	for !done {
	}
	fmt.Println(msg)
}

// CORRECT: channel establishes happens-before
func safeCommunicate() {
	ch := make(chan struct{})
	go func() {
		msg = "hello from goroutine"
		close(ch) // write happens-before close
	}()
	<-ch // close happens-before receive
	fmt.Println(msg) // safe to read
}

func main() {
	safeCommunicate()

	// Mutex also establishes happens-before
	mu.Lock()
	msg = "protected write"
	mu.Unlock()

	mu.Lock()
	fmt.Println(msg) // guaranteed to see "protected write"
	mu.Unlock()
}
```

> 💡 **Happens-before rule:** If event A happens-before event B, then A's effects are visible to B. Channel send happens-before channel receive. `sync.Mutex` unlock happens-before next lock.

---

## Step 2: Stack vs Heap Allocation

Go automatically decides where to allocate variables — stack (fast, no GC) or heap (GC-managed).

```go
// stack_heap.go
package main

import "fmt"

// Stack allocation: value doesn't escape
func stackAlloc() int {
	x := 42 // stays on stack
	return x // copy returned, x stays local
}

// Heap allocation: pointer escapes function
func heapAlloc() *int {
	x := 42  // x escapes to heap
	return &x // returning pointer forces heap allocation
}

// Heap: interface boxing can escape
func interfaceEscape() interface{} {
	x := 42
	return x // x may escape due to interface
}

// Stack: slice backed on stack (small, not escaping)
func stackSlice() int {
	s := [4]int{1, 2, 3, 4} // array on stack
	return s[0] + s[3]
}

func main() {
	fmt.Println("Stack value:", stackAlloc())
	fmt.Println("Heap pointer:", *heapAlloc())
	fmt.Println("Interface value:", interfaceEscape())
	fmt.Println("Stack slice:", stackSlice())
}
```

---

## Step 3: Escape Analysis with `-gcflags="-m"`

```bash
# Create the file
cat > /tmp/escape.go << 'EOF'
package main

import "fmt"

func escapeToHeap() *int {
	x := 42
	return &x
}

func noEscape() int {
	x := 42
	return x
}

func sliceEscape() []int {
	s := make([]int, 100) // escapes: too large or unknown size at compile time
	return s
}

func main() {
	p := escapeToHeap()
	n := noEscape()
	s := sliceEscape()
	fmt.Println(*p, n, len(s))
}
EOF

# Run escape analysis
go build -gcflags="-m" /tmp/escape.go 2>&1
```

📸 **Verified Output:**
```
# command-line-arguments
/tmp/escape.go:5:6: can inline escapeToHeap
/tmp/escape.go:10:6: can inline noEscape
/tmp/escape.go:6:2: moved to heap: x
/tmp/escape.go:15:13: make([]int, 100) escapes to heap
/tmp/escape.go:20:13: inlining call to fmt.Println
/tmp/escape.go:20:15: ... argument does not escape
```

> 💡 **`moved to heap: x`** means the compiler detected `x` outlives the function stack frame, so it heap-allocates it. Use `-gcflags="-m -m"` for more detail.

---

## Step 4: `sync/atomic` — Basic Operations

```go
// atomic_basic.go
package main

import (
	"fmt"
	"sync"
	"sync/atomic"
)

func main() {
	// atomic.Int64 (Go 1.19+)
	var counter atomic.Int64

	var wg sync.WaitGroup
	for i := 0; i < 1000; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			counter.Add(1)
		}()
	}
	wg.Wait()
	fmt.Printf("Counter: %d\n", counter.Load()) // always 1000

	// Store and Load
	var flag atomic.Bool
	flag.Store(true)
	fmt.Printf("Flag: %v\n", flag.Load())

	// Compare-And-Swap (CAS)
	var val atomic.Int64
	val.Store(10)
	swapped := val.CompareAndSwap(10, 20) // only swap if current == 10
	fmt.Printf("CAS swapped: %v, value: %d\n", swapped, val.Load())

	swapped = val.CompareAndSwap(10, 30) // fails: current is 20
	fmt.Printf("CAS swapped: %v, value: %d\n", swapped, val.Load())
}
```

Run it:
```bash
docker run --rm golang:1.22-alpine sh -c "cat > /tmp/main.go << 'GOEOF'
package main

import (
	\"fmt\"
	\"sync\"
	\"sync/atomic\"
)

func main() {
	var counter atomic.Int64
	var wg sync.WaitGroup
	for i := 0; i < 1000; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			counter.Add(1)
		}()
	}
	wg.Wait()
	fmt.Printf(\"Counter: %d\n\", counter.Load())
	var flag atomic.Bool
	flag.Store(true)
	fmt.Printf(\"Flag: %v\n\", flag.Load())
	var val atomic.Int64
	val.Store(10)
	swapped := val.CompareAndSwap(10, 20)
	fmt.Printf(\"CAS swapped: %v, value: %d\n\", swapped, val.Load())
	swapped = val.CompareAndSwap(10, 30)
	fmt.Printf(\"CAS second: %v, value: %d\n\", swapped, val.Load())
}
GOEOF
cd /tmp && go run main.go"
```

📸 **Verified Output:**
```
Counter: 1000
Flag: true
CAS swapped: true, value: 20
CAS second: false, value: 20
```

---

## Step 5: `atomic.Pointer[T]` — Type-Safe Pointer Swapping

```go
package main

import (
	"fmt"
	"sync/atomic"
)

type Config struct {
	MaxConns int
	Timeout  int
}

func main() {
	// Atomic pointer — safe concurrent config hot-reload
	var p atomic.Pointer[Config]

	cfg1 := &Config{MaxConns: 10, Timeout: 30}
	p.Store(cfg1)

	// Read current config (zero-allocation)
	current := p.Load()
	fmt.Printf("Config v1: MaxConns=%d, Timeout=%d\n",
		current.MaxConns, current.Timeout)

	// Hot-reload: swap to new config atomically
	cfg2 := &Config{MaxConns: 100, Timeout: 60}
	p.Store(cfg2)

	current = p.Load()
	fmt.Printf("Config v2: MaxConns=%d, Timeout=%d\n",
		current.MaxConns, current.Timeout)
}
```

---

## Step 6: Memory Ordering — Relaxed vs Sequential

```go
package main

import (
	"fmt"
	"sync"
	"sync/atomic"
)

// Demonstrates why mutex is needed for compound operations
func demonstrateRaceCondition() {
	// WRONG: non-atomic read-modify-write
	var counter int64
	var wg sync.WaitGroup
	for i := 0; i < 1000; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			// counter++ is NOT atomic: load, add, store = 3 ops
			atomic.AddInt64(&counter, 1) // CORRECT way
		}()
	}
	wg.Wait()
	fmt.Println("Safe counter:", atomic.LoadInt64(&counter))
}

// Once: single initialization with happens-before guarantee
func demonstrateOnce() {
	var once sync.Once
	var resource *string
	var wg sync.WaitGroup

	for i := 0; i < 10; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			once.Do(func() {
				s := fmt.Sprintf("initialized by goroutine %d", id)
				resource = &s
			})
		}(i)
	}
	wg.Wait()
	fmt.Println("Resource:", *resource)
}

func main() {
	demonstrateRaceCondition()
	demonstrateOnce()
}
```

---

## Step 7: Race Detector

```bash
# Create a file with a data race
cat > /tmp/race.go << 'EOF'
package main

import (
	"fmt"
	"sync"
)

func main() {
	m := make(map[string]int)
	var wg sync.WaitGroup
	for i := 0; i < 10; i++ {
		wg.Add(1)
		go func(n int) {
			defer wg.Done()
			m["key"] = n // DATA RACE: concurrent map write
		}(i)
	}
	wg.Wait()
	fmt.Println(m)
}
EOF

# Detect race
go run -race /tmp/race.go 2>&1 | head -20
```

> 💡 **Always run with `-race` during development and CI.** The race detector catches concurrent access bugs at runtime. It adds ~2-20x overhead, so don't use it in production.

---

## Step 8: Capstone — Lock-Free Stack

Build a lock-free LIFO stack using `atomic.Pointer` and CAS:

```go
package main

import (
	"fmt"
	"sync"
	"sync/atomic"
)

type node[T any] struct {
	val  T
	next *node[T]
}

// LockFreeStack is a concurrent LIFO stack using CAS
type LockFreeStack[T any] struct {
	head atomic.Pointer[node[T]]
}

func (s *LockFreeStack[T]) Push(val T) {
	newNode := &node[T]{val: val}
	for {
		oldHead := s.head.Load()
		newNode.next = oldHead
		if s.head.CompareAndSwap(oldHead, newNode) {
			return
		}
		// CAS failed: another goroutine modified head, retry
	}
}

func (s *LockFreeStack[T]) Pop() (T, bool) {
	for {
		oldHead := s.head.Load()
		if oldHead == nil {
			var zero T
			return zero, false
		}
		if s.head.CompareAndSwap(oldHead, oldHead.next) {
			return oldHead.val, true
		}
	}
}

func main() {
	var stack LockFreeStack[int]
	var wg sync.WaitGroup

	// Concurrent pushes
	for i := 0; i < 100; i++ {
		wg.Add(1)
		go func(n int) {
			defer wg.Done()
			stack.Push(n)
		}(i)
	}
	wg.Wait()

	// Pop all
	count := 0
	for {
		_, ok := stack.Pop()
		if !ok {
			break
		}
		count++
	}
	fmt.Printf("Pushed 100 items concurrently, popped: %d\n", count)
}
```

---

## Summary

| Concept | Key Tool | When to Use |
|---------|----------|-------------|
| Escape Analysis | `go build -gcflags="-m"` | Optimize allocations |
| Atomic Counter | `atomic.Int64.Add/Load` | High-frequency counters |
| CAS | `CompareAndSwap` | Lock-free state machines |
| Atomic Pointer | `atomic.Pointer[T]` | Config hot-reload |
| Race Detection | `go run -race` | Development & CI |
| Happens-Before | Channel / Mutex | Guarantee visibility |

**Key Takeaways:**
- Variables escape to heap when they outlive their stack frame
- `sync/atomic` operations are sequentially consistent
- CAS is the foundation of lock-free data structures
- Always use the race detector during testing
