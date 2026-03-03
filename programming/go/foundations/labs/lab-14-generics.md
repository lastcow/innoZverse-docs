# Lab 14: Generics (Go 1.18+)

## Objective
Write type-safe generic functions and data structures using Go's generics: type parameters, constraints, `comparable`, `any`, and the `constraints` package.

## Time
30 minutes

## Prerequisites
- Lab 03 (Slices & Maps), Lab 05 (Interfaces)

## Tools
- Docker image: `zchencow/innozverse-go:latest` (Go 1.22)

---

## Lab Instructions

### Step 1: Generic Functions

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import "fmt"

// Generic Min/Max — T must be ordered
type Ordered interface {
    ~int | ~int8 | ~int16 | ~int32 | ~int64 |
    ~uint | ~uint8 | ~uint16 | ~uint32 | ~uint64 |
    ~float32 | ~float64 | ~string
}

func Min[T Ordered](a, b T) T {
    if a < b { return a }
    return b
}

func Max[T Ordered](a, b T) T {
    if a > b { return a }
    return b
}

func Clamp[T Ordered](val, lo, hi T) T {
    return Max(lo, Min(val, hi))
}

// Generic slice functions
func Map[T, U any](slice []T, fn func(T) U) []U {
    result := make([]U, len(slice))
    for i, v := range slice { result[i] = fn(v) }
    return result
}

func Filter[T any](slice []T, pred func(T) bool) []T {
    result := make([]T, 0)
    for _, v := range slice {
        if pred(v) { result = append(result, v) }
    }
    return result
}

func Reduce[T, U any](slice []T, initial U, fn func(U, T) U) U {
    acc := initial
    for _, v := range slice { acc = fn(acc, v) }
    return acc
}

func Contains[T comparable](slice []T, val T) bool {
    for _, v := range slice {
        if v == val { return true }
    }
    return false
}

func Keys[K comparable, V any](m map[K]V) []K {
    keys := make([]K, 0, len(m))
    for k := range m { keys = append(keys, k) }
    return keys
}

func Values[K comparable, V any](m map[K]V) []V {
    vals := make([]V, 0, len(m))
    for _, v := range m { vals = append(vals, v) }
    return vals
}

