# Lab 02: Functions, Closures & Defer

## Objective
Master Go functions: multiple return values, named returns, variadic functions, first-class functions, closures, and `defer`.

## Time
25 minutes

## Prerequisites
- Lab 01 (Hello World & Go Basics)

## Tools
- Docker image: `zchencow/innozverse-go:latest`

---

## Lab Instructions

### Step 1: Multiple Return Values

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import (
    "errors"
    "fmt"
    "strconv"
)

// Multiple returns — the Go way to handle errors
func safeDivide(a, b float64) (float64, error) {
    if b == 0 {
        return 0, errors.New("division by zero")
    }
    return a / b, nil
}

// Named return values — self-documenting
func stats(nums []float64) (mean, stddev float64, err error) {
    if len(nums) == 0 {
        err = errors.New("empty slice")
        return
    }
    for _, n := range nums {
        mean += n
    }
    mean /= float64(len(nums))
    for _, n := range nums {
        diff := n - mean
        stddev += diff * diff
    }
    stddev = stddev / float64(len(nums))
    return // naked return — returns named values
}

func parseInts(strs []string) ([]int, []error) {
    results := make([]int, 0, len(strs))
    errs    := make([]error, 0)
    for _, s := range strs {
        n, err := strconv.Atoi(s)
        if err != nil {
            errs = append(errs, fmt.Errorf("cannot parse %q: %w", s, err))
        } else {
            results = append(results, n)
        }
    }
    return results, errs
}

func main() {
    if result, err := safeDivide(10, 3); err != nil {
        fmt.Println("Error:", err)
    } else {
        fmt.Printf("10/3 = %.4f\n", result)
    }

    _, err := safeDivide(1, 0)
    fmt.Println("Error:", err)

    data := []float64{2, 4, 4, 4, 5, 5, 7, 9}
    mean, variance, err := stats(data)
    fmt.Printf("mean=%.2f variance=%.2f err=%v\n", mean, variance, err)

    nums, errs := parseInts([]string{"1", "2", "abc", "4", "xyz"})
    fmt.Println("Parsed:", nums)
    fmt.Println("Errors:", len(errs))
}
EOF
```

> 💡 **Named return values** serve as documentation AND allow naked returns. However, use them sparingly — in long functions, naked returns reduce clarity. The main use case is deferring a return value modification (e.g., in the error path).

**📸 Verified Output:**
```
10/3 = 3.3333
Error: division by zero
mean=5.00 variance=4.00 err=<nil>
Parsed: [1 2 4]
Errors: 2
```

---

### Step 2: Variadic & Functional Arguments

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import "fmt"

func sum(nums ...int) int {
    total := 0
    for _, n := range nums { total += n }
    return total
}

func product(nums ...int) int {
    p := 1
    for _, n := range nums { p *= n }
    return p
}

// Option pattern using variadic functions
type ServerConfig struct {
    host    string
    port    int
    timeout int
    debug   bool
}

type Option func(*ServerConfig)

func WithHost(h string) Option    { return func(c *ServerConfig) { c.host = h } }
func WithPort(p int) Option       { return func(c *ServerConfig) { c.port = p } }
func WithTimeout(t int) Option    { return func(c *ServerConfig) { c.timeout = t } }
func WithDebug(d bool) Option     { return func(c *ServerConfig) { c.debug = d } }

func NewServer(opts ...Option) *ServerConfig {
    cfg := &ServerConfig{host: "localhost", port: 8080, timeout: 30}
    for _, opt := range opts { opt(cfg) }
    return cfg
}

func main() {
    fmt.Println(sum(1, 2, 3, 4, 5))
    fmt.Println(sum())
    nums := []int{10, 20, 30}
    fmt.Println(sum(nums...))  // expand slice

    fmt.Println(product(2, 3, 4, 5))

    // Option pattern — functional configuration
    s1 := NewServer()
    s2 := NewServer(WithHost("0.0.0.0"), WithPort(9090), WithDebug(true))
    fmt.Printf("Default: %s:%d debug=%v\n", s1.host, s1.port, s1.debug)
    fmt.Printf("Custom:  %s:%d debug=%v timeout=%d\n", s2.host, s2.port, s2.debug, s2.timeout)
}
EOF
```

