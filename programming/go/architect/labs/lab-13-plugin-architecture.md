# Lab 13: Plugin Architecture

**Time:** 60 minutes | **Level:** Architect | **Docker:** `golang:1.22-alpine`

## Overview

Plugin systems in Go: `plugin` package (Open/Lookup), hashicorp/go-plugin (gRPC-based), interface-contract versioning, hot-reload pattern, WASM-based plugins for isolation, and capability-based plugin security.

---

## Step 1: Go `plugin` Package

```go
// plugin/greeter/main.go — compiled as shared library
package main

// Exported symbol: must be package-level variable or function
var PluginName = "greeter-v1"

func Greet(name string) string {
    return "Hello, " + name + "! (from plugin)"
}

// Build:
// go build -buildmode=plugin -o greeter.so ./plugin/greeter/

// Limitations:
// - Same Go version (exact match required)
// - Linux/macOS only (no Windows)
// - Cannot unload (process-lifetime)
// - Plugin and host must use same module path for shared types
```

```go
// main.go — host program
package main

import (
    "fmt"
    "plugin"
)

type Greeter interface {
    Greet(string) string
}

func main() {
    // Open plugin
    p, err := plugin.Open("./greeter.so")
    if err != nil {
        panic(err)
    }

    // Look up exported symbol
    sym, err := p.Lookup("Greet")
    if err != nil {
        panic(err)
    }

    // Assert type
    greetFn, ok := sym.(func(string) string)
    if !ok {
        panic("unexpected type from module symbol")
    }

    fmt.Println(greetFn("Alice"))

    // Look up variable
    nameSym, _ := p.Lookup("PluginName")
    name := *nameSym.(*string)
    fmt.Printf("Plugin: %s\n", name)
}
```

---

## Step 2: Plugin Interface Contract

```go
// Versioned plugin interface — critical for stability
package pluginapi

const APIVersion = 2

// Contract: plugins must implement this interface
type Plugin interface {
    // Metadata
    Name()       string
    Version()    string
    APIVersion() int    // Must match host's APIVersion

    // Lifecycle
    Init(config map[string]string) error
    Start(ctx context.Context) error
    Stop(ctx context.Context) error

    // Capability
    Execute(ctx context.Context, input Input) (Output, error)
}

type Input struct {
    Type    string
    Payload []byte
    Meta    map[string]string
}

type Output struct {
    Type    string
    Payload []byte
    Error   string
}

// Host-side loader with version checking
func LoadPlugin(path string) (Plugin, error) {
    p, err := plugin.Open(path)
    if err != nil {
        return nil, fmt.Errorf("open plugin %q: %w", path, err)
    }

    sym, err := p.Lookup("NewPlugin")
    if err != nil {
        return nil, fmt.Errorf("NewPlugin not found: %w", err)
    }

    factory, ok := sym.(func() Plugin)
    if !ok {
        return nil, fmt.Errorf("NewPlugin has wrong signature")
    }

    plugin := factory()
    if plugin.APIVersion() != APIVersion {
        return nil, fmt.Errorf("API version mismatch: plugin=%d, host=%d",
            plugin.APIVersion(), APIVersion)
    }

    return plugin, nil
}
```

---

## Step 3: hashicorp/go-plugin — Production Plugins

```go
// Advantages over standard plugin:
// - Works on all platforms (subprocess model)
// - Can crash-restart plugins
// - gRPC transport (type-safe, versioned)
// - Works across Go versions
// - Can be written in other languages

// server/main.go — plugin process
package main

import (
    hcplugin "github.com/hashicorp/go-plugin"
)

// Implement the interface (grpc server side)
type GreeterServer struct{}

func (g *GreeterServer) Greet(ctx context.Context, req *proto.GreetRequest) (*proto.GreetResponse, error) {
    return &proto.GreetResponse{Message: "Hello, " + req.Name}, nil
}

func main() {
    hcplugin.Serve(&hcplugin.ServeConfig{
        HandshakeConfig: hcplugin.HandshakeConfig{
            ProtocolVersion:  1,
            MagicCookieKey:   "GREETER_PLUGIN",
            MagicCookieValue: "greeter",
        },
        Plugins: map[string]hcplugin.Plugin{
            "greeter": &GreeterPlugin{Impl: &GreeterServer{}},
        },
        GRPCServer: hcplugin.DefaultGRPCServer,
    })
}

// client/main.go — host process
func loadPlugin(path string) (Greeter, func(), error) {
    client := hcplugin.NewClient(&hcplugin.ClientConfig{
        HandshakeConfig: handshakeConfig,
        Plugins:         pluginMap,
        Cmd:             exec.Command(path),
        AllowedProtocols: []hcplugin.Protocol{hcplugin.ProtocolGRPC},
    })

    grpcClient, err := client.Client()
    if err != nil {
        client.Kill()
        return nil, nil, err
    }

    raw, err := grpcClient.Dispense("greeter")
    if err != nil {
        client.Kill()
        return nil, nil, err
    }

    return raw.(Greeter), client.Kill, nil
}
```

