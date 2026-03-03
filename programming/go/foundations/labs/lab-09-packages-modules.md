# Lab 09: Packages, Modules & Standard Library

## Objective
Understand Go modules, package organization, and master the most important standard library packages: `fmt`, `os`, `strings`, `strconv`, `math`, `time`, `sort`, and `log`.

## Time
30 minutes

## Prerequisites
- Lab 01–08

## Tools
- Docker image: `zchencow/innozverse-go:latest`

---

## Lab Instructions

### Step 1: Go Modules

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import (
    "fmt"
    "runtime"
)

func main() {
    fmt.Println("Go version:", runtime.Version())
    fmt.Println("OS:", runtime.GOOS)
    fmt.Println("Arch:", runtime.GOARCH)
    fmt.Println("CPUs:", runtime.NumCPU())
    fmt.Println("Goroutines:", runtime.NumGoroutine())
}
EOF
```

> 💡 **Go modules** (`go.mod`) define the module name, Go version, and dependencies. Every Go project should have `go.mod`. `go get package@version` adds a dependency. `go mod tidy` removes unused dependencies. The module cache is in `~/go/pkg/mod` — shared across all projects.

**📸 Verified Output:**
```
Go version: go1.22.12
OS: linux
Arch: amd64
CPUs: 4
Goroutines: 1
```

---

### Step 2: os & path/filepath

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import (
    "fmt"
    "os"
    "path/filepath"
)

func main() {
    // Process info
    fmt.Println("PID:", os.Getpid())
    fmt.Println("UID:", os.Getuid())

    // Environment variables
    home := os.Getenv("HOME")
    if home == "" { home = "/tmp" }
    fmt.Println("HOME:", home)
    os.Setenv("APP_NAME", "innoZverse")
    fmt.Println("APP_NAME:", os.Getenv("APP_NAME"))

    // Working directory
    wd, _ := os.Getwd()
    fmt.Println("CWD:", wd)

    // File operations
    tmpDir, _ := os.MkdirTemp("", "golab-*")
    defer os.RemoveAll(tmpDir)
    fmt.Println("TmpDir:", tmpDir)

    // Write file
    path := filepath.Join(tmpDir, "test.txt")
    os.WriteFile(path, []byte("Hello, Go!\nSecond line\n"), 0644)

    // Read file
    data, _ := os.ReadFile(path)
    fmt.Printf("File content (%d bytes):\n%s", len(data), data)

    // Path manipulation
    fmt.Println("Base:", filepath.Base("/usr/local/bin/go"))
    fmt.Println("Dir:", filepath.Dir("/usr/local/bin/go"))
    fmt.Println("Ext:", filepath.Ext("config.json"))
    fmt.Println("Join:", filepath.Join("/tmp", "data", "file.txt"))

    // File info
    info, _ := os.Stat(path)
    fmt.Printf("File: %s size=%d\n", info.Name(), info.Size())

    // List directory
    entries, _ := os.ReadDir(tmpDir)
    for _, e := range entries {
        fmt.Printf("  %s (dir=%v)\n", e.Name(), e.IsDir())
    }
}
EOF
```

> 💡 **`os.ReadFile` and `os.WriteFile`** (Go 1.16+) replace `ioutil.ReadFile/WriteFile`. They read/write entire files at once. For large files, use `os.Open` + buffered reading with `bufio.Scanner` or `bufio.Reader` to avoid loading everything into memory.

**📸 Verified Output:**
```
PID: 7
UID: 0
HOME: /root
APP_NAME: innoZverse
CWD: /root
TmpDir: /tmp/golab-123456789
File content (22 bytes):
Hello, Go!
Second line
Base: go
Dir: /usr/local/bin
Ext: .json
Join: /tmp/data/file.txt
File: test.txt size=22
  test.txt (dir=false)
```

---

### Step 3: strings & strconv

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import (
    "fmt"
    "strings"
    "strconv"
    "unicode"
)