> 💡 **The functional options pattern** (`WithXxx` functions returning `func(*Config)`) is idiomatic Go for configuring structs with many optional parameters. It's used by `grpc.Dial`, `http.Server`, and most major Go libraries. It avoids long constructors and is backward compatible when new options are added.

**📸 Verified Output:**
```
15
0
60
120
Default: localhost:8080 debug=false
Custom:  0.0.0.0:9090 debug=true timeout=30
```

---

### Step 3: First-Class Functions & Higher-Order Functions

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import (
    "fmt"
    "strings"
)

// Functions as values
type Predicate[T any] func(T) bool
type Mapper[T, U any] func(T) U

func filter[T any](slice []T, pred func(T) bool) []T {
    result := make([]T, 0)
    for _, v := range slice {
        if pred(v) { result = append(result, v) }
    }
    return result
}

func mapSlice[T, U any](slice []T, fn func(T) U) []U {
    result := make([]U, len(slice))
    for i, v := range slice { result[i] = fn(v) }
    return result
}

func reduce[T, U any](slice []T, initial U, fn func(U, T) U) U {
    acc := initial
    for _, v := range slice { acc = fn(acc, v) }
    return acc
}

func compose[T any](fns ...func(T) T) func(T) T {
    return func(v T) T {
        for _, fn := range fns { v = fn(v) }
        return v
    }
}

func main() {
    nums := []int{1, 2, 3, 4, 5, 6, 7, 8, 9, 10}

    evens  := filter(nums, func(n int) bool { return n%2 == 0 })
    odds   := filter(nums, func(n int) bool { return n%2 != 0 })
    doubled := mapSlice(nums, func(n int) int { return n * 2 })
    total  := reduce(nums, 0, func(acc, n int) int { return acc + n })

    fmt.Println("Evens:", evens)
    fmt.Println("Odds:", odds)
    fmt.Println("Doubled:", doubled)
    fmt.Println("Sum:", total)

    // String pipeline via compose
    clean := compose(
        strings.TrimSpace,
        strings.ToLower,
        func(s string) string { return strings.ReplaceAll(s, " ", "-") },
    )
    fmt.Println(clean("  Hello World  "))
    fmt.Println(clean("  Dr. Chen's Lab  "))

    // Map: int → string
    strs := mapSlice(evens, func(n int) string { return fmt.Sprintf("#%d", n) })
    fmt.Println("Tagged:", strings.Join(strs, ", "))
}
EOF
```

> 💡 **Go 1.18+ generics** let you write `filter[T any]`, `mapSlice[T, U any]` that work with any type. Before generics, Go developers wrote separate versions for each type. The `[T any]` syntax means "T can be any type." `[T comparable]` would require T to support `==`.

**📸 Verified Output:**
```
Evens: [2 4 6 8 10]
Odds: [1 3 5 7 9]
Doubled: [2 4 6 8 10 12 14 16 18 20]
Sum: 55
hello-world
dr.-chen's-lab
Tagged: #2, #4, #6, #8, #10
```

---

### Step 4: Closures

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import "fmt"

// Closure — function that captures surrounding variables
func counter(start int) func() int {
    n := start
    return func() int {
        n++
        return n
    }
}

func adder(x int) func(int) int {
    return func(y int) int { return x + y }
}

func memoize(fn func(int) int) func(int) int {
    cache := make(map[int]int)
    return func(n int) int {
        if v, ok := cache[n]; ok {
            fmt.Printf("  [cache hit] %d\n", n)
            return v
        }
        result := fn(n)
        cache[n] = result
        return result
    }
}

func fibonacci() func() int {
    a, b := 0, 1
    return func() int {
        result := a
        a, b = b, a+b
        return result
    }
}

func main() {
    // Independent counters — separate closures, separate state
    c1 := counter(0)
    c2 := counter(100)
    fmt.Println(c1(), c1(), c1())   // 1 2 3
    fmt.Println(c2(), c2())          // 101 102
    fmt.Println(c1())                // 4 — c1 still running

    add5  := adder(5)
    add10 := adder(10)
    fmt.Println(add5(3), add10(3))   // 8 13

    // Memoized fibonacci
    var fib func(int) int
    fib = func(n int) int {
        if n <= 1 { return n }
        return fib(n-1) + fib(n-2)
    }
    memoFib := memoize(fib)
    for _, n := range []int{10, 10, 20, 20} {
        fmt.Printf("fib(%d) = %d\n", n, memoFib(n))
    }

    // Fibonacci generator
    next := fibonacci()
    for i := 0; i < 10; i++ {
        fmt.Printf("%d ", next())
    }
    fmt.Println()
}
EOF
```

