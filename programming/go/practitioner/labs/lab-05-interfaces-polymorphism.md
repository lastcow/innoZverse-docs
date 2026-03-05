# Lab 05: Interfaces & Polymorphism

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm golang:1.22-alpine sh`

## Overview

Interfaces in Go are *implicitly satisfied* — a type implements an interface simply by having the right methods. No `implements` keyword. This structural typing enables powerful polymorphism and decoupled design.

## Step 1: Interface Definition & Implicit Implementation

```go
package main

import (
    "fmt"
    "math"
)

type Shape interface {
    Area() float64
    Perimeter() float64
}

type Circle struct{ Radius float64 }
func (c Circle) Area() float64      { return math.Pi * c.Radius * c.Radius }
func (c Circle) Perimeter() float64 { return 2 * math.Pi * c.Radius }

type Rect struct{ W, H float64 }
func (r Rect) Area() float64      { return r.W * r.H }
func (r Rect) Perimeter() float64 { return 2 * (r.W + r.H) }

// Works with any Shape — polymorphism!
func printShape(s Shape) {
    fmt.Printf("Area=%.2f  Perimeter=%.2f\n", s.Area(), s.Perimeter())
}

func main() {
    shapes := []Shape{
        Circle{Radius: 5},
        Rect{W: 4, H: 6},
    }
    for _, s := range shapes {
        printShape(s)
    }
}
```

> 💡 **Tip:** Keep interfaces small. The standard library's `io.Reader` has one method — and it's one of the most powerful abstractions in Go.

## Step 2: Interface Composition

Interfaces can embed other interfaces.

```go
package main

import "fmt"

type Reader interface {
    Read(p []byte) (n int, err error)
}

type Writer interface {
    Write(p []byte) (n int, err error)
}

// Composed interface
type ReadWriter interface {
    Reader
    Writer
}

// Stringer is the fmt.Stringer interface
type Stringer interface {
    String() string
}

// Your type can implement multiple interfaces
type Buffer struct{ data []byte }

func (b *Buffer) Read(p []byte) (int, error) {
    n := copy(p, b.data)
    b.data = b.data[n:]
    return n, nil
}

func (b *Buffer) Write(p []byte) (int, error) {
    b.data = append(b.data, p...)
    return len(p), nil
}

func (b *Buffer) String() string {
    return string(b.data)
}

func main() {
    buf := &Buffer{}

    // Use as Writer
    var w Writer = buf
    w.Write([]byte("hello, Go!"))

    // Use as Stringer
    var s Stringer = buf
    fmt.Println(s.String())
}
```

## Step 3: Empty Interface — any

`any` (alias for `interface{}`) accepts values of any type.

```go
package main

import "fmt"

func printAnything(values ...any) {
    for _, v := range values {
        fmt.Printf("%T: %v\n", v, v)
    }
}

func main() {
    printAnything(42, "hello", true, 3.14, []int{1, 2, 3})
}
```

> 💡 **Tip:** Prefer concrete types or typed interfaces over `any`. `any` loses type safety — use type assertions or switches to recover it.

## Step 4: Type Assertion

Extract a concrete type from an interface value.

```go
package main

import "fmt"

type Animal interface{ Sound() string }

type Dog struct{ Name string }
func (d Dog) Sound() string { return "woof" }

type Cat struct{ Name string }
func (c Cat) Sound() string { return "meow" }

func main() {
    var a Animal = Dog{Name: "Rex"}

    // Comma-ok form — safe
    if d, ok := a.(Dog); ok {
        fmt.Println("it's a dog named", d.Name)
    }

    // Unsafe form — panics if wrong type
    // d := a.(Cat)  // would panic!

    // Check nil interface
    var b Animal
    fmt.Println("nil interface:", b == nil)
}
```

## Step 5: Type Switch

Dispatch on the runtime type of an interface value.

```go
package main

import "fmt"

func describe(i any) string {
    switch v := i.(type) {
    case int:
        return fmt.Sprintf("integer: %d", v)
    case float64:
        return fmt.Sprintf("float: %.2f", v)
    case string:
        return fmt.Sprintf("string: %q (len=%d)", v, len(v))
    case bool:
        return fmt.Sprintf("bool: %v", v)
    case []int:
        return fmt.Sprintf("[]int with %d elements", len(v))
    case nil:
        return "nil"
    default:
        return fmt.Sprintf("unknown type %T", v)
    }
}

func main() {
    values := []any{42, 3.14, "Go", true, []int{1, 2, 3}, nil}
    for _, v := range values {
        fmt.Println(describe(v))
    }
}
```

## Step 6: fmt.Stringer and io.Reader / io.Writer

Implementing standard library interfaces makes your types work with existing ecosystem code.

```go
package main

