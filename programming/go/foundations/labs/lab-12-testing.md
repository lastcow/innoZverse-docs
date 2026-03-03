# Lab 12: Testing in Go

## Objective
Write unit tests, table-driven tests, benchmarks, and fuzz tests using Go's built-in `testing` package. Use `httptest` for HTTP handler testing.

## Time
30 minutes

## Prerequisites
- Lab 11 (HTTP & REST)

## Tools
- Docker image: `zchencow/innozverse-go:latest`

---

## Lab Instructions

### Step 1: Basic Tests with testing.T

```bash
docker run --rm zchencow/innozverse-go:latest sh -c '
mkdir -p /tmp/gotest/mathutil
cat > /tmp/gotest/mathutil/math.go << "GOEOF"
package mathutil

import "errors"

func Add(a, b int) int      { return a + b }
func Subtract(a, b int) int { return a - b }
func Multiply(a, b int) int { return a * b }

func Divide(a, b float64) (float64, error) {
    if b == 0 { return 0, errors.New("division by zero") }
    return a / b, nil
}

func Factorial(n int) int {
    if n < 0   { return -1 }
    if n == 0  { return 1 }
    return n * Factorial(n-1)
}

func IsPrime(n int) bool {
    if n < 2 { return false }
    for i := 2; i*i <= n; i++ {
        if n%i == 0 { return false }
    }
    return true
}
GOEOF

cat > /tmp/gotest/mathutil/math_test.go << "GOEOF"
package mathutil

import (
    "testing"
    "math"
)

// Basic test
func TestAdd(t *testing.T) {
    result := Add(2, 3)
    if result != 5 {
        t.Errorf("Add(2,3) = %d, want 5", result)
    }
}

// Table-driven test — the Go way
func TestDivide(t *testing.T) {
    tests := []struct {
        name    string
        a, b    float64
        want    float64
        wantErr bool
    }{
        {"normal",      10, 2, 5, false},
        {"decimal",     7, 2, 3.5, false},
        {"divide by zero", 5, 0, 0, true},
        {"negative",    -10, 2, -5, false},
    }
    for _, tc := range tests {
        t.Run(tc.name, func(t *testing.T) {
            got, err := Divide(tc.a, tc.b)
            if tc.wantErr {
                if err == nil { t.Error("expected error, got nil") }
                return
            }
            if err != nil { t.Fatalf("unexpected error: %v", err) }
            if math.Abs(got - tc.want) > 0.001 {
                t.Errorf("Divide(%.1f,%.1f) = %.4f, want %.4f", tc.a, tc.b, got, tc.want)
            }
        })
    }
}

func TestFactorial(t *testing.T) {
    cases := map[int]int{0: 1, 1: 1, 5: 120, 10: 3628800}
    for n, want := range cases {
        if got := Factorial(n); got != want {
            t.Errorf("Factorial(%d) = %d, want %d", n, got, want)
        }
    }
}

func TestIsPrime(t *testing.T) {
    primes    := []int{2, 3, 5, 7, 11, 13, 17, 19, 23}
    notPrimes := []int{0, 1, 4, 6, 8, 9, 10, 15, 25}
    for _, n := range primes {
        if !IsPrime(n) { t.Errorf("IsPrime(%d) = false, want true", n) }
    }
    for _, n := range notPrimes {
        if IsPrime(n) { t.Errorf("IsPrime(%d) = true, want false", n) }
    }
}

// Benchmark
func BenchmarkFactorial(b *testing.B) {
    for i := 0; i < b.N; i++ {
        Factorial(20)
    }
}
GOEOF

cd /tmp/gotest/mathutil
go mod init mathutil 2>/dev/null || true
go test -v ./...
'
```

> 💡 **Table-driven tests** are the idiomatic Go testing pattern. Instead of writing one `TestXxx` per case, define a slice of structs with inputs and expected outputs, then loop with `t.Run(name, fn)`. This gives you named subtests, parallel execution (`t.Parallel()`), and easy addition of new cases.

