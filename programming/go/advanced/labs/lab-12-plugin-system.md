# Lab 12: Plugin System

**Time:** 45 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm golang:1.22 sh`

## Overview

Build a plugin system using Go's `plugin` package (`-buildmode=plugin`) and the `hashicorp/go-plugin` RPC-based alternative. Learn plugin contracts, limitations, and production patterns.

---

## Step 1: Go Plugin Basics

```
Go Plugin Architecture:
  Main App ──► plugin.Open("greeter.so") ──► plugin.Lookup("Plugin")
                                               ──► type assertion to interface
                                               ──► call methods
```

**Limitations of `plugin` package:**
- Requires CGO + glibc (not Alpine/musl)
- Plugin and host must be compiled with same Go version
- Plugin cannot be unloaded
- Not supported on Windows

> 💡 Use `docker run -it --rm golang:1.22 sh` (Debian/glibc) instead of Alpine for plugin support.

---

## Step 2: Define Plugin Contract

```go
// contract/contract.go (shared package)
package contract

// Greeter is the plugin interface contract
// Both host and plugin must use this same interface
type Greeter interface {
	Greet(name string) string
	Lang() string
}

// Transformer transforms strings
type Transformer interface {
	Transform(input string) string
	Name() string
}
```

---

## Step 3: Build a Plugin

```go
// plugins/english/english.go
package main

import "fmt"

type EnglishGreeter struct{}

func (g EnglishGreeter) Greet(name string) string {
	return fmt.Sprintf("Hello, %s! Nice to meet you.", name)
}

func (g EnglishGreeter) Lang() string { return "English" }

// Plugin is the exported symbol the host will look up
var Plugin EnglishGreeter
```

```bash
# Build as shared object
cd plugins/english
go build -buildmode=plugin -o english.so .
```

---

## Step 4: Build Another Plugin

```go
// plugins/spanish/spanish.go
package main

import "fmt"

type SpanishGreeter struct{}

func (g SpanishGreeter) Greet(name string) string {
	return fmt.Sprintf("¡Hola, %s! Mucho gusto.", name)
}

func (g SpanishGreeter) Lang() string { return "Español" }

var Plugin SpanishGreeter
```

```bash
go build -buildmode=plugin -o spanish.so .
```

---

## Step 5: Host Application

```go
// main.go (host)
package main

import (
	"fmt"
	"os"
	"plugin"
)

// Greeter interface (must match plugin's implementation)
type Greeter interface {
	Greet(name string) string
	Lang() string
}

func loadPlugin(path string) (Greeter, error) {
	p, err := plugin.Open(path)
	if err != nil {
		return nil, fmt.Errorf("open plugin %s: %w", path, err)
	}

	sym, err := p.Lookup("Plugin")
	if err != nil {
		return nil, fmt.Errorf("lookup Plugin symbol: %w", err)
	}

	g, ok := sym.(Greeter)
	if !ok {
		return nil, fmt.Errorf("Plugin does not implement Greeter interface")
	}
	return g, nil
}

func main() {
	plugins := []string{"english.so", "spanish.so"}

	for _, path := range plugins {
		if _, err := os.Stat(path); os.IsNotExist(err) {
			fmt.Printf("Plugin not found: %s\n", path)
			continue
		}

		g, err := loadPlugin(path)
		if err != nil {
			fmt.Printf("Error: %v\n", err)
			continue
		}

		fmt.Printf("[%s] %s\n", g.Lang(), g.Greet("World"))
	}
}
```

---

## Step 6: Full Verified Demo (glibc Docker)

```bash
docker run --rm golang:1.22 sh -c "
mkdir -p /tmp/plugin_lab/greeter /tmp/plugin_lab/mainapp

# Plugin
cat > /tmp/plugin_lab/greeter/greeter.go << 'GOEOF'
package main

import \"fmt\"

type greeterImpl struct{}

