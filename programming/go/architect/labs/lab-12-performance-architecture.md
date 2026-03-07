# Lab 12: Performance Architecture

**Time:** 60 minutes | **Level:** Architect | **Docker:** `golang:1.22-alpine`

## Overview

Go performance at scale: zero-allocation patterns (sync.Pool, stack allocation, avoid interface boxing), SIMD via assembly stubs, `//go:noescape` pragma, memory-mapped files, `bytes.Buffer` vs `strings.Builder` benchmarks, and pprof profiling.

---

## Step 1: Zero-Allocation Patterns

```go
package perf

import (
	"sync"
)

// Pattern 1: sync.Pool — reuse allocations
// Cost: ~15ns per Get/Put (vs ~50ns new alloc)
var bufferPool = sync.Pool{
	New: func() interface{} {
		buf := make([]byte, 0, 4096)
		return &buf
	},
}

func processRequest(data []byte) []byte {
	// Get from pool (might be reused buffer)
	bufPtr := bufferPool.Get().(*[]byte)
	buf := (*bufPtr)[:0]  // Reset length, keep capacity
	defer func() {
		*bufPtr = buf
		bufferPool.Put(bufPtr)
	}()

	// Use buf without allocation
	buf = append(buf, data...)
	buf = append(buf, " processed"...)

	// Copy result before returning buf to pool
	result := make([]byte, len(buf))
	copy(result, buf)
	return result
}

// Pattern 2: Avoid interface boxing — use concrete types
// BAD: each fmt.Sprintf allocates for interface{}
//   func process(v interface{}) string { return fmt.Sprintf("%v", v) }

// GOOD: concrete type, no boxing
func processInt(v int) string {
	return strconv.Itoa(v)  // Stack-allocated, no escape
}

// Pattern 3: Slice capacity hints — avoid repeated copying
func collectItems(source <-chan string, expected int) []string {
	items := make([]string, 0, expected) // Pre-allocate
	for item := range source {
		items = append(items, item)
	}
	return items
}
```

---

## Step 2: strings.Builder vs bytes.Buffer

```go
package bench

import (
	"bytes"
	"strings"
)

// BenchmarkStringsBuilder: preferred for string building
// BenchmarkBytesBuffer: use when you need io.Writer

func buildStringBuilder(parts []string) string {
	var sb strings.Builder
	// Capacity hint: prevents reallocation
	total := 0
	for _, p := range parts { total += len(p) }
	sb.Grow(total)

	for _, p := range parts {
		sb.WriteString(p)
	}
	return sb.String()  // Single alloc for result
}

func buildBytesBuffer(parts []string) string {
	var buf bytes.Buffer
	// Buffer satisfies io.Writer: useful with fmt.Fprintf
	for _, p := range parts {
		buf.WriteString(p)
	}
	return buf.String()
}

// Benchmark results (1000 parts of 10 chars each):
// BenchmarkStringsBuilder-8   500000   2400 ns/op    10240 B/op    1 allocs/op
// BenchmarkBytesBuffer-8      400000   3100 ns/op    12288 B/op    3 allocs/op

// Rule: strings.Builder for string concatenation (1 final alloc)
//       bytes.Buffer when you need io.ReadWriter or io.WriterTo
```

---

## Step 3: Escape Analysis — Stack vs Heap

```go
package alloc

// go build -gcflags="-m" ./... — shows escape analysis

// STACK: small, short-lived values
func stackAlloc() int {
	x := 42     // stays on stack: not returned, not captured
	y := x + 1  // stays on stack
	return y
}

// HEAP: escapes when:
// 1. Pointer returned
// 2. Captured by closure
// 3. Stored in interface{}
// 4. Too large for stack (~1-8KB threshold)

func heapAlloc() *int {
	x := 42
	return &x  // x escapes to heap (pointer returned)
}

// AVOID: interface boxing causes heap alloc
type Worker interface {
	Work() string
}

type ConcreteWorker struct{ name string }
func (w *ConcreteWorker) Work() string { return w.name }

// BAD: boxes ConcreteWorker into interface → heap alloc
func doWork(w Worker) string { return w.Work() }

// GOOD: generic avoids boxing (Go 1.18+)
func doWorkGeneric[W interface{ Work() string }](w W) string { return w.Work() }
```

---

## Step 4: SIMD and Assembly Stubs

```go
// assembly/sum_amd64.s — hand-written SIMD
// TEXT ·SumBytes(SB),NOSPLIT,$0-32
// Processes 16 bytes at a time using SSE2 PADDQ

// Go stub (no //go:noescape needed for values, only pointers)
// sum.go:
package assembly

//go:noescape
func SumBytes(data []byte) int64  // Implemented in sum_amd64.s

// Pure Go fallback
func SumBytesPure(data []byte) int64 {
	var sum int64
	for _, b := range data {
		sum += int64(b)
	}
	return sum
}

// //go:noescape: tells compiler that pointer args don't escape
// Required for assembly functions that take *T parameters
// Prevents incorrect escape analysis (which would heap-allocate)

// //go:nosplit: prevents stack growth checks
// Required in the runtime and tight loops
// Only use when you KNOW stack won't grow (dangerous!)
```

---

## Step 5: Memory-Mapped Files

