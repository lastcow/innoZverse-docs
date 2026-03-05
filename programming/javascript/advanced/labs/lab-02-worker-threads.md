# Lab 02: Worker Threads

**Time:** 30 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Master Node.js worker threads: the `worker_threads` module, `SharedArrayBuffer`, `Atomics`, `MessageChannel`, transferable objects, worker pool pattern, and offloading CPU-bound tasks.

---

## Step 1: Basic Worker Thread

```javascript
const { Worker, isMainThread, parentPort, workerData } = require('worker_threads');

if (isMainThread) {
  // Main thread — spawn worker
  const worker = new Worker(__filename, {
    workerData: { numbers: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] }
  });

  worker.on('message', result => {
    console.log('Sum from worker:', result); // 55
  });

  worker.on('error', err => console.error('Worker error:', err));
  worker.on('exit', code => {
    if (code !== 0) console.error('Worker stopped with code:', code);
  });
} else {
  // Worker thread
  const { numbers } = workerData;
  const sum = numbers.reduce((a, b) => a + b, 0);
  parentPort.postMessage(sum);
}
```

> 💡 Workers run in separate V8 contexts. They don't share heap memory (except SharedArrayBuffer).

---

## Step 2: Worker from String (eval mode)

```javascript
const { Worker, isMainThread, parentPort, workerData } = require('worker_threads');

// Inline worker code (no file needed)
function runInWorker(code, data) {
  return new Promise((resolve, reject) => {
    const wrappedCode = `
      const { parentPort, workerData } = require('worker_threads');
      const run = ${code};
      Promise.resolve(run(workerData))
        .then(result => parentPort.postMessage({ ok: true, result }))
        .catch(err => parentPort.postMessage({ ok: false, error: err.message }));
    `;

    const worker = new Worker(wrappedCode, { eval: true, workerData: data });
    worker.on('message', ({ ok, result, error }) => {
      if (ok) resolve(result);
      else reject(new Error(error));
    });
    worker.on('error', reject);
  });
}

// CPU-bound: Fibonacci
async function main() {
  const result = await runInWorker(
    `(data) => {
      function fib(n) { return n <= 1 ? n : fib(n-1) + fib(n-2); }
      return fib(data.n);
    }`,
    { n: 35 }
  );
  console.log('fib(35) =', result); // 9227465
}
main();
```

---

## Step 3: SharedArrayBuffer & Atomics

```javascript
const { Worker, isMainThread, parentPort, workerData } = require('worker_threads');

if (isMainThread) {
  // Shared memory between threads
  const sharedBuffer = new SharedArrayBuffer(4 * Int32Array.BYTES_PER_ELEMENT);
  const sharedArray = new Int32Array(sharedBuffer);
  sharedArray[0] = 0; // Counter

  const workerCode = `
    const { parentPort, workerData } = require('worker_threads');
    const { sharedBuffer, workerId } = workerData;
    const counter = new Int32Array(sharedBuffer);
    
    // Atomic increment — thread-safe!
    for (let i = 0; i < 1000; i++) {
      Atomics.add(counter, 0, 1);
    }
    parentPort.postMessage('done');
  `;

  const workers = [];
  for (let i = 0; i < 4; i++) {
    const w = new Worker(workerCode, { eval: true, workerData: { sharedBuffer, workerId: i } });
    workers.push(new Promise(resolve => w.on('message', resolve)));
  }

  Promise.all(workers).then(() => {
    console.log('Final counter:', sharedArray[0]); // Should be 4000
    // Without Atomics, we'd get race conditions!
  });
}
```

---

## Step 4: MessageChannel

```javascript
const { Worker, isMainThread, parentPort, MessageChannel } = require('worker_threads');

if (isMainThread) {
  const { port1, port2 } = new MessageChannel();

  const workerCode = `
    const { workerData, receiveMessageOnPort, MessageChannel } = require('worker_threads');
    const port = workerData.port;
    
    port.on('message', (data) => {
      const result = data.map(x => x * x);
      port.postMessage(result);
    });
  `;

  const worker = new Worker(workerCode, {
    eval: true,
    workerData: { port: port2 },
    transferList: [port2] // Transfer ownership!
  });

  port1.on('message', result => {
    console.log('Squared:', result); // [1, 4, 9, 16, 25]
    worker.terminate();
  });

  port1.postMessage([1, 2, 3, 4, 5]);
}
```

---

## Step 5: Transferable Objects

```javascript
const { Worker, isMainThread, parentPort, workerData } = require('worker_threads');

if (isMainThread) {
  const workerCode = `
    const { parentPort, workerData } = require('worker_threads');
    const { buffer } = workerData;
    const arr = new Float64Array(buffer);
    
    // Process in place — no copy!
    for (let i = 0; i < arr.length; i++) arr[i] = arr[i] * 2;
    
    // Transfer back
    parentPort.postMessage({ buffer: arr.buffer }, [arr.buffer]);
  `;

  const data = new Float64Array([1, 2, 3, 4, 5]);
  const buffer = data.buffer;

  const worker = new Worker(workerCode, {
    eval: true,
    workerData: { buffer },
    transferList: [buffer] // Zero-copy transfer!
  });

  // data.buffer is now detached (neutered) — can't use it
  worker.on('message', ({ buffer }) => {
    const result = new Float64Array(buffer);
    console.log('Doubled:', [...result]); // [2, 4, 6, 8, 10]
  });
}
```