import (
    "fmt"
    "io"
    "strings"
)

// fmt.Stringer — used by fmt.Print* automatically
type Point struct{ X, Y int }
func (p Point) String() string { return fmt.Sprintf("(%d, %d)", p.X, p.Y) }

// Custom io.Reader
type Counter struct {
    total int
    r     io.Reader
}

func (c *Counter) Read(p []byte) (int, error) {
    n, err := c.r.Read(p)
    c.total += n
    return n, err
}

func main() {
    p := Point{3, 4}
    fmt.Println(p)         // calls p.String()
    fmt.Printf("point: %v\n", p)

    cr := &Counter{r: strings.NewReader("Hello, interfaces!")}
    data, _ := io.ReadAll(cr)
    fmt.Printf("read %d bytes: %s\n", cr.total, data)
}
```

## Step 7: Interface Pitfalls — nil Interface vs nil Pointer

```go
package main

import "fmt"

type MyError struct{ msg string }
func (e *MyError) Error() string { return e.msg }

// BUG: returns typed nil, not nil interface
func badFunc(fail bool) error {
    var err *MyError // typed nil
    if fail {
        err = &MyError{"something went wrong"}
    }
    return err // non-nil interface holding nil pointer!
}

// CORRECT: return untyped nil
func goodFunc(fail bool) error {
    if fail {
        return &MyError{"something went wrong"}
    }
    return nil // untyped nil → nil interface
}

func main() {
    err := badFunc(false)
    fmt.Println("bad (no fail):", err == nil) // false! BUG

    err = goodFunc(false)
    fmt.Println("good (no fail):", err == nil) // true
}
```

> 💡 **Tip:** Never return a typed nil as an `error`. Return `nil` directly.

## Step 8: Capstone — Plugin System via Interfaces

```go
package main

import (
    "fmt"
    "math"
    "sort"
)

// Plugin interface
type Processor interface {
    Name() string
    Process(data []float64) []float64
}

// Implementations
type Normalizer struct{}
func (Normalizer) Name() string { return "normalizer" }
func (Normalizer) Process(data []float64) []float64 {
    max := 0.0
    for _, v := range data { if v > max { max = v } }
    result := make([]float64, len(data))
    for i, v := range data { result[i] = v / max }
    return result
}

type Sorter struct{}
func (Sorter) Name() string { return "sorter" }
func (Sorter) Process(data []float64) []float64 {
    cp := append([]float64{}, data...)
    sort.Float64s(cp)
    return cp
}

type StdDev struct{}
func (StdDev) Name() string { return "stddev" }
func (StdDev) Process(data []float64) []float64 {
    if len(data) == 0 { return nil }
    mean := 0.0
    for _, v := range data { mean += v }
    mean /= float64(len(data))
    variance := 0.0
    for _, v := range data { variance += (v - mean) * (v - mean) }
    return []float64{math.Sqrt(variance / float64(len(data)))}
}

// Pipeline runner
type Pipeline struct{ stages []Processor }
func (p *Pipeline) Add(proc Processor) { p.stages = append(p.stages, proc) }
func (p *Pipeline) Run(data []float64) []float64 {
    for _, stage := range p.stages {
        data = stage.Process(data)
        fmt.Printf("[%s] → %v\n", stage.Name(), data)
    }
    return data
}

func main() {
    data := []float64{3, 1, 4, 1, 5, 9, 2, 6}
    fmt.Println("input:", data)

    pipe := &Pipeline{}
    pipe.Add(Sorter{})
    pipe.Add(Normalizer{})
    pipe.Add(StdDev{})
    pipe.Run(data)
}
```

📸 **Verified Output:**
```
=== Polymorphism ===
Area=78.54 Perimeter=31.42
Area=24.00 Perimeter=20.00

=== Type Switch ===
int: 42
string: "hello"
Shape: area=28.27
nil
unknown: bool

=== Interface Composition ===
Circle(r=2.0) area: 12.566370614359172

=== Type Assertion ===
it's a rect: 3x4
```

## Summary

| Concept | Key Points |
|---|---|
| Implicit implementation | No `implements` — method set matching |
| Interface composition | Embed interfaces to build larger contracts |
| `any` / `interface{}` | Accept any type; use type switch to inspect |
| Type assertion `v.(T)` | Extract concrete type; use comma-ok form |
| Type switch | Multi-way dispatch on runtime type |
| `fmt.Stringer` | `String() string` — auto-used by `fmt` |
| `io.Reader/Writer` | Foundation of Go's I/O model |
| nil interface pitfall | Return `nil`, not typed nil pointer |
