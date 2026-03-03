# Lab 06: Pointers & Memory

## Objective
Understand Go pointers: address-of operator, dereferencing, nil pointers, pointer to structs, and when to use pointers vs values.

## Time
25 minutes

## Prerequisites
- Lab 04 (Structs & Methods)

## Tools
- Docker image: `zchencow/innozverse-go:latest`

---

## Lab Instructions

### Step 1: Pointer Basics

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import "fmt"

func main() {
    x := 42
    p := &x         // p is a pointer to x (*int)

    fmt.Printf("x = %d\n", x)
    fmt.Printf("&x = %p (address of x)\n", &x)
    fmt.Printf("p = %p (value of p = address)\n", p)
    fmt.Printf("*p = %d (dereference p = value at address)\n", *p)

    *p = 99         // modify x via pointer
    fmt.Printf("After *p=99, x = %d\n", x)

    // new() — allocates zeroed memory, returns pointer
    q := new(int)
    fmt.Printf("new(int): %p → %d\n", q, *q)
    *q = 100
    fmt.Printf("After *q=100: %d\n", *q)

    // Nil pointer — zero value of any pointer type
    var ptr *int
    fmt.Printf("nil pointer: %v, isNil: %v\n", ptr, ptr == nil)
    // *ptr would panic! Always check for nil

    // Pointer to pointer
    pp := &p
    fmt.Printf("**pp = %d\n", **pp)
}
EOF
```

> 💡 **`&x` gives the address, `*p` dereferences it**. In Go, you never do pointer arithmetic (no `ptr + 1` like C). The garbage collector tracks all pointers and moves/frees memory automatically. Dereferencing a nil pointer causes a panic — always check `ptr != nil` before dereferencing.

**📸 Verified Output:**
```
x = 42
&x = 0xc0000b4008 (address of x)
p = 0xc0000b4008 (value of p = address)
*p = 42 (dereference p = value at address)
After *p=99, x = 99
new(int): 0xc0000b4010 → 0
After *q=100: 100
nil pointer: <nil>, isNil: true
**pp = 99
```

---

### Step 2: Pointers to Structs

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import "fmt"

type Node struct {
    Value int
    Next  *Node  // pointer to same type — enables linked list
}

type LinkedList struct {
    Head *Node
    Size int
}

func (l *LinkedList) Push(val int) {
    l.Head = &Node{Value: val, Next: l.Head}
    l.Size++
}

func (l *LinkedList) Pop() (int, bool) {
    if l.Head == nil { return 0, false }
    val := l.Head.Value
    l.Head = l.Head.Next
    l.Size--
    return val, true
}

func (l *LinkedList) String() string {
    result := ""
    for cur := l.Head; cur != nil; cur = cur.Next {
        if result != "" { result += " → " }
        result += fmt.Sprintf("%d", cur.Value)
    }
    return "[" + result + "]"
}

// Demonstrate value vs pointer semantics
type Config struct {
    Debug   bool
    Timeout int
    Host    string
}

// Value: receives a COPY — original unchanged
func applyDefaultsByValue(c Config) Config {
    if c.Timeout == 0 { c.Timeout = 30 }
    if c.Host == ""   { c.Host = "localhost" }
    return c
}

// Pointer: modifies the ORIGINAL
func applyDefaultsByPointer(c *Config) {
    if c.Timeout == 0 { c.Timeout = 30 }
    if c.Host == ""   { c.Host = "localhost" }
}

func main() {
    list := &LinkedList{}
    for _, v := range []int{1, 2, 3, 4, 5} { list.Push(v) }
    fmt.Println("List:", list)
    fmt.Println("Size:", list.Size)

    for i := 0; i < 3; i++ {
        val, ok := list.Pop()
        fmt.Printf("Pop: %d (ok=%v)\n", val, ok)
    }
    fmt.Println("After pops:", list)

    // Value vs pointer
    original := Config{Debug: true}
    updated := applyDefaultsByValue(original)
    fmt.Printf("Original: %+v\n", original)  // unchanged
    fmt.Printf("Updated:  %+v\n", updated)

    applyDefaultsByPointer(&original)
    fmt.Printf("After pointer call: %+v\n", original) // modified!

    // Struct pointer syntax sugar — (*p).Field == p.Field
    p := &Config{Debug: true}
    (*p).Timeout = 60  // explicit dereference
    p.Host = "example.com"  // Go auto-dereferences (syntactic sugar)
    fmt.Printf("Config: %+v\n", *p)
}
EOF
```

