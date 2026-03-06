# Lab 08: Performance Profiling — V8 Profiler, perf_hooks & Load Testing

**Time:** 60 minutes | **Level:** Architect | **Docker:** `docker run -it --rm node:20-alpine sh`

You can't optimize what you can't measure. This lab covers V8's built-in profiler, `perf_hooks` PerformanceObserver, trace events, heap profiling, and load testing with autocannon.

---

## Step 1: `perf_hooks` — PerformanceObserver

The most important profiling tool in your daily Node.js work:

```javascript
// file: perf-observer.js
const { performance, PerformanceObserver } = require('perf_hooks');

// Set up observer BEFORE creating marks
const obs = new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    console.log(`${entry.name}: ${entry.duration.toFixed(3)}ms`);
  }
  obs.disconnect();
});
obs.observe({ entryTypes: ['measure'] });

// Benchmark: sort 100k elements
performance.mark('sort-start');
const arr = Array.from({ length: 100_000 }, () => Math.random());
arr.sort((a, b) => a - b);
performance.mark('sort-end');
performance.measure('array-sort-100k', 'sort-start', 'sort-end');

console.log('Sorted', arr.length, 'elements');
```

📸 **Verified Output:**
```
Sorted 100000 elements
array-sort-100k: 205.898ms
```

> 💡 `PerformanceObserver` is non-blocking and collects entries asynchronously. For synchronous measurements, use `performance.now()`.

---

## Step 2: Detailed Timing with `performance.now()`

```javascript
// file: detailed-timing.js
const { performance } = require('perf_hooks');

function benchmark(name, fn, iterations = 1000) {
  // Warm up
  for (let i = 0; i < 10; i++) fn();

  const start = performance.now();
  for (let i = 0; i < iterations; i++) fn();
  const elapsed = performance.now() - start;

  return {
    name,
    iterations,
    totalMs: elapsed.toFixed(3),
    avgUs: ((elapsed / iterations) * 1000).toFixed(3),
    opsPerSec: Math.round((iterations / elapsed) * 1000),
  };
}

// Compare array methods
const data = Array.from({ length: 1000 }, (_, i) => i);

const results = [
  benchmark('for loop sum',      () => { let s=0; for(let i=0;i<data.length;i++) s+=data[i]; return s; }),
  benchmark('reduce sum',        () => data.reduce((a,b) => a+b, 0)),
  benchmark('forEach sum',       () => { let s=0; data.forEach(x => s+=x); return s; }),
  benchmark('for...of sum',      () => { let s=0; for(const x of data) s+=x; return s; }),
  benchmark('TypedArray sum',    (() => { const ta = new Int32Array(data); return () => { let s=0; for(let i=0;i<ta.length;i++) s+=ta[i]; return s; }; })()),
];

console.log('\nArray Sum Benchmarks (1000 iterations):');
console.log('Name'.padEnd(25), 'Total'.padEnd(12), 'Avg(μs)'.padEnd(12), 'ops/sec');
console.log('-'.repeat(65));
results.forEach(r => {
  console.log(r.name.padEnd(25), `${r.totalMs}ms`.padEnd(12), `${r.avgUs}μs`.padEnd(12), r.opsPerSec.toLocaleString());
});
```

---

## Step 3: V8 Profiler with `--prof`

```bash
# Generate V8 profile
node --prof server.js
# Produces: isolate-0x...-.log

# Process the profile (shows hot functions)
node --prof-process isolate-0x...-.log > profile.txt

# View top functions
head -50 profile.txt
```

A minimal app to profile:
```javascript
// file: to-profile.js
function fibonacci(n) {
  if (n <= 1) return n;
  return fibonacci(n - 1) + fibonacci(n - 2);
}

// Hot loop
let total = 0;
for (let i = 0; i < 30; i++) total += fibonacci(25);
console.log('Total:', total);
```

Run:
```bash
node --prof to-profile.js
node --prof-process $(ls isolate-*.log) | head -30
```

Expected output includes:
```
 [JavaScript]:
   ticks  total  nonlib   name
   1234   45.2%   52.1%   Function: fibonacci
```

> 💡 Functions with high `ticks` percentage are your optimization targets. Focus on the top 3-5 functions.

---

## Step 4: `node:trace_events` — Event Loop Tracing

```javascript
// file: trace-events-demo.js
const trace = require('node:trace_events');

// Enable tracing for V8 and Node.js bootstrap
const tracing = trace.createTracing({
  categories: ['v8', 'node', 'node.async_hooks']
});

tracing.enable();

// Run some work
const { performance } = require('perf_hooks');

async function tracedWork() {
  performance.mark('work-start');
  await new Promise(r => setTimeout(r, 10));
  const arr = new Array(100000).fill(0).map((_, i) => i * 2);
  performance.mark('work-end');
  performance.measure('traced-work', 'work-start', 'work-end');
  return arr.length;
}

tracedWork().then(n => {
  tracing.disable();
  console.log('Traced work complete, processed:', n, 'items');
  console.log('Trace file: Use --trace-event-file-pattern=trace-{pid}-{seq}.json');
});
```

Run with:
```bash
node --trace-events-enabled --trace-event-categories v8,node trace-events-demo.js
# Open trace.json in chrome://tracing or Perfetto UI
```

---

## Step 5: Heap Profiling with `--heap-prof`

```bash
# Generate heap profile
node --heap-prof heap-intensive.js
# Produces: Heap.20240101.120000.12345.0.001.heapprofile

# Load in Chrome DevTools:
# 1. Open chrome://inspect → Memory tab
# 2. Load .heapprofile file
# 3. Analyze allocations by function
```

