# Lab 04: Error Handling

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm golang:1.22-alpine sh`

## Overview

Go treats errors as values — they are returned from functions, not thrown. This makes error paths explicit and forces callers to handle them. The `errors` package and `fmt.Errorf` with `%w` provide a rich error wrapping and inspection system.

## Step 1: The error Interface

`error` is a built-in interface with a single method:

```go
type error interface {
    Error() string
}
```

```go
package main

import (
    "errors"
    "fmt"
)

func divide(a, b float64) (float64, error) {
    if b == 0 {
        return 0, errors.New("division by zero")
    }
    return a / b, nil
}

func main() {
    result, err := divide(10, 2)
    if err != nil {
        fmt.Println("error:", err)
        return
    }
    fmt.Printf("10 / 2 = %.1f\n", result)

    _, err = divide(5, 0)
    if err != nil {
        fmt.Println("error:", err)
    }
}
```

## Step 2: Custom Error Types

Implement the `error` interface to carry structured context.

```go
package main

import "fmt"

type HTTPError struct {
    Code    int
    Message string
    URL     string
}

func (e *HTTPError) Error() string {
    return fmt.Sprintf("HTTP %d: %s (url: %s)", e.Code, e.Message, e.URL)
}

func fetch(url string) error {
    if url == "" {
        return &HTTPError{Code: 400, Message: "bad request", URL: url}
    }
    if url == "http://gone.example.com" {
        return &HTTPError{Code: 410, Message: "gone", URL: url}
    }
    return nil
}

func main() {
    err := fetch("http://gone.example.com")
    if err != nil {
        fmt.Println(err)
    }
}
```

## Step 3: Sentinel Errors

Predefined error values for comparison with `errors.Is`.

```go
package main

import (
    "errors"
    "fmt"
)

var (
    ErrNotFound   = errors.New("not found")
    ErrPermission = errors.New("permission denied")
    ErrTimeout    = errors.New("operation timed out")
)

func getRecord(id int, admin bool) error {
    if id <= 0 {
        return ErrNotFound
    }
    if !admin {
        return ErrPermission
    }
    return nil
}

func main() {
    cases := []struct{ id int; admin bool }{
        {-1, false},
        {1, false},
        {1, true},
    }
    for _, c := range cases {
        err := getRecord(c.id, c.admin)
        switch {
        case errors.Is(err, ErrNotFound):
            fmt.Println("→ record does not exist")
        case errors.Is(err, ErrPermission):
            fmt.Println("→ access denied")
        case err == nil:
            fmt.Println("→ success")
        }
    }
}
```

## Step 4: Error Wrapping with %w

`fmt.Errorf` with `%w` wraps an error while preserving the original for `errors.Is`/`errors.As`.

```go
package main

import (
    "errors"
    "fmt"
)

var ErrNotFound = errors.New("not found")

func findUser(id int) error {
    if id <= 0 {
        return fmt.Errorf("findUser(%d): %w", id, ErrNotFound)
    }
    return nil
}

func loadProfile(id int) error {
    if err := findUser(id); err != nil {
        return fmt.Errorf("loadProfile: %w", err)
    }
    return nil
}

func main() {
    err := loadProfile(-5)
    fmt.Println("error:", err)
    fmt.Println("is ErrNotFound:", errors.Is(err, ErrNotFound))

    // Unwrap chain
    unwrapped := errors.Unwrap(err)
    fmt.Println("unwrapped:", unwrapped)
}
```

> 💡 **Tip:** Use `%w` when callers need to inspect the cause. Use `%v` when you want to hide the original error type.

## Step 5: errors.As — Type Assertion for Errors

`errors.As` traverses the error chain looking for a specific error type.

```go
package main

import (
    "errors"
    "fmt"
)

type ValidationError struct {
    Field   string
    Message string
}

func (e *ValidationError) Error() string {
    return fmt.Sprintf("validation: field %q %s", e.Field, e.Message)
}

func validateAge(age int) error {
    if age < 0 {
        return &ValidationError{Field: "age", Message: "must be non-negative"}
    }
    if age > 150 {
        return &ValidationError{Field: "age", Message: "must be <= 150"}
    }
    return nil
}

func createUser(name string, age int) error {
    if err := validateAge(age); err != nil {
        return fmt.Errorf("createUser: %w", err)
    }
    return nil
}

func main() {
    err := createUser("Alice", -5)
    if err != nil {
        fmt.Println("error:", err)

        var ve *ValidationError
        if errors.As(err, &ve) {
            fmt.Printf("validation failed: field=%s reason=%s\n", ve.Field, ve.Message)
        }
    }
}
```

## Step 6: panic and recover

`panic` stops normal execution. `recover` — called inside a `defer` — catches it.

```go
package main

import "fmt"

func safeDivide(a, b int) (result int, err error) {
    defer func() {
        if r := recover(); r != nil {
            err = fmt.Errorf("recovered from panic: %v", r)
        }
    }()
    return a / b, nil
}

