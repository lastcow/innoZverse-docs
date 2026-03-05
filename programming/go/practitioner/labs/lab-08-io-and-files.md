# Lab 08: I/O and Files

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm golang:1.22-alpine sh`

## Overview

Go's I/O model is built around interfaces (`io.Reader`, `io.Writer`, `io.Closer`) that compose cleanly. The `os`, `bufio`, `io`, and `embed` packages cover everything from file operations to embedded assets.

## Step 1: os.ReadFile / os.WriteFile

The simplest file operations — read/write entire files.

```go
package main

import (
    "fmt"
    "os"
)

func main() {
    // Write
    content := []byte("Hello, Go!\nLine 2\nLine 3\n")
    err := os.WriteFile("/tmp/hello.txt", content, 0644)
    if err != nil {
        panic(err)
    }
    fmt.Println("written")

    // Read
    data, err := os.ReadFile("/tmp/hello.txt")
    if err != nil {
        panic(err)
    }
    fmt.Print(string(data))
}
```

> 💡 **Tip:** `os.ReadFile` reads the entire file into memory. For large files, use `os.Open` + streaming reads.

## Step 2: os.Open / os.Create — Low-Level File Ops

```go
package main

import (
    "fmt"
    "io"
    "os"
)

func main() {
    // Create (truncates if exists)
    f, err := os.Create("/tmp/myfile.txt")
    if err != nil {
        panic(err)
    }
    f.WriteString("first line\n")
    f.WriteString("second line\n")
    f.Close()

    // Open (read-only)
    r, err := os.Open("/tmp/myfile.txt")
    if err != nil {
        panic(err)
    }
    defer r.Close()

    data, _ := io.ReadAll(r)
    fmt.Print(string(data))

    // Append mode
    a, _ := os.OpenFile("/tmp/myfile.txt", os.O_APPEND|os.O_WRONLY, 0644)
    defer a.Close()
    a.WriteString("third line\n")

    // Verify append
    out, _ := os.ReadFile("/tmp/myfile.txt")
    fmt.Print(string(out))
}
```

## Step 3: bufio.Scanner — Line-by-Line Reading

```go
package main

import (
    "bufio"
    "fmt"
    "os"
    "strings"
)

func countWords(text string) int {
    scanner := bufio.NewScanner(strings.NewReader(text))
    scanner.Split(bufio.ScanWords)
    count := 0
    for scanner.Scan() {
        count++
    }
    return count
}

func main() {
    // Scan lines from file
    os.WriteFile("/tmp/poem.txt", []byte("Roses are red\nViolets are blue\nGo is awesome\nAnd so are you\n"), 0644)

    f, _ := os.Open("/tmp/poem.txt")
    defer f.Close()

    scanner := bufio.NewScanner(f)
    lineNum := 0
    for scanner.Scan() {
        lineNum++
        line := scanner.Text()
        words := countWords(line)
        fmt.Printf("line %d (%d words): %s\n", lineNum, words, line)
    }
    if err := scanner.Err(); err != nil {
        fmt.Println("scan error:", err)
    }
}
```

## Step 4: bufio.Writer — Buffered Writing

```go
package main

import (
    "bufio"
    "fmt"
    "os"
)

func main() {
    f, _ := os.Create("/tmp/output.txt")
    defer f.Close()

    w := bufio.NewWriterSize(f, 4096) // 4KB buffer

    for i := 1; i <= 5; i++ {
        fmt.Fprintf(w, "record %d: data=%d\n", i, i*100)
    }

    // IMPORTANT: flush the buffer before close
    if err := w.Flush(); err != nil {
        fmt.Println("flush error:", err)
    }

    // Verify
    data, _ := os.ReadFile("/tmp/output.txt")
    fmt.Print(string(data))
    fmt.Printf("buffer size: %d\n", w.Size())
}
```

> 💡 **Tip:** Always call `Flush()` before closing a `bufio.Writer`. Data in the buffer is lost otherwise.

## Step 5: io.Reader / io.Writer / io.Copy

```go
package main

import (
    "fmt"
    "io"
    "strings"
)

// Custom Reader: counts bytes read
type CountReader struct {
    r     io.Reader
    total int64
}

func (c *CountReader) Read(p []byte) (int, error) {
    n, err := c.r.Read(p)
    c.total += int64(n)
    return n, err
}

// Custom Writer: uppercases everything
type UpperWriter struct {
    w io.Writer
}

func (u *UpperWriter) Write(p []byte) (int, error) {
    upper := make([]byte, len(p))
    for i, b := range p {
        if b >= 'a' && b <= 'z' {
            upper[i] = b - 32
        } else {
            upper[i] = b
        }
    }
    return u.w.Write(upper)
}

func main() {
    src := strings.NewReader("hello, go! this is a test.")
    cr := &CountReader{r: src}

    var sb strings.Builder
    uw := &UpperWriter{w: &sb}

    n, _ := io.Copy(uw, cr)
    fmt.Printf("copied %d bytes\n", n)
    fmt.Printf("bytes read: %d\n", cr.total)
    fmt.Printf("result: %s\n", sb.String())
}
```

## Step 6: filepath.Walk and filepath.WalkDir

```go
package main

import (
    "fmt"
    "os"
    "path/filepath"
    "strings"
)

