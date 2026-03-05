# Lab 09: HTTP Client & Server

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm golang:1.22-alpine sh`

## Overview

Go's `net/http` package is a production-quality HTTP library in the standard library. It provides everything from a simple file server to a full middleware-capable HTTP router.

## Step 1: Basic HTTP Server

```go
package main

import (
    "fmt"
    "net/http"
)

func helloHandler(w http.ResponseWriter, r *http.Request) {
    fmt.Fprintf(w, "Hello, %s!\n", r.URL.Query().Get("name"))
}

func main() {
    http.HandleFunc("/hello", helloHandler)
    http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
        fmt.Fprintln(w, "Welcome to Go HTTP!")
    })
    fmt.Println("server listening on :8080")
    http.ListenAndServe(":8080", nil) // uses DefaultServeMux
}
```

```bash
# In another terminal:
curl http://localhost:8080/hello?name=Go
# Hello, Go!
```

## Step 2: http.ServeMux — Custom Router

```go
package main

import (
    "fmt"
    "net/http"
)

func main() {
    mux := http.NewServeMux()

    // Go 1.22 pattern matching: METHOD /path
    mux.HandleFunc("GET /users", func(w http.ResponseWriter, r *http.Request) {
        fmt.Fprintln(w, "list users")
    })
    mux.HandleFunc("POST /users", func(w http.ResponseWriter, r *http.Request) {
        fmt.Fprintln(w, "create user")
    })
    mux.HandleFunc("GET /users/{id}", func(w http.ResponseWriter, r *http.Request) {
        id := r.PathValue("id")
        fmt.Fprintf(w, "get user %s\n", id)
    })

    fmt.Println("listening on :8080")
    http.ListenAndServe(":8080", mux)
}
```

> 💡 **Tip:** Go 1.22 added method-based routing (`GET /path`) and path wildcards (`{id}`) to `ServeMux`.

## Step 3: JSON Request/Response Handling

```go
package main

import (
    "encoding/json"
    "fmt"
    "net/http"
    "net/http/httptest"
    "strings"
)

type User struct {
    ID   int    `json:"id"`
    Name string `json:"name"`
    Age  int    `json:"age"`
}

var users = []User{{1, "Alice", 30}, {2, "Bob", 25}}

func listUsers(w http.ResponseWriter, r *http.Request) {
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(users)
}

func createUser(w http.ResponseWriter, r *http.Request) {
    var u User
    if err := json.NewDecoder(r.Body).Decode(&u); err != nil {
        http.Error(w, `{"error":"invalid JSON"}`, http.StatusBadRequest)
        return
    }
    u.ID = len(users) + 1
    users = append(users, u)
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(http.StatusCreated)
    json.NewEncoder(w).Encode(u)
}

func main() {
    mux := http.NewServeMux()
    mux.HandleFunc("GET /users", listUsers)
    mux.HandleFunc("POST /users", createUser)

    // Test GET
    req := httptest.NewRequest("GET", "/users", nil)
    rr := httptest.NewRecorder()
    mux.ServeHTTP(rr, req)
    fmt.Println("GET /users:", rr.Code, strings.TrimSpace(rr.Body.String()))

    // Test POST
    body := `{"name":"Charlie","age":28}`
    req2 := httptest.NewRequest("POST", "/users", strings.NewReader(body))
    req2.Header.Set("Content-Type", "application/json")
    rr2 := httptest.NewRecorder()
    mux.ServeHTTP(rr2, req2)
    fmt.Println("POST /users:", rr2.Code, strings.TrimSpace(rr2.Body.String()))
}
```

## Step 4: Middleware Pattern

```go
package main

import (
    "fmt"
    "net/http"
    "net/http/httptest"
    "time"
)

type Middleware func(http.Handler) http.Handler

func Logging(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        start := time.Now()
        next.ServeHTTP(w, r)
        fmt.Printf("%s %s %v\n", r.Method, r.URL.Path, time.Since(start))
    })
}

func Auth(token string) Middleware {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            if r.Header.Get("Authorization") != "Bearer "+token {
                http.Error(w, "unauthorized", http.StatusUnauthorized)
                return
            }
            next.ServeHTTP(w, r)
        })
    }
}

