# Go Foundations

> Learn Go from first principles — types, concurrency, interfaces, and a complete CLI capstone.

{% hint style="info" %}
**Prerequisites:** Basic programming knowledge (any language). No Go experience required.
{% endhint %}

---

## Lab Overview

| # | Lab | Key Concepts | Time |
|---|-----|-------------|------|
| 01 | [Hello World & Basics](labs/lab-01-hello-world.md) | Variables, types, constants, iota, control flow | 20 min |
| 02 | [Functions, Closures & Defer](labs/lab-02-functions.md) | Multiple returns, variadic, closures, defer, panic/recover | 25 min |
| 03 | [Arrays, Slices & Maps](labs/lab-03-arrays-slices-maps.md) | Slice internals, append, copy, map patterns, generic set | 30 min |
| 04 | [Structs & Methods](labs/lab-04-structs-methods.md) | Value/pointer receivers, embedding, constructors | 30 min |
| 05 | [Interfaces & Polymorphism](labs/lab-05-interfaces.md) | Implicit satisfaction, type assertions, type switches | 30 min |
| 06 | [Pointers & Memory](labs/lab-06-pointers.md) | Address-of, dereference, nil safety, linked lists | 25 min |
| 07 | [Goroutines & Channels](labs/lab-07-goroutines-channels.md) | WaitGroup, buffered/unbuffered channels, select, worker pool | 35 min |
| 08 | [Error Handling](labs/lab-08-error-handling.md) | Custom errors, `errors.Is/As`, wrapping, retry | 30 min |
| 09 | [Packages & Stdlib](labs/lab-09-packages-modules.md) | os, strings, strconv, time, math, sort, log | 30 min |
| 10 | [File I/O & JSON](labs/lab-10-file-io-json.md) | bufio, os.ReadFile, encoding/json, CSV, streaming | 30 min |
| 11 | [HTTP & REST](labs/lab-11-http-rest.md) | http.Client, ServeMux, middleware, httptest | 35 min |
| 12 | [Testing](labs/lab-12-testing.md) | testing.T, table-driven tests, benchmarks, httptest | 30 min |
| 13 | [Context & Cancellation](labs/lab-13-context.md) | WithCancel, WithTimeout, values, graceful shutdown | 30 min |
| 14 | [Generics](labs/lab-14-generics.md) | Type parameters, constraints, `~`, generic data structures | 30 min |
| 15 | [Capstone: storecli](labs/lab-15-capstone.md) | Full CLI: JSON store, stats, concurrent fetch, context | 60 min |

**Total estimated time:** ~8 hours

---

{% hint style="success" %}
**Start here:** [Lab 01 — Hello World & Go Basics](labs/lab-01-hello-world.md)
{% endhint %}

---

## Docker Quick Start

```bash
docker pull zchencow/innozverse-go:latest
docker run --rm zchencow/innozverse-go:latest go run - << 'EOF'
package main
import "fmt"
func main() {
    fmt.Println("Hello, innoZverse!")
    fmt.Println("Go version ready for labs.")
}
EOF
```
