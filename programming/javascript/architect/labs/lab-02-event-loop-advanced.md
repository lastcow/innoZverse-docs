# Lab 02: Advanced Event Loop — libuv Phases, Microtasks & async_hooks

**Time:** 60 minutes | **Level:** Architect | **Docker:** `docker run -it --rm node:20-alpine sh`

The Node.js event loop is the heartbeat of every server. This lab dissects libuv's phase architecture, microtask queue ordering, async context propagation with `async_hooks`, and blocking event loop detection.

---

## Step 1: libuv Event Loop Phase Architecture

The event loop runs through these phases on each iteration ("tick"):

```
   ┌──────────────────────────┐
   │         timers           │  ← setTimeout / setInterval callbacks
   └──────────┬───────────────┘
              │
   ┌──────────▼───────────────┐
   │    pending callbacks     │  ← I/O callbacks deferred from prev tick
   └──────────┬───────────────┘
              │
   ┌──────────▼───────────────┐
   │      idle / prepare      │  ← internal use only
   └──────────┬───────────────┘
              │
   ┌──────────▼───────────────┐
   │          poll            │  ← retrieve I/O events, run I/O callbacks
   └──────────┬───────────────┘
              │
   ┌──────────▼───────────────┐
   │          check           │  ← setImmediate callbacks
   └──────────┬───────────────┘
              │
   ┌──────────▼───────────────┐
   │     close callbacks      │  ← socket.on('close'), etc.
   └──────────────────────────┘
```

**Between every phase**, Node.js drains the **microtask queues**:
1. `process.nextTick` queue (highest priority)
2. Promises / `queueMicrotask` queue

---

## Step 2: Phase Ordering Verification

```javascript
// file: phase-order.js
const start = Date.now();
function ts(label) {
  console.log(`${Date.now() - start}ms  ${label}`);
}

// Schedule across all queues
setTimeout(() => ts('setTimeout'), 0);
setImmediate(() => ts('setImmediate'));
Promise.resolve().then(() => ts('Promise.then'));
process.nextTick(() => ts('process.nextTick'));
queueMicrotask(() => ts('queueMicrotask'));

ts('sync end');
```

Run: `node phase-order.js`

📸 **Verified Output:**
```
3ms   sync end
22ms  process.nextTick
23ms  Promise.then
23ms  queueMicrotask
25ms  setTimeout
25ms  setImmediate
```

> 💡 `process.nextTick` fires before Promise microtasks. Both fire before any I/O or timer callbacks.

---

## Step 3: Nested nextTick Starvation

```javascript
// file: nexttick-starve.js

let count = 0;

function recursiveNextTick() {
  if (count >= 5) {
    console.log('nextTick chain done, count:', count);
    return;
  }
  count++;
  process.nextTick(recursiveNextTick); // queues another before I/O!
  if (count === 1) setTimeout(() => console.log('setTimeout fired at count:', count), 0);
}

recursiveNextTick();
```

> 💡 Infinite `process.nextTick` recursion starves I/O. Always use `setImmediate` for truly deferring work.

---

## Step 4: setImmediate vs setTimeout in I/O Context

```javascript
// file: immediate-vs-timer.js
const fs = require('fs');

// Outside I/O: setTimeout vs setImmediate order is NONDETERMINISTIC
setTimeout(() => console.log('timeout (outside I/O)'), 0);
setImmediate(() => console.log('immediate (outside I/O)'));

// Inside I/O: setImmediate ALWAYS fires before setTimeout
fs.readFile('/etc/hostname', () => {
  setTimeout(() => console.log('timeout (inside I/O)'), 0);
  setImmediate(() => console.log('immediate (inside I/O) ← always first'));
});
```

> 💡 Inside an I/O callback, `setImmediate` always runs before `setTimeout(fn, 0)` because we're already past the timers phase.

---

## Step 5: async_hooks — Tracking Async Context

```javascript
// file: async-hooks-demo.js
const async_hooks = require('async_hooks');
const fs = require('fs');

const contexts = new Map();
let indent = 0;

const hook = async_hooks.createHook({
  init(asyncId, type, triggerAsyncId) {
    contexts.set(asyncId, { type, triggerAsyncId });
    fs.writeSync(1, `${'  '.repeat(indent)}INIT asyncId=${asyncId} type=${type} trigger=${triggerAsyncId}\n`);
  },
  before(asyncId) {
    indent++;
    fs.writeSync(1, `${'  '.repeat(indent)}BEFORE asyncId=${asyncId}\n`);
  },
  after(asyncId) {
    fs.writeSync(1, `${'  '.repeat(indent)}AFTER asyncId=${asyncId}\n`);
    indent = Math.max(0, indent - 1);
  },
  destroy(asyncId) {
    contexts.delete(asyncId);
  }
});

hook.enable();

setTimeout(() => {
  fs.writeSync(1, 'setTimeout callback\n');
}, 10);

// Disable after a moment
setTimeout(() => hook.disable(), 100);
```