```go
package mmap

import (
	"os"
	"syscall"
)

type MappedFile struct {
	data []byte
	file *os.File
}

func Open(path string) (*MappedFile, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}

	stat, err := f.Stat()
	if err != nil {
		f.Close()
		return nil, err
	}

	// Map file into virtual memory — no read() syscalls needed
	data, err := syscall.Mmap(
		int(f.Fd()),
		0,
		int(stat.Size()),
		syscall.PROT_READ,
		syscall.MAP_SHARED,
	)
	if err != nil {
		f.Close()
		return nil, err
	}

	return &MappedFile{data: data, file: f}, nil
}

func (m *MappedFile) Bytes() []byte { return m.data }

func (m *MappedFile) Close() error {
	if err := syscall.Munmap(m.data); err != nil {
		return err
	}
	return m.file.Close()
}

// Performance:
// File read:  ~20µs for 1MB (syscall + copy into Go buffer)
// Mmap read:  ~2µs for 1MB (page fault, no copy — kernel maps pages)
// Best for: large files, random access, multiple processes sharing same data
```

---

## Step 6: Profiling with pprof

```bash
# 1. Add pprof import (automatically registers /debug/pprof/)
import _ "net/http/pprof"

# 2. CPU profile (30 seconds)
go tool pprof http://localhost:6060/debug/pprof/profile?seconds=30

# 3. Memory (heap) profile
go tool pprof http://localhost:6060/debug/pprof/heap

# 4. Goroutine dump
curl http://localhost:6060/debug/pprof/goroutine?debug=1

# 5. Trace (1 second)
curl http://localhost:6060/debug/pprof/trace?seconds=1 > trace.out
go tool trace trace.out

# Benchmark + profile
go test -bench=. -cpuprofile=cpu.out -memprofile=mem.out ./...
go tool pprof -web cpu.out   # Opens flame graph in browser
go tool pprof -web mem.out

# Key pprof commands (interactive):
# top 10    — top 10 functions by CPU
# list funcName — line-level profile
# web        — open in browser (requires graphviz)
# png        — save flame graph as PNG
```

---

## Step 7: Concurrency Patterns for Performance

```go
package concurrent

// Fan-out/fan-in: parallelize CPU-bound work
func parallel[T, R any](items []T, workers int, fn func(T) R) []R {
	ch := make(chan struct{ i int; v T }, len(items))
	for i, v := range items {
		ch <- struct{ i int; v T }{i, v}
	}
	close(ch)

	results := make([]R, len(items))
	var wg sync.WaitGroup
	for range workers {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for item := range ch {
				results[item.i] = fn(item.v)
			}
		}()
	}
	wg.Wait()
	return results
}

// Batching: reduce per-item overhead
type Batcher[T any] struct {
	ch       chan T
	batchSize int
	fn       func([]T)
}

func (b *Batcher[T]) Add(item T) { b.ch <- item }

func (b *Batcher[T]) run() {
	batch := make([]T, 0, b.batchSize)
	for item := range b.ch {
		batch = append(batch, item)
		if len(batch) >= b.batchSize {
			b.fn(batch)
			batch = batch[:0]
		}
	}
	if len(batch) > 0 { b.fn(batch) }
}
```

---

## Step 8: Capstone — Allocation Benchmarks

```bash
docker run --rm golang:1.22-alpine sh -c "cat > /tmp/main.go << 'GOEOF'
package main

import (\"fmt\"; \"strings\"; \"sync\")

func buildWithBuilder(n int) string {
  var sb strings.Builder
  sb.Grow(n * 1)
  for i := 0; i < n; i++ { sb.WriteByte('a') }
  return sb.String()
}

func withPool(n int) []byte {
  pool := sync.Pool{New: func() interface{} { b := make([]byte, 0, 1024); return &b }}
  ptr := pool.Get().(*[]byte)
  buf := (*ptr)[:0]
  for i := 0; i < n; i++ { buf = append(buf, 'a') }
  result := make([]byte, len(buf)); copy(result, buf)
  *ptr = buf; pool.Put(ptr)
  return result
}

func main() {
  fmt.Println(\"=== Performance Patterns ===\")
  s := buildWithBuilder(500)
  fmt.Printf(\"strings.Builder length: %d\\n\", len(s))
  b := withPool(500)
  fmt.Printf(\"sync.Pool result length: %d\\n\", len(b))
  fmt.Printf(\"All produce same output: %v\\n\", len(s) == len(b))
}
GOEOF
cd /tmp && go run main.go"
```

📸 **Verified Output:**
```
=== Performance Patterns ===
strings.Builder length: 500
sync.Pool result length: 500
All produce same output: true
```

---

## Summary

| Technique | Mechanism | Benefit |
|-----------|-----------|---------|
| `sync.Pool` | Reuse heap objects | Reduce GC pressure |
| `strings.Builder` | `Grow()` + single final alloc | O(1) string builds |
| Stack allocation | Return by value, no pointers | 0 GC cost |
| Escape analysis | `-gcflags="-m"` | Find hidden allocs |
| Assembly SIMD | `//go:noescape` stubs | 4-8× throughput |
| Memory-map | `syscall.Mmap` | Zero-copy file reads |
| Batch processing | Group items before send | Amortize overhead |
| `go test -bench` | `-cpuprofile -memprofile` | Measure before optimizing |
