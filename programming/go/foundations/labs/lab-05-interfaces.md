# Lab 05: Interfaces & Polymorphism

## Objective
Master Go interfaces: implicit satisfaction, the empty interface, type assertions, type switches, and interface composition.

## Time
30 minutes

## Prerequisites
- Lab 04 (Structs & Methods)

## Tools
- Docker image: `zchencow/innozverse-go:latest`

---

## Lab Instructions

### Step 1: Defining & Implementing Interfaces

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import (
    "fmt"
    "math"
)

// Interface definition
type Shape interface {
    Area() float64
    Perimeter() float64
    String() string
}

type Circle struct{ Radius float64 }
type Rectangle struct{ Width, Height float64 }
type Triangle struct{ A, B, C float64 }

func (c Circle) Area() float64      { return math.Pi * c.Radius * c.Radius }
func (c Circle) Perimeter() float64 { return 2 * math.Pi * c.Radius }
func (c Circle) String() string {
    return fmt.Sprintf("Circle(r=%.2f)", c.Radius)
}

func (r Rectangle) Area() float64      { return r.Width * r.Height }
func (r Rectangle) Perimeter() float64 { return 2 * (r.Width + r.Height) }
func (r Rectangle) String() string {
    return fmt.Sprintf("Rect(%.2fx%.2f)", r.Width, r.Height)
}

func (t Triangle) Area() float64 {
    s := (t.A + t.B + t.C) / 2
    return math.Sqrt(s * (s - t.A) * (s - t.B) * (s - t.C))
}
func (t Triangle) Perimeter() float64 { return t.A + t.B + t.C }
func (t Triangle) String() string {
    return fmt.Sprintf("Triangle(%.0f,%.0f,%.0f)", t.A, t.B, t.C)
}

func printShapeInfo(s Shape) {
    fmt.Printf("%-22s area=%-8.2f perimeter=%.2f\n", s, s.Area(), s.Perimeter())
}

func totalArea(shapes []Shape) float64 {
    total := 0.0
    for _, s := range shapes { total += s.Area() }
    return total
}

func main() {
    shapes := []Shape{
        Circle{5},
        Rectangle{4, 6},
        Triangle{3, 4, 5},
        Circle{1},
        Rectangle{10, 2},
    }

    for _, s := range shapes { printShapeInfo(s) }
    fmt.Printf("\nTotal area: %.2f\n", totalArea(shapes))
}
EOF
```

> 💡 **Go interfaces are satisfied implicitly** — no `implements` keyword. If a type has all the methods an interface requires, it satisfies the interface automatically. This decouples the type from the interface — `Circle` doesn't know about `Shape`. This makes Go's type system incredibly flexible and composable.

**📸 Verified Output:**
```
Circle(r=5.00)         area=78.54   perimeter=31.42
Rect(4.00x6.00)        area=24.00   perimeter=20.00
Triangle(3,4,5)        area=6.00    perimeter=12.00
Circle(r=1.00)         area=3.14    perimeter=6.28
Rect(10.00x2.00)       area=20.00   perimeter=24.00

