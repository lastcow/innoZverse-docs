# Lab 11: JSON Encoding

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm golang:1.22-alpine sh`

## Overview

The `encoding/json` package handles JSON serialization and deserialization. Struct tags control field names, omission, and custom behaviour. Streaming encoders/decoders handle large data sets without loading everything into memory.

## Step 1: Marshal — Struct to JSON

```go
package main

import (
    "encoding/json"
    "fmt"
    "time"
)

type User struct {
    ID        int       `json:"id"`
    Name      string    `json:"name"`
    Email     string    `json:"email,omitempty"` // omit if empty
    CreatedAt time.Time `json:"created_at"`
    Password  string    `json:"-"`               // never marshal
}

func main() {
    u := User{
        ID:        1,
        Name:      "Alice",
        CreatedAt: time.Date(2024, 1, 15, 0, 0, 0, 0, time.UTC),
        Password:  "secret", // will not appear in JSON
    }

    b, err := json.MarshalIndent(u, "", "  ")
    if err != nil {
        panic(err)
    }
    fmt.Println(string(b))
}
```

Output:
```json
{
  "id": 1,
  "name": "Alice",
  "created_at": "2024-01-15T00:00:00Z"
}
```

> 💡 **Tip:** `omitempty` skips zero values: `""`, `0`, `false`, `nil`. Tag `json:"-"` excludes the field entirely.

## Step 2: Unmarshal — JSON to Struct

```go
package main

import (
    "encoding/json"
    "fmt"
)

type Address struct {
    Street string `json:"street"`
    City   string `json:"city"`
    Zip    string `json:"zip"`
}

type Person struct {
    Name    string  `json:"name"`
    Age     int     `json:"age"`
    Address Address `json:"address"`
    Tags    []string `json:"tags"`
}

func main() {
    raw := `{
        "name": "Bob",
        "age": 30,
        "address": {"street": "123 Main St", "city": "Goville", "zip": "10001"},
        "tags": ["developer", "gopher"]
    }`

    var p Person
    if err := json.Unmarshal([]byte(raw), &p); err != nil {
        panic(err)
    }

    fmt.Printf("Name: %s\n", p.Name)
    fmt.Printf("City: %s\n", p.Address.City)
    fmt.Printf("Tags: %v\n", p.Tags)
}
```

## Step 3: Custom MarshalJSON / UnmarshalJSON

```go
package main

import (
    "encoding/json"
    "fmt"
    "time"
)

// Custom date format: "2006-01-02"
type Date struct{ time.Time }

func (d Date) MarshalJSON() ([]byte, error) {
    return json.Marshal(d.Format("2006-01-02"))
}

func (d *Date) UnmarshalJSON(data []byte) error {
    var s string
    if err := json.Unmarshal(data, &s); err != nil {
        return err
    }
    t, err := time.Parse("2006-01-02", s)
    if err != nil {
        return err
    }
    d.Time = t
    return nil
}

type Event struct {
    Name string `json:"name"`
    Date Date   `json:"date"`
}

func main() {
    e := Event{
        Name: "Go Conference",
        Date: Date{time.Date(2024, 11, 10, 0, 0, 0, 0, time.UTC)},
    }

    b, _ := json.Marshal(e)
    fmt.Println(string(b)) // {"name":"Go Conference","date":"2024-11-10"}

    var e2 Event
    json.Unmarshal(b, &e2)
    fmt.Printf("parsed: %s on %s\n", e2.Name, e2.Date.Format("Jan 2, 2006"))
}
```

## Step 4: Streaming with json.Encoder / json.Decoder

```go
package main

import (
    "encoding/json"
    "fmt"
    "os"
    "strings"
)

type LogEntry struct {
    Level   string `json:"level"`
    Message string `json:"message"`
    Code    int    `json:"code,omitempty"`
}

func main() {
    // Encoder — write JSON lines to stdout
    enc := json.NewEncoder(os.Stdout)
    entries := []LogEntry{
        {"INFO", "server started", 0},
        {"WARN", "slow query", 500},
        {"ERROR", "connection refused", 503},
    }
    for _, e := range entries {
        enc.Encode(e) // writes one JSON line + newline
    }

    // Decoder — read multiple JSON objects from a stream
    fmt.Println("--- decoded ---")
    stream := `{"level":"DEBUG","message":"connecting"}
{"level":"INFO","message":"connected"}
{"level":"ERROR","message":"timeout","code":408}`

    dec := json.NewDecoder(strings.NewReader(stream))
    for dec.More() {
        var e LogEntry
        if err := dec.Decode(&e); err != nil {
            fmt.Println("decode error:", err)
            break
        }
        fmt.Printf("[%s] %s (code=%d)\n", e.Level, e.Message, e.Code)
    }
}
```

## Step 5: json.RawMessage — Deferred Parsing

```go
package main

import (
    "encoding/json"
    "fmt"
)

type Envelope struct {
    Type    string          `json:"type"`
    Payload json.RawMessage `json:"payload"` // raw bytes, parse later
}

type UserPayload  struct{ Name string `json:"name"` }
type OrderPayload struct{ Amount float64 `json:"amount"` }

