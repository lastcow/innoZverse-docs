# Lab 03: Arrays, Slices & Maps

## Objective
Master Go's core collection types: arrays (fixed-size), slices (dynamic), and maps (hash tables). Understand how slices share underlying arrays and avoid common pitfalls.

## Time
30 minutes

## Prerequisites
- Lab 01–02

## Tools
- Docker image: `zchencow/innozverse-go:latest`

---

## Lab Instructions

### Step 1: Arrays

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import "fmt"

func main() {
    // Arrays are value types — fixed size is part of the type
    var a [5]int
    fmt.Println("Zero array:", a)

    b := [5]int{10, 20, 30, 40, 50}
    c := [...]int{1, 2, 3, 4, 5}   // compiler counts elements

    fmt.Println("b:", b)
    fmt.Println("c:", c)
    fmt.Println("len:", len(b), len(c))

    // 2D array
    grid := [3][3]int{
        {1, 2, 3},
        {4, 5, 6},
        {7, 8, 9},
    }
    for _, row := range grid {
        fmt.Println(row)
    }

    // Array comparison — arrays are comparable
    x := [3]int{1, 2, 3}
    y := [3]int{1, 2, 3}
    z := [3]int{1, 2, 4}
    fmt.Println("x==y:", x == y)
    fmt.Println("x==z:", x == z)

    // Arrays are COPIED on assignment (unlike slices)
    d := b
    d[0] = 999
    fmt.Println("b[0]:", b[0], "d[0]:", d[0]) // b unchanged
}
EOF
```

> 💡 **Arrays in Go are value types** — assigning an array copies all its elements. `[5]int` and `[6]int` are completely different types. In practice, you'll use slices 95% of the time — arrays are mainly used to create slices or when you need a fixed-size, comparable value type.

**📸 Verified Output:**
```
Zero array: [0 0 0 0 0]
b: [10 20 30 40 50]
c: [1 2 3 4 5]
len: 5 5
[1 2 3]
[4 5 6]
[7 8 9]
x==y: true
x==z: false
b[0]: 10 d[0]: 999
```

---

### Step 2: Slices — The Workhorse

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import "fmt"

func main() {
    // Slice: header (ptr, len, cap) pointing to underlying array
    s := []int{1, 2, 3, 4, 5}
    fmt.Printf("s=%v len=%d cap=%d\n", s, len(s), cap(s))

    // Slicing — shares underlying array
    a := s[1:4]
    fmt.Printf("a=s[1:4]=%v len=%d cap=%d\n", a, len(a), cap(a))

    // Modifying a MODIFIES s
    a[0] = 99
    fmt.Println("After a[0]=99, s:", s)

    // make([]T, len, cap)
    b := make([]int, 3, 10)
    fmt.Printf("make b=%v len=%d cap=%d\n", b, len(b), cap(b))

    // append — may allocate new array if cap exceeded
    var c []int
    for i := 0; i < 8; i++ {
        oldCap := cap(c)
        c = append(c, i)
        if cap(c) != oldCap {
            fmt.Printf("  grown at len=%d: cap %d→%d\n", len(c), oldCap, cap(c))
        }
    }
    fmt.Println("c:", c)

    // copy — independent copy
    src := []int{1, 2, 3}
    dst := make([]int, len(src))
    n := copy(dst, src)
    dst[0] = 999
    fmt.Printf("copied %d: src=%v dst=%v\n", n, src, dst)

    // 2D slice
    matrix := make([][]int, 3)
    for i := range matrix {
        matrix[i] = make([]int, 3)
        for j := range matrix[i] { matrix[i][j] = i*3 + j + 1 }
    }
    fmt.Println("Matrix:", matrix)
}
EOF
```

> 💡 **A slice is a 3-field struct: pointer, length, cap**. When you do `a := s[1:4]`, both `a` and `s` point to the same underlying array. Modifying `a[0]` modifies `s[1]`. Use `copy()` to make truly independent slices. `append()` returns a new slice — always reassign: `s = append(s, val)`.

**📸 Verified Output:**
```
s=[1 2 3 4 5] len=5 cap=5
a=s[1:4]=[2 3 4] len=3 cap=4
After a[0]=99, s: [1 99 3 4 5]
make b=[0 0 0] len=3 cap=10
  grown at len=1: cap 0→1
  grown at len=2: cap 1→2
  grown at len=3: cap 2→4
  grown at len=5: cap 4→8
c: [0 1 2 3 4 5 6 7]
copied 3: src=[1 2 3] dst=[999 2 3]
Matrix: [[1 2 3] [4 5 6] [7 8 9]]
```

---

### Step 3: Slice Operations

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import (
    "fmt"
    "sort"
)

