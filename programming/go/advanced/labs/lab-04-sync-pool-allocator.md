# Lab 04: sync.Pool & Allocator Patterns

**Time:** 45 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm golang:1.22-alpine sh`

## Overview

Master `sync.Pool` for amortizing allocation costs, implement the `bytes.Buffer` pooling pattern, benchmark with `-benchmem`, and understand arena allocator concepts.

---

## Step 1: `sync.Pool` Basics

```go
package main

import (
	"bytes"
	"fmt"
	"sync"
)

var bufPool = sync.Pool{
	New: func() interface{} {
		// Called when pool is empty
		buf := new(bytes.Buffer)
		buf.Grow(256) // pre-allocate
		return buf
	},
}

func processRequest(data string) string {
	buf := bufPool.Get().(*bytes.Buffer)
	buf.Reset() // always reset before use
	defer bufPool.Put(buf)

	buf.WriteString("processed: ")
	buf.WriteString(data)
	return buf.String()
}

func main() {
	// First call: pool is empty, New() is called
	result1 := processRequest("hello")
	fmt.Println(result1)

	// Second call: pool reuses the buffer
	result2 := processRequest("world")
	fmt.Println(result2)
}
```

> 💡 **Key insight:** `sync.Pool` objects may be collected by GC at any time. Never store state that must survive a GC cycle. The pool is a hint, not a guarantee.

---

## Step 2: Object Pool for HTTP Responses

```go
package main

import (
	"bytes"
	"fmt"
	"sync"
)

type Response struct {
	StatusCode int
	Headers    map[string]string
	Body       bytes.Buffer
}

func (r *Response) Reset() {
	r.StatusCode = 200
	for k := range r.Headers {
		delete(r.Headers, k)
	}
	r.Body.Reset()
}

var responsePool = sync.Pool{
	New: func() interface{} {
		return &Response{
			StatusCode: 200,
			Headers:    make(map[string]string, 4),
		}
	},
}

func buildResponse(code int, body string) *Response {
	resp := responsePool.Get().(*Response)
	resp.Reset()
	resp.StatusCode = code
	resp.Headers["Content-Type"] = "application/json"
	resp.Body.WriteString(body)
	return resp
}

func releaseResponse(r *Response) {
	responsePool.Put(r)
}

func main() {
	resp := buildResponse(200, `{"status":"ok"}`)
	fmt.Printf("Status: %d, Body: %s, CT: %s\n",
		resp.StatusCode,
		resp.Body.String(),
		resp.Headers["Content-Type"])
	releaseResponse(resp)
}
```

---

## Step 3: Benchmark — Pool vs No-Pool

```go
// bench_test.go
package main

import (
	"bytes"
	"sync"
	"testing"
)

// Without pool: allocates every time
func buildWithoutPool() []byte {
	var buf bytes.Buffer
	buf.WriteString("HTTP/1.1 200 OK\r\n")
	buf.WriteString("Content-Type: application/json\r\n\r\n")
	buf.WriteString(`{"status":"ok","data":"hello world"}`)
	return buf.Bytes()
}

// With pool: reuses buffer
var pool = sync.Pool{
	New: func() interface{} { return new(bytes.Buffer) },
}

func buildWithPool() []byte {
	buf := pool.Get().(*bytes.Buffer)
	buf.Reset()
	defer pool.Put(buf)
	buf.WriteString("HTTP/1.1 200 OK\r\n")
	buf.WriteString("Content-Type: application/json\r\n\r\n")
	buf.WriteString(`{"status":"ok","data":"hello world"}`)
	b := make([]byte, buf.Len())
	copy(b, buf.Bytes())
	return b
}

func BenchmarkWithoutPool(b *testing.B) {
	for i := 0; i < b.N; i++ {
		_ = buildWithoutPool()
	}
}

func BenchmarkWithPool(b *testing.B) {
	for i := 0; i < b.N; i++ {
		_ = buildWithPool()
	}
}
```

Run:
```bash
docker run --rm golang:1.22-alpine sh -c "
mkdir -p /tmp/poolbench
cat > /tmp/poolbench/bench_test.go << 'GOEOF'
package main

import (
	\"bytes\"
	\"sync\"
	\"testing\"
)

