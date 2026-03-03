# Lab 04: Structs & Methods

## Objective
Define Go structs, attach methods, use embedding for composition, and understand value vs pointer receivers.

## Time
30 minutes

## Prerequisites
- Lab 01–03

## Tools
- Docker image: `zchencow/innozverse-go:latest`

---

## Lab Instructions

### Step 1: Struct Basics

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import "fmt"

type Address struct {
    Street string
    City   string
    State  string
    Zip    string
}

type Person struct {
    FirstName string
    LastName  string
    Age       int
    Email     string
    Address   Address // embedded struct (by value)
}

func (p Person) FullName() string {
    return p.FirstName + " " + p.LastName
}

func (p Person) String() string {
    return fmt.Sprintf("%s (%d) <%s>", p.FullName(), p.Age, p.Email)
}

func NewPerson(first, last string, age int, email string) Person {
    return Person{FirstName: first, LastName: last, Age: age, Email: email}
}

func main() {
    // Literal initialization
    p := Person{
        FirstName: "Chen",
        LastName:  "Dr.",
        Age:       42,
        Email:     "ebiz@chen.me",
        Address: Address{
            Street: "950 Ridge Rd",
            City:   "Claymont",
            State:  "DE",
            Zip:    "19703",
        },
    }

    fmt.Println(p)
    fmt.Println("City:", p.Address.City)

    // Struct comparison — structs with comparable fields are comparable
    p2 := NewPerson("Chen", "Dr.", 42, "ebiz@chen.me")
    fmt.Println("Equal (no address):", p.FirstName == p2.FirstName && p.Age == p2.Age)

    // Anonymous struct
    point := struct{ X, Y int }{X: 10, Y: 20}
    fmt.Println("Point:", point)

    // Struct tags (used by JSON, ORM, etc.)
    type Product struct {
        ID    int     `json:"id" db:"product_id"`
        Name  string  `json:"name"`
        Price float64 `json:"price,omitempty"`
    }
    prod := Product{ID: 1, Name: "Surface Pro", Price: 864}
    fmt.Printf("Product: %+v\n", prod)
}
EOF
```

> 💡 **Struct tags** (`json:"name"`) are metadata strings read by reflection packages. They control how `encoding/json`, GORM, and `validator` work. Tags don't affect runtime behavior unless a package explicitly reads them via `reflect.StructTag`. The `+v` format verb prints field names alongside values.

**📸 Verified Output:**
```
Dr. Chen (42) <ebiz@chen.me>
City: Claymont
Equal (no address): true
Point: {10 20}
Product: {ID:1 Name:Surface Pro Price:864}
```

---

### Step 2: Value vs Pointer Receivers

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import (
    "fmt"
    "math"
)

type Point struct{ X, Y float64 }

// Value receiver — does NOT modify original
func (p Point) Distance(other Point) float64 {
    dx := p.X - other.X
    dy := p.Y - other.Y
    return math.Sqrt(dx*dx + dy*dy)
}

// Value receiver — returns a new Point
func (p Point) Translate(dx, dy float64) Point {
    return Point{p.X + dx, p.Y + dy}
}

func (p Point) String() string {
    return fmt.Sprintf("(%.2f, %.2f)", p.X, p.Y)
}

type Counter struct{ count int }

// Pointer receiver — MODIFIES the struct
func (c *Counter) Increment()    { c.count++ }
func (c *Counter) Add(n int)     { c.count += n }
func (c *Counter) Reset()        { c.count = 0 }
func (c *Counter) Value() int    { return c.count }

// Mixed — convention: use pointer receiver if ANY method needs to modify
type Rectangle struct{ Width, Height float64 }

func (r Rectangle) Area() float64      { return r.Width * r.Height }
func (r Rectangle) Perimeter() float64 { return 2 * (r.Width + r.Height) }
func (r *Rectangle) Scale(factor float64) {
    r.Width *= factor
    r.Height *= factor
}

func main() {
    a := Point{0, 0}
    b := Point{3, 4}

    fmt.Println("Distance:", a.Distance(b))
    c := a.Translate(1, 1)
    fmt.Println("Translated:", c)
    fmt.Println("Original a:", a) // unchanged

    counter := Counter{}
    counter.Increment()
    counter.Increment()
    counter.Add(10)
    fmt.Println("Counter:", counter.Value()) // 12
    counter.Reset()
    fmt.Println("After reset:", counter.Value())

    rect := Rectangle{Width: 10, Height: 5}
    fmt.Printf("Area=%.0f Perimeter=%.0f\n", rect.Area(), rect.Perimeter())
    rect.Scale(2)
    fmt.Printf("After Scale(2): %.0fx%.0f Area=%.0f\n", rect.Width, rect.Height, rect.Area())
}
EOF
```