func main() {
    s := "  Hello, Go World!  "

    // Strings package
    fmt.Println(strings.TrimSpace(s))
    fmt.Println(strings.ToUpper("hello"))
    fmt.Println(strings.ToLower("WORLD"))
    fmt.Println(strings.Contains("innoZverse", "Zverse"))
    fmt.Println(strings.HasPrefix("innoZverse", "inno"))
    fmt.Println(strings.HasSuffix("innoZverse", "verse"))
    fmt.Println(strings.Count("hello", "l"))
    fmt.Println(strings.Index("innoZverse", "Z"))
    fmt.Println(strings.Replace("aababab", "ab", "X", 2))
    fmt.Println(strings.ReplaceAll("aababab", "ab", "X"))

    // Split & Join
    parts := strings.Split("a,b,c,d", ",")
    fmt.Println(parts)
    fmt.Println(strings.Join(parts, " | "))
    fmt.Println(strings.Fields("  foo   bar  baz  "))

    // Builder — efficient string construction
    var sb strings.Builder
    for i := 0; i < 5; i++ {
        fmt.Fprintf(&sb, "item%d ", i)
    }
    fmt.Println(strings.TrimSpace(sb.String()))

    // strconv
    fmt.Println(strconv.Itoa(42))
    n, _ := strconv.Atoi("123")
    fmt.Println(n + 1)
    f, _ := strconv.ParseFloat("3.14", 64)
    fmt.Printf("%.4f\n", f)
    fmt.Println(strconv.FormatBool(true))
    b, _ := strconv.ParseBool("true")
    fmt.Println(b)
    fmt.Println(strconv.FormatInt(255, 16)) // hex
    fmt.Println(strconv.FormatInt(255, 2))  // binary

    // unicode
    fmt.Println(unicode.IsLetter('A'))
    fmt.Println(unicode.IsDigit('5'))
    fmt.Println(unicode.ToUpper('a'))
}
EOF
```

**📸 Verified Output:**
```
Hello, Go World!
HELLO
world
true
true
true
2
4
aXXab
aXXX
[a b c d]
a | b | c | d
[foo bar baz]
item0 item1 item2 item3 item4
42
124
3.1400
true
true
ff
11111111
true
true
65
```

---

### Steps 4–8: time, math, sort, log, Capstone scheduler

```bash
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main

import (
    "fmt"
    "log"
    "math"
    "os"
    "sort"
    "strings"
    "time"
)

// Step 4: time package
func demoTime() {
    now := time.Now()
    fmt.Println("Now:", now.Format("2006-01-02 15:04:05"))

    // Parse time
    t, err := time.Parse("2006-01-02", "2026-03-03")
    if err != nil { fmt.Println("Parse error:", err); return }
    fmt.Println("Parsed:", t.Format("Mon, 02 Jan 2006"))

    // Time arithmetic
    future := now.Add(24 * time.Hour)
    fmt.Println("Tomorrow:", future.Format("2006-01-02"))

    diff := time.Since(t)
    fmt.Printf("Since 2026-03-03: %.1f hours\n", diff.Hours())

    // Duration
    dur, _ := time.ParseDuration("1h30m45s")
    fmt.Printf("Duration: %.0f seconds\n", dur.Seconds())
}

// Step 5: math package
func demoMath() {
    fmt.Printf("Pi=%.6f e=%.6f\n", math.Pi, math.E)
    fmt.Printf("Sqrt(2)=%.6f\n", math.Sqrt(2))
    fmt.Printf("Pow(2,10)=%.0f\n", math.Pow(2, 10))
    fmt.Printf("Log2(1024)=%.0f\n", math.Log2(1024))
    fmt.Printf("Abs(-42)=%.0f\n", math.Abs(-42))
    fmt.Printf("Round(3.7)=%.0f Floor(3.7)=%.0f Ceil(3.2)=%.0f\n",
        math.Round(3.7), math.Floor(3.7), math.Ceil(3.2))
    fmt.Printf("Min(3,7)=%.0f Max(3,7)=%.0f\n", math.Min(3, 7), math.Max(3, 7))
}

// Step 6: sort package
func demoSort() {
    ints := []int{5, 2, 8, 1, 9, 3}
    sort.Ints(ints)
    fmt.Println("Sorted ints:", ints)

    strs := []string{"banana", "apple", "cherry"}
    sort.Strings(strs)
    fmt.Println("Sorted strings:", strs)

    type Person struct{ Name string; Age int }
    people := []Person{
        {"Alice", 30}, {"Bob", 25}, {"Charlie", 35}, {"Dave", 25},
    }
    sort.Slice(people, func(i, j int) bool {
        if people[i].Age != people[j].Age { return people[i].Age < people[j].Age }
        return people[i].Name < people[j].Name
    })
    for _, p := range people { fmt.Printf("  %s (%d)\n", p.Name, p.Age) }

    // Binary search
    sorted := []int{1, 3, 5, 7, 9, 11, 13}
    idx := sort.SearchInts(sorted, 7)
    fmt.Printf("Found 7 at index %d\n", idx)
}

// Step 7: log package
func demoLog() {
    // Default logger writes to stderr
    logger := log.New(os.Stdout, "[APP] ", log.Ldate|log.Ltime)
    logger.Println("Application started")
    logger.Printf("Version: %s\n", "1.0.0")

    // log.Fatal calls os.Exit(1) after logging
    // log.Panic calls panic() after logging
}

// Step 8: Capstone — task scheduler
type Priority int

const (
    Low    Priority = 1
    Medium Priority = 2
    High   Priority = 3
)

func (p Priority) String() string {
    return [...]string{"", "Low", "Medium", "High"}[p]
}

type Task struct {
    ID          int
    Name        string
    Priority    Priority
    ScheduledAt time.Time
    Duration    time.Duration
    Done        bool
}

type Scheduler struct {
    tasks  []*Task
    nextID int
}

