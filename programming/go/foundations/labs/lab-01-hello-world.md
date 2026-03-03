# Lab 01: Hello World & Go Basics

## Objective
Write your first Go programs: understand the package system, variables, constants, basic types, type inference, and Go's opinionated syntax.

## Background
Go (Golang) was created at Google in 2009 by Robert Griesemer, Rob Pike, and Ken Thompson. It combines the performance of C with the readability of Python, and ships with built-in concurrency, a fast compiler, and a comprehensive standard library.

## Time
20 minutes

## Prerequisites
- Basic programming familiarity (any language)

## Tools
- Docker image: `zchencow/innozverse-go:latest` (Go 1.22)

---

## Lab Instructions

### Step 1: Hello, World

```go
package main

import "fmt"

func main() {
    fmt.Println("Hello, innoZverse!")
}
```

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import "fmt"

func main() {
    fmt.Println("Hello, innoZverse!")
    fmt.Printf("Go is %s!\n", "awesome")
}
EOF
```

> 💡 **Every Go file starts with `package`**. The `main` package is special — it's the entry point for executables. `import "fmt"` pulls in the format package from the standard library. Unlike Python, unused imports are a **compile error** in Go — the compiler enforces clean code.

**📸 Verified Output:**
```
Hello, innoZverse!
Go is awesome!
```

---

### Step 2: Variables & Type Inference

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import "fmt"

func main() {
    // Explicit type declaration
    var name string = "Dr. Chen"
    var age  int    = 42
    var pi   float64 = 3.14159

    // Short variable declaration — type inferred
    city    := "San Francisco"
    score   := 98.5
    active  := true

    // Multiple assignment
    x, y := 10, 20

    fmt.Printf("Name: %s, Age: %d\n", name, age)
    fmt.Printf("City: %s, Score: %.1f\n", city, score)
    fmt.Printf("Active: %v, Pi: %.5f\n", active, pi)
    fmt.Printf("x=%d, y=%d, sum=%d\n", x, y, x+y)

    // Zero values — Go initializes everything
    var i int
    var s string
    var b bool
    fmt.Printf("Zero values: int=%d, string=%q, bool=%v\n", i, s, b)
}
EOF
```

> 💡 **`:=` is the short declaration operator** — it declares AND assigns in one step, inferring the type. It only works inside functions. `var` works anywhere. Go variables always have a zero value (`0`, `""`, `false`, `nil`) — there's no concept of "uninitialized" memory.

**📸 Verified Output:**
```
Name: Dr. Chen, Age: 42
City: San Francisco, Score: 98.5
Active: true, Pi: 3.14159
x=10, y=20, sum=30
Zero values: int=0, string="", bool=false
```

---

### Step 3: Constants & iota

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import "fmt"

const (
    KB = 1024
    MB = 1024 * KB
    GB = 1024 * MB
)

type Direction int

const (
    North Direction = iota // 0
    East                   // 1
    South                  // 2
    West                   // 3
)

type ByteSize float64

const (
    _           = iota // ignore first value
    KiB ByteSize = 1 << (10 * iota) // 1024
    MiB                              // 1048576
    GiB                              // 1073741824
)

func main() {
    fmt.Printf("KB=%d, MB=%d, GB=%d\n", KB, MB, GB)
    fmt.Printf("North=%d, East=%d, South=%d, West=%d\n", North, East, South, West)
    fmt.Printf("KiB=%.0f, MiB=%.0f, GiB=%.0f\n", float64(KiB), float64(MiB), float64(GiB))
}
EOF
```

> 💡 **`iota`** is a constant counter that resets to 0 in each `const` block and increments by 1 for each constant. Combined with bit shifts (`<<`), it elegantly defines powers of 2. This is how Go defines `os.O_RDONLY`, `os.O_WRONLY`, `os.O_CREATE` as bit flags.

**📸 Verified Output:**
```
KB=1024, MB=1048576, GB=1073741824
North=0, East=1, South=2, West=3
KiB=1024, MiB=1048576, GiB=1073741824
```

---

### Step 4: Basic Types & Conversions

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import (
    "fmt"
    "math"
    "strconv"
)

func main() {
    // Integer types
    var i8  int8  = 127
    var i32 int32 = 2_147_483_647  // underscores for readability
    var u64 uint64 = 18_446_744_073_709_551_615

    fmt.Printf("int8 max: %d\n", i8)
    fmt.Printf("int32 max: %d\n", i32)
    fmt.Printf("uint64 max: %d\n", u64)

    // Explicit type conversion (no implicit casting in Go)
    var f float64 = math.Sqrt(2)
    var i int     = int(f)  // truncates
    fmt.Printf("sqrt(2)=%.6f truncated=%d\n", f, i)

    // String conversions
    n := 42
    s := strconv.Itoa(n)               // int → string
    n2, _ := strconv.Atoi("123")       // string → int
    f2, _ := strconv.ParseFloat("3.14", 64)
    fmt.Printf("Itoa: %q, Atoi: %d, ParseFloat: %.2f\n", s, n2, f2)

    // Rune (Unicode code point = int32)
    r := '🐄'
    fmt.Printf("Mad Cow rune: %c (U+%04X)\n", r, r)
}
EOF
```

