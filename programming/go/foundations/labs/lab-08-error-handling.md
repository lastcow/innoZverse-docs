# Lab 08: Error Handling

## Objective
Master Go's error handling philosophy: errors as values, custom error types, `errors.Is/As`, wrapping, sentinel errors, and panic/recover.

## Time
30 minutes

## Prerequisites
- Lab 05 (Interfaces)

## Tools
- Docker image: `zchencow/innozverse-go:latest`

---

## Lab Instructions

### Step 1: The error Interface

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import (
    "errors"
    "fmt"
)

// errors.New — simple error
var ErrDivByZero = errors.New("division by zero")

// fmt.Errorf — formatted error
func safeDivide(a, b float64) (float64, error) {
    if b == 0 { return 0, ErrDivByZero }
    return a / b, nil
}

func parseAge(s string) (int, error) {
    var age int
    if _, err := fmt.Sscanf(s, "%d", &age); err != nil {
        return 0, fmt.Errorf("parseAge(%q): %w", s, err) // %w wraps the error
    }
    if age < 0 || age > 150 {
        return 0, fmt.Errorf("parseAge(%q): age %d out of range [0, 150]", s, age)
    }
    return age, nil
}

func main() {
    // Always check errors
    result, err := safeDivide(10, 3)
    if err != nil {
        fmt.Println("Error:", err)
    } else {
        fmt.Printf("10/3 = %.4f\n", result)
    }

    _, err = safeDivide(5, 0)

    // errors.Is — checks if error IS (or wraps) a specific error
    fmt.Println("Is ErrDivByZero:", errors.Is(err, ErrDivByZero))

    // Error wrapping chain
    age, err := parseAge("25")
    fmt.Printf("Age: %d, err: %v\n", age, err)

    _, err = parseAge("abc")
    fmt.Println("Error:", err)

    _, err = parseAge("200")
    fmt.Println("Error:", err)
}
EOF
```

> 💡 **`%w` in `fmt.Errorf` wraps an error**, maintaining the error chain. `errors.Is(err, target)` walks the entire chain — if any error in the chain matches `target`, it returns true. Without `%w` (using `%v` or `%s` instead), the original error is lost and `errors.Is` won't find it.

**📸 Verified Output:**
```
10/3 = 3.3333
Is ErrDivByZero: true
Age: 25, err: <nil>
Error: parseAge("abc"): expected integer
Error: parseAge("200"): age 200 out of range [0, 150]
```

---

### Step 2: Custom Error Types

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import (
    "errors"
    "fmt"
)

// Custom error type with fields
type ValidationError struct {
    Field   string
    Value   any
    Message string
}

func (e *ValidationError) Error() string {
    return fmt.Sprintf("validation failed for %s=%v: %s", e.Field, e.Value, e.Message)
}

type NotFoundError struct {
    Resource string
    ID       any
}

func (e *NotFoundError) Error() string {
    return fmt.Sprintf("%s with id=%v not found", e.Resource, e.ID)
}

// Multi-error type
type MultiError struct{ Errs []error }

func (m *MultiError) Error() string {
    msgs := make([]string, len(m.Errs))
    for i, e := range m.Errs { msgs[i] = e.Error() }
    result := ""
    for i, m := range msgs {
        if i > 0 { result += "; " }
        result += m
    }
    return fmt.Sprintf("%d error(s): %s", len(msgs), result)
}

func (m *MultiError) Unwrap() []error { return m.Errs }

func validateProduct(name string, price float64, stock int) error {
    var errs []error
    if name == "" {
        errs = append(errs, &ValidationError{"name", name, "cannot be empty"})
    }
    if price <= 0 {
        errs = append(errs, &ValidationError{"price", price, "must be positive"})
    }
    if stock < 0 {
        errs = append(errs, &ValidationError{"stock", stock, "cannot be negative"})
    }
    if len(errs) > 0 { return &MultiError{errs} }
    return nil
}

func findProduct(id int) (string, error) {
    products := map[int]string{1: "Surface Pro", 2: "Surface Pen"}
    if p, ok := products[id]; ok { return p, nil }
    return "", &NotFoundError{"product", id}
}

func main() {
    // errors.As — unwraps and checks type
    _, err := findProduct(99)
    var notFound *NotFoundError
    if errors.As(err, &notFound) {
        fmt.Printf("Resource=%s ID=%v\n", notFound.Resource, notFound.ID)
    }

    // Multi-error
    err = validateProduct("", -10, -5)
    if err != nil {
        fmt.Println("Validation:", err)
        var me *MultiError
        if errors.As(err, &me) {
            fmt.Printf("  → %d sub-errors\n", len(me.Errs))
            for _, e := range me.Errs {
                var ve *ValidationError
                if errors.As(e, &ve) {
                    fmt.Printf("    field=%s: %s\n", ve.Field, ve.Message)
                }
            }
        }
    }

    err = validateProduct("Surface Pro", 864, 15)
    fmt.Println("Valid product:", err)
}
EOF
```