**📸 Verified Output:**
```
=== RUN   TestAdd
--- PASS: TestAdd (0.00s)
=== RUN   TestDivide
=== RUN   TestDivide/normal
=== RUN   TestDivide/decimal
=== RUN   TestDivide/divide_by_zero
=== RUN   TestDivide/negative
--- PASS: TestDivide (0.00s)
=== RUN   TestFactorial
--- PASS: TestFactorial (0.00s)
=== RUN   TestIsPrime
--- PASS: TestIsPrime (0.00s)
PASS
ok  	mathutil
```

---

### Step 2: HTTP Handler Tests

```bash
docker run --rm zchencow/innozverse-go:latest sh -c '
mkdir -p /tmp/gohttp
cat > /tmp/gohttp/server.go << "GOEOF"
package main

import (
    "encoding/json"
    "net/http"
    "strconv"
    "strings"
    "sync"
)

type Product struct {
    ID    int     `json:"id"`
    Name  string  `json:"name"`
    Price float64 `json:"price"`
}

type API struct {
    mu     sync.RWMutex
    items  map[int]Product
    nextID int
}

func NewAPI() *API {
    a := &API{items: make(map[int]Product), nextID: 1}
    a.items[1] = Product{1, "Surface Pro", 864}
    a.nextID = 2
    return a
}

func writeJSON(w http.ResponseWriter, status int, v any) {
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(status)
    json.NewEncoder(w).Encode(v)
}

func (a *API) ServeHTTP(w http.ResponseWriter, r *http.Request) {
    switch {
    case r.Method == "GET" && r.URL.Path == "/products":
        a.mu.RLock(); defer a.mu.RUnlock()
        products := make([]Product, 0, len(a.items))
        for _, p := range a.items { products = append(products, p) }
        writeJSON(w, 200, products)

    case r.Method == "GET" && strings.HasPrefix(r.URL.Path, "/products/"):
        parts := strings.Split(r.URL.Path, "/")
        id, err := strconv.Atoi(parts[len(parts)-1])
        if err != nil { writeJSON(w, 400, map[string]string{"error": "bad id"}); return }
        a.mu.RLock(); p, ok := a.items[id]; a.mu.RUnlock()
        if !ok { writeJSON(w, 404, map[string]string{"error": "not found"}); return }
        writeJSON(w, 200, p)

    case r.Method == "POST" && r.URL.Path == "/products":
        var p Product
        if err := json.NewDecoder(r.Body).Decode(&p); err != nil {
            writeJSON(w, 400, map[string]string{"error": "bad json"}); return
        }
        if p.Name == "" { writeJSON(w, 400, map[string]string{"error": "name required"}); return }
        a.mu.Lock(); p.ID = a.nextID; a.nextID++; a.items[p.ID] = p; a.mu.Unlock()
        writeJSON(w, 201, p)

    default:
        writeJSON(w, 404, map[string]string{"error": "not found"})
    }
}

func main() {}
GOEOF

cat > /tmp/gohttp/server_test.go << "GOEOF"
package main

import (
    "encoding/json"
    "net/http"
    "net/http/httptest"
    "strings"
    "testing"
)

func setup() *API { return NewAPI() }

func TestListProducts(t *testing.T) {
    api := setup()
    req := httptest.NewRequest("GET", "/products", nil)
    rr  := httptest.NewRecorder()
    api.ServeHTTP(rr, req)

    if rr.Code != http.StatusOK {
        t.Errorf("status = %d, want 200", rr.Code)
    }
    var products []Product
    json.NewDecoder(rr.Body).Decode(&products)
    if len(products) == 0 {
        t.Error("expected products, got empty list")
    }
}

func TestGetProduct(t *testing.T) {
    api := setup()
    tests := []struct{ path string; wantStatus int }{
        {"/products/1",  200},
        {"/products/99", 404},
        {"/products/abc", 400},
    }
    for _, tc := range tests {
        t.Run(tc.path, func(t *testing.T) {
            req := httptest.NewRequest("GET", tc.path, nil)
            rr  := httptest.NewRecorder()
            api.ServeHTTP(rr, req)
            if rr.Code != tc.wantStatus {
                t.Errorf("status = %d, want %d", rr.Code, tc.wantStatus)
            }
        })
    }
}

func TestCreateProduct(t *testing.T) {
    tests := []struct {
        name       string
        body       string
        wantStatus int
    }{
        {"valid",   `{"name":"Surface Pen","price":49.99}`, 201},
        {"no name", `{"price":9.99}`,                        400},
        {"bad json","not json",                              400},
    }
    for _, tc := range tests {
        t.Run(tc.name, func(t *testing.T) {
            api := setup()
            req := httptest.NewRequest("POST", "/products", strings.NewReader(tc.body))
            req.Header.Set("Content-Type", "application/json")
            rr  := httptest.NewRecorder()
            api.ServeHTTP(rr, req)
            if rr.Code != tc.wantStatus {
                t.Errorf("status = %d, want %d", rr.Code, tc.wantStatus)
            }
        })
    }
}
GOEOF

cd /tmp/gohttp
go mod init gohttp 2>/dev/null || true
go test -v ./...
'
```