> 💡 Transferring ownership is O(1) and zero-copy. The original buffer becomes unusable after transfer.

---

## Step 6: Worker Pool Pattern

```javascript
const { Worker } = require('worker_threads');
const os = require('node:os');

class WorkerPool {
  #workers = [];
  #queue = [];
  #activeWorkers = 0;
  #workerCode;

  constructor(workerCode, size = os.cpus().length) {
    this.size = size;
    this.#workerCode = workerCode;
    // Pre-create workers
    for (let i = 0; i < size; i++) {
      this.#createWorker();
    }
  }

  #createWorker() {
    const worker = new Worker(this.#workerCode, { eval: true });
    worker.on('message', ({ taskId, result, error }) => {
      const task = worker._currentTask;
      this.#activeWorkers--;
      worker._currentTask = null;
      if (error) task.reject(new Error(error));
      else task.resolve(result);
      this.#processQueue(worker);
    });
    worker.on('error', err => {
      if (worker._currentTask) worker._currentTask.reject(err);
    });
    this.#workers.push(worker);
    return worker;
  }

  #processQueue(worker) {
    if (this.#queue.length > 0) {
      const { data, resolve, reject } = this.#queue.shift();
      this.#dispatch(worker, data, resolve, reject);
    }
  }

  #dispatch(worker, data, resolve, reject) {
    this.#activeWorkers++;
    worker._currentTask = { resolve, reject };
    worker.postMessage(data);
  }

  run(data) {
    return new Promise((resolve, reject) => {
      const idle = this.#workers.find(w => !w._currentTask);
      if (idle) {
        this.#dispatch(idle, data, resolve, reject);
      } else {
        this.#queue.push({ data, resolve, reject });
      }
    });
  }

  async destroy() {
    await Promise.all(this.#workers.map(w => w.terminate()));
  }
}
```

---

## Step 7: CPU-Bound Task Offloading

```javascript
// Example: Image processing simulation with worker pool

const workerScript = `
  const { parentPort } = require('worker_threads');
  
  function processMatrix(matrix) {
    // Simulate heavy CPU computation
    const rows = matrix.length;
    const cols = matrix[0].length;
    const result = Array.from({length: rows}, () => new Array(cols).fill(0));
    
    for (let i = 1; i < rows - 1; i++) {
      for (let j = 1; j < cols - 1; j++) {
        // Blur kernel
        result[i][j] = (
          matrix[i-1][j-1] + matrix[i-1][j] + matrix[i-1][j+1] +
          matrix[i][j-1]   + matrix[i][j]   + matrix[i][j+1] +
          matrix[i+1][j-1] + matrix[i+1][j] + matrix[i+1][j+1]
        ) / 9;
      }
    }
    return result;
  }
  
  parentPort.on('message', (data) => {
    const result = processMatrix(data.matrix);
    parentPort.postMessage({ result });
  });
`;

// Usage
async function main() {
  const pool = new WorkerPool(workerScript, 2);
  
  const matrix = Array.from({length: 100}, () =>
    Array.from({length: 100}, () => Math.random() * 255)
  );
  
  const start = Date.now();
  const results = await Promise.all(
    Array.from({length: 4}, () => pool.run({ matrix }))
  );
  console.log(`Processed 4 matrices in ${Date.now() - start}ms`);
  await pool.destroy();
}
```

---

## Step 8: Capstone — Worker fib(35)

```javascript
const { Worker, isMainThread, parentPort, workerData } = require('worker_threads');

if (isMainThread) {
  const code = `
    const { parentPort, workerData } = require('worker_threads');
    function fib(n) { return n <= 1 ? n : fib(n-1) + fib(n-2); }
    parentPort.postMessage(fib(workerData.n));
  `;
  const w = new Worker(code, { eval: true, workerData: { n: 35 } });
  w.on('message', result => console.log('fib(35) =', result));
  w.on('error', e => console.error(e));
}
```

**Run verification:**
```bash
docker run --rm node:20-alpine sh -c "node -e '
const { Worker, isMainThread, parentPort, workerData } = require(\"worker_threads\");
if (isMainThread) {
  const code = \`
    const { parentPort, workerData } = require(\"worker_threads\");
    function fib(n) { return n <= 1 ? n : fib(n-1) + fib(n-2); }
    parentPort.postMessage(fib(workerData.n));
  \`;
  const w = new Worker(code, { eval: true, workerData: { n: 35 } });
  w.on(\"message\", result => console.log(\"fib(35) =\", result));
  w.on(\"error\", e => console.error(e));
}
'"
```

📸 **Verified Output:**
```
fib(35) = 9227465
```

---

## Summary

| Concept | API | Use Case |
|---------|-----|----------|
| Worker creation | `new Worker(file/code, opts)` | Isolate CPU work |
| Communication | `parentPort.postMessage()` | Send data between threads |
| Shared memory | `SharedArrayBuffer` | Zero-copy shared state |
| Atomic ops | `Atomics.add/load/store` | Thread-safe operations |
| Channels | `MessageChannel` | Direct worker-to-worker |
| Transfer | `transferList: [buf]` | Zero-copy buffer move |
| Worker pool | Custom class | Manage N workers for tasks |
| `workerData` | Constructor option | Initial data to worker |