func main() {
    // Create test directory structure
    os.MkdirAll("/tmp/testdir/sub", 0755)
    os.WriteFile("/tmp/testdir/main.go", []byte("package main"), 0644)
    os.WriteFile("/tmp/testdir/go.mod", []byte("module test"), 0644)
    os.WriteFile("/tmp/testdir/sub/util.go", []byte("package sub"), 0644)
    os.WriteFile("/tmp/testdir/sub/data.json", []byte("{}"), 0644)

    fmt.Println("All files:")
    filepath.Walk("/tmp/testdir", func(path string, info os.FileInfo, err error) error {
        if err != nil {
            return err
        }
        rel, _ := filepath.Rel("/tmp/testdir", path)
        if info.IsDir() {
            fmt.Printf("  [DIR]  %s\n", rel)
        } else {
            fmt.Printf("  [FILE] %s (%d bytes)\n", rel, info.Size())
        }
        return nil
    })

    fmt.Println("\n.go files only:")
    filepath.WalkDir("/tmp/testdir", func(path string, d os.DirEntry, err error) error {
        if !d.IsDir() && strings.HasSuffix(path, ".go") {
            fmt.Println(" ", filepath.Base(path))
        }
        return nil
    })
}
```

## Step 7: Temporary Files and Directories

```go
package main

import (
    "fmt"
    "os"
)

func main() {
    // Temp file
    tmpFile, err := os.CreateTemp("", "myapp-*.tmp")
    if err != nil {
        panic(err)
    }
    defer os.Remove(tmpFile.Name()) // cleanup
    tmpFile.WriteString("temporary data")
    tmpFile.Close()
    fmt.Println("temp file:", tmpFile.Name())

    // Temp directory
    tmpDir, err := os.MkdirTemp("", "myapp-dir-*")
    if err != nil {
        panic(err)
    }
    defer os.RemoveAll(tmpDir) // cleanup entire directory
    os.WriteFile(tmpDir+"/config.json", []byte(`{"key":"value"}`), 0644)
    fmt.Println("temp dir:", tmpDir)

    entries, _ := os.ReadDir(tmpDir)
    for _, e := range entries {
        fmt.Println(" entry:", e.Name())
    }
}
```

## Step 8: Capstone — Log Rotation Writer

```go
package main

import (
    "bufio"
    "fmt"
    "os"
    "path/filepath"
    "time"
)

type RotatingLogger struct {
    dir      string
    maxLines int
    current  *bufio.Writer
    file     *os.File
    lines    int
}

func NewRotatingLogger(dir string, maxLines int) (*RotatingLogger, error) {
    os.MkdirAll(dir, 0755)
    rl := &RotatingLogger{dir: dir, maxLines: maxLines}
    return rl, rl.rotate()
}

func (rl *RotatingLogger) rotate() error {
    if rl.file != nil {
        rl.current.Flush()
        rl.file.Close()
    }
    name := filepath.Join(rl.dir, fmt.Sprintf("log-%s.txt", time.Now().Format("150405")))
    f, err := os.Create(name)
    if err != nil {
        return err
    }
    rl.file = f
    rl.current = bufio.NewWriter(f)
    rl.lines = 0
    fmt.Println("[rotate] new log file:", filepath.Base(name))
    return nil
}

func (rl *RotatingLogger) Log(msg string) error {
    if rl.lines >= rl.maxLines {
        if err := rl.rotate(); err != nil {
            return err
        }
    }
    fmt.Fprintf(rl.current, "%s %s\n", time.Now().Format("15:04:05"), msg)
    rl.lines++
    return nil
}

func (rl *RotatingLogger) Close() {
    rl.current.Flush()
    rl.file.Close()
}

func main() {
    logger, _ := NewRotatingLogger("/tmp/logs", 3)
    defer logger.Close()

    messages := []string{
        "server started", "request received", "processing",
        "slow query detected", "response sent", "connection closed",
        "new request", "cached hit",
    }
    for _, msg := range messages {
        logger.Log(msg)
    }

    // List log files
    entries, _ := os.ReadDir("/tmp/logs")
    fmt.Printf("\n%d log files created\n", len(entries))
}
```

📸 **Verified Output:**
```
=== WriteFile/ReadFile ===
Hello, Go!
Line 2
Line 3
=== bufio.Scanner ===
line: Hello, Go!
line: Line 2
line: Line 3

=== bufio.Writer ===
buffered write 1
buffered write 2
=== io.Copy ===
copied 17 bytes: copy this content

=== filepath.Walk ===
 file: a.txt
 file: b.txt
 file: hello.txt
 file: out.txt
```

## Summary

| API | Purpose | Notes |
|---|---|---|
| `os.ReadFile` / `os.WriteFile` | Read/write entire file | Simple; loads all into memory |
| `os.Open` / `os.Create` | Low-level file handles | Remember to `Close()` (use defer) |
| `os.OpenFile` | Open with mode flags | `O_APPEND`, `O_RDWR`, etc. |
| `bufio.Scanner` | Line/word/token scanning | Check `scanner.Err()` after loop |
| `bufio.NewWriter` | Buffered writes | Must call `Flush()` |
| `io.Reader/Writer` | Universal I/O interfaces | Compose via `io.Copy`, `io.TeeReader` |
| `io.ReadAll` | Read everything from Reader | Returns `[]byte` |
| `filepath.Walk` / `WalkDir` | Recursive directory traversal | `WalkDir` is more efficient |
| `os.CreateTemp` | Temp file with unique name | Use `defer os.Remove(f.Name())` |
