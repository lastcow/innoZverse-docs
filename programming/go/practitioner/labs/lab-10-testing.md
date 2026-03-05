# Lab 10: Testing

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm golang:1.22-alpine sh`

## Overview

Go has first-class testing support built in. The `testing` package, `go test` command, and `httptest` package make it easy to write unit tests, benchmarks, and integration tests without third-party libraries.

## Step 1: Basic Tests with testing.T

```go
// calc/calc.go
package calc

func Add(a, b int) int      { return a + b }
func Subtract(a, b int) int { return a - b }
func Multiply(a, b int) int { return a * b }
```

```go
// calc/calc_test.go
package calc

import "testing"

func TestAdd(t *testing.T) {
    got := Add(2, 3)
    want := 5
    if got != want {
        t.Errorf("Add(2, 3) = %d; want %d", got, want)
    }
}

func TestSubtract(t *testing.T) {
    if got := Subtract(10, 3); got != 7 {
        t.Errorf("Subtract(10, 3) = %d; want 7", got)
    }
}
```

```bash
go test ./...
go test -v ./...    # verbose output
go test -run TestAdd ./...  # run specific test
```

> 💡 **Tip:** Test files must end in `_test.go`. Test functions must start with `Test` and take `*testing.T`.

## Step 2: Table-Driven Tests

The idiomatic Go testing pattern — test many cases with one function.

```go
// calc/calc_test.go
package calc

import "testing"

func TestAdd_TableDriven(t *testing.T) {
    tests := []struct {
        name string
        a, b int
        want int
    }{
        {"both positive", 2, 3, 5},
        {"both negative", -1, -2, -3},
        {"mixed", 5, -3, 2},
        {"zeros", 0, 0, 0},
        {"large", 1000000, 2000000, 3000000},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got := Add(tt.a, tt.b)
            if got != tt.want {
                t.Errorf("Add(%d, %d) = %d; want %d", tt.a, tt.b, got, tt.want)
            }
        })
    }
}
```

## Step 3: Subtests with t.Run

`t.Run` creates named subtests that can be run individually.

```go
package calc

import (
    "testing"
    "fmt"
)

func TestMultiply(t *testing.T) {
    cases := map[string]struct{ a, b, want int }{
        "two positives":  {3, 4, 12},
        "positive/neg":   {3, -4, -12},
        "two negatives":  {-3, -4, 12},
        "by zero":        {5, 0, 0},
    }

    for name, tc := range cases {
        t.Run(name, func(t *testing.T) {
            if got := Multiply(tc.a, tc.b); got != tc.want {
                t.Errorf("Multiply(%d,%d)=%d want %d", tc.a, tc.b, got, tc.want)
            }
        })
    }
}

// Run: go test -run TestMultiply/two_positives
// Run: go test -run TestMultiply/by_zero
```

> 💡 **Tip:** Spaces in subtest names become underscores in `go test -run` patterns.

## Step 4: Benchmarks

```go
package calc

import "testing"

func BenchmarkAdd(b *testing.B) {
    for i := 0; i < b.N; i++ {
        Add(100, 200)
    }
}

func BenchmarkMultiply(b *testing.B) {
    b.ReportAllocs() // show allocations
    for i := 0; i < b.N; i++ {
        _ = fmt.Sprintf("%d", Multiply(i, 2))
    }
}
```

```bash
go test -bench=. ./...
go test -bench=BenchmarkAdd -benchtime=2s ./...
go test -bench=. -benchmem ./...  # include memory stats
```

## Step 5: Test Helpers

```go
package calc

import "testing"

// Helper marks a function as test helper — errors report the caller's line
func assertEqual(t *testing.T, got, want int) {
    t.Helper()
    if got != want {
        t.Errorf("got %d, want %d", got, want)
    }
}

func TestWithHelper(t *testing.T) {
    assertEqual(t, Add(1, 2), 3)
    assertEqual(t, Add(0, 0), 0)
    assertEqual(t, Add(-1, 1), 0)
}
```

## Step 6: httptest.NewRecorder — HTTP Handler Tests

```go
package calc

import (
    "encoding/json"
    "net/http"
    "net/http/httptest"
    "strings"
    "testing"
)

type Response struct {
    Result int `json:"result"`
}

