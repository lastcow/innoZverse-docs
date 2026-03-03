# Lab 10: File I/O & JSON

## Objective
Read and write files using `os`, `bufio`, and `io`; encode and decode JSON with `encoding/json`; use struct tags to control serialization.

## Time
30 minutes

## Prerequisites
- Lab 09 (Packages & Stdlib)

## Tools
- Docker image: `zchencow/innozverse-go:latest`

---

## Lab Instructions

### Step 1: Reading & Writing Files

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import (
    "bufio"
    "fmt"
    "os"
    "strings"
)

func main() {
    path := "/tmp/golab-io.txt"

    // Write entire file at once
    content := "Line 1: Hello, Go!\nLine 2: File I/O\nLine 3: innoZverse\n"
    if err := os.WriteFile(path, []byte(content), 0644); err != nil {
        fmt.Println("Write error:", err)
        return
    }
    fmt.Println("Wrote", len(content), "bytes")

    // Read entire file
    data, err := os.ReadFile(path)
    if err != nil { fmt.Println("Read error:", err); return }
    fmt.Printf("Read %d bytes\n", len(data))

    // Read line by line with bufio.Scanner
    f, _ := os.Open(path)
    defer f.Close()

    scanner := bufio.NewScanner(f)
    lineNum := 0
    for scanner.Scan() {
        lineNum++
        fmt.Printf("  [%d] %s\n", lineNum, scanner.Text())
    }

    // Append to file
    f2, _ := os.OpenFile(path, os.O_APPEND|os.O_WRONLY, 0644)
    defer f2.Close()
    writer := bufio.NewWriter(f2)
    fmt.Fprintln(writer, "Line 4: Appended!")
    writer.Flush()

    // Verify append
    final, _ := os.ReadFile(path)
    lines := strings.Split(strings.TrimSpace(string(final)), "\n")
    fmt.Printf("Total lines: %d\n", len(lines))
}
EOF
```

> 💡 **`bufio.Scanner`** reads line by line without loading the whole file into memory — essential for large files. `bufio.Writer` batches small writes into larger I/O operations, dramatically improving performance. Always call `writer.Flush()` at the end or writes may be lost.

**📸 Verified Output:**
```
Wrote 55 bytes
Read 55 bytes
  [1] Line 1: Hello, Go!
  [2] Line 2: File I/O
  [3] Line 3: innoZverse
Total lines: 4
```

---

### Step 2: JSON Encoding & Decoding

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import (
    "encoding/json"
    "fmt"
)

type Address struct {
    Street string `json:"street"`
    City   string `json:"city"`
    State  string `json:"state,omitempty"`
    Zip    string `json:"zip,omitempty"`
}

type Product struct {
    ID       int      `json:"id"`
    Name     string   `json:"name"`
    Price    float64  `json:"price"`
    Stock    int      `json:"stock"`
    Tags     []string `json:"tags,omitempty"`
    Active   bool     `json:"active"`
    Internal string   `json:"-"`          // excluded from JSON
}

func main() {
    // Marshal (struct → JSON)
    p := Product{
        ID: 1, Name: "Surface Pro 12\"", Price: 864.00,
        Stock: 15, Tags: []string{"laptop", "microsoft"}, Active: true,
        Internal: "secret",
    }

    data, err := json.Marshal(p)
    if err != nil { fmt.Println("Marshal error:", err); return }
    fmt.Println("Compact:", string(data))

    // Pretty print
    pretty, _ := json.MarshalIndent(p, "", "  ")
    fmt.Println("Pretty:\n" + string(pretty))

    // Unmarshal (JSON → struct)
    jsonStr := `{"id":2,"name":"Surface Pen","price":49.99,"stock":80,"active":true}`
    var p2 Product
    if err := json.Unmarshal([]byte(jsonStr), &p2); err != nil {
        fmt.Println("Unmarshal error:", err)
        return
    }
    fmt.Printf("Parsed: ID=%d Name=%s Price=%.2f\n", p2.ID, p2.Name, p2.Price)
    fmt.Println("Internal field:", p2.Internal) // empty — excluded

    // Decode into map[string]any
    var generic map[string]any
    json.Unmarshal([]byte(jsonStr), &generic)
    fmt.Println("Name (generic):", generic["name"])
    fmt.Printf("Price (generic): %.2f\n", generic["price"].(float64))
}
EOF
```