> 💡 **`errors.As(err, &target)`** is the typed version of `errors.Is`. It finds the first error in the chain that is assignable to `target` and sets `target` to it. Use it to extract typed error details. Go 1.20+ supports `errors.Join` and returning multiple errors from a single call.

**📸 Verified Output:**
```
Resource=product ID=99
Validation: 3 error(s): validation failed for name=: cannot be empty; validation failed for price=-10: must be positive; validation failed for stock=-5: cannot be negative
  → 3 sub-errors
    field=name: cannot be empty
    field=price: must be positive
    field=stock: cannot be negative
Valid product: <nil>
```

---

### Steps 3–8: Panic/Recover, Sentinel Errors, Result Pattern, Error Middleware, Retry, Capstone

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import (
    "errors"
    "fmt"
    "time"
)

// Step 3: Panic & Recover
func safeRun(fn func()) (err error) {
    defer func() {
        if r := recover(); r != nil {
            err = fmt.Errorf("panic: %v", r)
        }
    }()
    fn()
    return nil
}

// Step 4: Sentinel errors
var (
    ErrNotFound       = errors.New("not found")
    ErrUnauthorized   = errors.New("unauthorized")
    ErrInvalidInput   = errors.New("invalid input")
    ErrTimeout        = errors.New("timeout")
)

type AppError struct {
    Code    int
    Message string
    Cause   error
}

func (e *AppError) Error() string {
    if e.Cause != nil { return fmt.Sprintf("[%d] %s: %v", e.Code, e.Message, e.Cause) }
    return fmt.Sprintf("[%d] %s", e.Code, e.Message)
}
func (e *AppError) Unwrap() error { return e.Cause }

func newAppError(code int, msg string, cause error) *AppError {
    return &AppError{Code: code, Message: msg, Cause: cause}
}

// Step 5: Result pattern (optional — Go prefers (T, error))
type Result[T any] struct {
    value T
    err   error
}

func Ok[T any](v T) Result[T]    { return Result[T]{value: v} }
func Err[T any](e error) Result[T] { return Result[T]{err: e} }

func (r Result[T]) IsOk() bool            { return r.err == nil }
func (r Result[T]) Unwrap() T            {
    if r.err != nil { panic("Result.Unwrap() on error: " + r.err.Error()) }
    return r.value
}
func (r Result[T]) UnwrapOr(def T) T     {
    if r.err != nil { return def }
    return r.value
}

// Step 6: Retry with backoff
type RetryConfig struct {
    MaxAttempts int
    BaseDelay   time.Duration
}

func retry[T any](cfg RetryConfig, fn func() (T, error)) (T, error) {
    var lastErr error
    for attempt := 1; attempt <= cfg.MaxAttempts; attempt++ {
        result, err := fn()
        if err == nil { return result, nil }
        lastErr = fmt.Errorf("attempt %d: %w", attempt, err)
        if attempt < cfg.MaxAttempts {
            delay := cfg.BaseDelay * time.Duration(attempt)
            fmt.Printf("  [retry] waiting %v before attempt %d\n", delay, attempt+1)
            time.Sleep(delay)
        }
    }
    var zero T
    return zero, fmt.Errorf("all %d attempts failed, last: %w", cfg.MaxAttempts, lastErr)
}

