# Lab 14: Performance Tuning

**Time:** 45 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm golang:1.22-alpine sh`

## Overview

Master Go runtime performance tuning: GOGC, GOMEMLIMIT, GOMAXPROCS, goroutine stack growth, zero-copy I/O with `net.Buffers`, TCP socket options, and systematic benchmarking with `-benchmem`.

---

## Step 1: GOMAXPROCS — CPU Parallelism

```go
package main

import (
	"fmt"
	"runtime"
	"sync"
	"time"
)

func cpuIntensiveWork(n int) float64 {
	result := 0.0
	for i := 0; i < n; i++ {
		result += float64(i) * 1.0001
	}
	return result
}

func parallelWork(procs int) time.Duration {
	runtime.GOMAXPROCS(procs)
	var wg sync.WaitGroup
	start := time.Now()

	numTasks := runtime.NumCPU() * 2
	for i := 0; i < numTasks; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			cpuIntensiveWork(1_000_000)
		}()
	}
	wg.Wait()
	return time.Since(start)
}

func main() {
	fmt.Printf("NumCPU: %d\n", runtime.NumCPU())
	fmt.Printf("Current GOMAXPROCS: %d\n", runtime.GOMAXPROCS(0))

	// GOMAXPROCS controls how many OS threads run Go code concurrently
	// Default: runtime.NumCPU()
	// Set via env: GOMAXPROCS=4 go run main.go
	// Set programmatically:
	old := runtime.GOMAXPROCS(4)
	fmt.Printf("Set GOMAXPROCS=4 (was %d)\n", old)
	runtime.GOMAXPROCS(old) // restore
}
```

---

## Step 2: GOGC Tuning

```go
package main

import (
	"fmt"
	"runtime"
	"runtime/debug"
)

func printGCStats(label string) {
	var ms runtime.MemStats
	runtime.ReadMemStats(&ms)
	fmt.Printf("[%s] Alloc=%.1fMB HeapSys=%.1fMB NumGC=%d PauseTotalMs=%.2f\n",
		label,
		float64(ms.Alloc)/1024/1024,
		float64(ms.HeapSys)/1024/1024,
		ms.NumGC,
		float64(ms.PauseTotalNs)/1e6,
	)
}

func allocateMB(mb int) [][]byte {
	chunks := make([][]byte, mb)
	for i := range chunks {
		chunks[i] = make([]byte, 1024*1024) // 1MB each
	}
	return chunks
}

func main() {
	// Default GOGC=100: GC runs when heap doubles since last collection
	fmt.Printf("Default GOGC: %d\n", debug.SetGCPercent(-1)) // -1 = query
	debug.SetGCPercent(100)                                    // restore

	printGCStats("before alloc")
	data := allocateMB(50) // allocate 50MB
	printGCStats("after 50MB alloc")
	_ = data

	runtime.GC()
	printGCStats("after GC")

	// Higher GOGC = fewer GC cycles, higher memory usage
	// Lower GOGC = more GC cycles, lower memory usage
	// GOGC=off disables GC entirely (use with GOMEMLIMIT)
	old := debug.SetGCPercent(200) // GC less frequently
	fmt.Printf("\nSet GOGC=200 (was %d)\n", old)

	data2 := allocateMB(20)
	printGCStats("with GOGC=200 after 20MB")
	_ = data2

	debug.SetGCPercent(old) // restore
}
```

---

## Step 3: GOMEMLIMIT (Go 1.19+)

```go
package main

import (
	"fmt"
	"math"
	"runtime"
	"runtime/debug"
)

func main() {
	fmt.Printf("NumCPU: %d\n", runtime.NumCPU())
	fmt.Printf("Current GOMAXPROCS: %d\n", runtime.GOMAXPROCS(0))

	// GOMEMLIMIT: soft memory limit
	// Prevents the process from using more than N bytes of memory
	// GC runs aggressively when approaching the limit
	current := debug.SetMemoryLimit(math.MaxInt64) // query current
	fmt.Printf("Current memory limit: %d (unlimited)\n", current)

	// Set 256MB limit
	debug.SetMemoryLimit(256 * 1024 * 1024)
	fmt.Println("Set GOMEMLIMIT=256MB")

	// Set via environment: GOMEMLIMIT=256MiB go run main.go

	var ms runtime.MemStats
	runtime.ReadMemStats(&ms)
	fmt.Printf("Alloc=%.1fMB HeapSys=%.1fMB NumGC=%d\n",
		float64(ms.Alloc)/1024/1024,
		float64(ms.HeapSys)/1024/1024,
		ms.NumGC)

	// Allocate and observe GC behavior near limit
	data := make([][]byte, 50)
	for i := range data {
		data[i] = make([]byte, 1024*1024) // 1MB each
	}
	runtime.ReadMemStats(&ms)
	fmt.Printf("After 50MB alloc: Alloc=%.1fMB NumGC=%d\n",
		float64(ms.Alloc)/1024/1024, ms.NumGC)
	_ = data

	// Restore unlimited
	debug.SetMemoryLimit(math.MaxInt64)
	fmt.Println("Done")
}
```

---

## Step 4: Goroutine Stack Growth

```go
package main

