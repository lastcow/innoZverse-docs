# Lab 04: Worker Threads Advanced — SharedArrayBuffer, Atomics & Thread Pools

**Time:** 60 minutes | **Level:** Architect | **Docker:** `docker run -it --rm node:20-alpine sh`

Node.js is single-threaded by default, but `worker_threads` enables true parallelism for CPU-bound tasks. This lab covers SharedArrayBuffer, Atomics, zero-copy transfers, and building a thread pool.

---

## Step 1: Worker Threads Architecture

```
Main Thread
│
├── Worker 1 (own V8 isolate + libuv event loop)
├── Worker 2 (own V8 isolate + libuv event loop)
├── Worker 3 (own V8 isolate + libuv event loop)
└── Worker 4 (own V8 isolate + libuv event loop)

Communication:
  - MessageChannel: structured clone (copy)
  - SharedArrayBuffer: true shared memory (zero-copy)
  - transferList: transfer ownership (zero-copy, original invalidated)
```

Workers have their own V8 heap but can share memory via SharedArrayBuffer.

---

## Step 2: Basic Worker with workerData

```javascript
// file: basic-worker.mjs
import { Worker, isMainThread, parentPort, workerData } from 'worker_threads';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);

if (isMainThread) {
  const worker = new Worker(__filename, {
    workerData: { start: 1, end: 1_000_000 }
  });

  worker.on('message', (result) => {
    console.log('Sum result:', result);
  });
  worker.on('error', console.error);
  worker.on('exit', (code) => console.log('Worker exited with code', code));

} else {
  // Worker thread
  const { start, end } = workerData;
  let sum = 0;
  for (let i = start; i <= end; i++) sum += i;
  parentPort.postMessage(sum);
}
```

> 💡 `workerData` is deep-cloned via structured clone algorithm. Use `SharedArrayBuffer` for large data to avoid copying.

---

## Step 3: SharedArrayBuffer + Atomics

SharedArrayBuffer provides memory shared between threads. Atomics ensures thread-safe operations:

```javascript
// file: shared-counter.mjs
import { Worker, isMainThread, parentPort, workerData } from 'worker_threads';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);

if (isMainThread) {
  const sab = new SharedArrayBuffer(4);   // 4 bytes = 1 Int32
  const arr = new Int32Array(sab);

  let done = 0;
  const NUM_WORKERS = 4;
  const INCREMENTS = 1000;

  for (let i = 0; i < NUM_WORKERS; i++) {
    const w = new Worker(__filename, {
      workerData: { sab, increments: INCREMENTS }
    });
    w.on('exit', () => {
      done++;
      if (done === NUM_WORKERS) {
        console.log('Final counter:', arr[0], '(expected', NUM_WORKERS * INCREMENTS + ')');
      }
    });
  }
} else {
  const arr = new Int32Array(workerData.sab);
  for (let i = 0; i < workerData.increments; i++) {
    Atomics.add(arr, 0, 1);  // atomic increment — thread-safe!
  }
  parentPort.postMessage('done');
}
```

Run: `node shared-counter.mjs`

📸 **Verified Output:**
```
Final counter: 4000 (expected 4000)
```

> 💡 Without `Atomics.add`, concurrent `arr[0]++` would lose updates (race condition). Atomics prevents this with CPU-level memory ordering.

---

## Step 4: Atomics.wait / Atomics.notify (Mutex Pattern)