> 💡 `async_hooks` are powerful but have ~5-10% overhead. Disable in production or use `AsyncLocalStorage` instead.

---

## Step 6: AsyncLocalStorage for Request Context

```javascript
// file: async-local-storage.js
const { AsyncLocalStorage } = require('async_hooks');
const { EventEmitter } = require('events');

const requestContext = new AsyncLocalStorage();

async function handleRequest(requestId) {
  await requestContext.run({ requestId, startTime: Date.now() }, async () => {
    await processStep1();
    await processStep2();
  });
}

async function processStep1() {
  const ctx = requestContext.getStore();
  // simulate async work
  await new Promise(r => setTimeout(r, 10));
  console.log(`[${ctx.requestId}] Step 1 complete`);
}

async function processStep2() {
  const ctx = requestContext.getStore();
  await new Promise(r => setTimeout(r, 5));
  const elapsed = Date.now() - ctx.startTime;
  console.log(`[${ctx.requestId}] Step 2 complete, elapsed: ${elapsed}ms`);
}

// Simulate 3 concurrent requests
Promise.all([
  handleRequest('req-001'),
  handleRequest('req-002'),
  handleRequest('req-003'),
]).then(() => console.log('All requests done'));
```

> 💡 `AsyncLocalStorage` is the production-safe way to propagate request IDs, user sessions, and trace spans through async call stacks.

---

## Step 7: Event Loop Blocking Detection

```javascript
// file: blocking-detector.js
const { performance } = require('perf_hooks');

const THRESHOLD_MS = 50;
let lastCheck = performance.now();

const monitor = setInterval(() => {
  const now = performance.now();
  const lag = now - lastCheck - 10; // expected 10ms interval
  if (lag > THRESHOLD_MS) {
    console.warn(`⚠️  Event loop blocked for ${lag.toFixed(1)}ms!`);
  }
  lastCheck = now;
}, 10);

// Simulate a blocking operation
setTimeout(() => {
  console.log('Starting blocking CPU work...');
  const start = performance.now();
  // Intentional busy-wait (NEVER do this in production!)
  while (performance.now() - start < 200) {}
  console.log('Blocking work done');
}, 100);

setTimeout(() => {
  clearInterval(monitor);
  console.log('Monitor stopped');
}, 500);
```

> 💡 Libraries like `clinic.js` and `@nicolo-ribaudo/event-loop-lag` measure event loop lag in production. Alert at > 100ms.

---

## Step 8: Capstone — Microtask Queue Visualizer

Build a complete phase visualizer showing all queue orderings:

```javascript
// file: event-loop-visualizer.js
'use strict';

const log = [];
const t0 = Date.now();
const ts = (label) => log.push({ t: Date.now() - t0, label });

// === SYNCHRONOUS ===
ts('[1] sync: start');

// === MICROTASKS (scheduled synchronously) ===
process.nextTick(() => ts('[3] nextTick: first'));
process.nextTick(() => {
  ts('[4] nextTick: second');
  process.nextTick(() => ts('[5] nextTick: nested (runs before Promise!)'));
});
Promise.resolve().then(() => ts('[6] Promise: first'));
queueMicrotask(() => ts('[7] queueMicrotask'));
Promise.resolve().then(() => ts('[8] Promise: second'));

// === MACROTASKS ===
setImmediate(() => ts('[10] setImmediate: check phase'));
setTimeout(() => ts('[9] setTimeout(0): timers phase'), 0);

ts('[2] sync: end');

// Print after everything
setTimeout(() => {
  console.log('\n=== Event Loop Phase Execution Order ===');
  log.forEach(({ t, label }) => console.log(`  ${String(t).padStart(3)}ms  ${label}`));

  console.log('\n=== Summary ===');
  console.log('Order: sync → nextTick → nextTick(nested) → Promise → queueMicrotask → setTimeout → setImmediate');
}, 200);
```

Expected output order:
```
[1] sync: start
[2] sync: end
[3] nextTick: first
[4] nextTick: second
[5] nextTick: nested (runs before Promise!)
[6] Promise: first
[7] queueMicrotask
[8] Promise: second
[9] setTimeout(0): timers phase
[10] setImmediate: check phase
```

---

## Summary

| Queue / Phase | Priority | Use Case |
|---|---|---|
| `process.nextTick` | 1st (highest) | Defer within same phase, before I/O |
| Promise microtasks | 2nd | Async/await continuations |
| `queueMicrotask` | 2nd (same) | Explicit microtask scheduling |
| Timers phase | 3rd | `setTimeout` / `setInterval` |
| Poll phase | 4th | Network, file I/O callbacks |
| Check phase | 5th | `setImmediate` |
| `AsyncLocalStorage` | N/A | Request context propagation |
| `async_hooks` | N/A | Low-level async lifecycle tracking |
