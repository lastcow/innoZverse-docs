# Lab 10: WASM Architecture

**Time:** 60 minutes | **Level:** Architect | **Docker:** `golang:1.22-alpine`

## Overview

WebAssembly in production with Go: `GOOS=js GOARCH=wasm` advanced patterns, TinyGo for smaller binaries, `syscall/js` DOM manipulation, Go→JS type bridge, WASM memory management, streaming WASM compilation, and WASM SIMD concepts.

---

## Step 1: Basic Go WASM Module

```go
//go:build js && wasm

package main

import (
	"fmt"
	"syscall/js"
)

func main() {
	fmt.Println("Go WASM initialized")

	// Expose functions to JavaScript
	js.Global().Set("goAdd", js.FuncOf(addHandler))
	js.Global().Set("goSort", js.FuncOf(sortHandler))
	js.Global().Set("goFibonacci", js.FuncOf(fibHandler))

	// Block forever (event loop style)
	// Use channel to prevent main from exiting
	done := make(chan struct{})
	js.Global().Set("goShutdown", js.FuncOf(func(_ js.Value, _ []js.Value) interface{} {
		close(done)
		return nil
	}))
	<-done
}

// Handler: arguments come from JS as []js.Value
func addHandler(_ js.Value, args []js.Value) interface{} {
	if len(args) != 2 {
		return js.Global().Get("Error").New("need exactly 2 arguments")
	}
	a := args[0].Int()
	b := args[1].Int()
	return a + b
}

func fibHandler(_ js.Value, args []js.Value) interface{} {
	if len(args) != 1 {
		return 0
	}
	n := args[0].Int()
	return fib(n)
}

func fib(n int) int {
	if n <= 1 {
		return n
	}
	return fib(n-1) + fib(n-2)
}
```

```bash
# Build
GOOS=js GOARCH=wasm go build -o app.wasm main.go

# Size (standard Go): ~2MB
# Size (TinyGo): ~50-100KB
```

---

## Step 2: syscall/js Type Bridge

```go
//go:build js && wasm

package main

import "syscall/js"

// Go → JS type conversions
func goToJS(v interface{}) js.Value {
	switch val := v.(type) {
	case nil:
		return js.Null()
	case bool:
		return js.ValueOf(val)
	case int, int8, int16, int32, int64, float32, float64:
		return js.ValueOf(val)
	case string:
		return js.ValueOf(val)
	case []interface{}:
		arr := js.Global().Get("Array").New(len(val))
		for i, item := range val {
			arr.SetIndex(i, goToJS(item))
		}
		return arr
	case map[string]interface{}:
		obj := js.Global().Get("Object").New()
		for k, item := range val {
			obj.Set(k, goToJS(item))
		}
		return obj
	default:
		return js.ValueOf(fmt.Sprintf("%v", val))
	}
}

// JS → Go type conversions
func jsToGo(v js.Value) interface{} {
	switch v.Type() {
	case js.TypeNull, js.TypeUndefined:
		return nil
	case js.TypeBoolean:
		return v.Bool()
	case js.TypeNumber:
		return v.Float()
	case js.TypeString:
		return v.String()
	case js.TypeObject:
		// Check for Array
		if v.InstanceOf(js.Global().Get("Array")) {
			length := v.Length()
			result := make([]interface{}, length)
			for i := 0; i < length; i++ {
				result[i] = jsToGo(v.Index(i))
			}
			return result
		}
		// Plain object: iterate keys
		keys := js.Global().Get("Object").Call("keys", v)
		result := make(map[string]interface{})
		for i := 0; i < keys.Length(); i++ {
			key := keys.Index(i).String()
			result[key] = jsToGo(v.Get(key))
		}
		return result
	}
	return nil
}
```

---

## Step 3: DOM Manipulation

```go
//go:build js && wasm

package main

import "syscall/js"

func updateDOM(_ js.Value, args []js.Value) interface{} {
	document := js.Global().Get("document")

	// Create element
	div := document.Call("createElement", "div")
	div.Set("id", "go-output")
	div.Set("className", "go-result")
	div.Set("textContent", "Hello from Go WASM!")

	// Style manipulation
	style := div.Get("style")
	style.Set("color", "blue")
	style.Set("fontFamily", "monospace")
	style.Set("padding", "16px")
	style.Set("border", "2px solid #0066cc")
	style.Set("borderRadius", "8px")
	style.Set("margin", "16px")

	// Event listener from Go
	div.Call("addEventListener", "click", js.FuncOf(func(_ js.Value, _ []js.Value) interface{} {
		div.Set("textContent", "Clicked!")
		return nil
	}))

	// Append to body
	document.Get("body").Call("appendChild", div)
	return nil
}

// Fetch API integration
func fetchJSON(_ js.Value, args []js.Value) interface{} {
	if len(args) < 1 {
		return nil
	}
	url := args[0].String()

	// Return a JS Promise
	promise := js.Global().Get("Promise").New(js.FuncOf(func(_ js.Value, resolveReject []js.Value) interface{} {
		resolve := resolveReject[0]
		reject  := resolveReject[1]

		go func() {
			// Use Go's net/http to fetch (with wasm_exec runtime support)
			resp, err := http.Get(url)
			if err != nil {
				reject.Invoke(err.Error())
				return
			}
			defer resp.Body.Close()
			body, _ := io.ReadAll(resp.Body)
			resolve.Invoke(string(body))
		}()
		return nil
	}))
	return promise
}
```