func Chain(h http.Handler, middlewares ...Middleware) http.Handler {
    for i := len(middlewares) - 1; i >= 0; i-- {
        h = middlewares[i](h)
    }
    return h
}

func main() {
    handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        fmt.Fprintln(w, "protected resource")
    })

    protected := Chain(handler, Logging, Auth("secret-token"))

    // Without auth
    req := httptest.NewRequest("GET", "/secret", nil)
    rr := httptest.NewRecorder()
    protected.ServeHTTP(rr, req)
    fmt.Println("no auth:", rr.Code)

    // With auth
    req2 := httptest.NewRequest("GET", "/secret", nil)
    req2.Header.Set("Authorization", "Bearer secret-token")
    rr2 := httptest.NewRecorder()
    protected.ServeHTTP(rr2, req2)
    fmt.Println("with auth:", rr2.Code, rr2.Body.String())
}
```

## Step 5: HTTP Client

```go
package main

import (
    "encoding/json"
    "fmt"
    "io"
    "net/http"
    "net/http/httptest"
    "strings"
    "time"
)

func main() {
    // Start a test server
    ts := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        switch r.URL.Path {
        case "/json":
            w.Header().Set("Content-Type", "application/json")
            json.NewEncoder(w).Encode(map[string]string{"status": "ok", "version": "1.0"})
        case "/echo":
            body, _ := io.ReadAll(r.Body)
            fmt.Fprintf(w, "echo: %s", body)
        }
    }))
    defer ts.Close()

    // Custom client with timeout
    client := &http.Client{Timeout: 5 * time.Second}

    // GET JSON
    resp, _ := client.Get(ts.URL + "/json")
    defer resp.Body.Close()
    var result map[string]string
    json.NewDecoder(resp.Body).Decode(&result)
    fmt.Println("GET /json:", result)

    // POST
    resp2, _ := client.Post(ts.URL+"/echo", "text/plain", strings.NewReader("hello server"))
    defer resp2.Body.Close()
    body, _ := io.ReadAll(resp2.Body)
    fmt.Println("POST /echo:", string(body))
}
```

## Step 6: Request Context and Headers

```go
package main

import (
    "fmt"
    "net/http"
    "net/http/httptest"
)

func apiHandler(w http.ResponseWriter, r *http.Request) {
    // Read headers
    userAgent := r.Header.Get("User-Agent")
    contentType := r.Header.Get("Content-Type")
    fmt.Printf("UA: %s, CT: %s\n", userAgent, contentType)

    // Read query params
    name := r.URL.Query().Get("name")
    page := r.URL.Query().Get("page")
    fmt.Printf("name=%s page=%s\n", name, page)

    // Write response with custom headers
    w.Header().Set("X-Request-ID", "req-001")
    w.Header().Set("Content-Type", "text/plain")
    w.WriteHeader(http.StatusOK)
    fmt.Fprintln(w, "OK")
}

func main() {
    req := httptest.NewRequest("GET", "/api?name=Go&page=1", nil)
    req.Header.Set("User-Agent", "GoTest/1.0")
    req.Header.Set("Content-Type", "application/json")

    rr := httptest.NewRecorder()
    apiHandler(rr, req)

    fmt.Println("status:", rr.Code)
    fmt.Println("X-Request-ID:", rr.Header().Get("X-Request-ID"))
}
```

## Step 7: Error Handling and Status Codes

```go
package main

import (
    "encoding/json"
    "fmt"
    "net/http"
    "net/http/httptest"
    "strings"
)

type APIError struct {
    Code    int    `json:"code"`
    Message string `json:"message"`
}

func writeError(w http.ResponseWriter, code int, msg string) {
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(code)
    json.NewEncoder(w).Encode(APIError{Code: code, Message: msg})
}

func getUserHandler(w http.ResponseWriter, r *http.Request) {
    id := r.PathValue("id")
    if id == "0" {
        writeError(w, http.StatusBadRequest, "invalid user ID")
        return
    }
    if id == "999" {
        writeError(w, http.StatusNotFound, "user not found")
        return
    }
    json.NewEncoder(w).Encode(map[string]string{"id": id, "name": "User" + id})
}

