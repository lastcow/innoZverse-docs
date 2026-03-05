# Lab 04: Node.js Performance & Profiling

**Time:** 30 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Profile and optimize Node.js applications: V8 `--prof` flag, flame graphs, deoptimization tracing, heap snapshots, `perf_hooks` PerformanceObserver, and memory leak detection.

---

## Step 1: Performance Measurement with perf_hooks

```javascript
const { performance, PerformanceObserver } = require('node:perf_hooks');
const v8 = require('node:v8');

// Mark and measure
performance.mark('algo:start');

let sum = 0;
for (let i = 0; i < 1e7; i++) sum += i;

performance.mark('algo:end');
performance.measure('loop', 'algo:start', 'algo:end');

const [entry] = performance.getEntriesByName('loop');
console.log(`Loop duration: ${entry.duration.toFixed(2)}ms`);
console.log(`Sum: ${sum}`);

// PerformanceObserver — async notifications
const obs = new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    console.log(`[PERF] ${entry.name}: ${entry.duration.toFixed(2)}ms`);
  }
});
obs.observe({ entryTypes: ['measure', 'function'] });

// Wrap functions for automatic measurement
function timedFunction(name, fn) {
  return function(...args) {
    performance.mark(`${name}:start`);
    const result = fn.apply(this, args);
    performance.mark(`${name}:end`);
    performance.measure(name, `${name}:start`, `${name}:end`);
    return result;
  };
}

const timedSort = timedFunction('quicksort', (arr) => arr.sort());
timedSort(Array.from({length: 100000}, () => Math.random()));
```

---

## Step 2: V8 Heap Statistics

```javascript
const v8 = require('node:v8');
const { performance } = require('node:perf_hooks');

// Current heap state
function printHeapStats() {
  const stats = v8.getHeapStatistics();
  console.log({
    heapUsed: `${(stats.used_heap_size / 1024 / 1024).toFixed(1)} MB`,
    heapTotal: `${(stats.total_heap_size / 1024 / 1024).toFixed(1)} MB`,
    heapLimit: `${(stats.heap_size_limit / 1024 / 1024).toFixed(1)} MB`,
    external: `${(stats.external_memory / 1024 / 1024).toFixed(1)} MB`,
    objects: stats.number_of_native_contexts,
  });
}

// Heap space breakdown
function printHeapSpaces() {
  const spaces = v8.getHeapSpaceStatistics();
  for (const space of spaces) {
    const usedMB = (space.space_used_size / 1024 / 1024).toFixed(2);
    if (parseFloat(usedMB) > 0) {
      console.log(`  ${space.space_name}: ${usedMB} MB used`);
    }
  }
}

printHeapStats();
printHeapSpaces();

// Force GC (requires --expose-gc flag)
// if (global.gc) global.gc();
```

---

## Step 3: Memory Leak Detection

```javascript
const v8 = require('node:v8');

// Common memory leaks patterns and fixes

// LEAK 1: Unbounded cache
const leakyCache = {}; // Grows forever
// FIX: Use WeakMap for object keys
const safeCache = new WeakMap();

// LEAK 2: Event listeners not removed
class LeakyEmitter {
  constructor(emitter) {
    // This listener is never cleaned up!
    emitter.on('data', this.handleData);
  }
  handleData(data) { /* ... */ }
}

class SafeEmitter {
  constructor(emitter) {
    this.emitter = emitter;
    this.handleData = this.handleData.bind(this); // Keep reference
    emitter.on('data', this.handleData);
  }
  handleData(data) { /* ... */ }
  destroy() {
    this.emitter.removeListener('data', this.handleData); // Clean up!
  }
}

// LEAK 3: Closures holding large data
function createLeakyHook() {
  const bigData = new Array(1000000).fill('x'); // 1M items
  return function hook() {
    return bigData[0]; // Forces bigData to stay in memory
  };
}

// FIX: Only capture what you need
function createSafeHook() {
  const firstItem = 'x'; // Only capture what's needed
  return function hook() {
    return firstItem;
  };
}

// Detect memory growth
function detectLeak(intervalMs = 1000, maxChecks = 5) {
  let snapshots = [];
  const interval = setInterval(() => {
    const stats = v8.getHeapStatistics();
    const mb = stats.used_heap_size / 1024 / 1024;
    snapshots.push(mb);

    if (snapshots.length >= maxChecks) {
      clearInterval(interval);
      const growth = snapshots[snapshots.length - 1] - snapshots[0];
      if (growth > 5) { // 5MB growth threshold
        console.warn(`Possible memory leak: +${growth.toFixed(1)}MB in ${maxChecks}s`);
      } else {
        console.log(`Memory stable: ${mb.toFixed(1)}MB`);
      }
    }
  }, intervalMs);
}
```

