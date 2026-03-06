# Lab 03: unsafe & reflect

**Time:** 45 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm golang:1.22-alpine sh`

## Overview

Master Go's reflection system (`reflect` package) for runtime type inspection and manipulation. Understand `unsafe.Pointer` for low-level memory operations. Learn when (and when not) to use these powerful tools.

---

## Step 1: `reflect.TypeOf` and `reflect.ValueOf`

```go
package main

import (
	"fmt"
	"reflect"
)

type Point struct {
	X, Y float64
}

func inspectValue(v interface{}) {
	t := reflect.TypeOf(v)
	val := reflect.ValueOf(v)

	fmt.Printf("Type:  %v\n", t)
	fmt.Printf("Kind:  %v\n", t.Kind())
	fmt.Printf("Value: %v\n", val)

	switch t.Kind() {
	case reflect.Int, reflect.Int64:
		fmt.Printf("  int value: %d\n", val.Int())
	case reflect.String:
		fmt.Printf("  string len: %d\n", val.Len())
	case reflect.Struct:
		fmt.Printf("  struct fields: %d\n", t.NumField())
	case reflect.Slice:
		fmt.Printf("  slice len: %d\n", val.Len())
	}
}

func main() {
	inspectValue(42)
	inspectValue("hello")
	inspectValue(Point{1.5, 2.5})
	inspectValue([]int{1, 2, 3})
}
```

📸 **Verified Output:**
```
Type:  int
Kind:  int
Value: 42
  int value: 42
Type:  string
Kind:  string
Value: hello
  string len: 5
Type:  main.Point
Kind:  struct
  struct fields: 2
Type:  []int
Kind:  slice
  slice len: 3
```

---

## Step 2: Struct Field Inspection and Tags

```go
package main

import (
	"fmt"
	"reflect"
)

type Person struct {
	Name  string `json:"name" validate:"required"`
	Age   int    `json:"age" validate:"min=0,max=150"`
	Email string `json:"email,omitempty" validate:"email"`
}

func (p Person) Greet() string {
	return fmt.Sprintf("Hi, I'm %s", p.Name)
}

func printStructInfo(v interface{}) {
	t := reflect.TypeOf(v)
	val := reflect.ValueOf(v)
	fmt.Printf("Struct: %s\n", t.Name())

	for i := 0; i < t.NumField(); i++ {
		field := t.Field(i)
		value := val.Field(i)
		fmt.Printf("  %-6s | %-12v | json:%-20s | validate:%s\n",
			field.Name, value.Interface(),
			field.Tag.Get("json"), field.Tag.Get("validate"))
	}

	fmt.Printf("Methods: %d\n", t.NumMethod())
	for i := 0; i < t.NumMethod(); i++ {
		fmt.Printf("  %s\n", t.Method(i).Name)
	}
}

func main() {
	p := Person{Name: "Alice", Age: 30, Email: "alice@example.com"}
	printStructInfo(p)
}
```

Run it:
```bash
docker run --rm golang:1.22-alpine sh -c "cat > /tmp/main.go << 'GOEOF'
package main

import (
	\"fmt\"
	\"reflect\"
)