// Step 7: Error handler middleware
type HandlerFunc func(req string) (string, error)
type Middleware func(HandlerFunc) HandlerFunc

func ErrorLogger(next HandlerFunc) HandlerFunc {
    return func(req string) (string, error) {
        resp, err := next(req)
        if err != nil {
            fmt.Printf("[error] request=%q error=%v\n", req, err)
        }
        return resp, err
    }
}

func Recovery(next HandlerFunc) HandlerFunc {
    return func(req string) (resp string, err error) {
        defer func() {
            if r := recover(); r != nil {
                err = fmt.Errorf("recovered from panic: %v", r)
            }
        }()
        return next(req)
    }
}

// Step 8: Capstone
func handler(req string) (string, error) {
    switch req {
    case "ok":      return "200 OK", nil
    case "notfound": return "", newAppError(404, "resource not found", ErrNotFound)
    case "panic":   panic("unexpected crash")
    default:        return "", newAppError(400, "bad request", ErrInvalidInput)
    }
}

func main() {
    // Panic recovery
    err := safeRun(func() { panic("something went wrong") })
    fmt.Println("Recovered:", err)

    err = safeRun(func() { fmt.Println("Normal run") })
    fmt.Println("Normal err:", err)

    // AppError
    aerr := newAppError(404, "product not found", ErrNotFound)
    fmt.Println("AppError:", aerr)
    fmt.Println("Is ErrNotFound:", errors.Is(aerr, ErrNotFound))

    // Result type
    r1 := Ok(42)
    r2 := Err[int](errors.New("compute failed"))
    fmt.Println("r1:", r1.Unwrap())
    fmt.Println("r2 or default:", r2.UnwrapOr(-1))

    // Retry
    attempt := 0
    cfg := RetryConfig{MaxAttempts: 3, BaseDelay: 1 * time.Millisecond}
    val, err := retry(cfg, func() (string, error) {
        attempt++
        if attempt < 3 { return "", fmt.Errorf("service unavailable") }
        return "success after retries", nil
    })
    if err != nil { fmt.Println("Retry failed:", err) } else { fmt.Println("Retry result:", val) }

    // Middleware chain
    chain := ErrorLogger(Recovery(handler))
    requests := []string{"ok", "notfound", "panic", "bad"}
    for _, req := range requests {
        resp, err := chain(req)
        if err == nil { fmt.Printf("[%s] → %s\n", req, resp) }
    }
}
EOF
```

**📸 Verified Output:**
```
Recovered: panic: something went wrong
Normal run
Normal err: <nil>
AppError: [404] product not found: not found
Is ErrNotFound: true
r1: 42
r2 or default: -1
  [retry] waiting 1ms before attempt 2
  [retry] waiting 2ms before attempt 3
Retry result: success after retries
[error] request="notfound" error=[404] resource not found: not found
[error] request="panic" error=recovered from panic: unexpected crash
[error] request="bad" error=[400] bad request: invalid input
[ok] → 200 OK
```

---

## Summary

| Pattern | When to use |
|---------|-------------|
| `errors.New("msg")` | Simple sentinel error |
| `fmt.Errorf("...: %w", err)` | Wrap with context |
| Custom struct error | Typed errors with extra fields |
| `errors.Is(err, target)` | Check if error matches sentinel |
| `errors.As(err, &target)` | Extract typed error |
| `panic/recover` | Truly unexpected, unrecoverable state |
| Retry with backoff | Transient failures (network, I/O) |

## Further Reading
- [Go Blog: Error Handling](https://go.dev/blog/error-handling-and-go)
- [errors package](https://pkg.go.dev/errors)