---

## Step 4: V8 Profiling with --prof

```bash
# Run with profiling enabled
node --prof server.js

# Process the profiling data
node --prof-process isolate-*.log > profile.txt

# Key sections in output:
# [Summary]: % time in JS, C++, GC
# [Bottom up (heavy) profile]: hottest functions
# [Top down (heavy) profile]: call tree

# Example: Profile a CPU-intensive script
cat > /tmp/prof-demo.js << 'EOF'
function heavyComputation() {
  let sum = 0;
  for (let i = 0; i < 1e8; i++) {
    sum += Math.sqrt(i);
  }
  return sum;
}

for (let i = 0; i < 5; i++) {
  heavyComputation();
}
EOF

# node --prof /tmp/prof-demo.js
# node --prof-process isolate-*.log 2>/dev/null | head -30
```

---

## Step 5: Deoptimization Tracing

```javascript
// V8 optimizes "hot" functions, but deoptimizes on type changes

// FAST: Monomorphic (one type)
function addNumbers(a, b) { return a + b; }
for (let i = 0; i < 10000; i++) addNumbers(1, 2); // Optimized for numbers

// SLOW: Polymorphic (multiple types)
// addNumbers(1, 2);     // numbers
// addNumbers('a', 'b'); // strings — causes deoptimization!

// Hidden classes — maintain consistent object shapes
// FAST: Same shape
function createPoint(x, y) { return { x, y }; }
const points = Array.from({length: 10000}, (_, i) => createPoint(i, i * 2));

// SLOW: Different shapes
function createMixed(x, y, addZ) {
  const p = { x, y };
  if (addZ) p.z = 0; // Different hidden class!
  return p;
}

// Arrays: monomorphic is faster
const numbers = new Array(1000).fill(0); // All numbers — fast
// Mixed arrays are slower
// const mixed = [1, 'two', 3, null]; // Polymorphic

// Run with: node --trace-deopt script.js
// Or:       node --trace-ic script.js
```

---

## Step 6: Heap Snapshot

```javascript
const v8 = require('node:v8');
const fs = require('node:fs');

// Write heap snapshot to file
function takeHeapSnapshot(filename = 'heap.heapsnapshot') {
  const snapshot = v8.writeHeapSnapshot(filename);
  console.log(`Heap snapshot written to: ${snapshot}`);
  return snapshot;
}

// Compare two heap states
function heapGrowth(before, after) {
  return {
    heapUsedDelta: ((after.used_heap_size - before.used_heap_size) / 1024 / 1024).toFixed(2) + ' MB',
    externalDelta: ((after.external_memory - before.external_memory) / 1024 / 1024).toFixed(2) + ' MB'
  };
}

const before = v8.getHeapStatistics();

// Create some objects
const bigArray = new Array(100000).fill({ data: 'test' });

const after = v8.getHeapStatistics();
console.log('Heap growth:', heapGrowth(before, after));

// Cleanup
bigArray.length = 0;
// In real app: takeHeapSnapshot('after-request.heapsnapshot');
// Then open in Chrome DevTools Memory tab
```

