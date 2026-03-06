# Lab 02: Profiling with pprof

**Time:** 45 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm golang:1.22-alpine sh`

## Overview

Master Go's profiling tools: CPU profiling, heap profiling, goroutine analysis, and the `net/http/pprof` HTTP endpoint. Learn to benchmark with `testing.B` and analyze profiles with `go tool pprof`.

---

## Step 1: CPU Profiling with `runtime/pprof`

```go
// cpu_profile.go
package main

import (
	"os"
	"runtime/pprof"
	"math"
	"fmt"
)

func expensiveComputation(n int) float64 {
	result := 0.0
	for i := 0; i < n; i++ {
		result += math.Sqrt(float64(i)) * math.Sin(float64(i))
	}
	return result
}

func main() {
	// Start CPU profile
	f, _ := os.Create("cpu.prof")
	defer f.Close()
	pprof.StartCPUProfile(f)
	defer pprof.StopCPUProfile()

	// Do work
	result := expensiveComputation(10_000_000)
	fmt.Printf("Result: %.4f\n", result)
}
```

```bash
go run cpu_profile.go
go tool pprof -top cpu.prof
```

---

## Step 2: Heap Profiling

```go
// heap_profile.go
package main

import (
	"os"
	"runtime"
	"runtime/pprof"
	"fmt"
)

func allocateSlices(n int) [][]byte {
	slices := make([][]byte, n)
	for i := range slices {
		slices[i] = make([]byte, 1024) // 1KB each
	}
	return slices
}

func main() {
	data := allocateSlices(100_000) // ~100MB
	fmt.Printf("Allocated %d slices\n", len(data))
	_ = data

	runtime.GC() // force GC before heap snapshot

	f, _ := os.Create("heap.prof")
	defer f.Close()
	pprof.WriteHeapProfile(f)
	fmt.Println("Heap profile written to heap.prof")
}
```

```bash
go run heap_profile.go
go tool pprof -top heap.prof
```

---

## Step 3: HTTP pprof Endpoint

```go
// http_pprof.go
package main

import (
	"fmt"
	"math"
	"net/http"
	_ "net/http/pprof" // registers /debug/pprof/ routes
	"time"
)

func cpuBurn() {
	for {
		x := 0.0
		for i := 0; i < 1000; i++ {
			x += math.Sqrt(float64(i))
		}
		_ = x
		time.Sleep(time.Microsecond)
	}
}

func main() {
	go cpuBurn()

	fmt.Println("pprof server at http://localhost:6060/debug/pprof/")
	fmt.Println("Try:")
	fmt.Println("  go tool pprof http://localhost:6060/debug/pprof/profile?seconds=5")
	fmt.Println("  go tool pprof http://localhost:6060/debug/pprof/heap")
	fmt.Println("  curl http://localhost:6060/debug/pprof/goroutine?debug=1")

	http.ListenAndServe(":6060", nil)
}
```

> 💡 **The `/debug/pprof/` routes are registered automatically** when you import `net/http/pprof` with a blank identifier. Never expose this endpoint publicly — it leaks internals.

---

## Step 4: Benchmarks with Profiling

```go
// fib_bench_test.go
package main

import "testing"

func fibRecursive(n int) int {
	if n <= 1 { return n }
	return fibRecursive(n-1) + fibRecursive(n-2)
}

func fibIterative(n int) int {
	if n <= 1 { return n }
	a, b := 0, 1
	for i := 2; i <= n; i++ {
		a, b = b, a+b
	}
	return b
}

func BenchmarkFibRecursive(b *testing.B) {
	for i := 0; i < b.N; i++ {
		fibRecursive(30)
	}
}

func BenchmarkFibIterative(b *testing.B) {
	for i := 0; i < b.N; i++ {
		fibIterative(30)
	}
}
```

```bash
# Run benchmarks and generate CPU profile
go test -bench=. -cpuprofile=cpu.prof -benchmem

# Analyze
go tool pprof -top cpu.prof
```

---

## Step 5: Goroutine Profile

```go
// goroutine_profile.go
package main

import (
	"fmt"
	"os"
	"runtime/pprof"
	"sync"
	"time"
)

func worker(id int, wg *sync.WaitGroup) {
	defer wg.Done()
	time.Sleep(100 * time.Millisecond) // simulate work
}

func main() {
	var wg sync.WaitGroup
	for i := 0; i < 50; i++ {
		wg.Add(1)
		go worker(i, &wg)
	}

	// Capture goroutine profile while workers run
	f, _ := os.Create("goroutine.prof")
	pprof.Lookup("goroutine").WriteTo(f, 0)
	f.Close()
	fmt.Println("Goroutine profile written")

	wg.Wait()
}
```

```bash
go run goroutine_profile.go
go tool pprof -top goroutine.prof
```

---

## Step 6: Allocs Profile

```go
// allocs_test.go
package main

import (
	"strings"
	"testing"
)

// Bad: allocates new string each iteration
func buildStringBad(n int) string {
	s := ""
	for i := 0; i < n; i++ {
		s += "x"
	}
	return s
}