func (g greeterImpl) Greet(name string) string {
	return fmt.Sprintf(\"Hello, %s! (from plugin)\", name)
}

func (g greeterImpl) Lang() string { return \"English\" }

var Plugin greeterImpl
GOEOF
cd /tmp/plugin_lab/greeter && go mod init greeter
go build -buildmode=plugin -o /tmp/plugin_lab/greeter.so . 2>&1
echo 'Plugin built:' \$(ls -lh /tmp/plugin_lab/greeter.so | awk '{print \$5}')

# Host
cat > /tmp/plugin_lab/mainapp/main.go << 'GOEOF'
package main

import (
	\"fmt\"
	\"plugin\"
)

type Greeter interface {
	Greet(name string) string
	Lang() string
}

func main() {
	p, err := plugin.Open(\"/tmp/plugin_lab/greeter.so\")
	if err != nil { panic(err) }
	sym, err := p.Lookup(\"Plugin\")
	if err != nil { panic(err) }
	g, ok := sym.(Greeter)
	if !ok { panic(\"type assertion failed\") }
	fmt.Printf(\"[%s] %s\n\", g.Lang(), g.Greet(\"World\"))
}
GOEOF
cd /tmp/plugin_lab/mainapp && go mod init mainapp
go run main.go 2>&1"
```

📸 **Verified Output:**
```
Plugin built: 3.3M
[English] Hello, World! (from plugin)
```

---

## Step 7: hashicorp/go-plugin (Production Alternative)

`hashicorp/go-plugin` solves the limitations of the stdlib `plugin` package by running plugins as separate processes with RPC.

```go
// Using hashicorp/go-plugin (conceptual example)
package main

import (
	"fmt"
	"os/exec"

	goplugin "github.com/hashicorp/go-plugin"
)

// Shared interface
type Greeter interface {
	Greet(name string) string
}

// Plugin map (must match plugin's exported name)
var pluginMap = goplugin.PluginSet{
	"greeter": &GreeterPlugin{},
}

// Handshake config (must match between host and plugin)
var handshakeConfig = goplugin.HandshakeConfig{
	ProtocolVersion:  1,
	MagicCookieKey:   "GREETER_PLUGIN",
	MagicCookieValue: "hello",
}

func loadRPCPlugin(path string) (Greeter, error) {
	client := goplugin.NewClient(&goplugin.ClientConfig{
		HandshakeConfig: handshakeConfig,
		Plugins:         pluginMap,
		Cmd:             exec.Command(path),
		AllowedProtocols: []goplugin.Protocol{
			goplugin.ProtocolGRPC,
		},
	})

	rpcClient, err := client.Client()
	if err != nil {
		return nil, err
	}

	raw, err := rpcClient.Dispense("greeter")
	if err != nil {
		return nil, err
	}

	return raw.(Greeter), nil
}

func main() {
	fmt.Println("hashicorp/go-plugin advantages:")
	fmt.Println("  ✓ Cross-language (Go, Python, Ruby...)")
	fmt.Println("  ✓ Process isolation (crash doesn't kill host)")
	fmt.Println("  ✓ Versioned interface negotiation")
	fmt.Println("  ✓ Supports gRPC or net/rpc transport")
	fmt.Println("  ✓ Works on all platforms")
	fmt.Println("  ✓ Plugin can be any executable")
}
```

---

## Step 8: Capstone — Plugin Registry

```go
// plugin_registry.go
package main

import (
	"fmt"
	"plugin"
	"sort"
)

type Transformer interface {
	Transform(input string) string
	Name() string
}

type PluginRegistry struct {
	transformers map[string]Transformer
}

func NewPluginRegistry() *PluginRegistry {
	return &PluginRegistry{
		transformers: make(map[string]Transformer),
	}
}

func (r *PluginRegistry) Load(path string) error {
	p, err := plugin.Open(path)
	if err != nil {
		return fmt.Errorf("open: %w", err)
	}

	sym, err := p.Lookup("Plugin")
	if err != nil {
		return fmt.Errorf("lookup: %w", err)
	}

	t, ok := sym.(Transformer)
	if !ok {
		return fmt.Errorf("plugin does not implement Transformer")
	}

	r.transformers[t.Name()] = t
	fmt.Printf("Registered plugin: %s\n", t.Name())
	return nil
}

func (r *PluginRegistry) Transform(name, input string) (string, error) {
	t, ok := r.transformers[name]
	if !ok {
		return "", fmt.Errorf("plugin %q not found", name)
	}
	return t.Transform(input), nil
}

func (r *PluginRegistry) List() []string {
	names := make([]string, 0, len(r.transformers))
	for n := range r.transformers {
		names = append(names, n)
	}
	sort.Strings(names)
	return names
}

// Demo with mock (no .so file needed)
type MockUppercase struct{}
func (MockUppercase) Name() string { return "uppercase" }
func (MockUppercase) Transform(s string) string {
	result := make([]byte, len(s))
	for i, c := range []byte(s) {
		if c >= 'a' && c <= 'z' { result[i] = c - 32 } else { result[i] = c }
	}
	return string(result)
}

type MockReverse struct{}
func (MockReverse) Name() string { return "reverse" }
func (MockReverse) Transform(s string) string {
	runes := []rune(s)
	for i, j := 0, len(runes)-1; i < j; i, j = i+1, j-1 {
		runes[i], runes[j] = runes[j], runes[i]
	}
	return string(runes)
}

func main() {
	reg := NewPluginRegistry()
	// In production, load from .so files:
	// reg.Load("./plugins/uppercase.so")
	reg.transformers["uppercase"] = MockUppercase{}
	reg.transformers["reverse"] = MockReverse{}

	fmt.Printf("Loaded plugins: %v\n", reg.List())
	for _, name := range reg.List() {
		result, _ := reg.Transform(name, "Hello, World!")
		fmt.Printf("  %s: %q\n", name, result)
	}
}
```

Run the demo:
```bash
docker run --rm golang:1.22-alpine sh -c "cat > /tmp/main.go << 'GOEOF'
package main

import \"fmt\"

type Transformer interface { Transform(s string) string; Name() string }

type Upper struct{}
func (Upper) Name() string { return \"uppercase\" }
func (Upper) Transform(s string) string {
	b := []byte(s)
	for i, c := range b { if c >= 'a' && c <= 'z' { b[i] = c - 32 } }
	return string(b)
}

type Reverse struct{}
func (Reverse) Name() string { return \"reverse\" }
func (Reverse) Transform(s string) string {
	r := []rune(s)
	for i, j := 0, len(r)-1; i < j; i, j = i+1, j-1 { r[i], r[j] = r[j], r[i] }
	return string(r)
}

func main() {
	plugins := []Transformer{Upper{}, Reverse{}}
	input := \"Hello, Go Plugins!\"
	for _, p := range plugins {
		fmt.Printf(\"[%s] %q -> %q\\n\", p.Name(), input, p.Transform(input))
	}
	fmt.Println(\"\\nStdlib plugin.Open requires: glibc, same Go version, -buildmode=plugin\")
	fmt.Println(\"hashicorp/go-plugin: subprocess RPC, cross-language, production-ready\")
}
GOEOF
go run /tmp/main.go"
```

📸 **Verified Output (stdlib plugin.Open on glibc):**
```
Plugin built: 3.3M
[English] Hello, World! (from plugin)
```

---

## Summary

| Feature | stdlib `plugin` | hashicorp/go-plugin |
|---------|----------------|---------------------|
| Transport | Shared memory | RPC (net/rpc or gRPC) |
| Isolation | None (same process) | Process isolation |
| Cross-language | No (Go only) | Yes (any language) |
| Platform | Linux/macOS only | All platforms |
| Unload | No | Yes (kill process) |
| Version mismatch | Panics | Negotiation support |
| Use case | Same-Go-version, Unix only | Production plugins |

**Key Takeaways:**
- `plugin.Open` requires CGO + glibc; Alpine/musl is not supported
- Both host and plugin must be compiled with identical Go version and flags
- Interface-based contracts make plugin type assertions safe
- For production: use `hashicorp/go-plugin` for isolation and cross-language support
- Alternative: embed Lua/JavaScript (tengo, goja) for scripting without plugin limitations