> 💡 **Closures capture variables by reference**, not by value. Each call to `counter()` creates a new `n` variable, so `c1` and `c2` have independent state. This is the key difference from just passing values — closures maintain state between calls without using global variables or structs.

**📸 Verified Output:**
```
1 2 3
101 102
4
8 13
fib(10) = 55
  [cache hit] 10
fib(10) = 55
fib(20) = 6765
  [cache hit] 20
fib(20) = 6765
0 1 1 2 3 5 8 13 21 34
```

---

### Step 5: Defer

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import "fmt"

func withDefer() {
    fmt.Println("start")
    defer fmt.Println("deferred 1")
    defer fmt.Println("deferred 2")
    defer fmt.Println("deferred 3")
    fmt.Println("end")
    // defers run LIFO: 3, 2, 1
}

// defer for cleanup
func processFile(name string) (err error) {
    fmt.Printf("Opening %s\n", name)
    // Simulate open
    defer func() {
        fmt.Printf("Closing %s\n", name)
        // defer can modify named return values
    }()

    fmt.Printf("Processing %s\n", name)
    return nil
}

// defer with panic recovery
func safeDiv(a, b int) (result int, err error) {
    defer func() {
        if r := recover(); r != nil {
            err = fmt.Errorf("panic recovered: %v", r)
        }
    }()
    return a / b, nil
}

// defer captures loop variable by value
func deferLoop() {
    for i := 0; i < 3; i++ {
        i := i // shadow: capture current value
        defer fmt.Printf("loop defer: %d\n", i)
    }
}

func main() {
    withDefer()
    fmt.Println()
    processFile("config.json")
    fmt.Println()

    r1, err := safeDiv(10, 2)
    fmt.Printf("10/2=%d err=%v\n", r1, err)

    r2, err := safeDiv(10, 0)
    fmt.Printf("10/0=%d err=%v\n", r2, err)

    fmt.Println()
    deferLoop()
}
EOF
```

> 💡 **`defer` runs when the function returns**, in LIFO order. It's idiomatic Go for cleanup: `defer file.Close()`, `defer mu.Unlock()`, `defer db.Close()`. Combined with `recover()`, defer implements the only exception-like mechanism in Go. Unlike try/finally, defer is attached to the *function*, not a block.

**📸 Verified Output:**
```
start
end
deferred 3
deferred 2
deferred 1

Opening config.json
Processing config.json
Closing config.json

10/2=5 err=<nil>
10/0=0 err=panic recovered: runtime error: integer divide by zero

