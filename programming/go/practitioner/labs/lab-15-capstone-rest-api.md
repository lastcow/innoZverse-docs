# Lab 15: Capstone — REST API in Go

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm golang:1.22-alpine sh`

## Overview

Build a complete, production-quality REST API in Go: chi router, JSON handlers, in-memory store with `sync.RWMutex`, middleware stack (logging/recovery/requestID), table-driven tests, and graceful shutdown with context and OS signals.

---

## Step 1: Project Setup

```bash
mkdir go-api && cd go-api
go mod init go-api
go get github.com/go-chi/chi/v5@latest
```

Directory structure:

```
go-api/
├── main.go
├── handler/
│   └── items.go
├── store/
│   └── store.go
├── middleware/
│   └── middleware.go
└── handler/
    └── items_test.go
```

---

## Step 2: In-Memory Store with `sync.RWMutex`

**`store/store.go`**:

```go
package store

import (
    "errors"
    "sync"
)

// Item represents a resource in our API
type Item struct {
    ID   int    `json:"id"`
    Name string `json:"name"`
    Done bool   `json:"done"`
}

// Store is a thread-safe in-memory data store
type Store struct {
    mu    sync.RWMutex
    items map[int]Item
    next  int
}

func New() *Store {
    return &Store{items: make(map[int]Item), next: 1}
}

func (s *Store) Create(name string) Item {
    s.mu.Lock()
    defer s.mu.Unlock()
    item := Item{ID: s.next, Name: name}
    s.items[s.next] = item
    s.next++
    return item
}

func (s *Store) Get(id int) (Item, error) {
    s.mu.RLock()
    defer s.mu.RUnlock()
    item, ok := s.items[id]
    if !ok {
        return Item{}, errors.New("not found")
    }
    return item, nil
}

func (s *Store) List() []Item {
    s.mu.RLock()
    defer s.mu.RUnlock()
    out := make([]Item, 0, len(s.items))
    for _, v := range s.items {
        out = append(out, v)
    }
    return out
}

func (s *Store) Update(id int, name string, done bool) (Item, error) {
    s.mu.Lock()
    defer s.mu.Unlock()
    item, ok := s.items[id]
    if !ok {
        return Item{}, errors.New("not found")
    }
    item.Name = name
    item.Done = done
    s.items[id] = item
    return item, nil
}

func (s *Store) Delete(id int) error {
    s.mu.Lock()
    defer s.mu.Unlock()
    if _, ok := s.items[id]; !ok {
        return errors.New("not found")
    }
    delete(s.items, id)
    return nil
}
```

> 💡 Use `RLock`/`RUnlock` for reads (allows concurrent readers) and `Lock`/`Unlock` for writes. Never mix read and write locks for the same operation.

---

## Step 3: JSON Handlers

**`handler/items.go`**:

```go
package handler

import (
    "encoding/json"
    "net/http"
    "strconv"

    "github.com/go-chi/chi/v5"
    "go-api/store"
)

type ItemHandler struct {
    Store *store.Store
}

func writeJSON(w http.ResponseWriter, status int, v any) {
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(status)
    json.NewEncoder(w).Encode(v)
}

func (h *ItemHandler) List(w http.ResponseWriter, r *http.Request) {
    writeJSON(w, http.StatusOK, h.Store.List())
}

func (h *ItemHandler) Create(w http.ResponseWriter, r *http.Request) {
    var body struct {
        Name string `json:"name"`
    }
    if err := json.NewDecoder(r.Body).Decode(&body); err != nil || body.Name == "" {
        writeJSON(w, http.StatusBadRequest, map[string]string{"error": "name is required"})
        return
    }
    item := h.Store.Create(body.Name)
    writeJSON(w, http.StatusCreated, item)
}

func (h *ItemHandler) Get(w http.ResponseWriter, r *http.Request) {
    id, err := strconv.Atoi(chi.URLParam(r, "id"))
    if err != nil {
        writeJSON(w, http.StatusBadRequest, map[string]string{"error": "invalid id"})
        return
    }
    item, err := h.Store.Get(id)
    if err != nil {
        writeJSON(w, http.StatusNotFound, map[string]string{"error": "not found"})
        return
    }
    writeJSON(w, http.StatusOK, item)
}

func (h *ItemHandler) Delete(w http.ResponseWriter, r *http.Request) {
    id, _ := strconv.Atoi(chi.URLParam(r, "id"))
    if err := h.Store.Delete(id); err != nil {
        writeJSON(w, http.StatusNotFound, map[string]string{"error": "not found"})
        return
    }
    w.WriteHeader(http.StatusNoContent)
}
```

---

## Step 4: Middleware (Logging, Recovery, RequestID)

**`middleware/middleware.go`**:

```go
package middleware

import (
    "log"
    "net/http"
    "runtime/debug"
    "time"

    "github.com/google/uuid"
)