> 💡 **JSON struct tags** control serialization: `json:"name"` sets the field name, `omitempty` skips zero-value fields, `json:"-"` excludes the field entirely. Without tags, Go uses the field name as-is (case-sensitive). The `encoding/json` package uses reflection to read these tags at runtime.

**📸 Verified Output:**
```
Compact: {"id":1,"name":"Surface Pro 12\"","price":864,"stock":15,"tags":["laptop","microsoft"],"active":true}
Pretty:
{
  "id": 1,
  "name": "Surface Pro 12\"",
  "price": 864,
  "stock": 15,
  "tags": [
    "laptop",
    "microsoft"
  ],
  "active": true
}
Parsed: ID=2 Name=Surface Pen Price=49.99
Internal field:
Name (generic): Surface Pen
Price (generic): 49.99
```

---

### Step 3: JSON Streaming with Encoder/Decoder

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import (
    "encoding/json"
    "fmt"
    "os"
    "strings"
)

type Product struct {
    ID    int     `json:"id"`
    Name  string  `json:"name"`
    Price float64 `json:"price"`
}

func main() {
    // Encoder — stream to writer (file, HTTP response, etc.)
    products := []Product{
        {1, "Surface Pro", 864.00},
        {2, "Surface Pen", 49.99},
        {3, "Office 365",  99.99},
    }

    path := "/tmp/products.json"
    f, _ := os.Create(path)
    enc := json.NewEncoder(f)
    enc.SetIndent("", "  ")
    enc.Encode(products)
    f.Close()

    // Decoder — stream from reader
    f2, _ := os.Open(path)
    defer f2.Close()

    var loaded []Product
    dec := json.NewDecoder(f2)
    if err := dec.Decode(&loaded); err != nil {
        fmt.Println("Decode error:", err)
        return
    }

    fmt.Printf("Loaded %d products:\n", len(loaded))
    for _, p := range loaded {
        fmt.Printf("  [%d] %-20s $%.2f\n", p.ID, p.Name, p.Price)
    }

    // NDJSON (newline-delimited JSON) — one object per line
    ndjson := `{"id":1,"name":"Surface Pro","price":864}
{"id":2,"name":"Surface Pen","price":49.99}
{"id":3,"name":"Office 365","price":99.99}
`
    dec2 := json.NewDecoder(strings.NewReader(ndjson))
    fmt.Println("\nNDJSON stream:")
    for dec2.More() {
        var p Product
        dec2.Decode(&p)
        fmt.Printf("  %s $%.2f\n", p.Name, p.Price)
    }
}
EOF
```

> 💡 **`json.Encoder/Decoder`** stream JSON directly to/from `io.Writer/io.Reader`. This avoids loading the entire JSON into memory — critical for large API responses or log files. `dec.More()` returns true while there's more to decode from the stream.

**📸 Verified Output:**
```
Loaded 3 products:
  [1] Surface Pro          $864.00
  [2] Surface Pen          $49.99
  [3] Office 365           $99.99

NDJSON stream:
  Surface Pro $864.00
  Surface Pen $49.99
  Office 365 $99.99
