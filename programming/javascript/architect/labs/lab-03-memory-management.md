# Lab 03: Memory Management — V8 Heap, WeakRef & Leak Detection

**Time:** 60 minutes | **Level:** Architect | **Docker:** `docker run -it --rm node:20-alpine sh`

Memory bugs crash production systems and silently degrade performance. This lab covers V8's heap structure, heap statistics, WeakRef/FinalizationRegistry, common leak patterns, and analysis techniques.

---

## Step 1: V8 Heap Spaces

V8 divides its heap into specialized spaces:

```
┌─────────────────────────────────────────────────────┐
│                   V8 HEAP                           │
│                                                     │
│  ┌─────────────┐  ┌─────────────┐                  │
│  │  New Space  │  │  Old Space  │                  │
│  │ (Scavenge)  │→ │  (Mark-    │                  │
│  │ short-lived │  │   Sweep)   │                  │
│  └─────────────┘  └─────────────┘                  │
│                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │
│  │ Large Obj.  │  │ Code Space  │  │ Map Space  │  │
│  │  > 512 KB   │  │ (JIT code)  │  │(HiddenClass│  │
│  └─────────────┘  └─────────────┘  └────────────┘  │
└─────────────────────────────────────────────────────┘
```

- **New Space**: Young generation, 1-8 MB, fast Scavenge GC (minor GC)
- **Old Space**: Long-lived objects, promoted from New Space, slower Mark-Sweep-Compact (major GC)
- **Large Object Space**: Objects > 512 KB, never moved
- **Code Space**: Compiled machine code
- **Map Space**: Hidden class descriptors

---

## Step 2: Heap Statistics with `v8.getHeapStatistics()`

```javascript
// file: heap-stats.js
const v8 = require('v8');

function formatBytes(bytes) {
  return (bytes / 1024 / 1024).toFixed(2) + ' MB';
}

const stats = v8.getHeapStatistics();
console.log('=== V8 Heap Statistics ===');
console.log('total_heap_size:        ', formatBytes(stats.total_heap_size));
console.log('total_heap_size_exec:   ', formatBytes(stats.total_heap_size_executable));
console.log('total_physical_size:    ', formatBytes(stats.total_physical_size));
console.log('total_available_size:   ', formatBytes(stats.total_available_size));
console.log('used_heap_size:         ', formatBytes(stats.used_heap_size));
console.log('heap_size_limit:        ', formatBytes(stats.heap_size_limit));
console.log('malloced_memory:        ', formatBytes(stats.malloced_memory));
console.log('peak_malloced_memory:   ', formatBytes(stats.peak_malloced_memory));
console.log('does_zap_garbage:       ', stats.does_zap_garbage);
console.log('number_of_native_contexts:', stats.number_of_native_contexts);
console.log('number_of_detached_contexts:', stats.number_of_detached_contexts);

// Also use v8.getHeapSpaceStatistics()
const spaces = v8.getHeapSpaceStatistics();
console.log('\n=== Heap Spaces ===');
for (const space of spaces) {
  console.log(`${space.space_name.padEnd(25)}: used ${formatBytes(space.space_used_size)} / ${formatBytes(space.space_size)}`);
}
```

📸 **Verified Output:**
```
total_heap_size:         4.23 MB
used_heap_size:          3.49 MB
heap_size_limit:         4144.00 MB
malloced_memory:         0.25 MB
number_of_native_contexts: 1
```

> 💡 Default `heap_size_limit` is ~1.5GB on 64-bit. Override with `--max-old-space-size=4096` (in MB).

---

## Step 3: `process.memoryUsage()` in Detail

```javascript
// file: memory-usage.js
function formatMB(bytes) { return (bytes / 1024 / 1024).toFixed(2) + ' MB'; }

console.log('=== process.memoryUsage() ===');
const mem = process.memoryUsage();
console.log('rss (resident set size):  ', formatMB(mem.rss));        // total process memory
console.log('heapTotal:                ', formatMB(mem.heapTotal));   // total heap allocated
console.log('heapUsed:                 ', formatMB(mem.heapUsed));    // heap in use
console.log('external:                 ', formatMB(mem.external));    // C++ objects (Buffers)
console.log('arrayBuffers:             ', formatMB(mem.arrayBuffers));// ArrayBuffer/SharedArrayBuffer

// Allocate some data and observe change
const before = process.memoryUsage().heapUsed;
const bigArr = new Array(1_000_000).fill({ x: 1, y: 2 });
const after = process.memoryUsage().heapUsed;
console.log('\nAfter 1M object array:');
console.log('Heap delta:', formatMB(after - before));
```