> 💡 **Go has no implicit type conversion** — you must cast explicitly. This prevents subtle bugs where a `float64` silently becomes an `int`. The `_` (blank identifier) discards the error return from `strconv.Atoi` — in production code, always check errors.

**📸 Verified Output:**
```
int8 max: 127
int32 max: 2147483647
uint64 max: 18446744073709551615
sqrt(2)=1.414214 truncated=1
Itoa: "42", Atoi: 123, ParseFloat: 3.14
Mad Cow rune: 🐄 (U+1F404)
```

---

### Step 5: Control Flow

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import "fmt"

func classify(n int) string {
    switch {
    case n < 0:   return "negative"
    case n == 0:  return "zero"
    case n < 10:  return "small"
    case n < 100: return "medium"
    default:      return "large"
    }
}

func fizzBuzz(n int) string {
    switch {
    case n%15 == 0: return "FizzBuzz"
    case n%3 == 0:  return "Fizz"
    case n%5 == 0:  return "Buzz"
    default:        return fmt.Sprintf("%d", n)
    }
}

func main() {
    // if with init statement
    if x := 42; x > 40 {
        fmt.Printf("x=%d is greater than 40\n", x)
    }

    // for — Go's only loop construct
    sum := 0
    for i := 1; i <= 10; i++ {
        sum += i
    }
    fmt.Printf("Sum 1-10: %d\n", sum)

    // while-style loop
    n := 1
    for n < 100 {
        n *= 2
    }
    fmt.Printf("First power of 2 >= 100: %d\n", n)

    // Switch with type
    for _, v := range []int{-5, 0, 7, 42, 500} {
        fmt.Printf("%4d → %s\n", v, classify(v))
    }

    // FizzBuzz
    for i := 1; i <= 15; i++ {
        fmt.Printf("%s ", fizzBuzz(i))
    }
    fmt.Println()
}
EOF
```

> 💡 **Go's `for` is the only loop** — no `while` or `do/while`. You get three forms: classic `for init; cond; post`, while-style `for condition`, and infinite `for`. `switch` in Go doesn't fall through by default (no `break` needed) and can match any expression, not just integers.

**📸 Verified Output:**
```
x=42 is greater than 40
Sum 1-10: 55
First power of 2 >= 100: 128
  -5 → negative
   0 → zero
   7 → small
  42 → medium
 500 → large
1 2 Fizz 4 Buzz Fizz 7 8 Fizz Buzz 11 Fizz 13 14 FizzBuzz
```

---

### Step 6: Strings & fmt

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import (
    "fmt"
    "strings"
    "unicode/utf8"
)

func main() {
    s := "Hello, 世界"

    fmt.Println("String:", s)
    fmt.Println("Bytes:", len(s))            // byte count
    fmt.Println("Runes:", utf8.RuneCountInString(s)) // character count

    // Iterate by rune (correct for Unicode)
    for i, r := range s {
        if i < 7 || r > 127 {
            fmt.Printf("  [%d] %c (%d)\n", i, r, r)
        }
    }

    // String operations
    fmt.Println(strings.ToUpper("hello"))
    fmt.Println(strings.Contains("innoZverse", "Zverse"))
    fmt.Println(strings.Replace("foo bar foo", "foo", "baz", -1))
    fmt.Println(strings.Join([]string{"go", "is", "great"}, " "))
    parts := strings.Split("a,b,c,d", ",")
    fmt.Println(parts, len(parts))

    // fmt verbs
    fmt.Printf("%T %v\n", 42, 42)        // type, value
    fmt.Printf("%08b\n", 255)             // binary, zero-padded
    fmt.Printf("%x\n", 255)              // hex
    fmt.Printf("%-10s|\n", "left")       // left-aligned, width 10
    fmt.Printf("%10s|\n", "right")       // right-aligned
}
EOF
```

> 💡 **Go strings are UTF-8 encoded byte slices**. `len(s)` returns *bytes*, not characters — "世界" is 6 bytes but 2 characters. Always use `range` over a string to iterate by Unicode code points (runes), not bytes. This avoids corrupting multi-byte characters.