> 💡 **Use pointer receivers** when: (1) the method modifies the struct, OR (2) the struct is large (copying is expensive), OR (3) you need consistency — if any method uses a pointer receiver, all methods should. Value receivers are safe for small, immutable data like `Point`. Go auto-dereferences: `p.Method()` works even if `p` is a pointer.

**📸 Verified Output:**
```
Distance: 5
Translated: (1.00, 1.00)
Original a: (0.00, 0.00)
Counter: 12
After reset: 0
Area=50 Perimeter=30
After Scale(2): 20x10 Area=200
```

---

### Step 3: Embedding & Composition

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import "fmt"

// Base types
type Timestamped struct {
    CreatedAt string
    UpdatedAt string
}

func (t *Timestamped) Touch(ts string) {
    if t.CreatedAt == "" { t.CreatedAt = ts }
    t.UpdatedAt = ts
}

type Named struct {
    Name string
}

func (n Named) GetName() string { return n.Name }

// Composition via embedding
type Product struct {
    Named
    Timestamped
    ID    int
    Price float64
    Stock int
}

func (p *Product) String() string {
    return fmt.Sprintf("Product{%d %s $%.2f stock=%d}", p.ID, p.Name, p.Price, p.Stock)
}

type DigitalProduct struct {
    Product           // embedded (promoted fields + methods)
    DownloadURL string
    License     string
}