// Good: uses strings.Builder
func buildStringGood(n int) string {
	var b strings.Builder
	b.Grow(n)
	for i := 0; i < n; i++ {
		b.WriteByte('x')
	}
	return b.String()
}

func BenchmarkStringBad(b *testing.B) {
	for i := 0; i < b.N; i++ {
		buildStringBad(100)
	}
}

func BenchmarkStringGood(b *testing.B) {
	for i := 0; i < b.N; i++ {
		buildStringGood(100)
	}
}
```

```bash
go test -bench=. -benchmem -memprofile=mem.prof
go tool pprof -top mem.prof
```

---

## Step 7: `go tool pprof` Interactive Mode

```bash
# Generate a 30-second CPU profile
go tool pprof http://localhost:6060/debug/pprof/profile?seconds=30

# Inside pprof interactive mode:
# (pprof) top10          -- show top 10 functions by CPU
# (pprof) top10 -cum     -- cumulative (includes callees)
# (pprof) list funcName  -- show source with annotations
# (pprof) web            -- open flame graph in browser
# (pprof) png            -- save graph as PNG
# (pprof) quit

# One-liner analysis
go tool pprof -top cpu.prof
go tool pprof -svg cpu.prof > cpu.svg
```

> 💡 **Use `-http=:8080`** to launch the pprof web UI with flame graphs: `go tool pprof -http=:8080 cpu.prof`

---

## Step 8: Capstone — Full Profiling Workflow

```go
// capstone_profile_test.go
package main

import (
	"fmt"
	"math/rand"
	"sort"
	"testing"
)

// Slow: allocates new slice each call
func sortNumbersSlow(n int) []int {
	nums := make([]int, n)
	for i := range nums {
		nums[i] = rand.Intn(1000)
	}
	sort.Ints(nums)
	return nums
}

// Fast: reuses slice via sync.Pool
var slicePool = make(chan []int, 10)

func getSlice(n int) []int {
	select {
	case s := <-slicePool:
		if cap(s) >= n {
			return s[:n]
		}
	default:
	}
	return make([]int, n)
}

func returnSlice(s []int) {
	select {
	case slicePool <- s:
	default:
	}
}

func sortNumbersFast(n int) []int {
	nums := getSlice(n)
	for i := range nums {
		nums[i] = rand.Intn(1000)
	}
	sort.Ints(nums)
	result := make([]int, n)
	copy(result, nums)
	returnSlice(nums)
	return result
}

func BenchmarkSortSlow(b *testing.B) {
	for i := 0; i < b.N; i++ {
		_ = sortNumbersSlow(1000)
	}
}

func BenchmarkSortFast(b *testing.B) {
	for i := 0; i < b.N; i++ {
		_ = sortNumbersFast(1000)
	}
}

func main() {
	fmt.Println("Run: go test -bench=. -benchmem -cpuprofile=cpu.prof")
	fmt.Println("Then: go tool pprof -top cpu.prof")
}
```

Run the full workflow:
```bash
cat > /tmp/prof_test.go << 'EOF'
package main

import (
	"math/rand"
	"sort"
	"testing"
)

func sortNumbers(n int) []int {
	nums := make([]int, n)
	for i := range nums { nums[i] = rand.Intn(10000) }
	sort.Ints(nums)
	return nums
}

func BenchmarkSort(b *testing.B) {
	for i := 0; i < b.N; i++ { _ = sortNumbers(1000) }
}
EOF
cat > /tmp/main.go << 'EOF'
package main
func main() {}
EOF
cd /tmp && go test -bench=BenchmarkSort -benchmem -cpuprofile=cpu.prof -count=1
go tool pprof -top cpu.prof 2>&1 | head -15
```

📸 **Verified Output:**
```
goos: linux
goarch: amd64
pkg: proflab
cpu: Intel(R) Xeon(R) CPU E5-2699 v4 @ 2.20GHz
BenchmarkSort-32    	   46464	     25702 ns/op	    8192 B/op	       1 allocs/op
PASS

File: prof.test
Type: cpu
...
Showing top 10 nodes out of 28
      flat  flat%   sum%        cum   cum%
     340ms 34.00% 34.00%      340ms 34.00%  runtime.memmove
     150ms 15.00% 49.00%      150ms 15.00%  sort.pdqsort...
```

---

## Summary

| Tool | Command | Purpose |
|------|---------|---------|
| CPU Profile | `pprof.StartCPUProfile(f)` | Find CPU hotspots |
| Heap Profile | `pprof.WriteHeapProfile(f)` | Find memory usage |
| Goroutine Profile | `pprof.Lookup("goroutine")` | Find goroutine leaks |
| HTTP pprof | `import _ "net/http/pprof"` | Live server profiling |
| Benchmark + profile | `go test -bench -cpuprofile` | Measure + profile together |
| Analysis | `go tool pprof -top file.prof` | Analyze profiles |

**Key Takeaways:**
- CPU profiles sample goroutine stacks at 100Hz by default
- Heap profiles show in-use allocations at snapshot time
- Always use `-benchmem` to see allocation counts
- `go tool pprof -http=:8080` provides an interactive flame graph UI
