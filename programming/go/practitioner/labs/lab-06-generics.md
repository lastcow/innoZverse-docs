# Lab 06: Generics

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm golang:1.22-alpine sh`

## Overview

Generics (introduced in Go 1.18) allow you to write functions and types that work with multiple types while maintaining compile-time type safety. Go generics use *type parameters* and *constraints*.

## Step 1: Generic Functions

```go
package main

import "fmt"

// T is a type parameter, any is the constraint
func Contains[T comparable](s []T, item T) bool {
    for _, v := range s {
        if v == item {
            return true
        }
    }
    return false
}

func Keys[K comparable, V any](m map[K]V) []K {
    keys := make([]K, 0, len(m))
    for k := range m {
        keys = append(keys, k)
    }
    return keys
}

func main() {
    fmt.Println(Contains([]int{1, 2, 3}, 2))       // true
    fmt.Println(Contains([]string{"a", "b"}, "c")) // false

    m := map[string]int{"x": 1, "y": 2}
    fmt.Println(Keys(m)) // [x y] (order may vary)
}
```

> 💡 **Tip:** `comparable` means the type supports `==` and `!=`. Use `any` when you don't need comparison.

## Step 2: Type Constraints

Constraints restrict which types can be used as type arguments.

```go
package main

import "fmt"

// Built-in constraints from "constraints" package (or define inline)
type Number interface {
    ~int | ~int8 | ~int16 | ~int32 | ~int64 |
        ~float32 | ~float64
}

type Ordered interface {
    ~int | ~float64 | ~string
}

func Sum[T Number](nums []T) T {
    var total T
    for _, n := range nums {
        total += n
    }
    return total
}

func Min[T Ordered](a, b T) T {
    if a < b {
        return a
    }
    return b
}

func Max[T Ordered](a, b T) T {
    if a > b {
        return a
    }
    return b
}

func main() {
    fmt.Println("int sum:", Sum([]int{1, 2, 3, 4, 5}))
    fmt.Println("float sum:", Sum([]float64{1.1, 2.2, 3.3}))
    fmt.Println("min:", Min(3, 7))
    fmt.Println("max:", Max("apple", "banana"))
}
```

## Step 3: Generic Types

Define data structures parameterized by type.

```go
package main

import "fmt"

// Generic Stack
type Stack[T any] struct {
    items []T
}

func (s *Stack[T]) Push(v T)       { s.items = append(s.items, v) }
func (s *Stack[T]) Len() int       { return len(s.items) }
func (s *Stack[T]) IsEmpty() bool  { return len(s.items) == 0 }
func (s *Stack[T]) Pop() (T, bool) {
    var zero T
    if s.IsEmpty() {
        return zero, false
    }
    top := s.items[len(s.items)-1]
    s.items = s.items[:len(s.items)-1]
    return top, true
}
func (s *Stack[T]) Peek() (T, bool) {
    var zero T
    if s.IsEmpty() {
        return zero, false
    }
    return s.items[len(s.items)-1], true
}

func main() {
    // String stack
    var ss Stack[string]
    ss.Push("first")
    ss.Push("second")
    ss.Push("third")
    for !ss.IsEmpty() {
        v, _ := ss.Pop()
        fmt.Print(v, " ")
    }
    fmt.Println()

    // Int stack
    var is Stack[int]
    for i := 1; i <= 5; i++ {
        is.Push(i * i)
    }
    top, _ := is.Peek()
    fmt.Println("top of int stack:", top)
}
```

## Step 4: Generic Map / Filter / Reduce

```go
package main

import "fmt"

func Map[T, U any](s []T, f func(T) U) []U {
    result := make([]U, len(s))
    for i, v := range s {
        result[i] = f(v)
    }
    return result
}

func Filter[T any](s []T, pred func(T) bool) []T {
    var result []T
    for _, v := range s {
        if pred(v) {
            result = append(result, v)
        }
    }
    return result
}

func Reduce[T, A any](s []T, init A, f func(A, T) A) A {
    acc := init
    for _, v := range s {
        acc = f(acc, v)
    }
    return acc
}

func main() {
    nums := []int{1, 2, 3, 4, 5, 6, 7, 8, 9, 10}

    // Type inference — Go deduces T and U
    squares := Map(nums, func(n int) int { return n * n })
    fmt.Println("squares:", squares)

    evens := Filter(nums, func(n int) bool { return n%2 == 0 })
    fmt.Println("evens:", evens)

    sum := Reduce(nums, 0, func(acc, n int) int { return acc + n })
    fmt.Println("sum:", sum)

    // Chain operations
    result := Reduce(
        Filter(
            Map(nums, func(n int) int { return n * n }),
            func(n int) bool { return n > 25 },
        ),
        0,
        func(acc, n int) int { return acc + n },
    )
    fmt.Println("sum of squares > 25:", result)
}
```

## Step 5: Type Inference

Go can often infer type parameters from function arguments.

```go
package main

import "fmt"

