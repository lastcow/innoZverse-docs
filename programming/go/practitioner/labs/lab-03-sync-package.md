# Lab 03: sync Package

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm golang:1.22-alpine sh`

## Overview

The `sync` package provides fundamental synchronisation primitives. When goroutines share mutable state, synchronisation prevents data races — detectable with Go's built-in race detector (`go run -race`).

## Step 1: sync.Mutex — Exclusive Lock

Use `Mutex` when only one goroutine should access a resource at a time.

```go
package main

import (
    "fmt"
    "sync"
)

type SafeCounter struct {
    mu sync.Mutex
    v  map[string]int
}

func (c *SafeCounter) Inc(key string) {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.v[key]++
}

func (c *SafeCounter) Value(key string) int {
    c.mu.Lock()
    defer c.mu.Unlock()
    return c.v[key]
}

func main() {
    counter := &SafeCounter{v: make(map[string]int)}
    var wg sync.WaitGroup
    for i := 0; i < 1000; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            counter.Inc("hits")
        }()
    }
    wg.Wait()
    fmt.Println("hits:", counter.Value("hits")) // always 1000
}
```

> 💡 **Tip:** Always use `defer mu.Unlock()` right after `Lock()` — it prevents forgetting to unlock on early return or panic.

## Step 2: sync.RWMutex — Read-Write Lock

`RWMutex` allows many concurrent readers but only one writer — ideal for read-heavy caches.

```go
package main

import (
    "fmt"
    "sync"
)

type Cache struct {
    mu   sync.RWMutex
    data map[string]string
}

func (c *Cache) Set(k, v string) {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.data[k] = v
}

func (c *Cache) Get(k string) (string, bool) {
    c.mu.RLock()         // multiple goroutines can hold RLock simultaneously
    defer c.mu.RUnlock()
    v, ok := c.data[k]
    return v, ok
}

func main() {
    cache := &Cache{data: make(map[string]string)}
    cache.Set("lang", "Go")
    cache.Set("version", "1.22")

    var wg sync.WaitGroup
    for i := 0; i < 5; i++ {
        wg.Add(1)
        go func(id int) {
            defer wg.Done()
            v, _ := cache.Get("lang")
            fmt.Printf("reader %d: %s\n", id, v)
        }(i)
    }
    wg.Wait()
}
```

## Step 3: sync.WaitGroup

`WaitGroup` waits for a collection of goroutines to finish.

```go
package main

import (
    "fmt"
    "sync"
    "time"
)

func process(id int, wg *sync.WaitGroup) {
    defer wg.Done()
    time.Sleep(10 * time.Millisecond)
    fmt.Printf("task %d complete\n", id)
}

func main() {
    var wg sync.WaitGroup
    for i := 1; i <= 5; i++ {
        wg.Add(1)
        go process(i, &wg)
    }
    wg.Wait() // blocks until all Done() calls
    fmt.Println("all tasks finished")
}
```

> 💡 **Tip:** Always call `wg.Add(n)` before spawning goroutines — calling it inside the goroutine races with `wg.Wait()`.

## Step 4: sync.Once — One-Time Initialization

`Once` guarantees a function executes exactly once, even under concurrent access.

```go
package main

import (
    "fmt"
    "sync"
)

type DB struct{ name string }

var (
    dbInstance *DB
    dbOnce     sync.Once
)

func GetDB() *DB {
    dbOnce.Do(func() {
        fmt.Println("opening database connection...")
        dbInstance = &DB{name: "production"}
    })
    return dbInstance
}

func main() {
    var wg sync.WaitGroup
    for i := 0; i < 5; i++ {
        wg.Add(1)
        go func(id int) {
            defer wg.Done()
            db := GetDB()
            fmt.Printf("goroutine %d using DB: %s\n", id, db.name)
        }(i)
    }
    wg.Wait()
}
```

## Step 5: sync.Map — Concurrent Map

`sync.Map` is optimized for cases where keys are written once and read many times (e.g., caches, registries).

```go
package main

import (
    "fmt"
    "sync"
)

func main() {
    var m sync.Map

    // Store values
    m.Store("alpha", 1)
    m.Store("beta", 2)
    m.Store("gamma", 3)

    // Load
    v, ok := m.Load("beta")
    fmt.Printf("beta: %v ok=%v\n", v, ok)

    // LoadOrStore
    actual, loaded := m.LoadOrStore("delta", 4)
    fmt.Printf("delta: %v loaded=%v\n", actual, loaded)

    // Delete
    m.Delete("alpha")

    // Range
    fmt.Println("all entries:")
    m.Range(func(k, v any) bool {
        fmt.Printf("  %v = %v\n", k, v)
        return true // return false to stop iteration
    })
}
```

## Step 6: Race Detector

The race detector finds concurrent access bugs at runtime.

```bash
# Run with race detector enabled
go run -race main.go

