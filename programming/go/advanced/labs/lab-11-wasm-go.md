# Lab 11: Go to WebAssembly (WASM)

**Time:** 45 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm golang:1.22-alpine sh`

## Overview

Compile Go to WebAssembly, use `syscall/js` for DOM interaction, call Go functions from JavaScript, and understand the WASM runtime model and binary size.

---

## Step 1: WASM Compilation Basics

```bash
# Compile Go to WASM
GOOS=js GOARCH=wasm go build -o app.wasm main.go

# Check binary size
wc -c app.wasm        # bytes
ls -lh app.wasm       # human-readable

# The WASM runtime shim (copy to serve with HTML)
cp "$(go env GOROOT)/misc/wasm/wasm_exec.js" .

# Minimize size with tinygo (optional)
# tinygo build -o app.wasm -target=wasm main.go
```

---

## Step 2: Minimal WASM Module

```go
// main.go (compile with GOOS=js GOARCH=wasm)
//go:build js && wasm

package main

import (
	"fmt"
	"syscall/js"
)

func main() {
	fmt.Println("Go WASM module initialized")

	// Register Go functions callable from JavaScript
	js.Global().Set("goAdd", js.FuncOf(add))
	js.Global().Set("goGreet", js.FuncOf(greet))
	js.Global().Set("goFib", js.FuncOf(fib))

	// Keep alive (don't exit main — WASM module must stay running)
	select {}
}

func add(_ js.Value, args []js.Value) interface{} {
	if len(args) != 2 {
		return "error: expected 2 arguments"
	}
	return args[0].Int() + args[1].Int()
}

func greet(_ js.Value, args []js.Value) interface{} {
	if len(args) == 0 {
		return "Hello from Go WASM!"
	}
	name := args[0].String()
	return fmt.Sprintf("Hello, %s! (from Go WASM)", name)
}

func fib(_ js.Value, args []js.Value) interface{} {
	if len(args) == 0 {
		return 0
	}
	n := args[0].Int()
	return fibonacci(n)
}

func fibonacci(n int) int {
	if n <= 1 {
		return n
	}
	a, b := 0, 1
	for i := 2; i <= n; i++ {
		a, b = b, a+b
	}
	return b
}
```

---

## Step 3: DOM Interaction with `syscall/js`

```go
//go:build js && wasm

package main

import (
	"fmt"
	"syscall/js"
	"time"
)

func main() {
	doc := js.Global().Get("document")

	// Create and append DOM elements
	div := doc.Call("createElement", "div")
	div.Set("id", "go-output")
	div.Set("textContent", "Go WASM loaded at "+time.Now().Format("15:04:05"))
	doc.Get("body").Call("appendChild", div)

	// Read DOM values
	updateDOM := js.FuncOf(func(_ js.Value, args []js.Value) interface{} {
		input := doc.Call("getElementById", "name-input")
		name := input.Get("value").String()
		output := doc.Call("getElementById", "go-output")
		output.Set("textContent", fmt.Sprintf("Hello, %s! (from Go)", name))
		return nil
	})
	js.Global().Set("updateFromGo", updateDOM)

	// Event listener
	btn := doc.Call("getElementById", "go-btn")
	if !btn.IsNull() {
		btn.Call("addEventListener", "click", js.FuncOf(func(_ js.Value, _ []js.Value) interface{} {
			updateDOM.Invoke(nil, nil)
			return nil
		}))
	}

	select {}
}
```

---

## Step 4: HTML Host Page

```html
<!-- index.html -->
<!DOCTYPE html>
<html>
<head>
  <title>Go WASM Demo</title>
</head>
<body>
  <h1>Go WebAssembly</h1>
  <input id="name-input" placeholder="Enter your name" />
  <button id="go-btn">Greet from Go</button>
  <div id="go-output"></div>

  <!-- WASM runtime -->
  <script src="wasm_exec.js"></script>
  <script>
    const go = new Go();
    WebAssembly.instantiateStreaming(fetch("app.wasm"), go.importObject)
      .then(result => {
        go.run(result.instance);

        // Call Go functions from JavaScript
        console.log("goAdd(3, 4) =", window.goAdd(3, 4));
        console.log("goGreet('World') =", window.goGreet("World"));
        console.log("goFib(10) =", window.goFib(10));
      });
  </script>
</body>
</html>
```

---

## Step 5: Bidirectional Calls

```go
//go:build js && wasm

package main

import (
	"fmt"
	"syscall/js"
)

// Promise wrapper for async Go operations
func asyncFetch(_ js.Value, args []js.Value) interface{} {
	url := args[0].String()

	// Return a JavaScript Promise
	handler := js.FuncOf(func(_ js.Value, promiseArgs []js.Value) interface{} {
		resolve := promiseArgs[0]
		reject := promiseArgs[1]

		go func() {
			// Simulate async work (in real code, use net/http if supported)
			result := fmt.Sprintf("fetched: %s (from Go goroutine)", url)
			resolve.Invoke(result)
			_ = reject
		}()
		return nil
	})

	promiseConstructor := js.Global().Get("Promise")
	return promiseConstructor.New(handler)
}