```javascript
// file: atomics-mutex.mjs
import { Worker, isMainThread, parentPort, workerData } from 'worker_threads';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);

if (isMainThread) {
  const sab = new SharedArrayBuffer(8);
  const lock = new Int32Array(sab);  // lock[0] = mutex, lock[1] = data

  const w1 = new Worker(__filename, { workerData: { sab, id: 1 } });
  const w2 = new Worker(__filename, { workerData: { sab, id: 2 } });

  let done = 0;
  [w1, w2].forEach(w => w.on('exit', () => {
    done++;
    if (done === 2) {
      const result = new Int32Array(sab)[1];
      console.log('Final shared data value:', result, '(both workers wrote safely)');
    }
  }));

} else {
  const lock = new Int32Array(workerData.sab);
  const data = new Int32Array(workerData.sab);

  for (let i = 0; i < 100; i++) {
    // Acquire lock (CAS: compare-and-swap 0→1)
    while (Atomics.compareExchange(lock, 0, 0, 1) !== 0) {
      Atomics.wait(lock, 0, 1); // wait if still locked
    }
    // Critical section
    data[1] += 1;
    // Release lock
    Atomics.store(lock, 0, 0);
    Atomics.notify(lock, 0, 1);
  }
  parentPort.postMessage('done');
}
```

---

## Step 5: Zero-Copy Transfer with transferList

```javascript
// file: zero-copy-transfer.mjs
import { Worker, isMainThread, parentPort } from 'worker_threads';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);

if (isMainThread) {
  const worker = new Worker(__filename);

  // Create large buffer
  const bigBuffer = new ArrayBuffer(1024 * 1024); // 1 MB
  console.log('Main: buffer byteLength before transfer:', bigBuffer.byteLength);

  // Transfer ownership (zero-copy — bigBuffer is now detached/unusable here)
  worker.postMessage({ buffer: bigBuffer }, [bigBuffer]);

  console.log('Main: buffer byteLength after transfer:', bigBuffer.byteLength); // 0 — detached!

  worker.on('message', (msg) => {
    console.log('Worker processed buffer of size:', msg.size, 'bytes');
  });

} else {
  parentPort.on('message', ({ buffer }) => {
    const arr = new Uint8Array(buffer);
    arr.fill(42); // fill the transferred buffer
    console.log('Worker: received buffer, size:', buffer.byteLength, 'bytes');
    // Transfer back to main thread
    parentPort.postMessage({ size: buffer.byteLength }, [buffer]);
  });
}
```

> 💡 `transferList` moves the buffer's backing memory to the other thread. The original `ArrayBuffer` becomes detached (byteLength = 0). Great for image/audio processing pipelines.

---

## Step 6: MessageChannel for Direct Worker-to-Worker Communication

```javascript
// file: worker-channel.mjs
import { Worker, isMainThread, parentPort, workerData, MessageChannel } from 'worker_threads';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);

if (isMainThread) {
  const { port1, port2 } = new MessageChannel();

  const w1 = new Worker(__filename, { workerData: { role: 'producer', port: port1 } });
  const w2 = new Worker(__filename, { workerData: { role: 'consumer', port: port2 } });

  // Transfer ports to workers
  w1.postMessage({ port: port1 }, [port1]);
  w2.postMessage({ port: port2 }, [port2]);

  w1.on('message', m => console.log('w1:', m));
  w2.on('message', m => console.log('w2:', m));
} else {
  const { role } = workerData;
  parentPort.on('message', ({ port }) => {
    if (role === 'producer') {
      for (let i = 0; i < 3; i++) port.postMessage(`msg-${i}`);
      parentPort.postMessage('producer done');
    } else {
      port.on('message', (msg) => {
        parentPort.postMessage(`consumer received: ${msg}`);
      });
    }
  });
}
```

---

## Step 7: Thread Pool Pattern