---

## Step 7: Benchmarking Patterns

```javascript
const { performance } = require('node:perf_hooks');

// Micro-benchmark helper
async function benchmark(name, fn, iterations = 10000) {
  // Warmup
  for (let i = 0; i < 100; i++) await fn();

  const times = [];
  for (let i = 0; i < iterations; i++) {
    const start = performance.now();
    await fn();
    times.push(performance.now() - start);
  }

  times.sort((a, b) => a - b);
  const sum = times.reduce((a, b) => a + b, 0);

  return {
    name,
    iterations,
    mean: (sum / iterations * 1000).toFixed(2) + ' μs',
    median: (times[Math.floor(iterations / 2)] * 1000).toFixed(2) + ' μs',
    p95: (times[Math.floor(iterations * 0.95)] * 1000).toFixed(2) + ' μs',
    min: (times[0] * 1000).toFixed(2) + ' μs',
    max: (times[times.length - 1] * 1000).toFixed(2) + ' μs',
  };
}

// Compare implementations
(async () => {
  const data = Array.from({length: 1000}, (_, i) => i);

  const results = await Promise.all([
    benchmark('for loop', () => { let s = 0; for (let i = 0; i < data.length; i++) s += data[i]; }),
    benchmark('reduce', () => data.reduce((a, b) => a + b, 0)),
    benchmark('forEach', () => { let s = 0; data.forEach(x => s += x); }),
  ]);

  console.table(results);
})();
```

---

## Step 8: Capstone — perf_hooks Measurement

```javascript
const { PerformanceObserver, performance } = require('node:perf_hooks');
const v8 = require('node:v8');

performance.mark('start');
let sum = 0;
for (let i = 0; i < 1e7; i++) sum += i;
performance.mark('end');
performance.measure('loop', 'start', 'end');

const [entry] = performance.getEntriesByName('loop');
console.log('Loop duration:', entry.duration.toFixed(2), 'ms');
console.log('Sum:', sum);

const heap = v8.getHeapStatistics();
console.log('Heap used:', Math.round(heap.used_heap_size / 1024 / 1024), 'MB');
console.log('Heap total:', Math.round(heap.total_heap_size / 1024 / 1024), 'MB');
```

**Run verification:**
```bash
docker run --rm node:20-alpine sh -c "node -e '
const { PerformanceObserver, performance } = require(\"perf_hooks\");
const v8 = require(\"v8\");
performance.mark(\"start\");
let sum = 0;
for (let i = 0; i < 1e7; i++) sum += i;
performance.mark(\"end\");
performance.measure(\"loop\", \"start\", \"end\");
const [entry] = performance.getEntriesByName(\"loop\");
console.log(\"Loop duration:\", entry.duration.toFixed(2), \"ms\");
console.log(\"Sum:\", sum);
const heap = v8.getHeapStatistics();
console.log(\"Heap used:\", Math.round(heap.used_heap_size / 1024 / 1024), \"MB\");
console.log(\"Heap total:\", Math.round(heap.total_heap_size / 1024 / 1024), \"MB\");
'"
```

📸 **Verified Output:**
```
Loop duration: 304.07 ms
Sum: 49999995000000
Heap used: 4 MB
Heap total: 6 MB
```

---

## Summary

| Tool | Command/API | Purpose |
|------|-------------|---------|
| `perf_hooks` | `performance.mark/measure` | High-precision timing |
| `PerformanceObserver` | `new PerformanceObserver()` | Async perf notifications |
| V8 stats | `v8.getHeapStatistics()` | Memory usage |
| Heap snapshot | `v8.writeHeapSnapshot()` | Memory leak analysis |
| CPU profiler | `node --prof` | Function-level CPU time |
| Deopt tracing | `node --trace-deopt` | V8 optimization issues |
| Flame graph | `clinic flame` or `0x` | Visual CPU profiling |