func mustPositive(n int) int {
    if n <= 0 {
        panic(fmt.Sprintf("expected positive, got %d", n))
    }
    return n
}

func safePositive(n int) (result int, err error) {
    defer func() {
        if r := recover(); r != nil {
            err = fmt.Errorf("%v", r)
        }
    }()
    return mustPositive(n), nil
}

func main() {
    r, err := safeDivide(10, 2)
    fmt.Printf("10/2 = %d, err=%v\n", r, err)

    r, err = safeDivide(10, 0)
    fmt.Printf("10/0 = %d, err=%v\n", r, err)

    r, err = safePositive(-3)
    fmt.Printf("positive(-3) = %d, err=%v\n", r, err)
}
```

> 💡 **Tip:** Use `panic` only for truly unrecoverable situations (programmer errors). For expected failures, return `error`.

## Step 7: Multiple Error Returns & Error Aggregation

```go
package main

import (
    "errors"
    "fmt"
    "strings"
)

type MultiError struct {
    errs []error
}

func (m *MultiError) Add(err error) {
    if err != nil {
        m.errs = append(m.errs, err)
    }
}

func (m *MultiError) Error() string {
    msgs := make([]string, len(m.errs))
    for i, e := range m.errs {
        msgs[i] = e.Error()
    }
    return strings.Join(msgs, "; ")
}

func (m *MultiError) ToError() error {
    if len(m.errs) == 0 {
        return nil
    }
    return m
}

func validateForm(name, email string, age int) error {
    var me MultiError
    if name == "" {
        me.Add(errors.New("name is required"))
    }
    if !strings.Contains(email, "@") {
        me.Add(fmt.Errorf("invalid email: %q", email))
    }
    if age < 18 {
        me.Add(fmt.Errorf("age %d is below minimum (18)", age))
    }
    return me.ToError()
}

func main() {
    err := validateForm("", "notanemail", 16)
    if err != nil {
        fmt.Println("validation errors:", err)
    }
    err = validateForm("Alice", "alice@example.com", 25)
    fmt.Println("valid form:", err)
}
```

## Step 8: Capstone — Layered Error Handling

```go
package main

import (
    "errors"
    "fmt"
)

// Domain errors
var (
    ErrNotFound   = errors.New("not found")
    ErrPermission = errors.New("permission denied")
)

// Repository layer
type UserRepo struct{}

func (r *UserRepo) FindByID(id int) (string, error) {
    users := map[int]string{1: "Alice", 2: "Bob"}
    u, ok := users[id]
    if !ok {
        return "", fmt.Errorf("UserRepo.FindByID(%d): %w", id, ErrNotFound)
    }
    return u, nil
}

// Service layer
type UserService struct{ repo *UserRepo }

func (s *UserService) GetUser(requesterID, targetID int) (string, error) {
    if requesterID != 1 { // only admin (id=1)
        return "", fmt.Errorf("GetUser: %w", ErrPermission)
    }
    name, err := s.repo.FindByID(targetID)
    if err != nil {
        return "", fmt.Errorf("GetUser: %w", err)
    }
    return name, nil
}

// Handler layer
func handleRequest(svc *UserService, requesterID, targetID int) {
    name, err := svc.GetUser(requesterID, targetID)
    switch {
    case err == nil:
        fmt.Printf("user found: %s\n", name)
    case errors.Is(err, ErrNotFound):
        fmt.Println("404: user not found")
    case errors.Is(err, ErrPermission):
        fmt.Println("403: forbidden")
    default:
        fmt.Println("500: internal error:", err)
    }
}

func main() {
    svc := &UserService{repo: &UserRepo{}}
    handleRequest(svc, 1, 1)   // admin gets user 1
    handleRequest(svc, 1, 99)  // admin gets missing user
    handleRequest(svc, 2, 1)   // non-admin → permission denied
}
```

📸 **Verified Output:**
```
=== Sentinel Errors ===
error: getProfile: findUser(-1): not found
is ErrNotFound: true

=== Custom Error Type ===
caught ValidationError: field=email

=== panic/recover ===
10/2 = 5 err=<nil>
10/0 = 0 err=recovered from panic: runtime error: integer divide by zero
```

## Summary

| Concept | API | When to Use |
|---|---|---|
| `errors.New` | Create simple error | Static error messages |
| `fmt.Errorf("%w")` | Wrap error with context | Add call-site info |
| `errors.Is` | Check error identity in chain | Sentinel error comparison |
| `errors.As` | Extract typed error from chain | Inspect structured error fields |
| `errors.Unwrap` | Get next error in chain | Manual chain traversal |
| `panic/recover` | Catch unrecoverable situations | Libraries preventing crashes |
| Sentinel errors | Package-level `var Err... = errors.New(...)` | Stable, comparable error values |