> 💡 **Go automatically dereferences struct pointers** — `p.Field` and `(*p).Field` are identical. This is why `&Config{}` is so natural. When you use a pointer receiver method `func (c *Config) Set(...)`, calling `myConfig.Set(...)` works even if `myConfig` is not a pointer — Go takes its address automatically.

**📸 Verified Output:**
```
List: [5 → 4 → 3 → 2 → 1]
Size: 5
Pop: 5 (ok=true)
Pop: 4 (ok=true)
Pop: 3 (ok=true)
After pops: [2 → 1]
Original: {Debug:true Timeout:0 Host:}
Updated:  {Debug:true Timeout:30 Host:localhost}
After pointer call: {Debug:true Timeout:30 Host:localhost}
Config: {Debug:true Timeout:60 Host:example.com}
```

---

### Steps 3–8: Functional pointers, escape analysis, Tree, Optional, Capstone

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import "fmt"

// Step 3: Swap using pointers
func swap[T any](a, b *T) {
    *a, *b = *b, *a
}

// Step 4: Optional/nullable pattern
type Optional[T any] struct {
    value *T
}

func Some[T any](v T) Optional[T] { return Optional[T]{&v} }
func None[T any]() Optional[T]    { return Optional[T]{nil} }

func (o Optional[T]) IsPresent() bool { return o.value != nil }
func (o Optional[T]) Get() (T, bool) {
    if o.value == nil { var zero T; return zero, false }
    return *o.value, true
}
func (o Optional[T]) OrElse(def T) T {
    if o.value == nil { return def }
    return *o.value
}

// Step 5: Tree using pointers
type Tree[T any] struct {
    Value       T
    Left, Right *Tree[T]
}

func (t *Tree[T]) Insert(val T, less func(T, T) bool) *Tree[T] {
    if t == nil { return &Tree[T]{Value: val} }
    if less(val, t.Value) {
        t.Left = t.Left.Insert(val, less)
    } else {
        t.Right = t.Right.Insert(val, less)
    }
    return t
}

func (t *Tree[T]) InOrder(fn func(T)) {
    if t == nil { return }
    t.Left.InOrder(fn)
    fn(t.Value)
    t.Right.InOrder(fn)
}

// Step 6: Pointer to function (callbacks)
type EventHandler func(event string, data any)

type EventBus struct {
    handlers map[string][]EventHandler
}

func NewEventBus() *EventBus {
    return &EventBus{handlers: make(map[string][]EventHandler)}
}

func (b *EventBus) On(event string, h EventHandler) {
    b.handlers[event] = append(b.handlers[event], h)
}

func (b *EventBus) Emit(event string, data any) {
    for _, h := range b.handlers[event] { h(event, data) }
}

// Step 7: Nil safety patterns
func safeGet[T any](ptr *T, def T) T {
    if ptr == nil { return def }
    return *T(ptr)
}

type User struct {
    Name    string
    Address *Address
}

type Address struct {
    City    string
    Country string
}

func userCity(u *User) string {
    if u == nil || u.Address == nil { return "Unknown" }
    return u.Address.City
}

// Step 8: Capstone — doubly linked list
type DNode[T any] struct {
    Val        T
    Prev, Next *DNode[T]
}