// Callback from JavaScript → Go
func processData(_ js.Value, args []js.Value) interface{} {
	if len(args) < 2 {
		return "error: need data and callback"
	}
	data := args[0].String()
	callback := args[1]

	go func() {
		result := fmt.Sprintf("processed: %q (length=%d)", data, len(data))
		callback.Invoke(result)
	}()
	return nil
}

func main() {
	js.Global().Set("goAsyncFetch", js.FuncOf(asyncFetch))
	js.Global().Set("goProcessData", js.FuncOf(processData))
	fmt.Println("Go WASM: bidirectional functions registered")
	select {}
}
```

---

## Step 6: WASM Binary Size Analysis

```bash
# Standard Go WASM (includes full Go runtime)
GOOS=js GOARCH=wasm go build -o app.wasm main.go
ls -lh app.wasm
# ~2MB for a simple program (Go runtime included)

# With optimization flags
GOOS=js GOARCH=wasm go build -ldflags="-s -w" -o app.wasm main.go
ls -lh app.wasm

# Compress with wasm-opt (from binaryen)
# wasm-opt -O3 --enable-bulk-memory -o app.opt.wasm app.wasm

# TinyGo (much smaller, subset of Go)
# tinygo build -o tiny.wasm -target=wasm ./...
# ls -lh tiny.wasm  # typically 10-100KB
```

> 💡 **Standard Go WASM is ~2MB** because it includes the full Go runtime (scheduler, GC, etc.). For minimal binaries, use [TinyGo](https://tinygo.org/) which produces 10-100KB WASM files.

---

## Step 7: Serve WASM Locally

```go
// serve.go — development HTTP server for WASM
package main

import (
	"fmt"
	"log"
	"net/http"
)

func main() {
	fs := http.FileServer(http.Dir("."))
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		// Set correct MIME type for .wasm files
		if r.URL.Path[len(r.URL.Path)-5:] == ".wasm" {
			w.Header().Set("Content-Type", "application/wasm")
		}
		// Required headers for cross-origin isolation (SharedArrayBuffer)
		w.Header().Set("Cross-Origin-Opener-Policy", "same-origin")
		w.Header().Set("Cross-Origin-Embedder-Policy", "require-corp")
		fs.ServeHTTP(w, r)
	})
	fmt.Println("Serving at http://localhost:8080")
	log.Fatal(http.ListenAndServe(":8080", nil))
}
```

---

## Step 8: Capstone — Compile and Measure

```bash
docker run --rm golang:1.22-alpine sh -c "
mkdir -p /tmp/wasm_lab

cat > /tmp/wasm_lab/main.go << 'GOEOF'
//go:build js && wasm

package main

import (
	\"fmt\"
	\"syscall/js\"
)

func add(_ js.Value, args []js.Value) interface{} {
	if len(args) != 2 { return \"error: need 2 args\" }
	return args[0].Int() + args[1].Int()
}

func greet(_ js.Value, args []js.Value) interface{} {
	name := args[0].String()
	return fmt.Sprintf(\"Hello from Go WASM, %s!\", name)
}

func main() {
	js.Global().Set(\"goAdd\", js.FuncOf(add))
	js.Global().Set(\"goGreet\", js.FuncOf(greet))
	fmt.Println(\"Go WASM module loaded\")
	select {}
}
GOEOF

cd /tmp/wasm_lab
GOOS=js GOARCH=wasm go build -o app.wasm main.go
echo 'Build successful!'
echo -n 'Binary size (bytes): '
wc -c < app.wasm
ls -lh app.wasm

# With size optimization
GOOS=js GOARCH=wasm go build -ldflags='-s -w' -o app_opt.wasm main.go
echo -n 'Optimized size (bytes): '
wc -c < app_opt.wasm
ls -lh app_opt.wasm

# Copy WASM exec shim
cp \$(go env GOROOT)/misc/wasm/wasm_exec.js .
echo -n 'wasm_exec.js size: '
wc -c < wasm_exec.js"
```

📸 **Verified Output:**
```
Build successful!
Binary size (bytes): 2160499
-rwxr-xr-x    1 root     root        2.1M Mar  6 18:38 app.wasm
Optimized size (bytes): 1594064
-rwxr-xr-x    1 root     root        1.5M Mar  6 18:38 app_opt.wasm
wasm_exec.js size: 17430
```

---

## Summary

| Aspect | Value | Notes |
|--------|-------|-------|
| Binary size (stdlib) | ~2.1MB | Includes full Go runtime |
| Binary size (-s -w) | ~1.5MB | Stripped symbols |
| Binary size (TinyGo) | ~10-100KB | Subset of Go |
| `syscall/js` | DOM access | js.Value wrapper |
| Go → JS | `js.Global().Set(name, FuncOf(fn))` | Export functions |
| JS → Go | `js.FuncOf(fn).Invoke(args...)` | Callback pattern |
| Async | Return `Promise.new(handler)` | Go goroutine inside |

**Key Takeaways:**
- Build tag `//go:build js && wasm` restricts code to WASM target
- `select {}` in `main()` keeps the WASM module alive
- `js.FuncOf` wraps Go functions for JavaScript consumption
- Always call `.Release()` on `js.Func` to prevent goroutine leaks
- Use `-ldflags="-s -w"` to strip debug symbols and reduce binary size
- TinyGo for production WASM (smaller), standard Go for complex programs