```javascript
// file: heap-intensive.js
// This creates many short-lived objects — good for heap profiling demo
function processData(n) {
  return Array.from({ length: n }, (_, i) => ({
    id: i,
    name: `item-${i}`,
    values: new Array(10).fill(i),
  }));
}

for (let round = 0; round < 10; round++) {
  const items = processData(10000);
  const sum = items.reduce((acc, item) => acc + item.values.reduce((a, b) => a + b, 0), 0);
  if (round === 0) console.log('Sum of round 0:', sum);
}
console.log('Heap profiling complete');
```

---

## Step 6: autocannon Load Testing

```bash
# Install
npm install -g autocannon

# Basic load test: 10 connections, 10 seconds
autocannon -c 10 -d 10 http://localhost:3000

# Ramp up: 100 connections, 30s, pipeline 10 requests
autocannon -c 100 -d 30 -p 10 http://localhost:3000

# POST request
autocannon -c 10 -d 5 -m POST -H "content-type=application/json" -b '{"key":"value"}' http://localhost:3000/api
```

Sample autocannon output:
```
Running 10s test @ http://localhost:3000
10 connections

┌─────────┬──────┬──────┬───────┬──────┬─────────┬─────────┬──────────┐
│ Stat    │ 2.5% │ 50%  │ 97.5% │ 99%  │ Avg     │ Stdev   │ Max      │
├─────────┼──────┼──────┼───────┼──────┼─────────┼─────────┼──────────┤
│ Latency │ 1 ms │ 2 ms │ 4 ms  │ 5 ms │ 2.05 ms │ 0.85 ms │ 16.45 ms │
└─────────┴──────┴──────┴───────┴──────┴─────────┴─────────┴──────────┘
Req/Sec: 4781.30 avg
```

---

## Step 7: clinic.js — Production Profiling Suite

```bash
# Install clinic
npm install -g clinic

# clinic doctor: detect event loop blocking, I/O bottlenecks
clinic doctor -- node server.js

# clinic flame: flamegraph from --prof
clinic flame -- node server.js

# clinic bubbleprof: async operations visualizer
clinic bubbleprof -- node server.js

# Then load test while clinic runs:
autocannon -c 10 -d 30 http://localhost:3000
```

> 💡 Clinic Doctor gives a traffic-light analysis: red for blocking event loop, yellow for GC pressure, green for healthy. Use it before every major release.

---

## Step 8: Capstone — Complete Performance Analysis Tool

```javascript
// file: perf-analyzer.js
'use strict';
const { performance, PerformanceObserver } = require('perf_hooks');
const v8 = require('v8');

class PerformanceAnalyzer {
  constructor() {
    this.measurements = new Map();
    this.gcEvents = [];

    // Track GC
    const gcObs = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        this.gcEvents.push({ type: entry.name, duration: entry.duration });
      }
    });
    gcObs.observe({ entryTypes: ['gc'] });
  }

  time(name, fn) {
    performance.mark(`${name}-start`);
    const result = fn();
    performance.mark(`${name}-end`);
    performance.measure(name, `${name}-start`, `${name}-end`);

    const entries = performance.getEntriesByName(name);
    const duration = entries[entries.length - 1].duration;
    if (!this.measurements.has(name)) this.measurements.set(name, []);
    this.measurements.get(name).push(duration);
    return result;
  }

  async timeAsync(name, fn) {
    performance.mark(`${name}-start`);
    const result = await fn();
    performance.mark(`${name}-end`);
    performance.measure(name, `${name}-start`, `${name}-end`);

    const entries = performance.getEntriesByName(name);
    const duration = entries[entries.length - 1].duration;
    if (!this.measurements.has(name)) this.measurements.set(name, []);
    this.measurements.get(name).push(duration);
    return result;
  }

  report() {
    console.log('\n=== Performance Report ===');
    const heap = v8.getHeapStatistics();
    console.log(`Heap: ${(heap.used_heap_size/1024/1024).toFixed(1)}MB used / ${(heap.heap_size_limit/1024/1024).toFixed(0)}MB limit`);

    for (const [name, times] of this.measurements) {
      const avg = times.reduce((a, b) => a + b, 0) / times.length;
      const min = Math.min(...times);
      const max = Math.max(...times);
      console.log(`\n${name}:`);
      console.log(`  calls: ${times.length}, avg: ${avg.toFixed(2)}ms, min: ${min.toFixed(2)}ms, max: ${max.toFixed(2)}ms`);
    }

    if (this.gcEvents.length > 0) {
      console.log(`\nGC events: ${this.gcEvents.length}`);
      const totalGC = this.gcEvents.reduce((a, e) => a + e.duration, 0);
      console.log(`Total GC time: ${totalGC.toFixed(2)}ms`);
    }
  }
}

// Demo
const analyzer = new PerformanceAnalyzer();

for (let i = 0; i < 5; i++) {
  analyzer.time('fibonacci', () => {
    const fib = (n) => n <= 1 ? n : fib(n-1) + fib(n-2);
    return fib(30);
  });

  analyzer.time('array-sort', () => {
    return Array.from({ length: 10000 }, () => Math.random()).sort();
  });
}

analyzer.report();
```

---

## Summary

| Tool | Command | Use Case |
|---|---|---|
| `perf_hooks` | `PerformanceObserver` | Code-level timing, marks, measures |
| `performance.now()` | Inline | High-res timestamps |
| V8 profiler | `--prof` + `--prof-process` | CPU hotspots, flamegraph |
| Heap profiler | `--heap-prof` | Memory allocation hotspots |
| Trace events | `--trace-events-enabled` | Deep V8/libuv trace |
| autocannon | CLI | HTTP load testing |
| clinic doctor | `clinic doctor --` | Automatic bottleneck detection |
| clinic flame | `clinic flame --` | Interactive flamegraph |