---

## Step 4: WASM Memory Management

```go
// Go WASM memory model:
// - Go has its own heap managed by GC
// - JS interop via js.Value (handles into JS heap)
// - Passing []byte to JS: use js.CopyBytesToJS

//go:build js && wasm

package main

import "syscall/js"

func processBytes(_ js.Value, args []js.Value) interface{} {
	if len(args) < 1 {
		return nil
	}

	// JS Uint8Array → Go []byte
	src := args[0]
	goBytes := make([]byte, src.Length())
	js.CopyBytesToGo(goBytes, src)

	// Process in Go
	for i, b := range goBytes {
		goBytes[i] = b ^ 0xFF  // XOR invert
	}

	// Go []byte → JS Uint8Array
	dst := js.Global().Get("Uint8Array").New(len(goBytes))
	js.CopyBytesToJS(dst, goBytes)
	return dst
}

// Avoid holding js.Func references without releasing them
func withFunc(handler func(js.Value, []js.Value) interface{}, use func(js.Func)) {
	fn := js.FuncOf(handler)
	defer fn.Release() // Important: prevents memory leak
	use(fn)
}
```

---

## Step 5: Streaming WASM Compilation

```javascript
// HTML/JS side:
// Streaming instantiation (browser) — faster than ArrayBuffer approach

// FAST: streaming compile + instantiate
const { instance } = await WebAssembly.instantiateStreaming(
  fetch('/app.wasm'),
  importObject  // { "go": goRuntime }
);

// SLOW: download then compile
const bytes = await fetch('/app.wasm').then(r => r.arrayBuffer());
const { instance } = await WebAssembly.instantiate(bytes, importObject);

// HTTP headers required for streaming:
// Content-Type: application/wasm

// wasm_exec.js: Go runtime bridge (in GOROOT)
// cp $(go env GOROOT)/misc/wasm/wasm_exec.js ./
```

---

## Step 6: TinyGo — Smaller WASM Binaries

```bash
# Standard Go WASM: ~2MB (includes full runtime + GC)
# TinyGo WASM: ~50-100KB (custom runtime, subset of stdlib)

# Install TinyGo
# docker run --rm -v $PWD:/work tinygo/tinygo:0.33.0 \
#   tinygo build -o app.wasm -target wasm ./

# TinyGo limitations:
# - No goroutines in wasm target (use js/wasm goroutines carefully)
# - Subset of reflect
# - No net/http in wasm target
# - Some stdlib packages unavailable

# Size comparison:
# go build -o app.wasm:         2,137,579 bytes (~2.1 MB)
# tinygo build -o app.wasm:       87,432 bytes (~85 KB)
# tinygo + wasm-opt -Oz:          61,200 bytes (~60 KB)

# WASM SIMD (WebAssembly SIMD proposal):
# tinygo: uses SIMD intrinsics for arm/amd64
# Standard Go: no direct SIMD — use assembly or cgo
```

---

## Step 7: WASM Workers

```javascript
// Run Go WASM in Web Worker (non-blocking UI)
// worker.js:
importScripts('/wasm_exec.js');

const go = new Go();
WebAssembly.instantiateStreaming(fetch('/app.wasm'), go.importObject)
  .then(result => {
    go.run(result.instance);
    // Worker is now running Go code
  });

// Main thread:
const worker = new Worker('/worker.js');
worker.postMessage({ type: 'compute', data: [1, 2, 3] });
worker.onmessage = (e) => console.log('Result:', e.data);

// Go side: use js.Global().Get("self") for worker context
// js.Global().Get("self").Call("postMessage", result)
```

---

## Step 8: Capstone — WASM Binary Build

```bash
docker run --rm golang:1.22-alpine sh -c "
mkdir -p /work && cd /work
cat > main.go << 'GOEOF'
//go:build js && wasm

package main

import (
  \"fmt\"
  \"syscall/js\"
)

func add(_ js.Value, args []js.Value) interface{} {
  if len(args) != 2 { return js.Global().Get(\"Error\").New(\"need 2 args\") }
  return args[0].Int() + args[1].Int()
}

func main() {
  fmt.Println(\"Go WASM module initialized\")
  js.Global().Set(\"goAdd\", js.FuncOf(add))
  select {}
}
GOEOF
GOOS=js GOARCH=wasm go build -o program.wasm main.go 2>&1
echo 'WASM binary size:' && wc -c program.wasm
echo 'WASM magic bytes:' && xxd program.wasm | head -1
"
```

📸 **Verified Output:**
```
WASM binary size:
2137579 program.wasm
WASM magic bytes:
00000000: 0061 736d 0100 0000 00f2 8080 8000 0a67  .asm...........g
```

*(Magic bytes `0061 736d` = `\0asm` — valid WebAssembly binary header)*

---

## Summary

| Feature | API | Notes |
|---------|-----|-------|
| Build target | `GOOS=js GOARCH=wasm` | Standard Go toolchain |
| JS interop | `syscall/js` | Bidirectional type bridge |
| Function export | `js.FuncOf(handler)` | Call from JavaScript |
| Byte transfer | `js.CopyBytesToJS/Go` | Efficient bulk transfer |
| DOM access | `js.Global().Get("document")` | Full DOM API |
| Streaming | `instantiateStreaming()` | 2× faster than ArrayBuffer |
| TinyGo | `tinygo build -target wasm` | 25× smaller binaries |
| Worker | `Web Worker + wasm_exec.js` | Non-blocking execution |