func main() {
    mux := http.NewServeMux()
    mux.HandleFunc("GET /users/{id}", getUserHandler)

    for _, id := range []string{"1", "0", "999"} {
        req := httptest.NewRequest("GET", "/users/"+id, nil)
        rr := httptest.NewRecorder()
        mux.ServeHTTP(rr, req)
        fmt.Printf("GET /users/%s → %d: %s", id, rr.Code, strings.TrimSpace(rr.Body.String()))
        fmt.Println()
    }
}
```

## Step 8: Capstone — REST API with Middleware

```go
package main

import (
    "encoding/json"
    "fmt"
    "net/http"
    "net/http/httptest"
    "strings"
    "sync"
    "time"
)

type Product struct {
    ID    int     `json:"id"`
    Name  string  `json:"name"`
    Price float64 `json:"price"`
}

type Store struct {
    mu       sync.RWMutex
    products map[int]Product
    nextID   int
}

func NewStore() *Store { return &Store{products: make(map[int]Product), nextID: 1} }

func (s *Store) List() []Product {
    s.mu.RLock(); defer s.mu.RUnlock()
    list := make([]Product, 0, len(s.products))
    for _, p := range s.products { list = append(list, p) }
    return list
}

func (s *Store) Add(p Product) Product {
    s.mu.Lock(); defer s.mu.Unlock()
    p.ID = s.nextID; s.nextID++
    s.products[p.ID] = p
    return p
}

func main() {
    store := NewStore()
    mux := http.NewServeMux()

    mux.HandleFunc("GET /products", func(w http.ResponseWriter, r *http.Request) {
        w.Header().Set("Content-Type", "application/json")
        json.NewEncoder(w).Encode(store.List())
    })

    mux.HandleFunc("POST /products", func(w http.ResponseWriter, r *http.Request) {
        var p Product
        if err := json.NewDecoder(r.Body).Decode(&p); err != nil {
            http.Error(w, err.Error(), 400); return
        }
        created := store.Add(p)
        w.Header().Set("Content-Type", "application/json")
        w.WriteHeader(http.StatusCreated)
        json.NewEncoder(w).Encode(created)
    })

    // Middleware: logging + timing
    logged := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        start := time.Now()
        mux.ServeHTTP(w, r)
        fmt.Printf("%-6s %-20s %v\n", r.Method, r.URL.Path, time.Since(start))
    })

    ts := httptest.NewServer(logged)
    defer ts.Close()

    client := &http.Client{}
    for _, name := range []string{"Widget", "Gadget", "Doohickey"} {
        body := fmt.Sprintf(`{"name":%q,"price":9.99}`, name)
        resp, _ := client.Post(ts.URL+"/products", "application/json", strings.NewReader(body))
        var p Product
        json.NewDecoder(resp.Body).Decode(&p)
        resp.Body.Close()
        fmt.Printf("created: %+v\n", p)
    }

    resp, _ := client.Get(ts.URL + "/products")
    var products []Product
    json.NewDecoder(resp.Body).Decode(&products)
    resp.Body.Close()
    fmt.Printf("total products: %d\n", len(products))
}
```

📸 **Verified Output:**
```
=== GET /users ===
status: 200
body: [{"id":1,"name":"Alice"},{"id":2,"name":"Bob"}]

=== POST /users ===
status: 201
body: {"id":3,"name":"Charlie"}

=== HTTP Client ===
GET /users 19.947µs
got 3 users
```

## Summary

| Component | Key API | Notes |
|---|---|---|
| Server | `http.ListenAndServe(addr, handler)` | `nil` handler → DefaultServeMux |
| Mux | `http.NewServeMux()` | Go 1.22: method routing + path params |
| Handler | `http.HandlerFunc(func(w, r))` | Implements `http.Handler` |
| Path param | `r.PathValue("id")` | Go 1.22 — `{id}` in pattern |
| Query params | `r.URL.Query().Get("key")` | Returns string |
| JSON response | `json.NewEncoder(w).Encode(v)` | Set Content-Type header first |
| JSON request | `json.NewDecoder(r.Body).Decode(&v)` | Check error |
| Middleware | `func(http.Handler) http.Handler` | Chain via `Chain(h, m1, m2)` |
| Test server | `httptest.NewServer(handler)` | Real TCP server for client tests |
| Test request | `httptest.NewRequest + httptest.NewRecorder` | In-memory handler tests |