import (
	"fmt"
	"runtime"
)

// Goroutines start with 2-8KB stack and grow as needed (up to 1GB by default)
func demonstrateStackGrowth() {
	done := make(chan int)

	go func() {
		var recurse func(depth int) int
		recurse = func(depth int) int {
			if depth == 0 {
				return depth
			}
			return recurse(depth - 1)
		}
		result := recurse(10000) // forces stack growth through many frames
		done <- result
	}()

	<-done
	fmt.Printf("After stack growth: goroutines=%d\n", runtime.NumGoroutine())
}

func goroutineStacks() {
	// Stack trace for all goroutines
	buf := make([]byte, 1<<16) // 64KB
	n := runtime.Stack(buf, true)
	fmt.Printf("Stack trace size: %d bytes\n", n)
	// fmt.Printf("%s\n", buf[:n]) // print full stack trace
}

func main() {
	fmt.Printf("Initial goroutines: %d\n", runtime.NumGoroutine())
	demonstrateStackGrowth()
	goroutineStacks()
}
```

---

## Step 5: Benchmark Comparison

```go
// bench_test.go
package main

import (
	"bytes"
	"strings"
	"testing"
)

// String concatenation methods
func concatPlus(n int) string {
	s := ""
	for i := 0; i < n; i++ {
		s += "x"
	}
	return s
}

func concatBuilder(n int) string {
	var b strings.Builder
	b.Grow(n)
	for i := 0; i < n; i++ {
		b.WriteByte('x')
	}
	return b.String()
}

func concatBuffer(n int) string {
	var b bytes.Buffer
	b.Grow(n)
	for i := 0; i < n; i++ {
		b.WriteByte('x')
	}
	return b.String()
}

func BenchmarkConcatPlus(b *testing.B) {
	for i := 0; i < b.N; i++ {
		_ = concatPlus(100)
	}
}

func BenchmarkConcatBuilder(b *testing.B) {
	for i := 0; i < b.N; i++ {
		_ = concatBuilder(100)
	}
}

func BenchmarkConcatBuffer(b *testing.B) {
	for i := 0; i < b.N; i++ {
		_ = concatBuffer(100)
	}
}
```

```bash
go test -bench=. -benchmem -count=3
```

---

## Step 6: TCP Socket Options

```go
package main

import (
	"fmt"
	"net"
	"syscall"
)

func configureTCPConn(conn net.Conn) error {
	tcpConn, ok := conn.(*net.TCPConn)
	if !ok {
		return fmt.Errorf("not a TCP connection")
	}

	// TCP_NODELAY: disable Nagle's algorithm (low latency vs throughput)
	if err := tcpConn.SetNoDelay(true); err != nil {
		return fmt.Errorf("SetNoDelay: %w", err)
	}

	// SO_KEEPALIVE: enable TCP keepalive (detect dead connections)
	if err := tcpConn.SetKeepAlive(true); err != nil {
		return fmt.Errorf("SetKeepAlive: %w", err)
	}

	// Set buffer sizes
	tcpConn.SetReadBuffer(64 * 1024)
	tcpConn.SetWriteBuffer(64 * 1024)

	return nil
}

// net.Buffers: zero-copy scatter-gather I/O
func writeMultipleBuffers(conn net.Conn) error {
	header := []byte("HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n")
	body := []byte("Hello, World!")

	// net.Buffers uses writev syscall — writes all buffers in one syscall
	buffers := net.Buffers{header, body}
	_, err := buffers.WriteTo(conn)
	return err
}

// Raw syscall for advanced socket options
func setSocketRecvBuffer(fd uintptr, size int) error {
	return syscall.SetsockoptInt(int(fd), syscall.SOL_SOCKET, syscall.SO_RCVBUF, size)
}

func main() {
	fmt.Println("TCP optimization options:")
	fmt.Println("  TCP_NODELAY: disable Nagle, reduce latency (use for interactive protocols)")
	fmt.Println("  SO_KEEPALIVE: detect dead connections (important for long-lived connections)")
	fmt.Println("  SetReadBuffer/SetWriteBuffer: tune OS socket buffers")
	fmt.Println("  net.Buffers: scatter-gather writev syscall")
	fmt.Println("  SO_RCVBUF/SO_SNDBUF: kernel socket buffer sizes")
}
```

---

## Step 7: GC Stats + Memory Limits Demo

```bash
docker run --rm golang:1.22-alpine sh -c "cat > /tmp/main.go << 'GOEOF'
package main

import (
	\"fmt\"
	\"math\"
	\"runtime\"
	\"runtime/debug\"
)

func printStats(label string) {
	var m runtime.MemStats
	runtime.ReadMemStats(&m)
	fmt.Printf(\"[%s] Alloc=%.1fMB HeapSys=%.1fMB NumGC=%d\\n\",
		label, float64(m.Alloc)/1024/1024, float64(m.HeapSys)/1024/1024, m.NumGC)
}