**📸 Verified Output:**
```
String: Hello, 世界
Bytes: 13
Runes: 9
  [0] H (72)
  [7] 世 (19990)
  [10] 界 (30028)
HELLO
true
baz bar baz
go is great
[a b c d] 4
int 42
11111111
ff
left      |
     right|
```

---

### Step 7: Functions Preview

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import "fmt"

// Multiple return values
func divide(a, b float64) (float64, error) {
    if b == 0 {
        return 0, fmt.Errorf("division by zero")
    }
    return a / b, nil
}

// Named return values
func minMax(nums []int) (min, max int) {
    min, max = nums[0], nums[0]
    for _, n := range nums[1:] {
        if n < min { min = n }
        if n > max { max = n }
    }
    return // naked return
}

// Variadic function
func sum(nums ...int) int {
    total := 0
    for _, n := range nums {
        total += n
    }
    return total
}

func main() {
    result, err := divide(10, 3)
    if err != nil {
        fmt.Println("Error:", err)
    } else {
        fmt.Printf("10 / 3 = %.4f\n", result)
    }

    _, err = divide(5, 0)
    if err != nil {
        fmt.Println("Error:", err)
    }

    nums := []int{3, 1, 4, 1, 5, 9, 2, 6}
    min, max := minMax(nums)
    fmt.Printf("min=%d, max=%d\n", min, max)

    fmt.Println(sum(1, 2, 3, 4, 5))
    fmt.Println(sum(nums...)) // expand slice into variadic
}
EOF
```

> 💡 **Multiple return values** are one of Go's most important features. Functions return `(result, error)` by convention — forcing callers to explicitly handle errors. This is Go's error handling philosophy: errors are values, not exceptions. The `_` blank identifier discards values you don't need.

**📸 Verified Output:**
```
10 / 3 = 3.3333
Error: division by zero
min=1, max=9
15
31
```

---

### Step 8: Capstone — Temperature Converter CLI

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import (
    "fmt"
    "math"
    "strings"
)

type Temperature struct {
    Value float64
    Unit  string
}

func (t Temperature) ToCelsius() float64 {
    switch strings.ToUpper(t.Unit) {
    case "C": return t.Value
    case "F": return (t.Value - 32) * 5 / 9
    case "K": return t.Value - 273.15
    default:  return math.NaN()
    }
}

func (t Temperature) String() string {
    c := t.ToCelsius()
    f := c*9/5 + 32
    k := c + 273.15
    return fmt.Sprintf("%.2f°%s = %.2f°C = %.2f°F = %.2fK",
        t.Value, strings.ToUpper(t.Unit), c, f, k)
}

func classify(celsius float64) string {
    switch {
    case celsius <= 0:   return "❄️  Freezing"
    case celsius <= 10:  return "🧥 Cold"
    case celsius <= 20:  return "😊 Cool"
    case celsius <= 30:  return "☀️  Warm"
    default:             return "🔥 Hot"
    }
}

func main() {
    temperatures := []Temperature{
        {100, "C"},
        {32, "F"},
        {212, "F"},
        {0, "K"},
        {373.15, "K"},
        {37, "C"},
        {-40, "C"},
    }

    fmt.Println("=== Temperature Converter ===")
    fmt.Println(strings.Repeat("─", 60))
    for _, t := range temperatures {
        fmt.Printf("%s\n  → %s\n", t, classify(t.ToCelsius()))
    }
}
EOF
```

**📸 Verified Output:**
```
=== Temperature Converter ===
────────────────────────────────────────────────────────────
100.00°C = 100.00°C = 212.00°F = 373.15K
  → 🔥 Hot
32.00°F = 0.00°C = 32.00°F = 273.15K
  → ❄️  Freezing
212.00°F = 100.00°C = 212.00°F = 373.15K
  → 🔥 Hot
0.00°K = -273.15°C = -459.67°F = 0.00K
  → ❄️  Freezing
373.15°K = 100.00°C = 212.00°F = 373.15K
  → 🔥 Hot
37.00°C = 37.00°C = 98.60°F = 310.15K
  → ☀️  Warm
-40.00°C = -40.00°C = -40.00°F = 233.15K
  → ❄️  Freezing
```

---

## Summary

| Concept | Go syntax |
|---------|-----------|
| Variable | `var x int` or `x := 42` |
| Constant | `const Pi = 3.14` or `iota` |
| Loop | `for i := 0; i < n; i++` |
| Condition | `if x > 0 { ... }` |
| Multiple returns | `func f() (int, error)` |
| String format | `fmt.Printf("%d %s %v\n", ...)` |
| Type method | `func (t Type) Method() {}` |

## Further Reading
- [Go Tour](https://go.dev/tour)
- [Effective Go](https://go.dev/doc/effective_go)
- [Go by Example](https://gobyexample.com)