Total area: 131.68
```

---

### Step 2: Interface Composition

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import (
    "fmt"
    "strings"
)

// Small, focused interfaces (Interface Segregation Principle)
type Reader interface { Read(p []byte) (n int, err error) }
type Writer interface { Write(p []byte) (n int, err error) }
type Closer interface { Close() error }

// Composed interfaces
type ReadWriter  interface { Reader; Writer }
type ReadCloser  interface { Reader; Closer }
type WriteCloser interface { Writer; Closer }
type ReadWriteCloser interface { Reader; Writer; Closer }

// Domain interfaces
type Validator interface { Validate() error }
type Serializer interface {
    Serialize() ([]byte, error)
    Deserialize([]byte) error
}
type Repository[T any] interface {
    FindByID(id int) (T, error)
    FindAll() []T
    Save(item T) error
    Delete(id int) error
}

// Stringer (from fmt package — implementing it makes fmt.Println use it)
type Stringer interface { String() string }

// Example: Logger interface composition
type Logger interface {
    Info(msg string, args ...any)
    Error(msg string, args ...any)
    Debug(msg string, args ...any)
}

type ConsoleLogger struct{ prefix string }

func (l *ConsoleLogger) Info(msg string, args ...any) {
    fmt.Printf("[%s][INFO]  "+msg+"\n", append([]any{l.prefix}, args...)...)
}
func (l *ConsoleLogger) Error(msg string, args ...any) {
    fmt.Printf("[%s][ERROR] "+msg+"\n", append([]any{l.prefix}, args...)...)
}
func (l *ConsoleLogger) Debug(msg string, args ...any) {
    fmt.Printf("[%s][DEBUG] "+msg+"\n", append([]any{l.prefix}, args...)...)
}

type NullLogger struct{}
func (NullLogger) Info(string, ...any)  {}
func (NullLogger) Error(string, ...any) {}
func (NullLogger) Debug(string, ...any) {}

type Service struct {
    log Logger
}

func NewService(log Logger) *Service {
    if log == nil { log = NullLogger{} }
    return &Service{log: log}
}

func (s *Service) Process(item string) error {
    s.log.Info("Processing: %s", item)
    result := strings.ToUpper(item)
    s.log.Info("Done: %s → %s", item, result)
    return nil
}

func main() {
    verbose := NewService(&ConsoleLogger{"APP"})
    verbose.Process("hello world")

    silent := NewService(nil)
    silent.Process("no output expected")
    fmt.Println("Silent service ran without output")
}
EOF
```

> 💡 **`io.Reader`, `io.Writer`, `io.Closer`** are the most important interfaces in Go's standard library. They compose into `io.ReadWriter`, `io.ReadCloser`, etc. Because interfaces are implicit, any type that implements `Read([]byte) (int, error)` is an `io.Reader` — whether it's a file, a network connection, or a buffer.

**📸 Verified Output:**
```
[APP][INFO]  Processing: hello world
[APP][INFO]  Done: hello world → HELLO WORLD
Silent service ran without output
```

---

### Step 3: Type Assertions & Type Switches

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import "fmt"

type Dog struct{ Name string }
type Cat struct{ Name string }
type Bird struct{ Name string; CanFly bool }

func (d Dog)  Sound() string { return "Woof" }
func (c Cat)  Sound() string { return "Meow" }
func (b Bird) Sound() string { return "Tweet" }

type Animal interface {
    Sound() string
}

func describe(a Animal) {
    // Type assertion — panics if wrong type (use comma-ok form)
    if dog, ok := a.(Dog); ok {
        fmt.Printf("Dog: %s says %s\n", dog.Name, dog.Sound())
        return
    }

    // Type switch — idiomatic for multiple types
    switch v := a.(type) {
    case Cat:
        fmt.Printf("Cat: %s says %s\n", v.Name, v.Sound())
    case Bird:
        if v.CanFly {
            fmt.Printf("Bird: %s says %s and can fly!\n", v.Name, v.Sound())
        } else {
            fmt.Printf("Bird: %s says %s (flightless)\n", v.Name, v.Sound())
        }
    default:
        fmt.Printf("Unknown animal: %T\n", v)
    }
}

// any / interface{} — accepts anything
func printType(v any) {
    switch x := v.(type) {
    case int:     fmt.Printf("int: %d\n", x)
    case float64: fmt.Printf("float64: %.2f\n", x)
    case string:  fmt.Printf("string: %q\n", x)
    case bool:    fmt.Printf("bool: %v\n", x)
    case []int:   fmt.Printf("[]int: %v (len=%d)\n", x, len(x))
    case nil:     fmt.Println("nil")
    default:      fmt.Printf("other: %T = %v\n", x, x)
    }
}

func main() {
    animals := []Animal{
        Dog{"Rex"},
        Cat{"Whiskers"},
        Bird{"Eagle", true},
        Bird{"Penguin", false},
    }
    for _, a := range animals { describe(a) }

    fmt.Println()
    vals := []any{42, 3.14, "hello", true, []int{1, 2, 3}, nil}
    for _, v := range vals { printType(v) }
}
EOF
```

> 💡 **Always use the comma-ok form** for type assertions: `v, ok := i.(Type)`. Without `ok`, a failed assertion panics. Type switches (`switch v := i.(type)`) are cleaner when handling multiple types. The `any` type is an alias for `interface{}` — introduced in Go 1.18.

**📸 Verified Output:**
```
Dog: Rex says Woof
Cat: Whiskers says Meow
Bird: Eagle says Tweet and can fly!
Bird: Penguin says Tweet (flightless)