func main() {
	fmt.Printf(\"GOMAXPROCS: %d\\n\", runtime.GOMAXPROCS(0))
	fmt.Printf(\"NumCPU: %d\\n\", runtime.NumCPU())
	old := debug.SetGCPercent(100)
	fmt.Printf(\"Old GOGC: %d, set to 100\\n\", old)
	limit := debug.SetMemoryLimit(256 * 1024 * 1024)
	fmt.Printf(\"Memory limit set to 256MB (was %d)\\n\", limit)
	printStats(\"before alloc\")
	data := make([][]byte, 10000)
	for i := range data { data[i] = make([]byte, 1024) }
	printStats(\"after alloc\")
	_ = data
	runtime.GC()
	printStats(\"after GC\")
	debug.SetGCPercent(old)
	debug.SetMemoryLimit(math.MaxInt64)
	fmt.Println(\"Done\")
}
GOEOF
go run /tmp/main.go"
```

📸 **Verified Output:**
```
GOMAXPROCS: 32
NumCPU: 32
Old GOGC: 100, set to 100
Memory limit set to 256MB (was 9223372036854775807)
[before alloc] Alloc=0.3MB HeapSys=3.7MB NumGC=0
[after alloc] Alloc=10.3MB HeapSys=11.5MB NumGC=2
[after GC] Alloc=0.3MB HeapSys=11.5MB NumGC=3
Done
```

---

## Step 8: Capstone — Systematic Performance Analysis

```bash
docker run --rm golang:1.22-alpine sh -c "
mkdir -p /tmp/benchlab
cat > /tmp/benchlab/main.go << 'GOEOF'
package main
import \"fmt\"
func main() { fmt.Println(\"bench lab\") }
GOEOF
cat > /tmp/benchlab/bench_test.go << 'GOEOF'
package main

import (
	\"bytes\"
	\"strings\"
	\"testing\"
)

func concatPlus(n int) string {
	s := \"\"
	for i := 0; i < n; i++ { s += \"x\" }
	return s
}

func concatBuilder(n int) string {
	var b strings.Builder; b.Grow(n)
	for i := 0; i < n; i++ { b.WriteByte('x') }
	return b.String()
}

func concatBuffer(n int) string {
	var b bytes.Buffer; b.Grow(n)
	for i := 0; i < n; i++ { b.WriteByte('x') }
	return b.String()
}

func BenchmarkConcatPlus(b *testing.B) { for i := 0; i < b.N; i++ { _ = concatPlus(100) } }
func BenchmarkConcatBuilder(b *testing.B) { for i := 0; i < b.N; i++ { _ = concatBuilder(100) } }
func BenchmarkConcatBuffer(b *testing.B) { for i := 0; i < b.N; i++ { _ = concatBuffer(100) } }
GOEOF
cd /tmp/benchlab && go mod init benchlab && go test -bench=. -benchmem -count=1 2>&1"
```

📸 **Verified Benchmark Output:**
```
goos: linux
goarch: amd64
pkg: benchlab
cpu: Intel(R) Xeon(R) CPU E5-2699 v4 @ 2.20GHz
BenchmarkConcatPlus-32       	  327231	      3603 ns/op	    5464 B/op	      99 allocs/op
BenchmarkConcatBuilder-32    	 6748960	       175.8 ns/op	     112 B/op	       1 allocs/op
BenchmarkConcatBuffer-32     	 4773376	       248.4 ns/op	     144 B/op	       2 allocs/op
PASS
ok  	benchlab	4.148s
```

**Analysis:**
- `concatPlus`: 99 allocs/op — quadratic allocation (string is immutable, every `+=` copies)
- `concatBuilder`: 1 alloc/op — 20x faster, ~48x fewer allocations
- `concatBuffer`: 2 allocs/op — good, but Builder is slightly better for pure string building

---

## Summary

| Knob | How to Set | Effect |
|------|-----------|--------|
| GOMAXPROCS | `runtime.GOMAXPROCS(n)` | CPU parallelism |
| GOGC | `debug.SetGCPercent(n)` | GC frequency vs memory |
| GOMEMLIMIT | `debug.SetMemoryLimit(n)` | Prevent OOM, control GC |
| TCP_NODELAY | `conn.SetNoDelay(true)` | Low-latency writes |
| SO_KEEPALIVE | `conn.SetKeepAlive(true)` | Dead connection detection |
| net.Buffers | `buffers.WriteTo(conn)` | Zero-copy scatter-gather |
| -benchmem | `go test -benchmem` | Measure allocs/op |

**Key Takeaways:**
- GOMEMLIMIT (Go 1.19) is the preferred way to control memory — beats GOGC alone
- GOMAXPROCS defaults to NumCPU — rarely needs tuning
- `strings.Builder` is 20x faster than `+= string` due to zero intermediate allocations
- TCP_NODELAY trades throughput for latency — enable for interactive protocols
- `net.Buffers` uses `writev` for efficient multi-buffer writes without copying
- Always benchmark before optimizing — measure, don't guess