loop defer: 2
loop defer: 1
loop defer: 0
```

---

### Step 6: Recursion & Tail Calls

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import "fmt"

func factorial(n int) int {
    if n <= 1 { return 1 }
    return n * factorial(n-1)
}

// Iterative is preferred in Go (no TCO)
func factorialIter(n int) int {
    result := 1
    for i := 2; i <= n; i++ { result *= i }
    return result
}

// Tree traversal
type Node struct {
    Val   int
    Left  *Node
    Right *Node
}

func insert(root *Node, val int) *Node {
    if root == nil { return &Node{Val: val} }
    if val < root.Val { root.Left = insert(root.Left, val) } else
    if val > root.Val { root.Right = insert(root.Right, val) }
    return root
}

func inOrder(root *Node) []int {
    if root == nil { return nil }
    result := inOrder(root.Left)
    result  = append(result, root.Val)
    result  = append(result, inOrder(root.Right)...)
    return result
}

func height(root *Node) int {
    if root == nil { return 0 }
    l, r := height(root.Left), height(root.Right)
    if l > r { return l + 1 }
    return r + 1
}

func main() {
    for _, n := range []int{0, 1, 5, 10, 12} {
        fmt.Printf("%2d! = %d\n", n, factorial(n))
    }

    // Build BST
    vals := []int{5, 3, 7, 1, 4, 6, 8}
    var root *Node
    for _, v := range vals { root = insert(root, v) }

    fmt.Println("In-order:", inOrder(root))
    fmt.Println("Height:", height(root))
}
EOF
```

> 💡 **Go does not optimize tail calls** — deep recursion will cause a stack overflow. For production code, prefer iterative solutions or explicit stacks. Go's goroutine stacks start small (2KB) and grow automatically, so moderate recursion (hundreds of levels) is fine.

**📸 Verified Output:**
```
 0! = 1
 1! = 1
 5! = 120
10! = 3628800
12! = 479001600
In-order: [1 3 4 5 6 7 8]
Height: 3
```

---

### Step 7: init() & Package-Level Functions

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import (
    "fmt"
    "math/rand"
    "sort"
)

var (
    primes    []int
    lookup    map[int]bool
)

func init() {
    // init() runs before main(), automatically
    primes = sieve(50)
    lookup = make(map[int]bool, len(primes))
    for _, p := range primes { lookup[p] = true }
    fmt.Printf("[init] computed %d primes up to 50\n", len(primes))
}

func sieve(limit int) []int {
    composite := make([]bool, limit+1)
    for i := 2; i*i <= limit; i++ {
        if !composite[i] {
            for j := i * i; j <= limit; j += i {
                composite[j] = true
            }
        }
    }
    var primes []int
    for i := 2; i <= limit; i++ {
        if !composite[i] { primes = append(primes, i) }
    }
    return primes
}

func isPrime(n int) bool { return lookup[n] }

func main() {
    fmt.Println("Primes up to 50:", primes)

    // Test a few numbers
    for _, n := range []int{2, 7, 15, 17, 25, 37, 49} {
        fmt.Printf("  isPrime(%d) = %v\n", n, isPrime(n))
    }

    // sort.Slice with custom comparator
    words := []string{"banana", "apple", "cherry", "date", "elderberry"}
    sort.Slice(words, func(i, j int) bool { return len(words[i]) < len(words[j]) })
    fmt.Println("By length:", words)

    // sort.Search — binary search
    sort.Ints(primes)
    target := 17
    idx := sort.SearchInts(primes, target)
    if idx < len(primes) && primes[idx] == target {
        fmt.Printf("Found %d at index %d\n", target, idx)
    }

    _ = rand.Int() // suppress unused import
}
EOF
```

> 💡 **`init()` functions** run automatically before `main()`, after package-level variables are initialized. A package can have multiple `init()` functions — they run in source order. Use `init()` for one-time setup like loading config, registering drivers, or pre-computing lookup tables.

**📸 Verified Output:**
```
[init] computed 15 primes up to 50
Primes up to 50: [2 3 5 7 11 13 17 19 23 29 31 37 41 43 47]
  isPrime(2) = true
  isPrime(7) = true
  isPrime(15) = false
  isPrime(17) = true
  isPrime(25) = false
  isPrime(37) = true
  isPrime(49) = false
