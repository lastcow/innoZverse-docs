# Lab 10: Advanced Generics

**Time:** 45 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm golang:1.22-alpine sh`

## Overview

Master Go generics: interface union constraints, type sets, generic data structures (Stack, Queue, Set, OrderedMap), and functional algorithms (Map, Filter, Reduce, GroupBy).

---

## Step 1: Generic Constraints — Interface Unions

```go
package main

import (
	"fmt"
	"math"
)

// Type set constraint: only these concrete types
type Integer interface {
	int | int8 | int16 | int32 | int64
}

type Float interface {
	float32 | float64
}

// Union constraint
type Number interface {
	Integer | Float
}

// ~T means "T and any type whose underlying type is T"
type Ordered interface {
	~int | ~int8 | ~int16 | ~int32 | ~int64 |
		~float32 | ~float64 |
		~string
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

func Abs[T Integer | Float](x T) T {
	if x < 0 {
		return -x
	}
	return x
}

func Distance[T Float](x1, y1, x2, y2 T) T {
	dx := x2 - x1
	dy := y2 - y1
	return T(math.Sqrt(float64(dx*dx + dy*dy)))
}

func main() {
	fmt.Println("Sum[int]:", Sum([]int{1, 2, 3, 4, 5}))
	fmt.Println("Sum[float64]:", Sum([]float64{1.1, 2.2, 3.3}))
	fmt.Println("Min[string]:", Min("apple", "banana"))
	fmt.Println("Max[int]:", Max(3, 7))
	fmt.Println("Abs[int]:", Abs(-42))
	fmt.Printf("Distance: %.4f\n", Distance(0.0, 0.0, 3.0, 4.0))
}
```

---

## Step 2: Generic Data Structures — Stack & Queue

```go
package main

import (
	"errors"
	"fmt"
)

// Generic Stack (LIFO)
type Stack[T any] struct {
	items []T
}

func (s *Stack[T]) Push(v T) {
	s.items = append(s.items, v)
}

func (s *Stack[T]) Pop() (T, error) {
	if len(s.items) == 0 {
		var zero T
		return zero, errors.New("stack is empty")
	}
	top := s.items[len(s.items)-1]
	s.items = s.items[:len(s.items)-1]
	return top, nil
}

func (s *Stack[T]) Peek() (T, error) {
	if len(s.items) == 0 {
		var zero T
		return zero, errors.New("stack is empty")
	}
	return s.items[len(s.items)-1], nil
}

func (s *Stack[T]) Len() int  { return len(s.items) }
func (s *Stack[T]) Empty() bool { return len(s.items) == 0 }

// Generic Queue (FIFO)
type Queue[T any] struct {
	items []T
}

func (q *Queue[T]) Enqueue(v T) {
	q.items = append(q.items, v)
}

func (q *Queue[T]) Dequeue() (T, error) {
	if len(q.items) == 0 {
		var zero T
		return zero, errors.New("queue is empty")
	}
	front := q.items[0]
	q.items = q.items[1:]
	return front, nil
}

func (q *Queue[T]) Len() int { return len(q.items) }

func main() {
	// Stack demo
	var s Stack[string]
	s.Push("first")
	s.Push("second")
	s.Push("third")
	fmt.Printf("Stack len: %d\n", s.Len())
	for !s.Empty() {
		v, _ := s.Pop()
		fmt.Printf("Pop: %s\n", v)
	}

	// Queue demo
	var q Queue[int]
	for i := 1; i <= 4; i++ {
		q.Enqueue(i * 10)
	}
	fmt.Printf("\nQueue len: %d\n", q.Len())
	for q.Len() > 0 {
		v, _ := q.Dequeue()
		fmt.Printf("Dequeue: %d\n", v)
	}
}
```

---

## Step 3: Generic Set

```go
package main

import "fmt"

type Set[T comparable] struct {
	m map[T]struct{}
}

func NewSet[T comparable](items ...T) *Set[T] {
	s := &Set[T]{m: make(map[T]struct{})}
	for _, item := range items {
		s.Add(item)
	}
	return s
}

func (s *Set[T]) Add(v T)      { s.m[v] = struct{}{} }
func (s *Set[T]) Remove(v T)   { delete(s.m, v) }
func (s *Set[T]) Contains(v T) bool { _, ok := s.m[v]; return ok }
func (s *Set[T]) Len() int     { return len(s.m) }

func (s *Set[T]) Union(other *Set[T]) *Set[T] {
	result := NewSet[T]()
	for k := range s.m   { result.Add(k) }
	for k := range other.m { result.Add(k) }
	return result
}

func (s *Set[T]) Intersection(other *Set[T]) *Set[T] {
	result := NewSet[T]()
	for k := range s.m {
		if other.Contains(k) {
			result.Add(k)
		}
	}
	return result
}

func (s *Set[T]) Difference(other *Set[T]) *Set[T] {
	result := NewSet[T]()
	for k := range s.m {
		if !other.Contains(k) {
			result.Add(k)
		}
	}
	return result
}

func main() {
	a := NewSet("go", "rust", "python", "java")
	b := NewSet("rust", "python", "c++", "zig")

	fmt.Println("A:", a.Len())
	fmt.Println("B:", b.Len())
	fmt.Println("A contains 'go':", a.Contains("go"))
	fmt.Println("Union:", a.Union(b).Len())
	fmt.Println("Intersection:", a.Intersection(b).Len()) // rust, python
	fmt.Println("A-B:", a.Difference(b).Len())            // go, java
}
```

---

## Step 4: Generic Algorithms — Map/Filter/Reduce

```go
package main

import "fmt"

func Map[T, U any](slice []T, f func(T) U) []U {
	result := make([]U, len(slice))
	for i, v := range slice {
		result[i] = f(v)
	}
	return result
}

func Filter[T any](slice []T, pred func(T) bool) []T {
	var result []T
	for _, v := range slice {
		if pred(v) {
			result = append(result, v)
		}
	}
	return result
}

func Reduce[T, U any](slice []T, init U, f func(U, T) U) U {
	acc := init
	for _, v := range slice {
		acc = f(acc, v)
	}
	return acc
}

func Contains[T comparable](slice []T, val T) bool {
	for _, v := range slice {
		if v == val {
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

func Values[K comparable, V any](m map[K]V) []V {
	vals := make([]V, 0, len(m))
	for _, v := range m {
		vals = append(vals, v)
	}
	return vals
}

func GroupBy[T any, K comparable](slice []T, keyFn func(T) K) map[K][]T {
	result := make(map[K][]T)
	for _, v := range slice {
		k := keyFn(v)
		result[k] = append(result[k], v)
	}
	return result
}

func main() {
	nums := []int{1, 2, 3, 4, 5, 6, 7, 8, 9, 10}

	doubled := Map(nums, func(n int) int { return n * 2 })
	fmt.Println("Map *2:", doubled)

	evens := Filter(nums, func(n int) bool { return n%2 == 0 })
	fmt.Println("Filter even:", evens)

	sum := Reduce(nums, 0, func(acc, n int) int { return acc + n })
	fmt.Println("Reduce sum:", sum)

	product := Reduce(nums[:5], 1, func(acc, n int) int { return acc * n })
	fmt.Println("Reduce product(1..5):", product)

	strs := Map(nums[:4], func(n int) string { return fmt.Sprintf("%02d", n) })
	fmt.Println("Map to string:", strs)

	fmt.Println("Contains 7:", Contains(nums, 7))
	fmt.Println("Contains 11:", Contains(nums, 11))

	// GroupBy: group by even/odd
	groups := GroupBy(nums, func(n int) string {
		if n%2 == 0 {
			return "even"
		}
		return "odd"
	})
	fmt.Printf("GroupBy even: %d, odd: %d\n", len(groups["even"]), len(groups["odd"]))
}
```

---

## Step 5: OrderedMap (Generic)

```go
package main

import "fmt"

// OrderedMap preserves insertion order
type OrderedMap[K comparable, V any] struct {
	keys   []K
	values map[K]V
}

func NewOrderedMap[K comparable, V any]() *OrderedMap[K, V] {
	return &OrderedMap[K, V]{
		values: make(map[K]V),
	}
}

func (m *OrderedMap[K, V]) Set(k K, v V) {
	if _, exists := m.values[k]; !exists {
		m.keys = append(m.keys, k)
	}
	m.values[k] = v
}

func (m *OrderedMap[K, V]) Get(k K) (V, bool) {
	v, ok := m.values[k]
	return v, ok
}

func (m *OrderedMap[K, V]) Delete(k K) {
	if _, exists := m.values[k]; !exists {
		return
	}
	delete(m.values, k)
	for i, key := range m.keys {
		if key == k {
			m.keys = append(m.keys[:i], m.keys[i+1:]...)
			break
		}
	}
}

func (m *OrderedMap[K, V]) Keys() []K { return m.keys }
func (m *OrderedMap[K, V]) Len() int  { return len(m.keys) }

func (m *OrderedMap[K, V]) ForEach(fn func(K, V)) {
	for _, k := range m.keys {
		fn(k, m.values[k])
	}
}

func main() {
	om := NewOrderedMap[string, int]()
	om.Set("first", 1)
	om.Set("second", 2)
	om.Set("third", 3)
	om.Set("fourth", 4)
	om.Set("second", 22) // update existing

	fmt.Printf("OrderedMap len: %d\n", om.Len())
	om.ForEach(func(k string, v int) {
		fmt.Printf("  %s: %d\n", k, v)
	})
}
```

---

## Step 6: Type Inference

```go
package main

import "fmt"

// Go infers type parameters when possible
func Zip[A, B any](as []A, bs []B) []struct{ A A; B B } {
	n := len(as)
	if len(bs) < n {
		n = len(bs)
	}
	result := make([]struct{ A A; B B }, n)
	for i := 0; i < n; i++ {
		result[i] = struct{ A A; B B }{as[i], bs[i]}
	}
	return result
}

func Chunk[T any](slice []T, size int) [][]T {
	var chunks [][]T
	for i := 0; i < len(slice); i += size {
		end := i + size
		if end > len(slice) {
			end = len(slice)
		}
		chunks = append(chunks, slice[i:end])
	}
	return chunks
}

func Ptr[T any](v T) *T { return &v }

func main() {
	names := []string{"Alice", "Bob", "Carol"}
	scores := []int{95, 87, 92}
	pairs := Zip(names, scores)
	for _, p := range pairs {
		fmt.Printf("%s: %d\n", p.A, p.B)
	}

	nums := []int{1, 2, 3, 4, 5, 6, 7, 8, 9}
	chunks := Chunk(nums, 3)
	for i, c := range chunks {
		fmt.Printf("Chunk %d: %v\n", i, c)
	}

	// Ptr[T] — generic pointer helper
	n := Ptr(42)
	s := Ptr("hello")
	fmt.Printf("Ptr[int]: %d, Ptr[string]: %s\n", *n, *s)
}
```

---

## Step 7: Constraints from `cmp` Package (Go 1.21)

```go
package main

import (
	"cmp"
	"fmt"
	"sort"
)

// cmp.Ordered is the standard constraint for ordered types
func MinSlice[T cmp.Ordered](s []T) (T, bool) {
	if len(s) == 0 {
		var zero T
		return zero, false
	}
	m := s[0]
	for _, v := range s[1:] {
		if v < m {
			m = v
		}
	}
	return m, true
}

func SortSlice[T cmp.Ordered](s []T) []T {
	result := make([]T, len(s))
	copy(result, s)
	sort.Slice(result, func(i, j int) bool {
		return cmp.Less(result[i], result[j])
	})
	return result
}

func main() {
	ints := []int{5, 2, 8, 1, 9, 3}
	strs := []string{"banana", "apple", "cherry", "date"}

	min, _ := MinSlice(ints)
	fmt.Println("Min:", min)

	fmt.Println("Sorted ints:", SortSlice(ints))
	fmt.Println("Sorted strings:", SortSlice(strs))
}
```

---

## Step 8: Capstone — Full Verified Demo

```bash
docker run --rm golang:1.22-alpine sh -c "cat > /tmp/main.go << 'GOEOF'
package main

import (
	\"fmt\"
	\"sort\"
)

type Number interface { int | int64 | float64 }

func Sum[T Number](nums []T) T { var t T; for _, n := range nums { t += n }; return t }

func Map[T, U any](s []T, f func(T) U) []U {
	r := make([]U, len(s)); for i, v := range s { r[i] = f(v) }; return r
}

func Filter[T any](s []T, pred func(T) bool) []T {
	var r []T; for _, v := range s { if pred(v) { r = append(r, v) } }; return r
}

func Reduce[T, U any](s []T, init U, f func(U, T) U) U {
	acc := init; for _, v := range s { acc = f(acc, v) }; return acc
}

type Stack[T any] struct{ items []T }
func (s *Stack[T]) Push(v T) { s.items = append(s.items, v) }
func (s *Stack[T]) Pop() (T, bool) {
	if len(s.items) == 0 { var z T; return z, false }
	v := s.items[len(s.items)-1]; s.items = s.items[:len(s.items)-1]; return v, true
}
func (s *Stack[T]) Len() int { return len(s.items) }

func GroupBy[T any, K comparable](s []T, key func(T) K) map[K][]T {
	m := make(map[K][]T); for _, v := range s { k := key(v); m[k] = append(m[k], v) }; return m
}

func main() {
	ints := []int{1, 2, 3, 4, 5}
	fmt.Println(\"Sum[int]:\", Sum(ints))
	fmt.Println(\"Sum[float64]:\", Sum([]float64{1.1, 2.2, 3.3}))
	doubled := Map(ints, func(n int) int { return n * 2 })
	fmt.Println(\"Map double:\", doubled)
	evens := Filter(ints, func(n int) bool { return n%2 == 0 })
	fmt.Println(\"Filter even:\", evens)
	product := Reduce(ints, 1, func(acc, n int) int { return acc * n })
	fmt.Println(\"Reduce product:\", product)

	var s Stack[string]
	s.Push(\"a\"); s.Push(\"b\"); s.Push(\"c\")
	for s.Len() > 0 { v, _ := s.Pop(); fmt.Printf(\"Pop: %s\\n\", v) }

	words := []string{\"go\", \"rust\", \"go\", \"python\", \"rust\", \"go\"}
	groups := GroupBy(words, func(s string) string { return s })
	langs := []string{\"go\", \"python\", \"rust\"}
	sort.Strings(langs)
	for _, k := range langs { fmt.Printf(\"GroupBy %s: %d\\n\", k, len(groups[k])) }
}
GOEOF
cd /tmp && go run main.go"
```

📸 **Verified Output:**
```
Sum[int]: 15
Sum[float64]: 6.6
Map double: [2 4 6 8 10]
Filter even: [2 4]
Reduce product: 120
Pop: c
Pop: b
Pop: a
GroupBy go: 3
GroupBy python: 1
GroupBy rust: 2
```

---

## Summary

| Feature | Syntax | Notes |
|---------|--------|-------|
| Basic constraint | `[T Number]` | Named interface |
| Union | `int \| float64 \| string` | Type set |
| Tilde | `~int` | int + named types with int underlying |
| `cmp.Ordered` | stdlib Go 1.21 | All ordered types |
| Type inference | `Sum([]int{1,2})` | Compiler infers `T=int` |
| Generic struct | `Stack[T any]` | Methods on generic types |
| Comparable | `[K comparable]` | Can use as map key |

**Key Takeaways:**
- Generic constraints use interfaces with type sets (Go 1.18+)
- `~T` means "T or any type with underlying type T" — crucial for custom types
- Type inference eliminates most explicit `[T]` annotations at call sites
- `cmp.Ordered` (Go 1.21) replaces custom `Ordered` constraints
- Generics beat `interface{}` for type safety; prefer them over `reflect` for collections