func addHandler(w http.ResponseWriter, r *http.Request) {
    a := r.URL.Query().Get("a")
    b := r.URL.Query().Get("b")
    var av, bv int
    fmt.Sscan(a, &av)
    fmt.Sscan(b, &bv)
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(Response{Result: av + bv})
}

func TestAddHandler(t *testing.T) {
    cases := []struct {
        query      string
        wantStatus int
        wantResult int
    }{
        {"a=3&b=4", 200, 7},
        {"a=0&b=0", 200, 0},
        {"a=-5&b=10", 200, 5},
    }

    for _, tc := range cases {
        t.Run(tc.query, func(t *testing.T) {
            req := httptest.NewRequest("GET", "/add?"+tc.query, nil)
            rr := httptest.NewRecorder()
            addHandler(rr, req)

            if rr.Code != tc.wantStatus {
                t.Errorf("status: got %d want %d", rr.Code, tc.wantStatus)
            }

            var resp Response
            json.NewDecoder(strings.NewReader(rr.Body.String())).Decode(&resp)
            if resp.Result != tc.wantResult {
                t.Errorf("result: got %d want %d", resp.Result, tc.wantResult)
            }
        })
    }
}
```

## Step 7: Coverage

```bash
# Run with coverage
go test -cover ./...

# Generate coverage profile
go test -coverprofile=coverage.out ./...

# View coverage report in browser
go tool cover -html=coverage.out

# Per-function coverage
go tool cover -func=coverage.out
```

Output example:
```
ok  example.com/calc  0.003s  coverage: 87.5% of statements
```

## Step 8: Capstone — Full Test Suite

```go
// save as /tmp/testpkg/calc.go and calc_test.go

// calc.go
package calc

import "fmt"

func Add(a, b int) int      { return a + b }
func Sub(a, b int) int      { return a - b }
func Mul(a, b int) int      { return a * b }
func Div(a, b int) (int, error) {
    if b == 0 { return 0, fmt.Errorf("division by zero") }
    return a / b, nil
}

// calc_test.go
package calc

import "testing"

func TestAdd(t *testing.T) {
    tests := []struct{ name string; a, b, want int }{
        {"positive", 2, 3, 5},
        {"negative", -1, -2, -3},
        {"zero", 0, 5, 5},
    }
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            if got := Add(tt.a, tt.b); got != tt.want {
                t.Errorf("Add(%d,%d)=%d want %d", tt.a, tt.b, got, tt.want)
            }
        })
    }
}

func TestDiv_ByZero(t *testing.T) {
    _, err := Div(10, 0)
    if err == nil { t.Error("expected error") }
}

func BenchmarkAdd(b *testing.B) {
    for i := 0; i < b.N; i++ { Add(100, 200) }
}
```

Run:
```bash
mkdir -p /tmp/testpkg
# write calc.go and calc_test.go
cd /tmp/testpkg
go test -v -bench=. -benchtime=100ms ./...
```

📸 **Verified Output:**
```
=== RUN   TestAdd
=== RUN   TestAdd/positive
=== RUN   TestAdd/negative
=== RUN   TestAdd/zero
--- PASS: TestAdd (0.00s)
    --- PASS: TestAdd/positive (0.00s)
    --- PASS: TestAdd/negative (0.00s)
    --- PASS: TestAdd/zero (0.00s)
=== RUN   TestDiv_ByZero
--- PASS: TestDiv_ByZero (0.00s)
goos: linux
goarch: amd64
BenchmarkAdd-32    	139462273	         0.8593 ns/op
PASS
ok  	example.com/calc	0.233s
```

## Summary

| Command | Purpose |
|---|---|
| `go test ./...` | Run all tests |
| `go test -v ./...` | Verbose output |
| `go test -run TestName` | Run matching tests |
| `go test -bench=. ./...` | Run benchmarks |
| `go test -benchmem` | Show allocs in benchmarks |
| `go test -cover` | Show coverage % |
| `go test -coverprofile=out.cov` | Generate coverage profile |
| `go test -race ./...` | Detect data races |
| `t.Run(name, func)` | Subtests |
| `t.Helper()` | Mark as test helper (better error lines) |
| `t.Fatal` / `t.Error` | `Fatal` stops; `Error` continues |
| `httptest.NewRecorder()` | Capture HTTP handler output |
| `httptest.NewServer(h)` | Real TCP server for client tests |
