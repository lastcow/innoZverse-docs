# Lab 05: Native Addons — N-API, node-gyp & FFI

**Time:** 60 minutes | **Level:** Architect | **Docker:** `docker run -it --rm node:20-alpine sh`

Native addons let Node.js call C/C++ code directly, unlocking SIMD, hardware I/O, legacy libraries, and extreme performance. This lab covers N-API with node-addon-api, node-gyp compilation, and FFI as an alternative.

---

## Step 1: Why Native Addons?

Use cases:
- CPU-intensive algorithms (image processing, crypto, compression)
- System-level APIs (hardware access, OS-specific features)
- Wrapping existing C/C++ libraries (OpenCV, BLAS, SQLite)
- Real-time constraints (audio processing, robotics)

**N-API** (Node-API) provides a stable ABI — addons compiled for Node 16 work on Node 20+ without recompilation.

---

## Step 2: Install Build Tools

```bash
# In Docker container:
apk add --no-cache python3 make g++ py3-pip
npm install -g node-gyp

# On Debian/Ubuntu:
# apt install python3 make g++ -y
# npm install -g node-gyp
```

> 💡 node-gyp uses Python to drive the GYP build system (Google's build tool). Always have Python 3.x installed.

---

## Step 3: C Source — N-API Hello World

```c
// file: hello.c
#include <node_api.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>

// C function: greet(name) -> "Hello, <name> from C!"
napi_value Greet(napi_env env, napi_callback_info info) {
    napi_status status;
    size_t argc = 1;
    napi_value args[1];

    // Get arguments
    status = napi_get_cb_info(env, info, &argc, args, NULL, NULL);
    if (status != napi_ok || argc < 1) {
        napi_throw_error(env, NULL, "Expected 1 argument");
        return NULL;
    }

    // Get string value from first argument
    size_t str_len = 0;
    napi_get_value_string_utf8(env, args[0], NULL, 0, &str_len);
    char* name = (char*)malloc(str_len + 1);
    napi_get_value_string_utf8(env, args[0], name, str_len + 1, &str_len);

    // Build result string
    char result[256];
    snprintf(result, sizeof(result), "Hello, %s from C!", name);
    free(name);

    // Create and return JS string
    napi_value ret;
    napi_create_string_utf8(env, result, NAPI_AUTO_LENGTH, &ret);
    return ret;
}

// Add function to native integer
napi_value AddInts(napi_env env, napi_callback_info info) {
    size_t argc = 2;
    napi_value args[2];
    napi_get_cb_info(env, info, &argc, args, NULL, NULL);

    int32_t a, b;
    napi_get_value_int32(env, args[0], &a);
    napi_get_value_int32(env, args[1], &b);

    napi_value result;
    napi_create_int32(env, a + b, &result);
    return result;
}

// Module initialization
napi_value Init(napi_env env, napi_value exports) {
    napi_value fn_greet, fn_add;

    napi_create_function(env, "greet", NAPI_AUTO_LENGTH, Greet, NULL, &fn_greet);
    napi_set_named_property(env, exports, "greet", fn_greet);

    napi_create_function(env, "add", NAPI_AUTO_LENGTH, AddInts, NULL, &fn_add);
    napi_set_named_property(env, exports, "add", fn_add);

    return exports;
}

NAPI_MODULE(NODE_GYP_MODULE_NAME, Init)
```

---

## Step 4: binding.gyp Build Configuration

```json
{
  "targets": [
    {
      "target_name": "hello",
      "sources": ["hello.c"],
      "include_dirs": [],
      "cflags": ["-O2", "-Wall"],
      "conditions": [
        ["OS=='win'", { "defines": ["WIN32"] }]
      ]
    }
  ]
}
```

> 💡 `target_name` matches the output filename: `build/Release/hello.node`

---

## Step 5: JavaScript Caller

```javascript
// file: index.js
let addon;
try {
  addon = require('./build/Release/hello.node');
} catch (e) {
  console.error('Build failed, run: node-gyp configure build');
  process.exit(1);
}

console.log('Native greet:', addon.greet('Architect'));
console.log('Native add:', addon.add(42, 58));

// Performance: compare native vs JS add
const ITERATIONS = 10_000_000;
let jsTime = Date.now();
let sum = 0;
for (let i = 0; i < ITERATIONS; i++) sum += (i + 1);
jsTime = Date.now() - jsTime;

let nativeTime = Date.now();
for (let i = 0; i < ITERATIONS; i++) addon.add(i, 1);
nativeTime = Date.now() - nativeTime;

console.log(`\nJS loop: ${jsTime}ms, Native loop: ${nativeTime}ms`);
console.log('Note: FFI overhead dominates for simple operations — native wins for complex work');
```

📸 **Verified Output** (from a real build environment):
```
Native greet: Hello, Architect from C!
Native add: 100
```

> 💡 N-API addons compiled with `node-gyp build` produce `build/Release/<name>.node` — a shared library loaded via `require()`.

---

## Step 6: Using node-addon-api (C++ Wrapper)

`node-addon-api` provides a C++ class-based wrapper over N-API:

```cpp
// file: hello_napi.cc
#include <napi.h>

Napi::String Greet(const Napi::CallbackInfo& info) {
    Napi::Env env = info.Env();
    if (info.Length() < 1 || !info[0].IsString()) {
        Napi::TypeError::New(env, "String expected").ThrowAsJavaScriptException();
        return Napi::String();
    }
    std::string name = info[0].As<Napi::String>();
    return Napi::String::New(env, "Hello, " + name + " from C++!");
}

Napi::Object Init(Napi::Env env, Napi::Object exports) {
    exports.Set("greet", Napi::Function::New(env, Greet));
    return exports;
}

NODE_API_MODULE(hello_napi, Init)
```

```json
// binding.gyp for node-addon-api
{
  "targets": [{
    "target_name": "hello_napi",
    "sources": ["hello_napi.cc"],
    "include_dirs": ["<!@(node -p \"require('node-addon-api').include\")"],
    "dependencies": ["<!(node -p \"require('node-addon-api').gyp\")"],
    "defines": ["NAPI_DISABLE_CPP_EXCEPTIONS"]
  }]
}
```

Install and build:
```bash
npm install node-addon-api
node-gyp configure build
```

---

## Step 7: FFI Alternative with ffi-napi

For calling existing C libraries WITHOUT writing C code:

```javascript
// file: ffi-demo.js
// npm install ffi-napi ref-napi

const ffi = require('ffi-napi');
const ref = require('ref-napi');

// Load libc
const libc = ffi.Library('libc', {
  'printf': ['int', ['string']],
  'strlen': ['size_t', ['string']],
  'abs': ['int', ['int']],
});

console.log('strlen("hello"):', libc.strlen('hello'));
console.log('abs(-42):', libc.abs(-42));

// Load libm (math library)
const libm = ffi.Library('libm', {
  'sqrt': ['double', ['double']],
  'pow': ['double', ['double', 'double']],
  'floor': ['double', ['double']],
});

console.log('sqrt(144):', libm.sqrt(144));
console.log('pow(2, 10):', libm.pow(2, 10));
```

> 💡 `ffi-napi` is great for prototyping. For production, use N-API for stability and performance (no marshaling overhead).

---

## Step 8: Capstone — Native Fibonacci Benchmark

Build a native addon for Fibonacci and compare performance:

```c
// file: fib.c
#include <node_api.h>

long long fibonacci(int n) {
    if (n <= 1) return n;
    long long a = 0, b = 1, temp;
    for (int i = 2; i <= n; i++) {
        temp = a + b;
        a = b;
        b = temp;
    }
    return b;
}

napi_value NativeFib(napi_env env, napi_callback_info info) {
    size_t argc = 1;
    napi_value args[1];
    napi_get_cb_info(env, info, &argc, args, NULL, NULL);

    int32_t n;
    napi_get_value_int32(env, args[0], &n);

    long long result = fibonacci(n);

    napi_value ret;
    napi_create_int64(env, result, &ret);
    return ret;
}

napi_value Init(napi_env env, napi_value exports) {
    napi_value fn;
    napi_create_function(env, "fib", NAPI_AUTO_LENGTH, NativeFib, NULL, &fn);
    napi_set_named_property(env, exports, "fib", fn);
    return exports;
}

NAPI_MODULE(NODE_GYP_MODULE_NAME, Init)
```

```javascript
// file: benchmark.js
const addon = require('./build/Release/fib.node');

// JS implementation
function jsFib(n) {
  if (n <= 1) return n;
  let a = 0, b = 1;
  for (let i = 2; i <= n; i++) { const t = a + b; a = b; b = t; }
  return b;
}

const N = 50;
const ITER = 1_000_000;

console.time('JS fib(50) x1M');
for (let i = 0; i < ITER; i++) jsFib(N);
console.timeEnd('JS fib(50) x1M');

console.time('Native fib(50) x1M');
for (let i = 0; i < ITER; i++) addon.fib(N);
console.timeEnd('Native fib(50) x1M');

console.log(`fib(50) = ${addon.fib(N)}`);
```

Complete setup and run:
```bash
# Install tools
apk add --no-cache python3 make g++
npm install -g node-gyp
npm install node-addon-api

# Build
node-gyp configure build

# Run
node benchmark.js
```

---

## Summary

| Method | Language | Stability | Best For |
|---|---|---|---|
| N-API (C) | C | Stable ABI | Lightweight, system calls |
| node-addon-api | C++ | Stable ABI | Complex addons, OOP patterns |
| ffi-napi | JS | Runtime | Quick bindings to existing .so/.dll |
| WebAssembly | C/Rust | Universal | Portable compute, sandboxed |
| `child_process` | Any | Process | External executables |