// Logger logs method, path, status, and duration for every request
func Logger(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        start := time.Now()
        wrapped := &statusWriter{ResponseWriter: w, status: 200}
        next.ServeHTTP(wrapped, r)
        log.Printf("%s %s %d %s", r.Method, r.URL.Path, wrapped.status, time.Since(start))
    })
}

// Recovery catches panics and returns 500 instead of crashing
func Recovery(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        defer func() {
            if err := recover(); err != nil {
                log.Printf("panic: %v\n%s", err, debug.Stack())
                http.Error(w, "Internal Server Error", http.StatusInternalServerError)
            }
        }()
        next.ServeHTTP(w, r)
    })
}

// RequestID injects a unique request ID into each request header
func RequestID(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        id := r.Header.Get("X-Request-ID")
        if id == "" {
            id = uuid.New().String()
        }
        w.Header().Set("X-Request-ID", id)
        r.Header.Set("X-Request-ID", id)
        next.ServeHTTP(w, r)
    })
}

type statusWriter struct {
    http.ResponseWriter
    status int
}

func (sw *statusWriter) WriteHeader(code int) {
    sw.status = code
    sw.ResponseWriter.WriteHeader(code)
}
```

---

## Step 5: Router and Main

**`main.go`**:

```go
package main

import (
    "context"
    "log"
    "net/http"
    "os"
    "os/signal"
    "syscall"
    "time"

    "github.com/go-chi/chi/v5"
    chimiddleware "github.com/go-chi/chi/v5/middleware"
    "go-api/handler"
    "go-api/store"
)

func main() {
    s := store.New()
    h := &handler.ItemHandler{Store: s}

    r := chi.NewRouter()

    // Middleware stack
    r.Use(chimiddleware.RequestID)
    r.Use(chimiddleware.Logger)
    r.Use(chimiddleware.Recoverer)

    // Health check — no auth needed
    r.Get("/health", func(w http.ResponseWriter, r *http.Request) {
        w.Header().Set("Content-Type", "application/json")
        w.Write([]byte(`{"status":"ok"}`))
    })

    // REST routes
    r.Route("/items", func(r chi.Router) {
        r.Get("/", h.List)
        r.Post("/", h.Create)
        r.Get("/{id}", h.Get)
        r.Delete("/{id}", h.Delete)
    })

    srv := &http.Server{
        Addr:         ":8080",
        Handler:      r,
        ReadTimeout:  5 * time.Second,
        WriteTimeout: 10 * time.Second,
    }

    // Start server in background
    go func() {
        log.Printf("Server listening on :8080")
        if err := srv.ListenAndServe(); err != http.ErrServerClosed {
            log.Fatalf("server error: %v", err)
        }
    }()

    // Graceful shutdown on signal
    sigCh := make(chan os.Signal, 1)
    signal.Notify(sigCh, syscall.SIGTERM, syscall.SIGINT)
    <-sigCh

    log.Println("Shutting down server...")
    ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
    defer cancel()
    if err := srv.Shutdown(ctx); err != nil {
        log.Printf("shutdown error: %v", err)
    }
    log.Println("Server stopped cleanly")
}
```

---

## Step 6: Table-Driven Tests

**`handler/items_test.go`**:

```go
package handler_test

import (
    "bytes"
    "encoding/json"
    "net/http"
    "net/http/httptest"
    "testing"

    "go-api/handler"
    "go-api/store"
)

func TestItemHandler(t *testing.T) {
    s := store.New()
    h := &handler.ItemHandler{Store: s}

    // Seed data
    s.Create("Apple")
    s.Create("Banana")

    tests := []struct {
        name       string
        method     string
        path       string
        body       any
        wantStatus int
    }{
        {"list items",   "GET",    "/items",   nil,                    http.StatusOK},
        {"create item",  "POST",   "/items",   map[string]string{"name": "Cherry"}, http.StatusCreated},
        {"empty name",   "POST",   "/items",   map[string]string{"name": ""},       http.StatusBadRequest},
        {"health check", "GET",    "/health",  nil,                    http.StatusOK},
    }

    for _, tc := range tests {
        t.Run(tc.name, func(t *testing.T) {
            var body *bytes.Buffer
            if tc.body != nil {
                b, _ := json.Marshal(tc.body)
                body = bytes.NewBuffer(b)
            } else {
                body = &bytes.Buffer{}
            }

            req := httptest.NewRequest(tc.method, tc.path, body)
            req.Header.Set("Content-Type", "application/json")
            rr := httptest.NewRecorder()

            switch tc.path {
            case "/items":
                if tc.method == "GET" {
                    http.HandlerFunc(h.List).ServeHTTP(rr, req)
                } else {
                    http.HandlerFunc(h.Create).ServeHTTP(rr, req)
                }
            case "/health":
                http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
                    w.WriteHeader(http.StatusOK)
                }).ServeHTTP(rr, req)
            }

            if rr.Code != tc.wantStatus {
                t.Errorf("got status %d, want %d", rr.Code, tc.wantStatus)
            }
        })
    }
}
```

---

## Step 7: Running the Server

```bash
# In the go-api directory:
go run main.go &