---

## Step 4: Hot Reload Plugin Pattern

```go
package loader

import (
    "path/filepath"
    "sync"
    "time"
)

// Watch for plugin changes and reload
type HotLoader struct {
    pluginDir string
    plugins   map[string]Plugin
    mu        sync.RWMutex
    watcher   *fsnotify.Watcher
}

func (l *HotLoader) Watch(ctx context.Context) {
    for {
        select {
        case <-ctx.Done():
            return
        case event := <-l.watcher.Events:
            if event.Has(fsnotify.Write) && filepath.Ext(event.Name) == ".so" {
                l.reload(event.Name)
            }
        case err := <-l.watcher.Errors:
            log.Printf("watcher error: %v", err)
        }
    }
}

func (l *HotLoader) reload(path string) {
    newPlugin, err := LoadPlugin(path)
    if err != nil {
        log.Printf("reload %s failed: %v", path, err)
        return
    }

    name := newPlugin.Name()
    l.mu.Lock()
    old := l.plugins[name]
    l.plugins[name] = newPlugin
    l.mu.Unlock()

    // Stop old plugin gracefully
    if old != nil {
        ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
        defer cancel()
        old.Stop(ctx)
    }

    // Start new plugin
    if err := newPlugin.Start(context.Background()); err != nil {
        log.Printf("start %s failed: %v", name, err)
    }

    log.Printf("Reloaded plugin: %s", name)
}
```

---

## Step 5: WASM-Based Plugins

```go
// WASM plugins: isolation without process overhead
// Each plugin is a .wasm file, run in a sandboxed WASM runtime

// Using wazero (pure Go WASM runtime)
package wasm

import (
    "context"
    "github.com/tetratelabs/wazero"
    "github.com/tetratelabs/wazero/api"
)

type WASMPlugin struct {
    runtime wazero.Runtime
    module  api.Module
    name    string
}

func LoadWASMPlugin(path string) (*WASMPlugin, error) {
    ctx := context.Background()
    r := wazero.NewRuntime(ctx)

    wasmBytes, err := os.ReadFile(path)
    if err != nil {
        return nil, err
    }

    // Instantiate with host function imports
    mod, err := r.Instantiate(ctx, wasmBytes)
    if err != nil {
        r.Close(ctx)
        return nil, err
    }

    return &WASMPlugin{runtime: r, module: mod}, nil
}

func (p *WASMPlugin) Execute(input []byte) ([]byte, error) {
    ctx := context.Background()

    // Allocate memory in WASM module
    malloc := p.module.ExportedFunction("malloc")
    free   := p.module.ExportedFunction("free")
    process := p.module.ExportedFunction("process")

    // Call: allocate + write input + call process + read output + free
    results, err := malloc.Call(ctx, uint64(len(input)))
    if err != nil {
        return nil, err
    }
    ptr := results[0]
    defer free.Call(ctx, ptr)

    // Write input to WASM memory
    p.module.Memory().Write(uint32(ptr), input)

    // Execute
    output, err := process.Call(ctx, ptr, uint64(len(input)))
    if err != nil {
        return nil, err
    }

    // Read output
    outPtr, outLen := uint32(output[0]), uint32(output[1])
    bytes, _ := p.module.Memory().Read(outPtr, outLen)
    return bytes, nil
}
```

---

## Step 6: Capability-Based Security