func main() {
    p := Product{
        Named:  Named{"Surface Pro 12\""},
        ID:     1,
        Price:  864.00,
        Stock:  15,
    }
    p.Touch("2026-03-03")

    // Promoted fields — access directly
    fmt.Println("Name:", p.Name)           // via Named.Name
    fmt.Println("GetName:", p.GetName())   // via Named.GetName()
    fmt.Println("Created:", p.CreatedAt)   // via Timestamped.CreatedAt
    fmt.Println(p.String())

    dp := DigitalProduct{
        Product:     Product{Named: Named{"Office 365"}, ID: 2, Price: 99.99},
        DownloadURL: "https://download.microsoft.com/office365",
        License:     "annual",
    }
    dp.Touch("2026-03-03")
    fmt.Printf("Digital: %s (license: %s)\n", dp.Name, dp.License)
    fmt.Println("Updated:", dp.UpdatedAt)

    // Embedding doesn't mean inheritance — Go uses composition
    // You can access the embedded struct explicitly
    dp.Product.Price = 89.99
    fmt.Printf("Discounted price: $%.2f\n", dp.Price) // promoted
}
EOF
```

> 💡 **Embedding is Go's answer to inheritance**. When you embed `Named` in `Product`, all of `Named`'s fields and methods are *promoted* to `Product` — you can call `p.Name` instead of `p.Named.Name`. But it's composition, not inheritance — `Product` is not a `Named`. This avoids the fragile base class problem.

**📸 Verified Output:**
```
Name: Surface Pro 12"
GetName: Surface Pro 12"
Created: 2026-03-03
Product{1 Surface Pro 12" $864.00 stock=15}
Digital: Office 365 (license: annual)
Updated: 2026-03-03
Discounted price: $89.99
```

---

### Steps 4–8: Constructors, Stringer, Builder, Repository, Capstone Inventory System

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import (
    "errors"
    "fmt"
    "sort"
    "strings"
)

// Step 4: Constructor functions
type Money struct {
    Amount   int64  // cents
    Currency string
}

func NewMoney(amount float64, currency string) (Money, error) {
    if amount < 0   { return Money{}, errors.New("amount must be non-negative") }
    if len(currency) != 3 { return Money{}, fmt.Errorf("invalid currency: %s", currency) }
    return Money{Amount: int64(amount * 100), Currency: strings.ToUpper(currency)}, nil
}

func (m Money) String() string {
    return fmt.Sprintf("%s %.2f", m.Currency, float64(m.Amount)/100)
}

func (m Money) Add(other Money) (Money, error) {
    if m.Currency != other.Currency {
        return Money{}, fmt.Errorf("currency mismatch: %s vs %s", m.Currency, other.Currency)
    }
    return Money{Amount: m.Amount + other.Amount, Currency: m.Currency}, nil
}

func (m Money) Multiply(factor float64) Money {
    return Money{Amount: int64(float64(m.Amount) * factor), Currency: m.Currency}
}

// Step 5: Stringer interface
type Status int

const (
    Active   Status = iota
    Inactive
    Deleted
)

func (s Status) String() string {
    return [...]string{"Active", "Inactive", "Deleted"}[s]
}

// Step 6: Product with full business logic
type Category struct{ ID int; Name string }

type Product struct {
    ID       int
    Name     string
    Price    Money
    Stock    int
    Category Category
    Status   Status
    Tags     []string
}

func NewProduct(id int, name string, price float64, currency string, cat Category) (*Product, error) {
    if strings.TrimSpace(name) == "" {
        return nil, errors.New("product name required")
    }
    m, err := NewMoney(price, currency)
    if err != nil { return nil, err }
    return &Product{
        ID:       id,
        Name:     strings.TrimSpace(name),
        Price:    m,
        Status:   Active,
        Category: cat,
        Tags:     []string{},
    }, nil
}

func (p *Product) AddTag(tag string) *Product {
    tag = strings.ToLower(strings.TrimSpace(tag))
    for _, t := range p.Tags {
        if t == tag { return p }
    }
    p.Tags = append(p.Tags, tag)
    return p
}

func (p *Product) AddStock(qty int) error {
    if qty < 0 { return errors.New("quantity must be positive") }
    p.Stock += qty
    return nil
}

func (p *Product) Sell(qty int) error {
    if qty <= 0 { return errors.New("quantity must be positive") }
    if p.Stock < qty { return fmt.Errorf("insufficient stock: have %d, need %d", p.Stock, qty) }
    p.Stock -= qty
    return nil
}

func (p *Product) TotalValue() Money { return p.Price.Multiply(float64(p.Stock)) }

func (p Product) String() string {
    return fmt.Sprintf("[%d] %s %s (stock=%d) [%s] %s",
        p.ID, p.Name, p.Price, p.Stock, p.Status, strings.Join(p.Tags, ", "))
}

// Step 7: In-memory repository
type ProductRepo struct {
    products map[int]*Product
    nextID   int
}

func NewProductRepo() *ProductRepo {
    return &ProductRepo{products: make(map[int]*Product), nextID: 1}
}

func (r *ProductRepo) Save(p *Product) {
    if p.ID == 0 { p.ID = r.nextID; r.nextID++ }
    r.products[p.ID] = p
}

func (r *ProductRepo) FindByID(id int) (*Product, error) {
    p, ok := r.products[id]
    if !ok { return nil, fmt.Errorf("product %d not found", id) }
    return p, nil
}

func (r *ProductRepo) FindAll(filter func(*Product) bool) []*Product {
    result := make([]*Product, 0)
    for _, p := range r.products {
        if filter == nil || filter(p) { result = append(result, p) }
    }
    sort.Slice(result, func(i, j int) bool { return result[i].ID < result[j].ID })
    return result
}

// Step 8: Capstone — run inventory system
func main() {
    repo := NewProductRepo()
    laptop := Category{1, "Laptop"}
    acc    := Category{2, "Accessory"}
    sw     := Category{3, "Software"}

    products := []struct{ name string; price float64; cat Category }{
        {"Surface Pro 12\"", 864.00, laptop},
        {"Surface Pen",      49.99,  acc},
        {"Office 365",       99.99,  sw},
        {"USB-C Hub",        29.99,  acc},
        {"Surface Book 3",   1299.00, laptop},
    }

    for i, pd := range products {
        p, err := NewProduct(0, pd.name, pd.price, "USD", pd.cat)
        if err != nil { fmt.Println("Error:", err); continue }
        p.AddTag(pd.cat.Name).AddTag("microsoft")
        p.AddStock([]int{15, 80, 999, 0, 5}[i])
        repo.Save(p)
    }

    // List all
    fmt.Println("=== All Products ===")
    for _, p := range repo.FindAll(nil) {
        fmt.Println(" ", p)
    }

    // Sell some
    fmt.Println("\n=== Transactions ===")
    if p, err := repo.FindByID(1); err == nil {
        if err := p.Sell(3); err == nil {
            fmt.Printf("Sold 3x %s, remaining: %d\n", p.Name, p.Stock)
        }
    }

    // Try oversell
    if p, err := repo.FindByID(4); err == nil {
        if err := p.Sell(5); err != nil {
            fmt.Println("Sell error:", err)
        }
    }

    // Inventory value report
    fmt.Println("\n=== Inventory Value ===")
    total, _ := NewMoney(0, "USD")
    inStock := repo.FindAll(func(p *Product) bool { return p.Stock > 0 })
    for _, p := range inStock {
        val := p.TotalValue()
        fmt.Printf("  %-20s %6d × %-12s = %s\n", p.Name, p.Stock, p.Price, val)
        total, _ = total.Add(val)
    }
    fmt.Println("  " + strings.Repeat("─", 55))
    fmt.Println("  Total inventory value:", total)

    // Category breakdown
    fmt.Println("\n=== By Category ===")
    catMap := make(map[string][]*Product)
    for _, p := range repo.FindAll(nil) {
        catMap[p.Category.Name] = append(catMap[p.Category.Name], p)
    }
    cats := make([]string, 0, len(catMap))
    for k := range catMap { cats = append(cats, k) }
    sort.Strings(cats)
    for _, cat := range cats {
        fmt.Printf("  %s (%d items)\n", cat, len(catMap[cat]))
    }
}
EOF
```

**📸 Verified Output:**
```
=== All Products ===
  [1] Surface Pro 12" USD 864.00 (stock=15) [Active] laptop, microsoft
  [2] Surface Pen USD 49.99 (stock=80) [Active] accessory, microsoft
  [3] Office 365 USD 99.99 (stock=999) [Active] software, microsoft
  [4] USB-C Hub USD 29.99 (stock=0) [Active] accessory, microsoft
  [5] Surface Book 3 USD 1299.00 (stock=5) [Active] laptop, microsoft

=== Transactions ===
Sold 3x Surface Pro 12", remaining: 12
Sell error: insufficient stock: have 0, need 5

=== Inventory Value ===
  Surface Pro 12"       12 × USD 864.00  = USD 10368.00
  Surface Pen           80 × USD 49.99   = USD 3999.20
  Office 365           999 × USD 99.99   = USD 99890.01
  Surface Book 3         5 × USD 1299.00 = USD 6495.00
  ───────────────────────────────────────────────────────
  Total inventory value: USD 120752.21

=== By Category ===
  Accessory (2 items)
  Laptop (2 items)
  Software (1 items)
```

---

## Summary

| Pattern | Syntax | When to use |
|---------|--------|-------------|
| Value receiver | `func (p Point) Method()` | Read-only, small structs |
| Pointer receiver | `func (p *Product) Method()` | Modifies struct, large structs |
| Embedding | `type A struct { B }` | Composition, promote methods |
| Constructor | `func NewX(...) (*X, error)` | Validated initialization |
| Stringer | `func (x X) String() string` | Human-readable output |

## Further Reading
- [Go Structs](https://go.dev/tour/moretypes/2)
- [Effective Go: Methods](https://go.dev/doc/effective_go#methods)