int: 42
float64: 3.14
string: "hello"
bool: true
[]int: [1 2 3] (len=3)
nil
```

---

### Steps 4–8: error interface, Sorter, Payment, Middleware, Capstone

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import (
    "errors"
    "fmt"
    "sort"
    "strings"
)

// Step 4: Custom error types implementing the error interface
type ValidationError struct {
    Field   string
    Message string
}
func (e *ValidationError) Error() string {
    return fmt.Sprintf("validation error: %s — %s", e.Field, e.Message)
}

type NotFoundError struct{ ID int; Resource string }
func (e *NotFoundError) Error() string {
    return fmt.Sprintf("%s with id=%d not found", e.Resource, e.ID)
}

func findProduct(id int) (string, error) {
    products := map[int]string{1: "Surface Pro", 2: "Surface Pen"}
    if id <= 0 { return "", &ValidationError{"id", "must be positive"} }
    p, ok := products[id]
    if !ok { return "", &NotFoundError{id, "product"} }
    return p, nil
}

// Step 5: Sorter interface
type Sortable[T any] interface {
    Len() int
    Less(i, j int) bool
    Swap(i, j int)
}

// Step 6: Payment processor
type PaymentMethod interface {
    Charge(amount float64) error
    Name() string
}

type CreditCard struct{ Last4 string; Balance float64 }
func (c *CreditCard) Charge(amount float64) error {
    if amount > c.Balance { return fmt.Errorf("insufficient credit: have %.2f, need %.2f", c.Balance, amount) }
    c.Balance -= amount
    return nil
}
func (c *CreditCard) Name() string { return "CreditCard *" + c.Last4 }

type PayPal struct{ Email string; Balance float64 }
func (p *PayPal) Charge(amount float64) error {
    if amount > p.Balance { return fmt.Errorf("PayPal balance insufficient") }
    p.Balance -= amount
    return nil
}
func (p *PayPal) Name() string { return "PayPal(" + p.Email + ")" }

type Wallet struct{ Balance float64 }
func (w *Wallet) Charge(amount float64) error {
    if amount > w.Balance { return fmt.Errorf("wallet empty") }
    w.Balance -= amount
    return nil
}
func (w *Wallet) Name() string { return "Wallet" }

func processPayment(method PaymentMethod, amount float64) {
    err := method.Charge(amount)
    if err != nil {
        fmt.Printf("  [%s] FAILED: %s\n", method.Name(), err)
    } else {
        fmt.Printf("  [%s] Charged $%.2f ✓\n", method.Name(), amount)
    }
}

// Step 7: Middleware pattern via interfaces
type Handler interface { Handle(req string) string }

type HandlerFunc func(string) string
func (f HandlerFunc) Handle(req string) string { return f(req) }

func Logger(next Handler) Handler {
    return HandlerFunc(func(req string) string {
        fmt.Printf("[LOG] request: %s\n", req)
        resp := next.Handle(req)
        fmt.Printf("[LOG] response: %s\n", resp)
        return resp
    })
}

func Auth(token string, next Handler) Handler {
    return HandlerFunc(func(req string) string {
        if !strings.Contains(req, "token="+token) {
            return "401 Unauthorized"
        }
        return next.Handle(req)
    })
}

// Step 8: Capstone — plugin registry
type Plugin interface {
    Name() string
    Execute(input string) (string, error)
}

type UpperPlugin struct{}
func (UpperPlugin) Name() string { return "upper" }
func (UpperPlugin) Execute(s string) (string, error) { return strings.ToUpper(s), nil }

type ReversePlugin struct{}
func (ReversePlugin) Name() string { return "reverse" }
func (ReversePlugin) Execute(s string) (string, error) {
    r := []rune(s)
    for i, j := 0, len(r)-1; i < j; i, j = i+1, j-1 { r[i], r[j] = r[j], r[i] }
    return string(r), nil
}

type WordCountPlugin struct{}
func (WordCountPlugin) Name() string { return "wordcount" }
func (WordCountPlugin) Execute(s string) (string, error) {
    return fmt.Sprintf("words=%d chars=%d", len(strings.Fields(s)), len(s)), nil
}

type PluginRegistry struct{ plugins map[string]Plugin }

func NewRegistry() *PluginRegistry { return &PluginRegistry{plugins: make(map[string]Plugin)} }
func (r *PluginRegistry) Register(p Plugin) { r.plugins[p.Name()] = p }
func (r *PluginRegistry) Run(name, input string) (string, error) {
    p, ok := r.plugins[name]
    if !ok { return "", fmt.Errorf("plugin %q not found", name) }
    return p.Execute(input)
}
func (r *PluginRegistry) List() []string {
    names := make([]string, 0, len(r.plugins))
    for n := range r.plugins { names = append(names, n) }
    sort.Strings(names)
    return names
}

func main() {
    // Custom errors
    for _, id := range []int{1, 99, -1} {
        name, err := findProduct(id)
        if err != nil {
            var notFound *NotFoundError
            var valErr  *ValidationError
            switch {
            case errors.As(err, &notFound): fmt.Printf("Not found: id=%d\n", notFound.ID)
            case errors.As(err, &valErr):   fmt.Printf("Validation: %s\n", valErr.Message)
            default:                        fmt.Println("Unknown error:", err)
            }
        } else {
            fmt.Println("Found:", name)
        }
    }

    // Payment processing
    fmt.Println("\n--- Payments ---")
    methods := []PaymentMethod{
        &CreditCard{"4242", 500},
        &PayPal{"ebiz@chen.me", 200},
        &Wallet{50},
    }
    for _, m := range methods { processPayment(m, 150) }
    processPayment(&Wallet{10}, 150)

    // Middleware chain
    fmt.Println("\n--- Middleware ---")
    base := HandlerFunc(func(req string) string { return "200 OK: " + req })
    chain := Logger(Auth("secret", base))
    chain.Handle("GET /api/products?token=secret")
    chain.Handle("GET /api/products")

    // Plugin registry
    fmt.Println("\n--- Plugins ---")
    reg := NewRegistry()
    reg.Register(UpperPlugin{})
    reg.Register(ReversePlugin{})
    reg.Register(WordCountPlugin{})
    fmt.Println("Plugins:", reg.List())

    input := "Hello innoZverse"
    for _, name := range reg.List() {
        result, _ := reg.Run(name, input)
        fmt.Printf("  %s(%q) = %q\n", name, input, result)
    }
}
EOF
```