func handleEvent(data string) {
    var env Envelope
    json.Unmarshal([]byte(data), &env)

    switch env.Type {
    case "user":
        var u UserPayload
        json.Unmarshal(env.Payload, &u)
        fmt.Printf("user event: name=%s\n", u.Name)
    case "order":
        var o OrderPayload
        json.Unmarshal(env.Payload, &o)
        fmt.Printf("order event: amount=%.2f\n", o.Amount)
    }
}

func main() {
    handleEvent(`{"type":"user","payload":{"name":"Alice"}}`)
    handleEvent(`{"type":"order","payload":{"amount":49.99}}`)
}
```

## Step 6: json.Number for Precise Numbers

```go
package main

import (
    "encoding/json"
    "fmt"
    "strings"
)

func main() {
    // Default: large numbers become float64 and lose precision
    raw := `{"id": 9007199254740993}` // larger than float64 can represent exactly

    var defaultMap map[string]any
    json.Unmarshal([]byte(raw), &defaultMap)
    fmt.Printf("default: %v (type: %T)\n", defaultMap["id"], defaultMap["id"])

    // With UseNumber: preserves as string
    dec := json.NewDecoder(strings.NewReader(raw))
    dec.UseNumber()
    var numMap map[string]any
    dec.Decode(&numMap)
    n := numMap["id"].(json.Number)
    fmt.Println("json.Number:", n.String())
    i64, _ := n.Int64()
    fmt.Println("as int64:", i64)
}
```

## Step 7: Map and Slice JSON

```go
package main

import (
    "encoding/json"
    "fmt"
)

func main() {
    // Marshal map
    m := map[string]any{
        "name":   "Alice",
        "scores": []int{95, 87, 92},
        "active": true,
        "ratio":  3.14,
    }
    b, _ := json.MarshalIndent(m, "", "  ")
    fmt.Println(string(b))

    // Unmarshal into map
    raw := `{"key1":"val1","key2":42,"key3":true}`
    var result map[string]any
    json.Unmarshal([]byte(raw), &result)
    for k, v := range result {
        fmt.Printf("%s: %v (%T)\n", k, v, v)
    }
}
```

## Step 8: Capstone — JSON API Response Builder

```go
package main

import (
    "encoding/json"
    "fmt"
    "time"
)

type Meta struct {
    Total   int    `json:"total"`
    Page    int    `json:"page"`
    PerPage int    `json:"per_page"`
}

type APIResponse[T any] struct {
    Success bool      `json:"success"`
    Data    T         `json:"data"`
    Meta    *Meta     `json:"meta,omitempty"`
    Error   string    `json:"error,omitempty"`
    Timestamp time.Time `json:"timestamp"`
}

func successResponse[T any](data T, meta *Meta) APIResponse[T] {
    return APIResponse[T]{
        Success:   true,
        Data:      data,
        Meta:      meta,
        Timestamp: time.Now().UTC().Truncate(time.Second),
    }
}

func errorResponse[T any](msg string) APIResponse[T] {
    return APIResponse[T]{
        Success:   false,
        Error:     msg,
        Timestamp: time.Now().UTC().Truncate(time.Second),
    }
}

type Product struct {
    ID    int     `json:"id"`
    Name  string  `json:"name"`
    Price float64 `json:"price"`
}

func main() {
    products := []Product{
        {1, "Widget", 9.99},
        {2, "Gadget", 19.99},
        {3, "Doohickey", 4.99},
    }

    resp := successResponse(products, &Meta{Total: 3, Page: 1, PerPage: 10})
    b, _ := json.MarshalIndent(resp, "", "  ")
    fmt.Println(string(b))

    errResp := errorResponse[[]Product]("not found")
    b2, _ := json.MarshalIndent(errResp, "", "  ")
    fmt.Println(string(b2))
}
```

📸 **Verified Output:**
```
=== Marshal ===
{
  "id": 1,
  "name": "Alice",
  "created_at": "2024-01-15T00:00:00Z"
}

=== omitempty ===
{"id":2,"name":"Bob","created_at":"0001-01-01T00:00:00Z"}

=== Streaming ===
decoded: map[name:Alice]
decoded: map[name:Bob]
decoded: map[name:Charlie]

=== RawMessage ===
type: user
raw payload: {"id":1,"name":"Alice"}
```

## Summary

| Feature | Struct Tag / API | Notes |
|---|---|---|
| Field name | `json:"name"` | Lowercase in JSON |
| Omit if zero | `json:"name,omitempty"` | Skips `""`, `0`, `false`, `nil` |
| Exclude field | `json:"-"` | Never serialized |
| Marshal | `json.Marshal(v)` | Returns `[]byte, error` |
| Pretty print | `json.MarshalIndent(v, "", "  ")` | Human-readable |
| Unmarshal | `json.Unmarshal(data, &v)` | `v` must be a pointer |
| Stream encode | `json.NewEncoder(w).Encode(v)` | Writes to `io.Writer` |
| Stream decode | `json.NewDecoder(r).Decode(&v)` | Reads from `io.Reader` |
| Raw defer | `json.RawMessage` | Delay parsing of nested object |
| Big ints | `dec.UseNumber()` + `json.Number` | Avoid float64 precision loss |
| Custom format | `MarshalJSON() / UnmarshalJSON()` | Implement on type |