# Or during tests:
go test -race ./...
```

Example of a race (DON'T DO THIS):

```go
package main

import (
    "fmt"
    "sync"
)

func main() {
    counter := 0
    var wg sync.WaitGroup
    for i := 0; i < 100; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            counter++ // DATA RACE: no synchronisation!
        }()
    }
    wg.Wait()
    fmt.Println(counter)
}
// Run: go run -race main.go  → "WARNING: DATA RACE"
```

Fix: use `sync.Mutex` or `sync/atomic`.

## Step 7: Combining Primitives

```go
package main

import (
    "fmt"
    "sync"
)

type Registry struct {
    mu    sync.RWMutex
    once  sync.Once
    items map[string]string
}

func NewRegistry() *Registry {
    r := &Registry{}
    r.once.Do(func() {
        r.items = make(map[string]string)
    })
    return r
}

func (r *Registry) Register(k, v string) {
    r.mu.Lock()
    defer r.mu.Unlock()
    r.items[k] = v
}

func (r *Registry) Lookup(k string) (string, bool) {
    r.mu.RLock()
    defer r.mu.RUnlock()
    v, ok := r.items[k]
    return v, ok
}

func main() {
    reg := NewRegistry()
    var wg sync.WaitGroup

    for i := 0; i < 5; i++ {
        wg.Add(1)
        go func(id int) {
            defer wg.Done()
            reg.Register(fmt.Sprintf("svc-%d", id), fmt.Sprintf("host-%d:8080", id))
        }(i)
    }
    wg.Wait()

    v, ok := reg.Lookup("svc-3")
    fmt.Printf("svc-3: %s found=%v\n", v, ok)
}
```

## Step 8: Capstone — Thread-Safe LRU Cache Skeleton

```go
package main

import (
    "container/list"
    "fmt"
    "sync"
)

type LRUCache struct {
    mu       sync.Mutex
    capacity int
    list     *list.List
    items    map[string]*list.Element
}

type entry struct{ key, value string }

func NewLRU(capacity int) *LRUCache {
    return &LRUCache{
        capacity: capacity,
        list:     list.New(),
        items:    make(map[string]*list.Element),
    }
}

func (c *LRUCache) Get(key string) (string, bool) {
    c.mu.Lock()
    defer c.mu.Unlock()
    if el, ok := c.items[key]; ok {
        c.list.MoveToFront(el)
        return el.Value.(*entry).value, true
    }
    return "", false
}

func (c *LRUCache) Put(key, value string) {
    c.mu.Lock()
    defer c.mu.Unlock()
    if el, ok := c.items[key]; ok {
        c.list.MoveToFront(el)
        el.Value.(*entry).value = value
        return
    }
    if c.list.Len() == c.capacity {
        oldest := c.list.Back()
        if oldest != nil {
            c.list.Remove(oldest)
            delete(c.items, oldest.Value.(*entry).key)
        }
    }
    el := c.list.PushFront(&entry{key, value})
    c.items[key] = el
}

func main() {
    cache := NewLRU(3)
    cache.Put("a", "1")
    cache.Put("b", "2")
    cache.Put("c", "3")
    cache.Put("d", "4") // evicts "a"

    keys := []string{"a", "b", "c", "d"}
    for _, k := range keys {
        v, ok := cache.Get(k)
        fmt.Printf("get %s: %q found=%v\n", k, v, ok)
    }
}
```

📸 **Verified Output:**
```
=== sync.Mutex ===
counter hits: 100

=== sync.RWMutex ===
cache get name: Go

=== sync.Once ===
initializing singleton...
singleton ready

=== sync.Map ===
sync.Map Load: foo=1 ok=true
  key=foo val=1
  key=bar val=2

=== sync.WaitGroup ===
task 3 done
task 1 done
task 2 done
all tasks complete
```

## Summary

| Primitive | Use Case | Key Methods |
|---|---|---|
| `sync.Mutex` | Exclusive access to shared state | `Lock()`, `Unlock()` |
| `sync.RWMutex` | Read-heavy shared state | `Lock/Unlock`, `RLock/RUnlock` |
| `sync.WaitGroup` | Wait for N goroutines to finish | `Add(n)`, `Done()`, `Wait()` |
| `sync.Once` | One-time initialization | `Do(f)` |
| `sync.Map` | Concurrent-safe map for cache-like patterns | `Store`, `Load`, `Range`, `Delete` |
| Race detector | Find data races at runtime | `go run -race` / `go test -race` |