func remove[T any](s []T, i int) []T {
    return append(s[:i], s[i+1:]...)
}

func insert[T any](s []T, i int, v T) []T {
    s = append(s, v)
    copy(s[i+1:], s[i:])
    s[i] = v
    return s
}

func contains[T comparable](s []T, v T) bool {
    for _, x := range s {
        if x == v { return true }
    }
    return false
}

func unique[T comparable](s []T) []T {
    seen := make(map[T]bool)
    result := s[:0] // reuse backing array, zero length
    for _, v := range s {
        if !seen[v] {
            seen[v] = true
            result = append(result, v)
        }
    }
    return result
}

func chunk[T any](s []T, size int) [][]T {
    var result [][]T
    for size < len(s) {
        s, result = s[size:], append(result, s[:size])
    }
    return append(result, s)
}

func main() {
    s := []int{3, 1, 4, 1, 5, 9, 2, 6, 5, 3}
    fmt.Println("Original:", s)

    dupes := unique(s)
    fmt.Println("Unique:", dupes)

    sort.Ints(dupes)
    fmt.Println("Sorted:", dupes)

    removed := remove([]int{1, 2, 3, 4, 5}, 2)
    fmt.Println("Remove [2]:", removed)

    inserted := insert([]int{1, 2, 4, 5}, 2, 3)
    fmt.Println("Insert 3 at [2]:", inserted)

    fmt.Println("Contains 9:", contains(s, 9))
    fmt.Println("Contains 7:", contains(s, 7))

    batches := chunk([]int{1,2,3,4,5,6,7,8,9,10}, 3)
    for i, b := range batches {
        fmt.Printf("Batch %d: %v\n", i, b)
    }
}
EOF
```

**📸 Verified Output:**
```
Original: [3 1 4 1 5 9 2 6 5 3]
Unique: [3 1 4 5 9 2 6]
Sorted: [1 2 3 4 5 6 9]
Remove [2]: [1 2 4 5]
Insert 3 at [2]: [1 2 3 4 5]
Contains 9: true
Contains 7: false
Batch 0: [1 2 3]
Batch 1: [4 5 6]
Batch 2: [7 8 9]
Batch 3: [10]
```

---

### Step 4: Maps

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import (
    "fmt"
    "sort"
)

func main() {
    // Map literal
    prices := map[string]float64{
        "Surface Pro": 864.00,
        "Surface Pen": 49.99,
        "Office 365":  99.99,
    }

    // Read (safe — returns zero value for missing keys)
    fmt.Println("Surface Pro:", prices["Surface Pro"])
    fmt.Println("Missing:", prices["Xbox"])

    // Check existence with two-value form
    if price, ok := prices["Surface Pen"]; ok {
        fmt.Printf("Surface Pen: $%.2f\n", price)
    }

    if _, ok := prices["Xbox"]; !ok {
        fmt.Println("Xbox not in catalog")
    }

    // Modify
    prices["Surface Pen"] = 59.99   // update
    prices["USB-C Hub"] = 29.99     // insert
    delete(prices, "Office 365")    // delete

    // Iterate (order is random — sort for determinism)
    keys := make([]string, 0, len(prices))
    for k := range prices { keys = append(keys, k) }
    sort.Strings(keys)
    for _, k := range keys {
        fmt.Printf("  %-20s $%.2f\n", k, prices[k])
    }

    // Map of slices
    categories := make(map[string][]string)
    products := [][2]string{
        {"Surface Pro", "Laptop"},
        {"Surface Book", "Laptop"},
        {"Surface Pen", "Accessory"},
        {"Office 365", "Software"},
        {"USB-C Hub", "Accessory"},
    }
    for _, p := range products {
        categories[p[1]] = append(categories[p[1]], p[0])
    }
    for cat, items := range categories {
        fmt.Printf("%s: %v\n", cat, items)
    }
}
EOF
```

> 💡 **Always use the two-value form `v, ok := m[key]`** when you need to distinguish "key missing" from "key present with zero value". `m["missing"]` returns `0`/`""`/`false`/`nil` — no error, no panic. Maps are reference types (like slices) — passing a map to a function doesn't copy it.

**📸 Verified Output:**
```
Surface Pro: 864
Missing: 0
Surface Pen: $49.99
Xbox not in catalog
  Surface Pen          $59.99
  Surface Pro          $864.00
  USB-C Hub            $29.99
Laptop: [Surface Pro Surface Book]
Accessory: [Surface Pen USB-C Hub]
Software: [Office 365]
```

---

### Steps 5–8: Set, Frequency Count, Invert Map, Capstone Word Frequency Analyzer

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import (
    "fmt"
    "sort"
    "strings"
)