func main() {
    fmt.Println("Min(3,5):", Min(3, 5))
    fmt.Println("Min(a,b):", Min("apple", "banana"))
    fmt.Println("Max(3.14,2.71):", Max(3.14, 2.71))
    fmt.Println("Clamp(15,0,10):", Clamp(15, 0, 10))
    fmt.Println("Clamp(-5,0,10):", Clamp(-5, 0, 10))
    fmt.Println("Clamp(7,0,10):", Clamp(7, 0, 10))

    nums := []int{1, 2, 3, 4, 5, 6, 7, 8, 9, 10}
    doubled := Map(nums, func(n int) int { return n * 2 })
    evens   := Filter(nums, func(n int) bool { return n%2 == 0 })
    sum     := Reduce(nums, 0, func(acc, n int) int { return acc + n })
    strs    := Map(nums, func(n int) string { return fmt.Sprintf("#%d", n) })

    fmt.Println("Doubled:", doubled)
    fmt.Println("Evens:", evens)
    fmt.Println("Sum:", sum)
    fmt.Println("Strings:", strs[:3], "...")
    fmt.Println("Contains 7:", Contains(nums, 7))
    fmt.Println("Contains 11:", Contains(nums, 11))
}
EOF
```

> 💡 **`~int`** in a constraint means "any type whose underlying type is int" — this includes custom types like `type UserID int`. Without `~`, `type UserID int` would NOT satisfy `int`. The tilde prefix enables user-defined types to satisfy constraints based on their underlying types.

**📸 Verified Output:**
```
Min(3,5): 3
Min(a,b): apple
Max(3.14,2.71): 3.14
Clamp(15,0,10): 10
Clamp(-5,0,10): 0
Clamp(7,0,10): 7
Doubled: [2 4 6 8 10 12 14 16 18 20]
Evens: [2 4 6 8 10]
Sum: 55
Strings: [#1 #2 #3] ...
Contains 7: true
Contains 11: false
```

---

### Step 2: Generic Data Structures

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import (
    "fmt"
    "sync"
)

// Generic Stack
type Stack[T any] struct {
    items []T
}

func (s *Stack[T]) Push(v T)        { s.items = append(s.items, v) }
func (s *Stack[T]) Pop() (T, bool) {
    if len(s.items) == 0 { var zero T; return zero, false }
    top := s.items[len(s.items)-1]
    s.items = s.items[:len(s.items)-1]
    return top, true
}
func (s *Stack[T]) Peek() (T, bool) {
    if len(s.items) == 0 { var zero T; return zero, false }
    return s.items[len(s.items)-1], true
}
func (s *Stack[T]) Len() int { return len(s.items) }

// Generic Queue
type Queue[T any] struct {
    items []T
}

func (q *Queue[T]) Enqueue(v T)      { q.items = append(q.items, v) }
func (q *Queue[T]) Dequeue() (T, bool) {
    if len(q.items) == 0 { var zero T; return zero, false }
    v := q.items[0]
    q.items = q.items[1:]
    return v, true
}
func (q *Queue[T]) Len() int { return len(q.items) }

// Generic concurrent map
type SyncMap[K comparable, V any] struct {
    mu sync.RWMutex
    m  map[K]V
}

func NewSyncMap[K comparable, V any]() *SyncMap[K, V] {
    return &SyncMap[K, V]{m: make(map[K]V)}
}

func (m *SyncMap[K, V]) Set(k K, v V) {
    m.mu.Lock(); defer m.mu.Unlock()
    m.m[k] = v
}

func (m *SyncMap[K, V]) Get(k K) (V, bool) {
    m.mu.RLock(); defer m.mu.RUnlock()
    v, ok := m.m[k]
    return v, ok
}

func (m *SyncMap[K, V]) Delete(k K) {
    m.mu.Lock(); defer m.mu.Unlock()
    delete(m.m, k)
}

func (m *SyncMap[K, V]) Len() int {
    m.mu.RLock(); defer m.mu.RUnlock()
    return len(m.m)
}

// Generic Result type
type Result[T any] struct {
    value T
    err   error
}

func Ok[T any](v T) Result[T]     { return Result[T]{value: v} }
func Err[T any](e error) Result[T] { return Result[T]{err: e} }

func (r Result[T]) IsOk() bool          { return r.err == nil }
func (r Result[T]) Unwrap() T          {
    if r.err != nil { panic(r.err) }
    return r.value
}
func (r Result[T]) UnwrapOr(def T) T   {
    if r.err != nil { return def }
    return r.value
}
func (r Result[T]) Map(fn func(T) T) Result[T] {
    if r.err != nil { return r }
    return Ok(fn(r.value))
}

func main() {
    // Stack
    s := &Stack[string]{}
    s.Push("first"); s.Push("second"); s.Push("third")
    fmt.Printf("Stack len=%d\n", s.Len())
    for {
        v, ok := s.Pop()
        if !ok { break }
        fmt.Printf("  pop: %s\n", v)
    }

    // Queue
    q := &Queue[int]{}
    for _, n := range []int{10, 20, 30, 40} { q.Enqueue(n) }
    fmt.Printf("Queue len=%d\n", q.Len())
    for {
        v, ok := q.Dequeue()
        if !ok { break }
        fmt.Printf("  dequeue: %d\n", v)
    }

    // SyncMap
    sm := NewSyncMap[string, int]()
    sm.Set("a", 1); sm.Set("b", 2); sm.Set("c", 3)
    if v, ok := sm.Get("b"); ok { fmt.Println("SyncMap b:", v) }

    // Result
    r := Ok(42).Map(func(n int) int { return n * 2 })
    fmt.Println("Result:", r.Unwrap())

    r2 := Err[int](fmt.Errorf("oops"))
    fmt.Println("Error result:", r2.UnwrapOr(-1))
}
EOF
```

> 💡 **`[T any]` in struct definition** creates a generic type — `Stack[string]` and `Stack[int]` are separate types with their own methods. Go generics are *monomorphized* at compile time (like C++ templates), so there's no runtime overhead from type erasure (unlike Java generics).

**📸 Verified Output:**
```
Stack len=3
  pop: third
  pop: second
  pop: first
Queue len=4
  dequeue: 10
  dequeue: 20
  dequeue: 30
  dequeue: 40
SyncMap b: 2
Result: 84
Error result: -1
```

---

### Steps 3–8: Type constraints, Pipeline, Cache, Optional, Sets, Capstone

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import (
    "fmt"
    "sort"
    "sync"
    "time"
)

// Step 3: Number constraint
type Number interface {
    ~int | ~int32 | ~int64 | ~float32 | ~float64
}

func Sum[T Number](nums []T) T {
    var total T
    for _, n := range nums { total += n }
    return total
}

func Average[T Number](nums []T) float64 {
    if len(nums) == 0 { return 0 }
    return float64(Sum(nums)) / float64(len(nums))
}

func SortSlice[T interface{ ~int | ~float64 | ~string }](s []T) []T {
    result := append([]T{}, s...)
    sort.Slice(result, func(i, j int) bool {
        return fmt.Sprint(result[i]) < fmt.Sprint(result[j])
    })
    return result
}

// Step 4: Generic TTL cache
type CacheEntry[V any] struct {
    value   V
    expiresAt time.Time
}

type Cache[K comparable, V any] struct {
    mu      sync.Mutex
    entries map[K]CacheEntry[V]
    ttl     time.Duration
}

func NewCache[K comparable, V any](ttl time.Duration) *Cache[K, V] {
    return &Cache[K, V]{entries: make(map[K]CacheEntry[V]), ttl: ttl}
}

func (c *Cache[K, V]) Set(k K, v V) {
    c.mu.Lock(); defer c.mu.Unlock()
    c.entries[k] = CacheEntry[V]{v, time.Now().Add(c.ttl)}
}

func (c *Cache[K, V]) Get(k K) (V, bool) {
    c.mu.Lock(); defer c.mu.Unlock()
    e, ok := c.entries[k]
    if !ok || time.Now().After(e.expiresAt) {
        delete(c.entries, k)
        var zero V; return zero, false
    }
    return e.value, true
}

func (c *Cache[K, V]) Len() int {
    c.mu.Lock(); defer c.mu.Unlock()
    return len(c.entries)
}

// Step 5: Generic Set
type Set[T comparable] map[T]struct{}

func NewSet[T comparable](vals ...T) Set[T] {
    s := make(Set[T])
    for _, v := range vals { s[v] = struct{}{} }
    return s
}

func (s Set[T]) Add(v T)      { s[v] = struct{}{} }
func (s Set[T]) Has(v T) bool { _, ok := s[v]; return ok }
func (s Set[T]) Len() int     { return len(s) }

func (s Set[T]) Union(other Set[T]) Set[T] {
    result := NewSet[T]()
    for v := range s     { result.Add(v) }
    for v := range other { result.Add(v) }
    return result
}

func (s Set[T]) Intersect(other Set[T]) Set[T] {
    result := NewSet[T]()
    for v := range s { if other.Has(v) { result.Add(v) } }
    return result
}

func (s Set[T]) Difference(other Set[T]) Set[T] {
    result := NewSet[T]()
    for v := range s { if !other.Has(v) { result.Add(v) } }
    return result
}

// Step 6: Generic Optional
type Optional[T any] struct{ val *T }

func Some[T any](v T) Optional[T] { return Optional[T]{&v} }
func None[T any]() Optional[T]    { return Optional[T]{} }

func (o Optional[T]) IsPresent() bool { return o.val != nil }
func (o Optional[T]) Get() (T, bool) {
    if o.val == nil { var z T; return z, false }
    return *o.val, true
}
func (o Optional[T]) OrElse(def T) T {
    if o.val == nil { return def }
    return *o.val
}
func (o Optional[T]) Map(fn func(T) T) Optional[T] {
    if o.val == nil { return o }
    return Some(fn(*o.val))
}

// Step 7: Generic Pair & Grouping
type Pair[A, B any] struct{ First A; Second B }

func Zip[A, B any](as []A, bs []B) []Pair[A, B] {
    n := len(as)
    if len(bs) < n { n = len(bs) }
    result := make([]Pair[A, B], n)
    for i := range result { result[i] = Pair[A, B]{as[i], bs[i]} }
    return result
}

func GroupBy[T any, K comparable](slice []T, key func(T) K) map[K][]T {
    result := make(map[K][]T)
    for _, v := range slice { k := key(v); result[k] = append(result[k], v) }
    return result
}

// Step 8: Capstone — type-safe product catalog
type Product struct {
    ID       int
    Name     string
    Price    float64
    Category string
    Tags     []string
}

func main() {
    // Number generics
    ints := []int{1, 2, 3, 4, 5}
    floats := []float64{1.5, 2.5, 3.5}
    fmt.Printf("Sum ints: %d, floats: %.1f\n", Sum(ints), Sum(floats))
    fmt.Printf("Avg ints: %.1f, floats: %.1f\n", Average(ints), Average(floats))

    // Cache
    cache := NewCache[string, Product](100 * time.Millisecond)
    cache.Set("p1", Product{1, "Surface Pro", 864, "Laptop", []string{"ms"}})
    if p, ok := cache.Get("p1"); ok {
        fmt.Printf("Cache hit: %s $%.2f\n", p.Name, p.Price)
    }
    time.Sleep(150 * time.Millisecond)
    _, ok := cache.Get("p1")
    fmt.Printf("After TTL expired: found=%v\n", ok)

    // Sets
    laptops := NewSet("Surface Pro", "Surface Book", "MacBook")
    microsoft := NewSet("Surface Pro", "Surface Book", "Office 365")
    both := laptops.Intersect(microsoft)
    fmt.Printf("MS Laptops: %d items\n", both.Len())

    // Optional
    name := Some("Dr. Chen")
    upper := name.Map(func(s string) string {
        result := ""
        for _, c := range s { if c >= 'a' && c <= 'z' { result += string(c-32) } else { result += string(c) } }
        return result
    })
    fmt.Println("Optional:", upper.OrElse("nobody"))

    // Zip & GroupBy
    products := []Product{
        {1, "Surface Pro",  864,   "Laptop",    nil},
        {2, "Surface Pen",  49.99, "Accessory", nil},
        {3, "Office 365",   99.99, "Software",  nil},
        {4, "Surface Book", 1299,  "Laptop",    nil},
        {5, "USB-C Hub",    29.99, "Accessory", nil},
    }

    byCategory := GroupBy(products, func(p Product) string { return p.Category })
    for cat, items := range byCategory {
        prices := Map(items, func(p Product) float64 { return p.Price })
        fmt.Printf("%-12s %d items, avg $%.2f\n", cat, len(items), Average(prices))
    }

    // Zip names with prices
    names := Map(products, func(p Product) string { return p.Name })
    prices := Map(products, func(p Product) float64 { return p.Price })
    pairs := Zip(names, prices)
    fmt.Println("\nName → Price pairs:")
    for _, pair := range pairs {
        fmt.Printf("  %-20s $%.2f\n", pair.First, pair.Second)
    }
}

// Map helper (local to avoid redeclaration)
func Map[T, U any](s []T, fn func(T) U) []U {
    r := make([]U, len(s))
    for i, v := range s { r[i] = fn(v) }
    return r
}
EOF
```

**📸 Verified Output:**
```
Sum ints: 15, floats: 7.5
Avg ints: 3.0, floats: 2.5
Cache hit: Surface Pro $864.00
After TTL expired: found=false
MS Laptops: 2 items
Optional: DR. CHEN
Laptop       2 items, avg $1081.50
Accessory    2 items, avg $39.99
Software     1 items, avg $99.99

Name → Price pairs:
  Surface Pro          $864.00
  Surface Pen          $49.99
  Office 365           $99.99
  Surface Book         $1299.00
  USB-C Hub            $29.99
```

---

## Summary

| Feature | Syntax | Use case |
|---------|--------|---------|
| Type parameter | `func F[T any]` | Generic function |
| Constraint | `interface { ~int \| ~string }` | Restrict allowed types |
| `comparable` | Built-in constraint | Types that support `==` |
| Multiple params | `func F[T, U any]` | Input/output type differ |
| Generic struct | `type Stack[T any] struct` | Reusable data structures |
| Tilde `~` | `~int` | Includes named types over int |

## Further Reading
- [Go Generics Tutorial](https://go.dev/doc/tutorial/generics)
- [Type Parameters Proposal](https://go.googlesource.com/proposal/+/refs/heads/master/design/43651-type-parameters.md)