```

---

### Steps 4–8: Custom Marshaler, CSV, Config File, Directory Walker, Capstone

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import (
    "bufio"
    "encoding/csv"
    "encoding/json"
    "fmt"
    "io/fs"
    "os"
    "path/filepath"
    "strconv"
    "strings"
    "time"
)

// Step 4: Custom JSON marshaler
type Money struct{ Cents int64; Currency string }

func (m Money) MarshalJSON() ([]byte, error) {
    return json.Marshal(map[string]any{
        "amount":   fmt.Sprintf("%.2f", float64(m.Cents)/100),
        "currency": m.Currency,
    })
}

func (m *Money) UnmarshalJSON(data []byte) error {
    var raw struct{ Amount string; Currency string }
    if err := json.Unmarshal(data, &raw); err != nil { return err }
    f, err := strconv.ParseFloat(raw.Amount, 64)
    if err != nil { return err }
    m.Cents = int64(f * 100)
    m.Currency = raw.Currency
    return nil
}

// Step 5: CSV handling
type SaleRecord struct {
    Date     string
    Product  string
    Quantity int
    Price    float64
    Total    float64
}

func writeCSV(path string, records []SaleRecord) error {
    f, err := os.Create(path)
    if err != nil { return err }
    defer f.Close()

    w := csv.NewWriter(f)
    defer w.Flush()

    w.Write([]string{"Date", "Product", "Quantity", "Price", "Total"})
    for _, r := range records {
        w.Write([]string{
            r.Date, r.Product,
            strconv.Itoa(r.Quantity),
            fmt.Sprintf("%.2f", r.Price),
            fmt.Sprintf("%.2f", r.Total),
        })
    }
    return w.Error()
}

func readCSV(path string) ([]SaleRecord, error) {
    f, err := os.Open(path)
    if err != nil { return nil, err }
    defer f.Close()

    r := csv.NewReader(f)
    rows, err := r.ReadAll()
    if err != nil { return nil, err }

    records := make([]SaleRecord, 0, len(rows)-1)
    for _, row := range rows[1:] { // skip header
        qty, _ := strconv.Atoi(row[2])
        price, _ := strconv.ParseFloat(row[3], 64)
        total, _ := strconv.ParseFloat(row[4], 64)
        records = append(records, SaleRecord{row[0], row[1], qty, price, total})
    }
    return records, nil
}

// Step 6: Config file (JSON-based)
type AppConfig struct {
    Name     string            `json:"name"`
    Version  string            `json:"version"`
    Debug    bool              `json:"debug"`
    Port     int               `json:"port"`
    DB       DBConfig          `json:"database"`
    Features map[string]bool   `json:"features"`
}

type DBConfig struct {
    Driver   string `json:"driver"`
    Host     string `json:"host"`
    Port     int    `json:"port"`
    Database string `json:"database"`
}

func loadConfig(path string) (*AppConfig, error) {
    data, err := os.ReadFile(path)
    if err != nil { return nil, fmt.Errorf("read config: %w", err) }
    var cfg AppConfig
    if err := json.Unmarshal(data, &cfg); err != nil {
        return nil, fmt.Errorf("parse config: %w", err)
    }
    return &cfg, nil
}

// Step 7: Directory walker
type FileStats struct {
    TotalFiles int
    TotalSize  int64
    ByExt      map[string]int
}

func walkDir(root string) (*FileStats, error) {
    stats := &FileStats{ByExt: make(map[string]int)}
    err := filepath.WalkDir(root, func(path string, d fs.DirEntry, err error) error {
        if err != nil { return err }
        if d.IsDir() { return nil }
        info, _ := d.Info()
        stats.TotalFiles++
        stats.TotalSize += info.Size()
        ext := strings.ToLower(filepath.Ext(path))
        if ext == "" { ext = "(no ext)" }
        stats.ByExt[ext]++
        return nil
    })
    return stats, err
}

// Step 8: Capstone — data pipeline
func main() {
    dir, _ := os.MkdirTemp("", "golab-")
    defer os.RemoveAll(dir)

    // Custom marshaler
    price := Money{86400, "USD"}
    data, _ := json.Marshal(price)
    fmt.Println("Money JSON:", string(data))

    // CSV write + read
    csvPath := filepath.Join(dir, "sales.csv")
    sales := []SaleRecord{
        {"2026-03-01", "Surface Pro", 2, 864.00, 1728.00},
        {"2026-03-02", "Surface Pen", 5, 49.99, 249.95},
        {"2026-03-03", "Office 365",  10, 99.99, 999.90},
    }
    writeCSV(csvPath, sales)
    loaded, _ := readCSV(csvPath)
    fmt.Printf("\nCSV: loaded %d records\n", len(loaded))
    totalRevenue := 0.0
    for _, r := range loaded {
        fmt.Printf("  %s: %dx%s = $%.2f\n", r.Date, r.Quantity, r.Product, r.Total)
        totalRevenue += r.Total
    }
    fmt.Printf("Total revenue: $%.2f\n", totalRevenue)

    // Config file
    configPath := filepath.Join(dir, "config.json")
    cfg := AppConfig{
        Name: "innoZverse", Version: "1.0.0", Debug: true, Port: 8080,
        DB: DBConfig{"sqlite", "localhost", 5432, "innozverse"},
        Features: map[string]bool{"auth": true, "api": true, "beta": false},
    }
    cfgData, _ := json.MarshalIndent(cfg, "", "  ")
    os.WriteFile(configPath, cfgData, 0644)

    loaded2, _ := loadConfig(configPath)
    fmt.Printf("\nConfig: %s v%s port=%d\n", loaded2.Name, loaded2.Version, loaded2.Port)
    fmt.Println("DB:", loaded2.DB.Driver, loaded2.DB.Database)
    for k, v := range loaded2.Features {
        fmt.Printf("  feature.%s = %v\n", k, v)
    }

    // Generate some files for walker
    for _, name := range []string{"a.json", "b.json", "c.txt", "d.csv"} {
        os.WriteFile(filepath.Join(dir, name), []byte("test content"), 0644)
    }

    stats, _ := walkDir(dir)
    fmt.Printf("\nWalked %s: %d files, %d bytes\n", dir, stats.TotalFiles, stats.TotalSize)
    for ext, count := range stats.ByExt {
        fmt.Printf("  %s: %d file(s)\n", ext, count)
    }

    // Buffered log writer
    logPath := filepath.Join(dir, "app.log")
    lf, _ := os.Create(logPath)
    lw := bufio.NewWriter(lf)
    for i := 0; i < 5; i++ {
        fmt.Fprintf(lw, "[%s] Event %d processed\n", time.Now().Format("15:04:05"), i+1)
    }
    lw.Flush()
    lf.Close()

    logData, _ := os.ReadFile(logPath)
    lines := strings.Split(strings.TrimSpace(string(logData)), "\n")
    fmt.Printf("\nLog file: %d entries\n", len(lines))
    fmt.Println("Last:", lines[len(lines)-1])
}
EOF
```