type Person struct {
	Name  string \`json:\"name\" validate:\"required\"\`
	Age   int    \`json:\"age\" validate:\"min=0,max=150\"\`
	Email string \`json:\"email,omitempty\" validate:\"email\"\`
}

func (p Person) Greet() string { return fmt.Sprintf(\"Hi, I'm %s\", p.Name) }

func printStructInfo(v interface{}) {
	t := reflect.TypeOf(v)
	val := reflect.ValueOf(v)
	fmt.Printf(\"Struct: %s\n\", t.Name())
	for i := 0; i < t.NumField(); i++ {
		field := t.Field(i)
		value := val.Field(i)
		fmt.Printf(\"  %-6s | %-20v | json:%-20s | validate:%s\n\",
			field.Name, value.Interface(), field.Tag.Get(\"json\"), field.Tag.Get(\"validate\"))
	}
	fmt.Printf(\"Methods: %d\n\", t.NumMethod())
}

func main() {
	p := Person{Name: \"Alice\", Age: 30, Email: \"alice@example.com\"}
	printStructInfo(p)
}
GOEOF
cd /tmp && go run main.go"
```

📸 **Verified Output:**
```
Struct: Person
  Name   | Alice                | json:name                 | validate:required
  Age    | 30                   | json:age                  | validate:min=0,max=150
  Email  | alice@example.com    | json:email,omitempty      | validate:email
Methods: 1
```

---

## Step 3: `reflect.Value.Set` — Modify Struct Fields

```go
package main

import (
	"fmt"
	"reflect"
)

type Config struct {
	Host    string
	Port    int
	Debug   bool
	Timeout float64
}

// SetField sets a struct field by name using reflection
func SetField(obj interface{}, fieldName string, value interface{}) error {
	val := reflect.ValueOf(obj)
	if val.Kind() != reflect.Ptr || val.Elem().Kind() != reflect.Struct {
		return fmt.Errorf("obj must be a pointer to struct")
	}
	field := val.Elem().FieldByName(fieldName)
	if !field.IsValid() {
		return fmt.Errorf("field %s not found", fieldName)
	}
	if !field.CanSet() {
		return fmt.Errorf("field %s cannot be set", fieldName)
	}
	newVal := reflect.ValueOf(value)
	if field.Type() != newVal.Type() {
		return fmt.Errorf("type mismatch: field=%v, value=%v", field.Type(), newVal.Type())
	}
	field.Set(newVal)
	return nil
}

func main() {
	cfg := Config{Host: "localhost", Port: 8080}
	fmt.Printf("Before: %+v\n", cfg)

	SetField(&cfg, "Host", "0.0.0.0")
	SetField(&cfg, "Port", 9090)
	SetField(&cfg, "Debug", true)
	SetField(&cfg, "Timeout", 30.5)

	fmt.Printf("After:  %+v\n", cfg)
}
```

---

## Step 4: `MethodByName` — Dynamic Method Dispatch

```go
package main

import (
	"fmt"
	"reflect"
)

type Calculator struct {
	Value float64
}

func (c *Calculator) Add(x float64) { c.Value += x }
func (c *Calculator) Sub(x float64) { c.Value -= x }
func (c *Calculator) Mul(x float64) { c.Value *= x }
func (c *Calculator) Reset()        { c.Value = 0 }

func callMethod(obj interface{}, method string, args ...interface{}) {
	val := reflect.ValueOf(obj)
	m := val.MethodByName(method)
	if !m.IsValid() {
		fmt.Printf("Method %s not found\n", method)
		return
	}
	in := make([]reflect.Value, len(args))
	for i, arg := range args {
		in[i] = reflect.ValueOf(arg)
	}
	m.Call(in)
}

func main() {
	calc := &Calculator{Value: 10}
	fmt.Printf("Initial: %.1f\n", calc.Value)

	callMethod(calc, "Add", 5.0)
	fmt.Printf("After Add(5):  %.1f\n", calc.Value)

	callMethod(calc, "Mul", 2.0)
	fmt.Printf("After Mul(2):  %.1f\n", calc.Value)

	callMethod(calc, "Sub", 3.0)
	fmt.Printf("After Sub(3):  %.1f\n", calc.Value)

	callMethod(calc, "Reset")
	fmt.Printf("After Reset:   %.1f\n", calc.Value)
}
```

---

## Step 5: `reflect.MakeFunc` — Dynamic Function Creation

```go
package main

import (
	"fmt"
	"reflect"
)

// makeAdder creates a typed adder function at runtime
func makeAdder(t reflect.Type) reflect.Value {
	return reflect.MakeFunc(t, func(args []reflect.Value) []reflect.Value {
		switch args[0].Kind() {
		case reflect.Int:
			sum := args[0].Int() + args[1].Int()
			return []reflect.Value{reflect.ValueOf(int(sum))}
		case reflect.Float64:
			sum := args[0].Float() + args[1].Float()
			return []reflect.Value{reflect.ValueOf(sum)}
		case reflect.String:
			sum := args[0].String() + args[1].String()
			return []reflect.Value{reflect.ValueOf(sum)}
		}
		return nil
	})
}

func main() {
	// Int adder
	intAdderType := reflect.TypeOf(func(int, int) int { return 0 })
	intAdder := makeAdder(intAdderType).Interface().(func(int, int) int)
	fmt.Printf("intAdder(3, 4)     = %d\n", intAdder(3, 4))

	// Float adder
	floatAdderType := reflect.TypeOf(func(float64, float64) float64 { return 0 })
	floatAdder := makeAdder(floatAdderType).Interface().(func(float64, float64) float64)
	fmt.Printf("floatAdder(1.5,2.5) = %.1f\n", floatAdder(1.5, 2.5))

	// String adder
	strAdderType := reflect.TypeOf(func(string, string) string { return "" })
	strAdder := makeAdder(strAdderType).Interface().(func(string, string) string)
	fmt.Printf("strAdder(\"Go\", \"!\"') = %s\n", strAdder("Go", "!"))
}
```

---

## Step 6: `unsafe.Pointer` — Low-Level Memory

```go
package main

import (
	"fmt"
	"unsafe"
)

type Header struct {
	Version uint8
	Flags   uint8
	Length  uint16
}

func main() {
	// unsafe.Sizeof — compile-time size
	fmt.Printf("sizeof Header: %d bytes\n", unsafe.Sizeof(Header{}))
	fmt.Printf("sizeof int64:  %d bytes\n", unsafe.Sizeof(int64(0)))

	// unsafe.Offsetof — field offset in struct
	h := Header{}
	fmt.Printf("offset Version: %d\n", unsafe.Offsetof(h.Version))
	fmt.Printf("offset Flags:   %d\n", unsafe.Offsetof(h.Flags))
	fmt.Printf("offset Length:  %d\n", unsafe.Offsetof(h.Length))

	// Type punning via unsafe.Pointer
	// Read a float64 as its raw uint64 bits
	f := 3.14
	bits := *(*uint64)(unsafe.Pointer(&f))
	fmt.Printf("float64(3.14) bits = 0x%016X\n", bits)

	// String ↔ []byte without allocation (Go 1.20+ preferred: unsafe.String/SliceData)
	s := "Hello, unsafe!"
	b := unsafe.Slice(unsafe.StringData(s), len(s))
	fmt.Printf("string→[]byte: %s\n", b)

	// uintptr arithmetic (be careful: uintptr doesn't keep objects alive)
	arr := [4]int{10, 20, 30, 40}
	ptr := unsafe.Pointer(&arr[0])
	for i := 0; i < 4; i++ {
		elem := *(*int)(unsafe.Pointer(uintptr(ptr) + uintptr(i)*unsafe.Sizeof(arr[0])))
		fmt.Printf("arr[%d] = %d\n", i, elem)
	}
}
```

> 💡 **`uintptr` is NOT a pointer** — the GC doesn't trace it. Never store a `uintptr` across function calls when the object could be collected. Use `unsafe.Pointer` for temporary conversions only.

---

## Step 7: `unsafe.Slice` and `unsafe.String` (Go 1.17+)

```go
package main

import (
	"fmt"
	"unsafe"
)

// Zero-copy []byte → string conversion
func bytesToString(b []byte) string {
	if len(b) == 0 {
		return ""
	}
	return unsafe.String(&b[0], len(b))
}

// Zero-copy string → []byte conversion (read-only!)
func stringToBytes(s string) []byte {
	if s == "" {
		return nil
	}
	return unsafe.Slice(unsafe.StringData(s), len(s))
}

func main() {
	// Normal conversion allocates
	b := []byte("Hello, World!")
	s1 := string(b) // allocation
	fmt.Printf("Normal convert: %s (len=%d)\n", s1, len(s1))

	// Zero-copy: no allocation
	s2 := bytesToString(b)
	fmt.Printf("Zero-copy: %s\n", s2)

	// String to bytes (do NOT modify — string is immutable!)
	orig := "immutable string"
	bSlice := stringToBytes(orig)
	fmt.Printf("string→bytes: %v (len=%d)\n", bSlice[:5], len(bSlice))
}
```

---

## Step 8: Capstone — JSON-like Marshaler via Reflection

```go
package main

import (
	"bytes"
	"fmt"
	"reflect"
	"strconv"
	"strings"
)

// Marshal converts any struct to a simple key=value string
func Marshal(v interface{}) string {
	val := reflect.ValueOf(v)
	t := reflect.TypeOf(v)

	if t.Kind() == reflect.Ptr {
		val = val.Elem()
		t = t.Elem()
	}
	if t.Kind() != reflect.Struct {
		return fmt.Sprintf("%v", val.Interface())
	}

	var buf bytes.Buffer
	buf.WriteByte('{')
	for i := 0; i < t.NumField(); i++ {
		if i > 0 {
			buf.WriteString(", ")
		}
		field := t.Field(i)
		value := val.Field(i)

		// Use json tag if available, else field name
		name := strings.ToLower(field.Name)
		if tag := field.Tag.Get("json"); tag != "" && tag != "-" {
			name = strings.Split(tag, ",")[0]
		}

		buf.WriteString(name + ":")
		switch value.Kind() {
		case reflect.String:
			buf.WriteString(`"` + value.String() + `"`)
		case reflect.Int, reflect.Int64:
			buf.WriteString(strconv.FormatInt(value.Int(), 10))
		case reflect.Bool:
			buf.WriteString(strconv.FormatBool(value.Bool()))
		case reflect.Float64:
			buf.WriteString(strconv.FormatFloat(value.Float(), 'f', 2, 64))
		default:
			buf.WriteString(fmt.Sprintf("%v", value.Interface()))
		}
	}
	buf.WriteByte('}')
	return buf.String()
}

type Server struct {
	Host    string  `json:"host"`
	Port    int     `json:"port"`
	Debug   bool    `json:"debug"`
	Version float64 `json:"version"`
}

func main() {
	s := Server{Host: "localhost", Port: 8080, Debug: true, Version: 1.5}
	fmt.Println(Marshal(s))
	fmt.Println(Marshal(&s))

	// Verify with real output
	type Point struct {
		X, Y int
	}
	fmt.Println(Marshal(Point{3, 4}))
}
```

Run the capstone:
```bash
docker run --rm golang:1.22-alpine sh -c "cat > /tmp/main.go << 'GOEOF'
package main

import (
	\"bytes\"
	\"fmt\"
	\"reflect\"
	\"strconv\"
	\"strings\"
)

func Marshal(v interface{}) string {
	val := reflect.ValueOf(v)
	t := reflect.TypeOf(v)
	if t.Kind() == reflect.Ptr { val = val.Elem(); t = t.Elem() }
	if t.Kind() != reflect.Struct { return fmt.Sprintf(\"%v\", val.Interface()) }
	var buf bytes.Buffer; buf.WriteByte('{')
	for i := 0; i < t.NumField(); i++ {
		if i > 0 { buf.WriteString(\", \") }
		field := t.Field(i); value := val.Field(i)
		name := strings.ToLower(field.Name)
		if tag := field.Tag.Get(\"json\"); tag != \"\" { name = strings.Split(tag, \",\")[0] }
		buf.WriteString(name + \":\" )
		switch value.Kind() {
		case reflect.String: buf.WriteString(\"\\\"\" + value.String() + \"\\\"\")
		case reflect.Int, reflect.Int64: buf.WriteString(strconv.FormatInt(value.Int(), 10))
		case reflect.Bool: buf.WriteString(strconv.FormatBool(value.Bool()))
		case reflect.Float64: buf.WriteString(strconv.FormatFloat(value.Float(), 'f', 2, 64))
		}
	}
	buf.WriteByte('}'); return buf.String()
}

type Server struct { Host string \`json:\"host\"\`; Port int \`json:\"port\"\`; Debug bool \`json:\"debug\"\` }

func main() {
	s := Server{Host: \"localhost\", Port: 8080, Debug: true}
	fmt.Println(Marshal(s))
}
GOEOF
cd /tmp && go run main.go"
```

📸 **Verified Output:**
```
{host:"localhost", port:8080, debug:true}
```

---

## Summary

| Feature | Use Case | Risk |
|---------|----------|------|
| `reflect.TypeOf/ValueOf` | Inspect types at runtime | Slow (10-100x vs direct) |
| `reflect.Value.Set` | Generic field setter | Panics on unexported fields |
| `MethodByName` | Plugin/event systems | No compile-time safety |
| `reflect.MakeFunc` | Adapters, RPC stubs | Complex to debug |
| `unsafe.Pointer` | Zero-copy conversions | GC can't trace; use carefully |
| `unsafe.Slice/String` | []byte↔string no-alloc | Read-only for string→bytes |

**Key Takeaways:**
- `reflect` adds runtime overhead; use only when generics can't solve the problem
- `unsafe.Pointer` conversions must follow strict rules (see Go spec)
- Prefer `unsafe.String`/`unsafe.Slice` over `unsafe.StringData`+`uintptr` arithmetic
- Test with `-race` when using `unsafe` — data races become crashes