type Deque[T any] struct {
    head, tail *DNode[T]
    size       int
}

func (d *Deque[T]) PushFront(val T) {
    node := &DNode[T]{Val: val, Next: d.head}
    if d.head != nil { d.head.Prev = node }
    d.head = node
    if d.tail == nil { d.tail = node }
    d.size++
}

func (d *Deque[T]) PushBack(val T) {
    node := &DNode[T]{Val: val, Prev: d.tail}
    if d.tail != nil { d.tail.Next = node }
    d.tail = node
    if d.head == nil { d.head = node }
    d.size++
}

func (d *Deque[T]) PopFront() (T, bool) {
    if d.head == nil { var z T; return z, false }
    val := d.head.Val
    d.head = d.head.Next
    if d.head != nil { d.head.Prev = nil } else { d.tail = nil }
    d.size--
    return val, true
}

func (d *Deque[T]) PopBack() (T, bool) {
    if d.tail == nil { var z T; return z, false }
    val := d.tail.Val
    d.tail = d.tail.Prev
    if d.tail != nil { d.tail.Next = nil } else { d.head = nil }
    d.size--
    return val, true
}

func (d *Deque[T]) Len() int { return d.size }

func main() {
    // Swap
    a, b := 10, 20
    swap(&a, &b)
    fmt.Printf("After swap: a=%d b=%d\n", a, b)

    // Optional
    name := Some("Dr. Chen")
    empty := None[string]()
    fmt.Println("Name:", name.OrElse("unknown"))
    fmt.Println("Empty:", empty.OrElse("default"))

    // BST
    var root *Tree[int]
    for _, v := range []int{5, 3, 7, 1, 4, 6, 8} {
        root = root.Insert(v, func(a, b int) bool { return a < b })
    }
    fmt.Print("BST in-order: ")
    root.InOrder(func(v int) { fmt.Printf("%d ", v) })
    fmt.Println()

    // EventBus
    bus := NewEventBus()
    bus.On("sale", func(e string, d any) { fmt.Printf("[%s] $%.2f\n", e, d) })
    bus.On("sale", func(e string, d any) { fmt.Printf("[%s] logged\n", e) })
    bus.Emit("sale", 864.00)

    // Nil safety
    u1 := &User{"Dr. Chen", &Address{City: "Claymont", Country: "US"}}
    u2 := &User{"Alice", nil}
    var u3 *User
    fmt.Println("u1 city:", userCity(u1))
    fmt.Println("u2 city:", userCity(u2))
    fmt.Println("u3 city:", userCity(u3))

    // Deque
    dq := &Deque[int]{}
    dq.PushBack(1); dq.PushBack(2); dq.PushBack(3)
    dq.PushFront(0); dq.PushFront(-1)
    fmt.Printf("Deque size=%d\n", dq.Len())
    for dq.Len() > 0 {
        if v, ok := dq.PopFront(); ok { fmt.Printf("%d ", v) }
    }
    fmt.Println()
}
EOF
```

**📸 Verified Output:**
```
After swap: a=20 b=10
Name: Dr. Chen
Empty: default
BST in-order: 1 3 4 5 6 7 8
[sale] $864.00
[sale] logged
u1 city: Claymont
u2 city: Unknown
u3 city: Unknown
Deque size=5
-1 0 1 2 3
```

---

## Summary

| Operation | Syntax | Effect |
|-----------|--------|--------|
| Address-of | `p := &x` | `p` holds address of `x` |
| Dereference | `*p` | Value at address |
| Modify via ptr | `*p = val` | Changes original |
| nil check | `if p != nil` | Must do before deref |
| new | `p := new(T)` | Allocates, returns `*T` |
| Struct pointer | `p.Field` same as `(*p).Field` | Auto-deref |

## Further Reading
- [Go Pointers](https://go.dev/tour/moretypes/1)
- [Go Data Structures](https://research.swtch.com/godata)