```go
// Limit what plugins can do via capability interfaces
package capabilities

type Capability interface {
    Name() string
}

// Each capability is a distinct interface
type HTTPCapability interface {
    Capability
    Get(ctx context.Context, url string) ([]byte, error)
    Post(ctx context.Context, url string, body []byte) ([]byte, error)
}

type DatabaseCapability interface {
    Capability
    Query(ctx context.Context, sql string, args ...interface{}) ([]map[string]interface{}, error)
}

type FileSystemCapability interface {
    Capability
    Read(path string) ([]byte, error)
    Write(path string, data []byte) error
    AllowedPaths() []string  // Sandboxed to specific dirs
}

// Plugin declaration: must declare required capabilities
type PluginManifest struct {
    Name         string   `json:"name"`
    Version      string   `json:"version"`
    Capabilities []string `json:"capabilities"` // ["http", "database:readonly"]
}

// Sandbox: only provide approved capabilities
type PluginSandbox struct {
    plugin     Plugin
    http       HTTPCapability
    db         DatabaseCapability
    fs         FileSystemCapability
    allowedCaps map[string]bool
}

func (s *PluginSandbox) Execute(ctx context.Context, input Input) (Output, error) {
    // Inject only approved capabilities into context
    if s.allowedCaps["http"] {
        ctx = context.WithValue(ctx, httpKey{}, s.http)
    }
    if s.allowedCaps["database:readonly"] {
        ctx = context.WithValue(ctx, dbKey{}, readonlyDB{s.db})
    }
    return s.plugin.Execute(ctx, input)
}
```

---

## Step 7: Plugin Registry

```go
package registry

type PluginRegistry struct {
    plugins map[string]PluginFactory
    mu      sync.RWMutex
}

type PluginFactory func(config map[string]string) (Plugin, error)

func (r *PluginRegistry) Register(name string, factory PluginFactory) {
    r.mu.Lock()
    defer r.mu.Unlock()
    r.plugins[name] = factory
}

func (r *PluginRegistry) Create(name string, config map[string]string) (Plugin, error) {
    r.mu.RLock()
    factory, ok := r.plugins[name]
    r.mu.RUnlock()

    if !ok {
        return nil, fmt.Errorf("plugin %q not registered", name)
    }
    return factory(config)
}

// Auto-discover plugins via init()
// Each plugin package registers itself:
func init() {
    registry.Register("my-plugin", func(config map[string]string) (Plugin, error) {
        return &MyPlugin{config: config}, nil
    })
}
```

---

## Step 8: Capstone — Plugin Build and Load

```bash
docker run --rm golang:1.22-alpine sh -c "cat > /tmp/main.go << 'GOEOF'
package main

import \"fmt\"

// Simulate plugin architecture without .so (Alpine/musl issues)
// Production: go build -buildmode=plugin requires glibc

type Plugin interface {
  Name() string
  Version() string
  Execute(input string) string
}

// Built-in plugin: registered at startup
type GreeterPlugin struct{}
func (p *GreeterPlugin) Name() string    { return \"greeter\" }
func (p *GreeterPlugin) Version() string { return \"v1.0.0\" }
func (p *GreeterPlugin) Execute(input string) string { return \"Hello, \" + input + \"!\" }

type TransformPlugin struct{}
func (p *TransformPlugin) Name() string    { return \"transform\" }
func (p *TransformPlugin) Version() string { return \"v1.0.0\" }
func (p *TransformPlugin) Execute(input string) string {
  result := make([]byte, len(input))
  for i, b := range []byte(input) {
    if b >= 'a' && b <= 'z' { result[i] = b - 32 } else { result[i] = b }
  }
  return string(result)
}

type Registry struct{ plugins map[string]Plugin }
func (r *Registry) Register(p Plugin) { r.plugins[p.Name()] = p }
func (r *Registry) Get(name string) (Plugin, bool) { p, ok := r.plugins[name]; return p, ok }

func main() {
  reg := &Registry{plugins: make(map[string]Plugin)}
  reg.Register(&GreeterPlugin{})
  reg.Register(&TransformPlugin{})
  fmt.Println(\"=== Plugin Architecture Demo ===\")
  for _, name := range []string{\"greeter\", \"transform\"} {
    p, ok := reg.Get(name)
    if !ok { fmt.Printf(\"Plugin %s not found\\n\", name); continue }
    fmt.Printf(\"Plugin: %s@%s\\n\", p.Name(), p.Version())
    fmt.Printf(\"  Execute('world'): %s\\n\", p.Execute(\"world\"))
  }
}
GOEOF
cd /tmp && go run main.go"
```

📸 **Verified Output:**
```
=== Plugin Architecture Demo ===
Plugin: greeter@v1.0.0
  Execute('world'): Hello, world!
Plugin: transform@v1.0.0
  Execute('world'): WORLD
```

---

## Summary

| Approach | Isolation | Cross-Platform | Reload |
|----------|-----------|---------------|--------|
| `plugin` package | None (same process) | Linux/macOS | No |
| hashicorp/go-plugin | Full (subprocess) | All platforms | Kill + restart |
| WASM (wazero) | Sandboxed | All platforms | Yes |
| Interface registry | None | All | Yes (rebuild) |
| Capability-based | API surface | All | With any approach |