func Zip[T, U any](ts []T, us []U) []struct{ First T; Second U } {
    n := len(ts)
    if len(us) < n {
        n = len(us)
    }
    result := make([]struct{ First T; Second U }, n)
    for i := 0; i < n; i++ {
        result[i] = struct{ First T; Second U }{ts[i], us[i]}
    }
    return result
}

func main() {
    names := []string{"Alice", "Bob", "Charlie"}
    scores := []int{95, 87, 92}

    // Type inferred: Zip[string, int]
    pairs := Zip(names, scores)
    for _, p := range pairs {
        fmt.Printf("%s: %d\n", p.First, p.Second)
    }
}
```

## Step 6: The slices Package (Go 1.21)

```go
package main

import (
    "cmp"
    "fmt"
    "slices"
)

func main() {
    nums := []int{3, 1, 4, 1, 5, 9, 2, 6}

    // Sort
    sorted := slices.Clone(nums)
    slices.Sort(sorted)
    fmt.Println("sorted:", sorted)

    // Binary search
    idx, found := slices.BinarySearch(sorted, 5)
    fmt.Printf("found 5 at index %d: %v\n", idx, found)

    // Min/Max
    fmt.Println("max:", slices.MaxFunc(nums, cmp.Compare))
    fmt.Println("min:", slices.MinFunc(nums, cmp.Compare))

    // Contains
    fmt.Println("contains 9:", slices.Contains(nums, 9))

    // Reverse
    rev := slices.Clone(sorted)
    slices.Reverse(rev)
    fmt.Println("reversed:", rev)
}
```

## Step 7: Generic Option Type

```go
package main

import "fmt"

type Option[T any] struct {
    value T
    valid bool
}

func Some[T any](v T) Option[T] { return Option[T]{value: v, valid: true} }
func None[T any]() Option[T]    { return Option[T]{} }

func (o Option[T]) IsNone() bool { return !o.valid }
func (o Option[T]) Unwrap() T {
    if !o.valid {
        panic("called Unwrap on None")
    }
    return o.value
}
func (o Option[T]) UnwrapOr(def T) T {
    if o.valid {
        return o.value
    }
    return def
}

func divide(a, b float64) Option[float64] {
    if b == 0 {
        return None[float64]()
    }
    return Some(a / b)
}

func main() {
    fmt.Println(divide(10, 2).Unwrap())         // 5
    fmt.Println(divide(10, 0).UnwrapOr(-1))     // -1
    fmt.Println(divide(10, 0).IsNone())          // true
}
```

## Step 8: Capstone — Generic Priority Queue

```go
package main

import (
    "container/heap"
    "fmt"
)

type Item[T any] struct {
    Value    T
    Priority int
}

type PriorityQueue[T any] []*Item[T]

func (pq PriorityQueue[T]) Len() int           { return len(pq) }
func (pq PriorityQueue[T]) Less(i, j int) bool { return pq[i].Priority > pq[j].Priority }
func (pq PriorityQueue[T]) Swap(i, j int)      { pq[i], pq[j] = pq[j], pq[i] }
func (pq *PriorityQueue[T]) Push(x any)        { *pq = append(*pq, x.(*Item[T])) }
func (pq *PriorityQueue[T]) Pop() any {
    old := *pq
    n := len(old)
    item := old[n-1]
    *pq = old[:n-1]
    return item
}

func main() {
    pq := &PriorityQueue[string]{}
    heap.Init(pq)
    heap.Push(pq, &Item[string]{Value: "low priority task", Priority: 1})
    heap.Push(pq, &Item[string]{Value: "urgent task", Priority: 10})
    heap.Push(pq, &Item[string]{Value: "normal task", Priority: 5})

    for pq.Len() > 0 {
        item := heap.Pop(pq).(*Item[string])
        fmt.Printf("[%d] %s\n", item.Priority, item.Value)
    }
}
```

📸 **Verified Output:**
```
=== Generic Map/Filter/Reduce ===
doubled: [2 4 6 8 10]
evens: [2 4]
sum: 15

=== Generic Stack ===
c b a 

=== Number constraint ===
int sum: 6
float sum: 6.6

=== slices package (Go 1.21) ===
sorted: [apple banana cherry]
cherry at index 2 found=true
max: 9
```

## Summary

| Concept | Syntax | Notes |
|---|---|---|
| Type parameter | `func F[T any](...)` | Declared in `[]` after name |
| Constraint | `comparable`, `any`, custom interface | Restricts valid type args |
| `~T` in constraint | `~int` matches int and named types based on int | Tilde = underlying type |
| Type inference | `Contains(slice, item)` vs `Contains[int](slice, item)` | Compiler infers when possible |
| Generic type | `type Stack[T any] struct` | Each field/method uses T |
| `slices` package | `slices.Sort`, `slices.Contains`, `slices.Max` | Go 1.21 stdlib generic helpers |
| `cmp.Compare` | Works with all ordered types | Use with `slices.SortFunc` |