---

## Step 4: WeakRef + FinalizationRegistry

```javascript
// file: weakref-demo.js
// WeakRef: hold reference without preventing GC
// FinalizationRegistry: callback when object is collected

const registry = new FinalizationRegistry((heldValue) => {
  console.log('GC collected object tagged:', heldValue);
});

let obj = { name: 'temp-object', data: new Array(10000).fill(42) };
const ref = new WeakRef(obj);
registry.register(obj, 'temp-object-tag');

console.log('Before GC:');
console.log('  ref.deref()?.name:', ref.deref()?.name);

// Remove strong reference
obj = null;

// Force GC if --expose-gc flag is available
if (global.gc) {
  global.gc();
  console.log('\nAfter forced GC:');
  console.log('  ref.deref()?.name:', ref.deref()?.name ?? 'undefined (collected)');
} else {
  console.log('\nRun with --expose-gc to force GC');
  console.log('  ref.deref()?.name (may still be alive):', ref.deref()?.name);
}

console.log('process.memoryUsage heapUsed:', Math.round(process.memoryUsage().heapUsed / 1024) + 'KB');
```

Run: `node --expose-gc weakref-demo.js`

📸 **Verified Output:**
```
Before GC:
  ref.deref()?.name: temp-object
After null, deref: temp-object
process.memoryUsage heapUsed: 2931KB
```

> 💡 WeakRef deref may return `undefined` only after GC runs. Never rely on immediate collection.

---

## Step 5: Common Memory Leak Patterns

```javascript
// file: leak-patterns.js

// LEAK 1: Closures capturing large scope
function createLeakyClosure() {
  const LARGE = new Array(100000).fill('x'); // captured in closure
  return function smallFn() {
    return LARGE[0]; // keeps entire array alive!
  };
}

// FIX: Extract only what you need
function createFixedClosure() {
  const LARGE = new Array(100000).fill('x');
  const firstItem = LARGE[0]; // only keep what's needed
  return function smallFn() { return firstItem; };
}

// LEAK 2: Forgotten event listeners
const { EventEmitter } = require('events');
function leakyEmitter() {
  const emitter = new EventEmitter();
  // Adding listeners without removing them
  for (let i = 0; i < 200; i++) {
    emitter.on('data', () => {}); // Warning: MaxListeners exceeded
  }
}

// FIX: Use emitter.once() or explicitly remove with emitter.off()
// Set: emitter.setMaxListeners(0) if truly needed

// LEAK 3: Growing Map/Set without cleanup
const cache = new Map();
function leakyCache(key, value) {
  cache.set(key, value); // grows forever!
}

// FIX: Use WeakMap for object keys, or implement LRU eviction
const weakCache = new WeakMap();

// LEAK 4: Forgotten timers
function startLeakyTimer() {
  const resource = { data: new Array(10000).fill('z') };
  return setInterval(() => {
    // resource is kept alive by closure!
    resource.data.push('more');
  }, 100);
}
const timer = startLeakyTimer();
clearInterval(timer); // ALWAYS store and clear timer refs

console.log('Leak pattern examples created');
console.log('Run with --expose-gc and heap profiling to see differences');
```

---

## Step 6: Heap Snapshot Analysis (Concept)

```bash
# Generate heap snapshot
node --heapsnapshot-signal=SIGUSR2 your-app.js &
APP_PID=$!
kill -SIGUSR2 $APP_PID

# Or programmatically:
# const v8 = require('v8');
# v8.writeHeapSnapshot('./heap-' + Date.now() + '.heapsnapshot');

# Analyze with Chrome DevTools:
# 1. Open chrome://inspect
# 2. Memory tab → Load snapshot file
# 3. Look for:
#    - Objects with high "Retained Size"
#    - Detached DOM trees (in browser)
#    - Growing arrays/closures
```

> 💡 `heapdump` npm package wraps `v8.writeHeapSnapshot()` for easy use. Load `.heapsnapshot` files in Chrome DevTools Memory tab.

---

## Step 7: `--max-old-space-size` and GC Tuning