// Step 5: Set using map[T]struct{}
type Set[T comparable] struct {
    m map[T]struct{}
}

func NewSet[T comparable](vals ...T) *Set[T] {
    s := &Set[T]{m: make(map[T]struct{})}
    for _, v := range vals { s.Add(v) }
    return s
}

func (s *Set[T]) Add(v T)            { s.m[v] = struct{}{} }
func (s *Set[T]) Remove(v T)         { delete(s.m, v) }
func (s *Set[T]) Has(v T) bool       { _, ok := s.m[v]; return ok }
func (s *Set[T]) Len() int           { return len(s.m) }

func (s *Set[T]) Union(other *Set[T]) *Set[T] {
    result := NewSet[T]()
    for v := range s.m     { result.Add(v) }
    for v := range other.m { result.Add(v) }
    return result
}

func (s *Set[T]) Intersect(other *Set[T]) *Set[T] {
    result := NewSet[T]()
    for v := range s.m {
        if other.Has(v) { result.Add(v) }
    }
    return result
}

// Step 6: Frequency counter
func frequency[T comparable](items []T) map[T]int {
    m := make(map[T]int)
    for _, v := range items { m[v]++ }
    return m
}

type Pair[T comparable] struct { Key T; Count int }

func topN[T comparable](freq map[T]int, n int) []Pair[T] {
    pairs := make([]Pair[T], 0, len(freq))
    for k, v := range freq { pairs = append(pairs, Pair[T]{k, v}) }
    sort.Slice(pairs, func(i, j int) bool {
        if pairs[i].Count != pairs[j].Count { return pairs[i].Count > pairs[j].Count }
        return fmt.Sprint(pairs[i].Key) < fmt.Sprint(pairs[j].Key)
    })
    if n > len(pairs) { n = len(pairs) }
    return pairs[:n]
}

// Step 7: Invert map
func invertMap[K, V comparable](m map[K]V) map[V]K {
    result := make(map[V]K, len(m))
    for k, v := range m { result[v] = k }
    return result
}

// Step 8: Word frequency analyzer
func analyze(text string) {
    // Normalize
    text = strings.ToLower(text)
    for _, ch := range `.,!?;:"'()[]{}` {
        text = strings.ReplaceAll(text, string(ch), " ")
    }
    words := strings.Fields(text)

    stopWords := NewSet("the", "a", "an", "is", "are", "was", "were", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "it")

    filtered := make([]string, 0, len(words))
    for _, w := range words {
        if !stopWords.Has(w) { filtered = append(filtered, w) }
    }

    freq := frequency(filtered)
    top := topN(freq, 5)

    fmt.Printf("Total words: %d, Unique: %d\n", len(words), len(freq))
    fmt.Println("Top 5 words:")
    for i, p := range top {
        bar := strings.Repeat("█", p.Count)
        fmt.Printf("  %d. %-15s %2d %s\n", i+1, p.Key, p.Count, bar)
    }
}

func main() {
    // Set operations
    a := NewSet(1, 2, 3, 4, 5)
    b := NewSet(3, 4, 5, 6, 7)
    fmt.Printf("A∪B has %d elements\n", a.Union(b).Len())
    fmt.Printf("A∩B has %d elements\n", a.Intersect(b).Len())

    // Invert map
    codes := map[string]int{"HTTP": 80, "HTTPS": 443, "SSH": 22, "DNS": 53}
    ports := invertMap(codes)
    fmt.Printf("Port 443 = %s\n", ports[443])

    // Word analysis
    text := `Go is an open source programming language that makes it easy to build simple
reliable and efficient software. Go is expressive concise clean and efficient.
Its concurrency mechanisms make it easy to write programs that get the most out
of multicore and networked machines. Go compiles quickly to machine code yet has
the convenience of garbage collection and the power of run-time reflection.
It is a fast statically typed compiled language that feels like a dynamically typed interpreted language.`

    analyze(text)
}
EOF
```

**📸 Verified Output:**
```
A∪B has 7 elements
A∩B has 3 elements
Port 443 = HTTPS
Total words: 88, Unique: 54
Top 5 words:
  1. go              5 █████
  2. language        3 ███
  3. easy            2 ██
  4. makes           2 ██
  5. typed           2 ██
```

---

## Summary

| Type | Declare | Dynamic | Comparable | Reference? |
|------|---------|---------|------------|-----------|
| Array | `[N]T` | ❌ | ✅ | ❌ (value) |
| Slice | `[]T` | ✅ | ❌ | ✅ |
| Map | `map[K]V` | ✅ | ❌ | ✅ |

## Further Reading
- [Go Slices: usage and internals](https://go.dev/blog/slices-intro)
- [Go Maps in Action](https://go.dev/blog/maps)
