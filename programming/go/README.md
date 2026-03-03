# Go (Golang)

> **Simple, fast, concurrent.** Go compiles to native code, ships with a powerful standard library, and makes concurrent programming straightforward with goroutines and channels.

---

<table data-view="cards">
<thead><tr><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead>
<tbody>
<tr>
<td><strong>🟩 Foundations</strong></td>
<td>Types, functions, structs, interfaces, goroutines, JSON</td>
<td><a href="foundations/README.md">foundations/README.md</a></td>
</tr>
<tr>
<td><strong>🟦 Practitioner</strong></td>
<td>REST APIs, databases, gRPC, testing at scale</td>
<td><a href="practitioner/README.md">practitioner/README.md</a></td>
</tr>
<tr>
<td><strong>🟧 Advanced</strong></td>
<td>Concurrency patterns, profiling, CGo, plugins</td>
<td><a href="advanced/README.md">advanced/README.md</a></td>
</tr>
<tr>
<td><strong>🟥 Expert</strong></td>
<td>Compiler internals, runtime, custom schedulers</td>
<td><a href="expert/README.md">expert/README.md</a></td>
</tr>
</tbody>
</table>

---

## Why Go?

Go was built at Google to solve real problems: long compile times, complex dependency management, and difficulty writing reliable concurrent code. It's now the language behind Docker, Kubernetes, Terraform, Prometheus, and CockroachDB.

| Feature | Benefit |
|---------|---------|
| **Fast compilation** | Sub-second builds even for large codebases |
| **Static typing** | Catch errors at compile time |
| **Goroutines** | Concurrency without callback hell or async/await |
| **Channels** | Safe communication between concurrent processes |
| **Standard library** | HTTP, JSON, testing, crypto — all built in |
| **Single binary** | Deploy anywhere, no runtime dependency |
| **Garbage collected** | No manual memory management |
| **Built-in tools** | `go fmt`, `go test`, `go vet`, `go build` |

---

## Quick Start

{% tabs %}
{% tab title="🐳 Docker (Recommended)" %}
```bash
# Pull the lab image — Go 1.22, Alpine
docker pull zchencow/zchencow/innozverse-go:latest

# Run a one-liner
docker run --rm zchencow/zchencow/innozverse-go:latest go run - << 'EOF'
package main
import "fmt"
func main() { fmt.Println("Hello, Go!") }
EOF

# Interactive shell
docker run --rm -it zchencow/zchencow/innozverse-go:latest sh
```
{% endtab %}
{% tab title="Ubuntu/Debian" %}
```bash
# Install Go 1.22
wget https://go.dev/dl/go1.22.0.linux-amd64.tar.gz
sudo tar -C /usr/local -xzf go1.22.0.linux-amd64.tar.gz
echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
source ~/.bashrc

go version  # go1.22.0 linux/amd64
```
{% endtab %}
{% tab title="macOS" %}
```bash
brew install go

go version
```
{% endtab %}
{% tab title="Windows" %}
```powershell
# Download from https://go.dev/dl/
# Or via winget:
winget install GoLang.Go

go version
```
{% endtab %}
{% endtabs %}

---

## What You'll Learn

### 🟩 Foundations (Labs 01–15)
Hello World, variables, functions, closures, arrays/slices/maps, structs, interfaces, pointers, goroutines, channels, error handling, packages, file I/O, JSON, HTTP, testing, context, generics, and a capstone CLI tool.

{% hint style="info" %}
**Start here:** [Foundations → Lab 01](foundations/labs/lab-01-hello-world.md)
{% endhint %}

{% hint style="success" %}
**Go philosophy:** "Don't communicate by sharing memory; share memory by communicating." Every design decision in Go flows from this idea.
{% endhint %}