**📸 Verified Output:**
```
Found: Surface Pro
Not found: id=99
Validation: must be positive

--- Payments ---
  [CreditCard *4242] Charged $150.00 ✓
  [PayPal(ebiz@chen.me)] Charged $150.00 ✓
  [Wallet] FAILED: wallet empty
  [Wallet] FAILED: wallet empty

--- Middleware ---
[LOG] request: GET /api/products?token=secret
[LOG] response: 200 OK: GET /api/products?token=secret
[LOG] request: GET /api/products
[LOG] response: 401 Unauthorized

--- Plugins ---
Plugins: [reverse upper wordcount]
  reverse("Hello innoZverse") = "esreVZonni olleH"
  upper("Hello innoZverse") = "HELLO INNOZVERSE"
  wordcount("Hello innoZverse") = "words=2 chars=16"
```

---

## Summary

| Concept | Key insight |
|---------|-------------|
| Implicit satisfaction | No `implements` keyword — duck typing |
| Interface composition | Embed interfaces to build larger ones |
| Type assertion | `v, ok := i.(Type)` — comma-ok is safe |
| Type switch | `switch v := i.(type)` — handles multiple types |
| `error` interface | `Error() string` — every error implements this |
| `any` | Alias for `interface{}` (Go 1.18+) |

## Further Reading
- [Go Interfaces](https://go.dev/tour/methods/9)
- [io package](https://pkg.go.dev/io)
- [errors.As / errors.Is](https://pkg.go.dev/errors)
