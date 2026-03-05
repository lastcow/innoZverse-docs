# Lab 01: Event Loop Deep Dive

**Time:** 30 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Master Node.js's event loop internals: phases (timers/poll/check), microtask queue, macrotask queue, `process.nextTick` vs `queueMicrotask`, libuv thread pool, and blocking detection.

---

## Step 1: Event Loop Phases

The Node.js event loop has 6 phases that execute in order:

```
   ┌───────────────────────────┐
┌─>│           timers          │  setTimeout, setInterval callbacks
│  └─────────────┬─────────────┘
│  ┌─────────────┴─────────────┐
│  │     pending callbacks     │  I/O errors from previous iteration
│  └─────────────┬─────────────┘
│  ┌─────────────┴─────────────┐
│  │       idle, prepare       │  Internal use only
│  └─────────────┬─────────────┘
│  ┌─────────────┴─────────────┐
│  │           poll            │  Retrieve I/O events, execute callbacks
│  └─────────────┬─────────────┘
│  ┌─────────────┴─────────────┐
│  │           check           │  setImmediate callbacks
│  └─────────────┬─────────────┘
│  ┌─────────────┴─────────────┐
└──┤      close callbacks      │  'close' events
   └───────────────────────────┘
```

Between each phase: **microtask queue** (nextTick + Promises) runs to completion.

---

## Step 2: Execution Order Demo

```javascript
console.log('1: sync start');

// Macrotask — timers phase
setTimeout(() => console.log('5: setTimeout 0'), 0);
setTimeout(() => console.log('6: setTimeout 100'), 100);

// Macrotask — check phase
setImmediate(() => console.log('7: setImmediate'));

// Microtask (highest priority)
process.nextTick(() => console.log('2: nextTick'));

// Microtask (Promise microtask)
Promise.resolve().then(() => console.log('3: Promise.resolve'));

// Microtask (queueMicrotask)
queueMicrotask(() => console.log('4: queueMicrotask'));

console.log('1b: sync end');

// Output order:
// 1: sync start
// 1b: sync end
// 2: nextTick         <- process.nextTick (before other microtasks)
// 3: Promise.resolve  <- Promise microtask
// 4: queueMicrotask   <- queueMicrotask
// 5: setTimeout 0     <- timers phase
// 7: setImmediate     <- check phase (may come before or after setTimeout 0)
// 6: setTimeout 100   <- timers phase (100ms later)
```

> 💡 `process.nextTick` fires before other microtasks. Overuse can starve I/O!

---

## Step 3: Microtask Queue In Detail

```javascript
// Microtasks run completely between event loop phases
console.log('sync');

Promise.resolve()
  .then(() => {
    console.log('promise 1');
    // This schedules ANOTHER microtask before next phase
    Promise.resolve().then(() => console.log('promise 1a (nested)'));
  })
  .then(() => console.log('promise 2'));

process.nextTick(() => {
  console.log('nextTick 1');
  process.nextTick(() => console.log('nextTick 1a (nested nextTick)'));
});

setTimeout(() => console.log('setTimeout'), 0);

// Output:
// sync
// nextTick 1
// nextTick 1a (nested nextTick)  <- nextTick queue drains first
// promise 1
// promise 1a (nested)
// promise 2
// setTimeout

// The microtask queue runs to COMPLETION before the next event loop phase
// nextTick runs BEFORE promise microtasks
```

---

## Step 4: setTimeout vs setImmediate

```javascript
// In the main module — order is NOT guaranteed
setTimeout(() => console.log('timeout'), 0);
setImmediate(() => console.log('immediate'));
// Could be either order depending on event loop state

// Inside an I/O callback — setImmediate ALWAYS comes first
const fs = require('node:fs');
fs.readFile('/etc/hostname', () => {
  setTimeout(() => console.log('timeout in I/O'), 0);
  setImmediate(() => console.log('immediate in I/O')); // ALWAYS first!
  // immediate in I/O -> timeout in I/O
});

// Why? After I/O callbacks, the loop is in 'poll' phase.
// Next comes 'check' (setImmediate), THEN next iteration starts timers.
```

---

## Step 5: libuv Thread Pool