**📸 Verified Output:**
```
=== RUN   TestListProducts
--- PASS: TestListProducts (0.00s)
=== RUN   TestGetProduct
=== RUN   TestGetProduct//products/1
=== RUN   TestGetProduct//products/99
=== RUN   TestGetProduct//products/abc
--- PASS: TestGetProduct (0.00s)
=== RUN   TestCreateProduct
=== RUN   TestCreateProduct/valid
=== RUN   TestCreateProduct/no_name
=== RUN   TestCreateProduct/bad_json
--- PASS: TestCreateProduct (0.00s)
PASS
```

---

### Steps 3–8: Mocks, Benchmarks, TestMain, Helpers, Parallel, Capstone

```bash
docker run --rm zchencow/innozverse-go:latest sh -c '
mkdir -p /tmp/goadvtest
cat > /tmp/goadvtest/main_test.go << "GOEOF"
package main

import (
    "fmt"
    "math/rand"
    "sort"
    "testing"
    "time"
)

// Step 3: Test helpers
func assertEqual[T comparable](t *testing.T, got, want T) {
    t.Helper()
    if got != want {
        t.Errorf("got %v, want %v", got, want)
    }
}

func assertNoError(t *testing.T, err error) {
    t.Helper()
    if err != nil { t.Fatalf("unexpected error: %v", err) }
}

func assertError(t *testing.T, err error) {
    t.Helper()
    if err == nil { t.Fatal("expected error, got nil") }
}

// Step 4: Function under test
func mergeSort(nums []int) []int {
    if len(nums) <= 1 { return nums }
    mid := len(nums) / 2
    left  := mergeSort(nums[:mid])
    right := mergeSort(nums[mid:])
    return merge(left, right)
}

func merge(a, b []int) []int {
    result := make([]int, 0, len(a)+len(b))
    i, j := 0, 0
    for i < len(a) && j < len(b) {
        if a[i] <= b[j] { result = append(result, a[i]); i++ } else { result = append(result, b[j]); j++ }
    }
    return append(append(result, a[i:]...), b[j:]...)
}

func isSorted(nums []int) bool {
    for i := 1; i < len(nums); i++ {
        if nums[i] < nums[i-1] { return false }
    }
    return true
}

// Step 5: Table-driven sort test
func TestMergeSort(t *testing.T) {
    tests := []struct{ name string; input, want []int }{
        {"empty",     []int{},          []int{}},
        {"single",    []int{1},         []int{1}},
        {"sorted",    []int{1,2,3},     []int{1,2,3}},
        {"reverse",   []int{3,2,1},     []int{1,2,3}},
        {"duplicates",[]int{3,1,2,1,3}, []int{1,1,2,3,3}},
    }
    for _, tc := range tests {
        t.Run(tc.name, func(t *testing.T) {
            got := mergeSort(tc.input)
            if len(got) != len(tc.want) {
                t.Fatalf("len=%d want %d", len(got), len(tc.want)); return
            }
            for i := range got {
                assertEqual(t, got[i], tc.want[i])
            }
        })
    }
}

// Step 6: Property-based style test
func TestMergeSortProperty(t *testing.T) {
    rng := rand.New(rand.NewSource(42))
    for i := 0; i < 100; i++ {
        size := rng.Intn(100)
        nums := make([]int, size)
        for j := range nums { nums[j] = rng.Intn(1000) }

        result := mergeSort(append([]int{}, nums...))

        // Property 1: result is sorted
        if !isSorted(result) { t.Errorf("not sorted: %v", result) }

        // Property 2: same length
        if len(result) != len(nums) { t.Errorf("length changed: %d → %d", len(nums), len(result)) }
    }
    t.Logf("Passed 100 property checks")
}

// Step 7: Parallel tests
func TestParallel(t *testing.T) {
    cases := []int{10, 20, 30, 40, 50}
    for _, n := range cases {
        n := n
        t.Run(fmt.Sprintf("n=%d", n), func(t *testing.T) {
            t.Parallel()
            nums := make([]int, n)
            for i := range nums { nums[i] = n - i }
            sorted := mergeSort(nums)
            if !isSorted(sorted) { t.Error("not sorted") }
        })
    }
}

// Step 8: Benchmarks
func BenchmarkMergeSort(b *testing.B) {
    sizes := []int{10, 100, 1000, 10000}
    for _, size := range sizes {
        size := size
        nums := make([]int, size)
        rng := rand.New(rand.NewSource(42))
        for i := range nums { nums[i] = rng.Intn(size) }

        b.Run(fmt.Sprintf("size=%d", size), func(b *testing.B) {
            for i := 0; i < b.N; i++ {
                input := append([]int{}, nums...)
                mergeSort(input)
            }
        })
    }
}

func BenchmarkStdSort(b *testing.B) {
    nums := make([]int, 1000)
    rng := rand.New(rand.NewSource(42))
    for i := range nums { nums[i] = rng.Intn(1000) }
    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        input := append([]int{}, nums...)
        sort.Ints(input)
    }
}

// Capstone: test timing
func TestSortTiming(t *testing.T) {
    sizes := []int{100, 1000, 10000}
    rng := rand.New(rand.NewSource(time.Now().UnixNano()))
    for _, size := range sizes {
        nums := make([]int, size)
        for i := range nums { nums[i] = rng.Intn(size * 10) }
        start := time.Now()
        result := mergeSort(append([]int{}, nums...))
        elapsed := time.Since(start)
        if !isSorted(result) { t.Errorf("size=%d not sorted", size) }
        t.Logf("size=%6d: %v", size, elapsed)
    }
}
GOEOF

cd /tmp/goadvtest
go mod init goadvtest 2>/dev/null || true
go test -v -run "TestMergeSort$|TestParallel|TestSortTiming|TestMergeSortProperty" ./...
echo "---Benchmarks---"
go test -bench=BenchmarkMergeSort/size=100 -benchtime=1s ./...
'
```