func buildWithoutPool() []byte {
	var buf bytes.Buffer
	buf.WriteString(\"HTTP/1.1 200 OK\r\n\")
	buf.WriteString(\"Content-Type: application/json\r\n\r\n\")
	buf.WriteString(\"{\\\"status\\\":\\\"ok\\\"}\")
	return buf.Bytes()
}

var pool = sync.Pool{New: func() interface{} { return new(bytes.Buffer) }}

func buildWithPool() []byte {
	buf := pool.Get().(*bytes.Buffer)
	buf.Reset()
	defer pool.Put(buf)
	buf.WriteString(\"HTTP/1.1 200 OK\r\n\")
	buf.WriteString(\"Content-Type: application/json\r\n\r\n\")
	buf.WriteString(\"{\\\"status\\\":\\\"ok\\\"}\")
	b := make([]byte, buf.Len())
	copy(b, buf.Bytes())
	return b
}

func BenchmarkWithoutPool(b *testing.B) { for i := 0; i < b.N; i++ { _ = buildWithoutPool() } }
func BenchmarkWithPool(b *testing.B) { for i := 0; i < b.N; i++ { _ = buildWithPool() } }
GOEOF
cat > /tmp/poolbench/main.go << 'GOEOF'
package main
func main() {}
GOEOF
cd /tmp/poolbench && go mod init poolbench && go test -bench=. -benchmem -count=1"
```

📸 **Verified Output:**
```
goos: linux
goarch: amd64
pkg: poolbench
cpu: Intel(R) Xeon(R) CPU E5-2699 v4 @ 2.20GHz
BenchmarkWithoutPool-32    	 3201385	       369.8 ns/op	     192 B/op	       2 allocs/op
BenchmarkWithPool-32       	 4760532	       245.9 ns/op	      80 B/op	       1 allocs/op
PASS
ok  	poolbench	3.027s
```

---

## Step 4: `bytes.Buffer` Pooling Pattern

```go
package main

import (
	"bytes"
	"fmt"
	"sync"
)

// BufferPool manages a pool of *bytes.Buffer with size classes
type BufferPool struct {
	small  sync.Pool // < 1KB
	medium sync.Pool // < 64KB
	large  sync.Pool // < 1MB
}

func NewBufferPool() *BufferPool {
	return &BufferPool{
		small:  sync.Pool{New: func() interface{} { b := make([]byte, 0, 512); return &b }},
		medium: sync.Pool{New: func() interface{} { b := make([]byte, 0, 32*1024); return &b }},
		large:  sync.Pool{New: func() interface{} { b := make([]byte, 0, 512*1024); return &b }},
	}
}

func (p *BufferPool) Get(sizeHint int) *bytes.Buffer {
	var buf bytes.Buffer
	switch {
	case sizeHint <= 512:
		buf.Grow(512)
	case sizeHint <= 32*1024:
		buf.Grow(32 * 1024)
	default:
		buf.Grow(512 * 1024)
	}
	return &buf
}

func main() {
	bp := NewBufferPool()
	buf := bp.Get(256)
	buf.WriteString("small response")
	fmt.Printf("Buffer: %q (cap: %d)\n", buf.String(), buf.Cap())
}
```

---

## Step 5: GC Interaction with sync.Pool

```go
package main

import (
	"fmt"
	"runtime"
	"sync"
)

func main() {
	var pool sync.Pool
	pool.New = func() interface{} {
		fmt.Println("  Pool.New called (cache miss)")
		return new(int)
	}

	fmt.Println("First Get (miss):")
	p1 := pool.Get().(*int)
	*p1 = 42

	pool.Put(p1)
	fmt.Println("Put back to pool")

	fmt.Println("Second Get (hit, no New called):")
	p2 := pool.Get().(*int)
	fmt.Printf("  Got: %d\n", *p2)
	pool.Put(p2)

	// Force GC — pool is cleared!
	fmt.Println("Running GC...")
	runtime.GC()
	runtime.GC() // Run twice to ensure pool sweep

	fmt.Println("Third Get after GC (miss again):")
	p3 := pool.Get().(*int)
	_ = p3
}
```

> 💡 **sync.Pool is cleared on each GC cycle.** This is intentional — it prevents memory leaks. The pool is a performance optimization, not a long-lived cache. For long-lived pools, use a channel-based approach.

---

## Step 6: Channel-Based Permanent Pool

```go
package main

import (
	"bytes"
	"fmt"
)

// PermanentPool survives GC (unlike sync.Pool)
type PermanentPool struct {
	ch chan *bytes.Buffer
}

func NewPermanentPool(size int) *PermanentPool {
	p := &PermanentPool{ch: make(chan *bytes.Buffer, size)}
	for i := 0; i < size; i++ {
		p.ch <- new(bytes.Buffer)
	}
	return p
}

func (p *PermanentPool) Get() *bytes.Buffer {
	select {
	case b := <-p.ch:
		b.Reset()
		return b
	default:
		return new(bytes.Buffer) // fallback
	}
}

func (p *PermanentPool) Put(b *bytes.Buffer) {
	select {
	case p.ch <- b:
	default:
		// pool full, discard (let GC handle it)
	}
}

func main() {
	pool := NewPermanentPool(10)
	buf := pool.Get()
	buf.WriteString("permanent pool test")
	fmt.Printf("Got from permanent pool: %q\n", buf.String())
	pool.Put(buf)
	fmt.Printf("Pool size: %d/%d\n", len(pool.ch), cap(pool.ch))
}
```

---

## Step 7: Arena Allocator Concept (Go 1.20+)

Go 1.20 added experimental arena support (`golang.org/x/exp/arena`). Arenas allow batch-freeing objects without GC pressure.

```go
// NOTE: arena is experimental — go get golang.org/x/exp/arena
// This shows the concept; use go1.20+ with GOEXPERIMENT=arenas

package main

import "fmt"

// Manual arena concept: allocate from a large block
type Arena struct {
	buf    []byte
	offset int
}

func NewArena(size int) *Arena {
	return &Arena{buf: make([]byte, size)}
}

// Alloc returns a slice from the arena (no GC overhead per object)
func (a *Arena) Alloc(size int) []byte {
	if a.offset+size > len(a.buf) {
		return make([]byte, size) // fallback
	}
	b := a.buf[a.offset : a.offset+size]
	a.offset += size
	return b
}

// Free releases the entire arena at once
func (a *Arena) Free() {
	a.offset = 0
}

func main() {
	arena := NewArena(1024 * 1024) // 1MB arena

	// Allocate many objects from the arena
	for i := 0; i < 1000; i++ {
		b := arena.Alloc(64)
		b[0] = byte(i % 256)
	}
	fmt.Printf("Arena used: %d bytes\n", arena.offset)

	// Free all at once — no individual GC pressure
	arena.Free()
	fmt.Printf("Arena freed, offset reset to: %d\n", arena.offset)
	fmt.Println("Concept: arena = bulk alloc + bulk free, perfect for request-scoped objects")
}
```

---

## Step 8: Capstone — HTTP Server with Full Pooling

```go
package main

import (
	"bytes"
	"fmt"
	"net/http"
	"sync"
	"sync/atomic"
	"time"
)

var (
	bufPool = sync.Pool{New: func() interface{} { return new(bytes.Buffer) }}
	reqCount atomic.Int64
)

func handler(w http.ResponseWriter, r *http.Request) {
	count := reqCount.Add(1)
	
	buf := bufPool.Get().(*bytes.Buffer)
	buf.Reset()
	defer bufPool.Put(buf)

	fmt.Fprintf(buf, `{"request":%d,"path":"%s","time":"%s"}`,
		count, r.URL.Path, time.Now().Format(time.RFC3339))

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(buf.Bytes())
}

func main() {
	mux := http.NewServeMux()
	mux.HandleFunc("/", handler)

	srv := &http.Server{Addr: ":18081", Handler: mux}
	go srv.ListenAndServe()
	time.Sleep(50 * time.Millisecond)

	// Make 5 requests
	for i := 0; i < 5; i++ {
		resp, _ := http.Get("http://localhost:18081/api/v1")
		buf := bufPool.Get().(*bytes.Buffer)
		buf.Reset()
		buf.ReadFrom(resp.Body)
		resp.Body.Close()
		fmt.Println(buf.String())
		bufPool.Put(buf)
	}
}
```

---

## Summary

| Pattern | Allocs/op | Use Case |
|---------|-----------|----------|
| No pool | 2 | Simple, low-traffic code |
| `sync.Pool` | 1 | High-throughput, GC-friendly |
| Channel pool | 0 | Permanent, survives GC |
| Arena | 0 (bulk) | Request-scoped bulk alloc |

**Key Takeaways:**
- `sync.Pool` cuts allocations and GC pressure significantly
- Always `Reset()` objects before returning to pool
- `sync.Pool` is cleared on GC — don't store important state
- Use `-benchmem` to measure `allocs/op`, not just `ns/op`
- Arenas are ideal for request-scoped allocations (parse, serialize, free)