```javascript
// Certain I/O operations use libuv's thread pool (default: 4 threads)
// - fs operations (file I/O)
// - DNS lookups (dns.lookup, not dns.resolve)
// - crypto (heavy operations like pbkdf2, randomBytes)
// - zlib
// - user-facing: none (HTTP uses OS event queue, not thread pool)

const crypto = require('node:crypto');
const { performance } = require('node:perf_hooks');

// Default thread pool size = 4
// process.env.UV_THREADPOOL_SIZE = '8'; // Increase if needed (set before require)

// 4 parallel crypto operations — uses all 4 threads
const start = performance.now();
let completed = 0;

function hashAsync(data) {
  return new Promise((resolve, reject) => {
    crypto.pbkdf2(data, 'salt', 1000, 32, 'sha256', (err, key) => {
      if (err) reject(err);
      else resolve(key);
    });
  });
}

Promise.all([
  hashAsync('password1'),
  hashAsync('password2'),
  hashAsync('password3'),
  hashAsync('password4')
]).then(() => {
  const elapsed = performance.now() - start;
  console.log(`4 parallel hashes: ${elapsed.toFixed(0)}ms`);
  // ~4x faster than sequential due to thread pool
});
```

---

## Step 6: Blocking the Event Loop

```javascript
const { performance } = require('node:perf_hooks');

// Blocking — prevents I/O handling during this time
function blockingOperation(ms) {
  const end = Date.now() + ms;
  while (Date.now() < end) {} // Busy-wait
}

// Non-blocking — returns immediately, schedules work
function nonBlockingOperation(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// Detect blocking with lag measurement
let lastTick = Date.now();
const lagInterval = setInterval(() => {
  const now = Date.now();
  const lag = now - lastTick - 10; // Expected 10ms
  if (lag > 50) {
    console.warn(`Event loop lag: ${lag}ms`);
  }
  lastTick = now;
}, 10);

// This will cause lag!
setTimeout(() => {
  console.log('About to block...');
  blockingOperation(200); // Blocks for 200ms
  console.log('Done blocking');
}, 100);

setTimeout(() => clearInterval(lagInterval), 1000);

// For CPU-heavy work, use Worker Threads (see Lab 02)
```

---

## Step 7: setImmediate vs nextTick Performance

```javascript
const { performance } = require('node:perf_hooks');

// nextTick can starve I/O if used recursively
// This is an ANTI-PATTERN:
function recursiveNextTick(n) {
  if (n <= 0) return;
  process.nextTick(() => recursiveNextTick(n - 1));
}

// setImmediate allows I/O between iterations
function recursiveImmediate(n, callback) {
  if (n <= 0) return callback();
  setImmediate(() => recursiveImmediate(n - 1, callback));
}

// Chunked processing with setImmediate (yields to event loop)
function processLargeArray(arr, processItem, chunkSize = 100) {
  return new Promise((resolve, reject) => {
    const results = [];
    let index = 0;

    function processChunk() {
      const end = Math.min(index + chunkSize, arr.length);
      try {
        while (index < end) {
          results.push(processItem(arr[index++]));
        }
        if (index < arr.length) {
          setImmediate(processChunk); // Yield to event loop
        } else {
          resolve(results);
        }
      } catch (e) {
        reject(e);
      }
    }

    setImmediate(processChunk);
  });
}
```

---

## Step 8: Capstone — Event Loop Timing

```javascript
console.log('1: sync start');
setTimeout(() => console.log('5: setTimeout 0'), 0);
Promise.resolve().then(() => console.log('3: microtask'));
process.nextTick(() => console.log('2: nextTick'));
queueMicrotask(() => console.log('4: queueMicrotask'));
console.log('1b: sync end');
```

**Run verification:**
```bash
docker run --rm node:20-alpine sh -c "node -e '
console.log(\"1: sync start\");
setTimeout(() => console.log(\"5: setTimeout 0\"), 0);
Promise.resolve().then(() => console.log(\"3: microtask\"));
process.nextTick(() => console.log(\"2: nextTick\"));
queueMicrotask(() => console.log(\"4: queueMicrotask\"));
console.log(\"1b: sync end\");
'"
```

📸 **Verified Output:**
```
1: sync start
1b: sync end
2: nextTick
3: microtask
4: queueMicrotask
5: setTimeout 0
```

---

## Summary

| Queue/Phase | API | Priority | When Runs |
|-------------|-----|----------|-----------|
| nextTick queue | `process.nextTick()` | Highest | After current op, before microtasks |
| Microtask queue | `Promise.then()`, `queueMicrotask()` | High | After nextTick, before phases |
| Timers phase | `setTimeout()`, `setInterval()` | Normal | When timer expires |
| Poll phase | I/O callbacks | Normal | Waiting for I/O |
| Check phase | `setImmediate()` | Normal | After poll |
| Thread pool | `crypto`, `fs`, `dns.lookup` | OS threads | Up to UV_THREADPOOL_SIZE parallel |