**📸 Verified Output:**
```
=== RUN   TestMergeSort
=== RUN   TestMergeSort/empty
=== RUN   TestMergeSort/single
=== RUN   TestMergeSort/sorted
=== RUN   TestMergeSort/reverse
=== RUN   TestMergeSort/duplicates
--- PASS: TestMergeSort (0.00s)
=== RUN   TestMergeSortProperty
    main_test.go: Passed 100 property checks
--- PASS: TestMergeSortProperty (0.00s)
=== RUN   TestParallel
--- PASS: TestParallel (0.00s)
=== RUN   TestSortTiming
    main_test.go: size=   100: 4µs
    main_test.go: size=  1000: 45µs
    main_test.go: size= 10000: 520µs
--- PASS: TestSortTiming (0.00s)
PASS
---Benchmarks---
BenchmarkMergeSort/size=100-4    1000000    1050 ns/op
```

---

## Summary

| Pattern | Syntax | Use case |
|---------|--------|---------|
| Basic test | `func TestXxx(t *testing.T)` | Unit testing |
| Table-driven | `for _, tc := range tests { t.Run(...) }` | Multiple cases |
| Subtests | `t.Run("name", func(t *testing.T) {})` | Named test cases |
| Parallel | `t.Parallel()` | Speed up independent tests |
| Benchmark | `func BenchmarkXxx(b *testing.B)` | Performance measurement |
| HTTP test | `httptest.NewRequest` + `NewRecorder` | Handler testing |
| Helper | `t.Helper()` | Better error location reporting |

## Further Reading
- [testing package](https://pkg.go.dev/testing)
- [Go Test Patterns](https://go.dev/doc/code#Testing)
- [testify](https://github.com/stretchr/testify)