```javascript
// file: thread-pool.mjs
import { Worker, isMainThread, parentPort, workerData } from 'worker_threads';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);

if (!isMainThread) {
  // Worker: CPU-bound task
  parentPort.on('message', ({ taskId, n }) => {
    let result = 0;
    for (let i = 0; i < n; i++) result += Math.sqrt(i);
    parentPort.postMessage({ taskId, result });
  });

} else {
  class ThreadPool {
    constructor(size) {
      this.workers = Array.from({ length: size }, () => new Worker(__filename));
      this.queue = [];
      this.idle = [...this.workers];
      this.resolvers = new Map();
      this.taskId = 0;

      this.workers.forEach(w => {
        w.on('message', ({ taskId, result }) => {
          this.resolvers.get(taskId)?.(result);
          this.resolvers.delete(taskId);
          this.idle.push(w);
          this._drain();
        });
      });
    }

    _drain() {
      while (this.queue.length > 0 && this.idle.length > 0) {
        const { task, resolve } = this.queue.shift();
        const worker = this.idle.pop();
        this.resolvers.set(task.taskId, resolve);
        worker.postMessage(task);
      }
    }

    exec(n) {
      const taskId = this.taskId++;
      return new Promise(resolve => {
        this.queue.push({ task: { taskId, n }, resolve });
        this._drain();
      });
    }

    async shutdown() {
      await Promise.all(this.workers.map(w => w.terminate()));
    }
  }

  const pool = new ThreadPool(4);
  const tasks = Array.from({ length: 8 }, (_, i) => pool.exec(1_000_000 * (i + 1)));
  const results = await Promise.all(tasks);
  console.log('Thread pool results (8 tasks, 4 workers):');
  results.forEach((r, i) => console.log(`  Task ${i}: ${r.toFixed(0)}`));
  await pool.shutdown();
}
```

---

## Step 8: Capstone — CPU-Bound Parallelism Benchmark

```javascript
// file: parallel-benchmark.mjs
import { Worker, isMainThread, parentPort } from 'worker_threads';
import { fileURLToPath } from 'url';
import { performance } from 'perf_hooks';

const __filename = fileURLToPath(import.meta.url);
const N = 5_000_000;

if (!isMainThread) {
  // Worker: compute primes
  parentPort.on('message', ({ start, end }) => {
    let count = 0;
    function isPrime(n) {
      if (n < 2) return false;
      for (let i = 2, s = Math.sqrt(n); i <= s; i++) if (n % i === 0) return false;
      return true;
    }
    for (let i = start; i <= end; i++) if (isPrime(i)) count++;
    parentPort.postMessage(count);
  });

} else {
  function isPrime(n) {
    if (n < 2) return false;
    for (let i = 2, s = Math.sqrt(n); i <= s; i++) if (n % i === 0) return false;
    return true;
  }

  // Single-threaded benchmark
  let t = performance.now();
  let count = 0;
  for (let i = 2; i <= N; i++) if (isPrime(i)) count++;
  const singleTime = performance.now() - t;
  console.log(`Single-thread: ${count} primes in ${singleTime.toFixed(0)}ms`);

  // Multi-threaded benchmark
  const NUM_WORKERS = 4;
  const chunk = Math.floor(N / NUM_WORKERS);
  t = performance.now();

  const results = await Promise.all(
    Array.from({ length: NUM_WORKERS }, (_, i) => {
      const start = i * chunk + 2;
      const end = i === NUM_WORKERS - 1 ? N : (i + 1) * chunk;
      return new Promise(resolve => {
        const w = new Worker(__filename);
        w.on('message', resolve);
        w.postMessage({ start, end });
      });
    })
  );

  const multiTime = performance.now() - t;
  const totalPrimes = results.reduce((a, b) => a + b, 0);
  console.log(`Multi-thread (${NUM_WORKERS} workers): ${totalPrimes} primes in ${multiTime.toFixed(0)}ms`);
  console.log(`Speedup: ${(singleTime / multiTime).toFixed(2)}x`);
}
```

---

## Summary

| API | Description | Use Case |
|---|---|---|
| `new Worker(filename)` | Spawn worker thread | CPU-bound parallelism |
| `workerData` | Pass data at creation | Initial config, immutable |
| `parentPort.postMessage` | Send structured-clone | General message passing |
| `SharedArrayBuffer` | Shared memory | Zero-copy high-frequency updates |
| `Atomics.add/sub` | Atomic arithmetic | Thread-safe counters |
| `Atomics.compareExchange` | CAS operation | Mutex/lock implementation |
| `Atomics.wait/notify` | Thread synchronization | Blocking wait / wake |
| `transferList` | Transfer ownership | Large buffers, zero-copy |
| `MessageChannel` | Worker-to-worker pipe | Direct inter-worker comms |