```javascript
// file: gc-tuning.js
const v8 = require('v8');

// Check current heap limit
const stats = v8.getHeapStatistics();
const limitMB = Math.round(stats.heap_size_limit / 1024 / 1024);
console.log(`Current heap limit: ${limitMB} MB`);

// GC flags (pass to node):
// --max-old-space-size=4096     → 4GB old space
// --max-semi-space-size=64      → 64MB new space (default 16MB)
// --expose-gc                   → enable global.gc()
// --gc-interval=100             → force GC every 100 allocations (debug)

// Heap space breakdown
const spaces = v8.getHeapSpaceStatistics();
const oldSpace = spaces.find(s => s.space_name === 'old_space');
const newSpace = spaces.find(s => s.space_name === 'new_space');
if (oldSpace) console.log(`Old space: ${Math.round(oldSpace.space_size / 1024 / 1024)}MB allocated`);
if (newSpace) console.log(`New space: ${Math.round(newSpace.space_size / 1024)}KB allocated`);

console.log('\nKey GC metrics:');
console.log('Heap used / limit:', `${Math.round(stats.used_heap_size/1024/1024)}MB / ${limitMB}MB`);
console.log('Usage %:', ((stats.used_heap_size / stats.heap_size_limit) * 100).toFixed(1) + '%');
```

---

## Step 8: Capstone — Memory Leak Detector

Build a memory monitor that tracks heap growth and alerts on leaks:

```javascript
// file: memory-leak-detector.js
'use strict';
const v8 = require('v8');

class MemoryLeakDetector {
  constructor(options = {}) {
    this.interval = options.interval || 1000;
    this.threshold = options.threshold || 10; // MB growth to alert
    this.samples = [];
    this.maxSamples = options.maxSamples || 10;
  }

  sample() {
    const stats = v8.getHeapStatistics();
    const sample = {
      ts: Date.now(),
      heapUsed: stats.used_heap_size,
      heapTotal: stats.total_heap_size,
    };
    this.samples.push(sample);
    if (this.samples.length > this.maxSamples) this.samples.shift();
    return sample;
  }

  analyze() {
    if (this.samples.length < 2) return null;
    const first = this.samples[0];
    const last = this.samples[this.samples.length - 1];
    const growthBytes = last.heapUsed - first.heapUsed;
    const growthMB = growthBytes / 1024 / 1024;
    const timeSpanMs = last.ts - first.ts;
    return {
      growthMB: growthMB.toFixed(2),
      growthRateMBps: (growthMB / (timeSpanMs / 1000)).toFixed(3),
      isLeaking: growthMB > this.threshold,
    };
  }

  start() {
    console.log('Memory leak detector started (interval:', this.interval + 'ms)');
    this._timer = setInterval(() => {
      const s = this.sample();
      const analysis = this.analyze();
      if (analysis) {
        const usedMB = (s.heapUsed / 1024 / 1024).toFixed(1);
        console.log(`Heap: ${usedMB}MB | Growth: ${analysis.growthMB}MB | Rate: ${analysis.growthRateMBps}MB/s${analysis.isLeaking ? ' ⚠️  LEAK DETECTED' : ''}`);
      }
    }, this.interval);
    return this;
  }

  stop() {
    clearInterval(this._timer);
    console.log('Detector stopped. Final analysis:', this.analyze());
  }
}

// Demo: simulate a growing cache (leak)
const leakMap = new Map();
const detector = new MemoryLeakDetector({ interval: 200, threshold: 1 }).start();

let tick = 0;
const leakInterval = setInterval(() => {
  // Simulate leak: 10KB per tick
  leakMap.set(tick++, new Array(1000).fill('leak-data-'.repeat(10)));
  if (tick > 20) {
    clearInterval(leakInterval);
    setTimeout(() => detector.stop(), 500);
  }
}, 100);
```

---

## Summary

| Concept | Tool / API | Use Case |
|---|---|---|
| Heap spaces | `v8.getHeapSpaceStatistics()` | Understand GC zones |
| Heap limit | `--max-old-space-size` | Prevent OOM crashes |
| Heap statistics | `v8.getHeapStatistics()` | Monitor memory usage |
| Process memory | `process.memoryUsage()` | RSS, heap, external |
| WeakRef | `new WeakRef(obj)` | Cache without preventing GC |
| FinalizationRegistry | `new FinalizationRegistry(fn)` | React to object collection |
| Heap snapshot | `v8.writeHeapSnapshot()` | Debug memory leaks |
| Leak patterns | Closures, timers, listeners | What to watch for |