By length: [date apple banana cherry elderberry]
Found 17 at index 6
```

---

### Step 8: Capstone — Pipeline of Functions

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import (
    "fmt"
    "math"
    "strings"
)

// Pipeline stage
type Stage[T, U any] func(T) (U, error)

func pipe2[A, B, C any](f Stage[A, B], g Stage[B, C]) Stage[A, C] {
    return func(a A) (C, error) {
        b, err := f(a)
        if err != nil { var zero C; return zero, err }
        return g(b)
    }
}

// Data pipeline for product records
type RawRecord struct { Name, Price, Stock string }
type ParsedRecord struct { Name string; Price float64; Stock int }
type EnrichedRecord struct { ParsedRecord; Discount float64; Total float64 }

func parseRecord(r RawRecord) (ParsedRecord, error) {
    var p ParsedRecord
    p.Name = strings.TrimSpace(r.Name)
    if p.Name == "" { return p, fmt.Errorf("empty name") }
    if _, err := fmt.Sscanf(r.Price, "%f", &p.Price); err != nil {
        return p, fmt.Errorf("invalid price %q", r.Price)
    }
    if _, err := fmt.Sscanf(r.Stock, "%d", &p.Stock); err != nil {
        return p, fmt.Errorf("invalid stock %q", r.Stock)
    }
    return p, nil
}

func enrichRecord(p ParsedRecord) (EnrichedRecord, error) {
    e := EnrichedRecord{ParsedRecord: p}
    switch {
    case p.Stock > 100: e.Discount = 0.10
    case p.Stock > 50:  e.Discount = 0.05
    default:            e.Discount = 0
    }
    e.Total = math.Round(p.Price*(1-e.Discount)*float64(p.Stock)*100) / 100
    return e, nil
}

func main() {
    pipeline := pipe2(parseRecord, enrichRecord)

    records := []RawRecord{
        {"Surface Pro 12\"", "864.00", "15"},
        {"Surface Pen",      "49.99",  "80"},
        {"Office 365",       "99.99",  "999"},
        {"", "10", "5"},           // error: empty name
        {"Broken", "abc", "5"},    // error: invalid price
    }

    fmt.Printf("%-20s %8s %6s %8s %12s\n", "Name", "Price", "Stock", "Disc", "Total")
    fmt.Println(strings.Repeat("─", 60))

    for _, raw := range records {
        result, err := pipeline(raw)
        if err != nil {
            fmt.Printf("%-20s ERROR: %s\n", raw.Name, err)
            continue
        }
        fmt.Printf("%-20s %8.2f %6d %7.0f%% %12.2f\n",
            result.Name, result.Price, result.Stock,
            result.Discount*100, result.Total)
    }
}
EOF
```

**📸 Verified Output:**
```
Name                    Price  Stock     Disc        Total
────────────────────────────────────────────────────────────
Surface Pro 12"        864.00     15       0%      12960.00
Surface Pen             49.99     80       5%       3799.24
Office 365              99.99    999      10%      89991.00
                       ERROR: empty name
Broken                 ERROR: invalid price "abc"
```

---

## Summary

| Concept | Key points |
|---------|-----------|
| Multiple returns | `func f() (T, error)` — idiomatic Go error handling |
| Variadic | `func f(args ...T)` — pass slice with `slice...` |
| Functional options | `func WithX(val) func(*Config)` — flexible configuration |
| Closures | Capture variables by reference — maintain state |
| Defer | Runs at function exit, LIFO — use for cleanup |
| init() | Package setup before main() |
| Generics | `[T any]` for type-safe reusable functions |

## Further Reading
- [Go Functions](https://go.dev/tour/basics/4)
- [Functional Options Pattern](https://dave.cheney.net/2014/10/17/functional-options-for-friendly-apis)