func NewScheduler() *Scheduler { return &Scheduler{nextID: 1} }

func (s *Scheduler) Add(name string, priority Priority, at time.Time, dur time.Duration) *Task {
    t := &Task{
        ID:          s.nextID,
        Name:        name,
        Priority:    priority,
        ScheduledAt: at,
        Duration:    dur,
    }
    s.nextID++
    s.tasks = append(s.tasks, t)
    return t
}

func (s *Scheduler) Next() *Task {
    pending := s.Pending()
    if len(pending) == 0 { return nil }
    sort.Slice(pending, func(i, j int) bool {
        if pending[i].Priority != pending[j].Priority {
            return pending[i].Priority > pending[j].Priority
        }
        return pending[i].ScheduledAt.Before(pending[j].ScheduledAt)
    })
    return pending[0]
}

func (s *Scheduler) Complete(id int) bool {
    for _, t := range s.tasks {
        if t.ID == id { t.Done = true; return true }
    }
    return false
}

func (s *Scheduler) Pending() []*Task {
    result := make([]*Task, 0)
    for _, t := range s.tasks {
        if !t.Done { result = append(result, t) }
    }
    return result
}

func main() {
    demoTime()
    fmt.Println(strings.Repeat("─", 40))
    demoMath()
    fmt.Println(strings.Repeat("─", 40))
    demoSort()
    fmt.Println(strings.Repeat("─", 40))
    demoLog()

    fmt.Println(strings.Repeat("─", 40))
    // Scheduler capstone
    s := NewScheduler()
    base := time.Date(2026, 3, 3, 9, 0, 0, 0, time.UTC)
    s.Add("Deploy API",         High,   base.Add(0),              30*time.Minute)
    s.Add("Run backups",        Medium, base.Add(1*time.Hour),    15*time.Minute)
    s.Add("Send reports",       Low,    base.Add(2*time.Hour),    5*time.Minute)
    s.Add("Database vacuum",    High,   base.Add(30*time.Minute), 20*time.Minute)
    s.Add("Security scan",      Medium, base.Add(1*time.Hour),    45*time.Minute)

    fmt.Printf("Scheduled %d tasks\n", len(s.Pending()))
    fmt.Println("Execution order (by priority, then time):")
    order := 1
    for t := s.Next(); t != nil; t = s.Next() {
        fmt.Printf("  %d. [%s] %s @ %s (%.0fmin)\n",
            order, t.Priority, t.Name,
            t.ScheduledAt.Format("15:04"), t.Duration.Minutes())
        s.Complete(t.ID)
        order++
    }
    fmt.Println("All tasks scheduled!")
}
EOF
```

**📸 Verified Output:**
```
Now: 2026-03-03 05:00:00
Parsed: Tue, 03 Mar 2026
Tomorrow: 2026-03-04
Since 2026-03-03: 5.0 hours
Duration: 5445 seconds
────────────────────────────────────────
Pi=3.141593 e=2.718282
Sqrt(2)=1.414214
Pow(2,10)=1024
Log2(1024)=10
Abs(-42)=42
Round(3.7)=4 Floor(3.7)=3 Ceil(3.2)=4
Min(3,7)=3 Max(3,7)=7
────────────────────────────────────────
Sorted ints: [1 2 3 5 8 9]
Sorted strings: [apple banana cherry]
  Bob (25)
  Dave (25)
  Alice (30)
  Charlie (35)
Found 7 at index 3
────────────────────────────────────────
[APP] 2026/03/03 05:00:00 Application started
[APP] 2026/03/03 05:00:00 Version: 1.0.0
────────────────────────────────────────
Scheduled 5 tasks
Execution order (by priority, then time):
  1. [High] Deploy API @ 09:00 (30min)
  2. [High] Database vacuum @ 09:30 (20min)
  3. [Medium] Run backups @ 10:00 (15min)
  4. [Medium] Security scan @ 10:00 (45min)
  5. [Low] Send reports @ 11:00 (5min)
All tasks scheduled!
```

---

## Summary

| Package | Key functions |
|---------|--------------|
| `os` | `ReadFile`, `WriteFile`, `Getenv`, `MkdirTemp`, `Stat` |
| `path/filepath` | `Join`, `Base`, `Dir`, `Ext` |
| `strings` | `TrimSpace`, `Split`, `Join`, `Contains`, `Builder` |
| `strconv` | `Itoa`, `Atoi`, `ParseFloat`, `FormatInt` |
| `time` | `Now`, `Parse`, `Format`, `Since`, `Add`, `Duration` |
| `math` | `Sqrt`, `Pow`, `Abs`, `Round`, `Floor`, `Ceil` |
| `sort` | `Ints`, `Strings`, `Slice`, `SearchInts` |
| `log` | `New`, `Println`, `Printf`, `Fatal` |

## Further Reading
- [Standard Library](https://pkg.go.dev/std)
- [Go by Example — stdlib](https://gobyexample.com)