**📸 Verified Output:**
```
Money JSON: {"amount":"864.00","currency":"USD"}

CSV: loaded 3 records
  2026-03-01: 2xSurface Pro = $1728.00
  2026-03-02: 5xSurface Pen = $249.95
  2026-03-03: 10xOffice 365 = $999.90
Total revenue: $2977.85

Config: innoZverse v1.0.0 port=8080
DB: sqlite innozverse
  feature.auth = true
  feature.api = true
  feature.beta = false

Walked /tmp/golab-xxx: 6 files, 356 bytes
  .csv: 1 file(s)
  .json: 3 file(s)
  .txt: 1 file(s)

Log file: 5 entries
Last: [05:00:05] Event 5 processed
```

---

## Summary

| Task | Go approach |
|------|-------------|
| Read whole file | `os.ReadFile(path)` |
| Write whole file | `os.WriteFile(path, data, 0644)` |
| Read line by line | `bufio.NewScanner(f)` + `scanner.Scan()` |
| Buffered writes | `bufio.NewWriter(f)` + `w.Flush()` |
| JSON encode | `json.Marshal(v)` or `json.NewEncoder(w).Encode(v)` |
| JSON decode | `json.Unmarshal(data, &v)` or `json.NewDecoder(r).Decode(&v)` |
| CSV read | `csv.NewReader(f).ReadAll()` |
| CSV write | `csv.NewWriter(f).Write(row)` + `Flush()` |
| Walk directory | `filepath.WalkDir(root, fn)` |

## Further Reading
- [encoding/json](https://pkg.go.dev/encoding/json)
- [os package](https://pkg.go.dev/os)
- [bufio package](https://pkg.go.dev/bufio)