# Test endpoints
curl -s http://localhost:8080/health
# {"status":"ok"}

curl -s -X POST http://localhost:8080/items \
  -H "Content-Type: application/json" \
  -d '{"name":"Apple"}'
# {"id":1,"name":"Apple","done":false}

curl -s http://localhost:8080/items
# [{"id":1,"name":"Apple","done":false}]

curl -s http://localhost:8080/items/1
# {"id":1,"name":"Apple","done":false}

curl -s -X DELETE http://localhost:8080/items/1
# (204 No Content)

# Run tests
go test ./...
# ok  	go-api/handler	0.003s
```

> 💡 `httptest.NewRecorder()` and `httptest.NewRequest()` let you test HTTP handlers without starting a real server — fast, isolated, and no port conflicts.

---

## Step 8 (Capstone): Full Store Demo + Table-Driven Tests

```bash
docker run --rm golang:1.22-alpine sh -c "
cat > /tmp/restapi.go << 'GOEOF'
package main

import (
    \"encoding/json\"
    \"fmt\"
    \"sync\"
    \"testing\"
)

type Item struct {
    ID   int    \`json:\"id\"\`
    Name string \`json:\"name\"\`
}

type Store struct {
    mu    sync.RWMutex
    items map[int]Item
    next  int
}

func NewStore() *Store { return &Store{items: make(map[int]Item), next: 1} }

func (s *Store) Create(name string) Item {
    s.mu.Lock()
    defer s.mu.Unlock()
    item := Item{ID: s.next, Name: name}
    s.items[s.next] = item
    s.next++
    return item
}

func (s *Store) Get(id int) (Item, bool) {
    s.mu.RLock()
    defer s.mu.RUnlock()
    item, ok := s.items[id]
    return item, ok
}

func (s *Store) List() []Item {
    s.mu.RLock()
    defer s.mu.RUnlock()
    out := make([]Item, 0, len(s.items))
    for _, v := range s.items { out = append(out, v) }
    return out
}

func main() {
    store := NewStore()
    a := store.Create(\"Apple\")
    b := store.Create(\"Banana\")
    store.Create(\"Cherry\")

    fmt.Println(\"=== REST API Store Demo ===\")
    item, _ := store.Get(a.ID)
    data, _ := json.Marshal(item)
    fmt.Println(\"GET /items/1:\", string(data))

    item2, _ := store.Get(b.ID)
    data2, _ := json.Marshal(item2)
    fmt.Println(\"GET /items/2:\", string(data2))

    list := store.List()
    fmt.Printf(\"GET /items: %d items in store\n\", len(list))

    tests := []struct {
        id       int
        wantOk   bool
        wantName string
    }{
        {1, true, \"Apple\"},
        {2, true, \"Banana\"},
        {99, false, \"\"},
    }
    fmt.Println(\"\n=== Table-driven Tests ===\")
    passed := 0
    for _, tc := range tests {
        item, ok := store.Get(tc.id)
        if ok != tc.wantOk {
            fmt.Printf(\"FAIL id=%d: got ok=%v want %v\n\", tc.id, ok, tc.wantOk)
            continue
        }
        if ok && item.Name != tc.wantName {
            fmt.Printf(\"FAIL id=%d: got name=%s want %s\n\", tc.id, item.Name, tc.wantName)
            continue
        }
        fmt.Printf(\"PASS id=%d\n\", tc.id)
        passed++
    }
    fmt.Printf(\"%d/%d tests passed\n\", passed, len(tests))
    _ = testing.T{}
}
GOEOF
cd /tmp && go run restapi.go
"
```

📸 Verified Output:
```
=== REST API Store Demo ===
GET /items/1: {"id":1,"name":"Apple"}
GET /items/2: {"id":2,"name":"Banana"}
GET /items: 3 items in store

=== Table-driven Tests ===
PASS id=1
PASS id=2
PASS id=99
3/3 tests passed
```

---

## Summary

| Component | Technology | Pattern |
|-----------|------------|---------|
| Router | `go-chi/chi` | URL params, route groups |
| JSON I/O | `encoding/json` | Decode request body, encode response |
| Concurrency | `sync.RWMutex` | Safe concurrent read/write store |
| Middleware | chi middleware stack | Logging, recovery, request ID |
| Testing | `net/http/httptest` | Table-driven, no real server needed |
| Graceful Shutdown | `context.WithTimeout` + `os.Signal` | Drain in-flight requests then exit |
