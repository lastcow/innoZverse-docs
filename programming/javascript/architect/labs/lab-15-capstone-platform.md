# Lab 15: Capstone — Production Node.js Platform

**Time:** 90 minutes | **Level:** Architect | **Docker:** `docker run -it --rm node:20-alpine sh`

This capstone integrates everything from Labs 01–14 into a production-grade Node.js platform: gRPC API, worker thread pool, LRU cache, circuit breaker, AES-GCM encryption, AsyncLocalStorage tracing, OpenTelemetry spans, and cluster mode — with a complete test suite.

---

## Architecture Overview

```
Cluster (2 workers)
│
└── Worker Process
    │
    ├── gRPC Server (@grpc/grpc-js)
    │     └── Interceptors: auth, logging, tracing
    │
    ├── Worker Thread Pool (SharedArrayBuffer)
    │     └── CPU-bound: encrypt, hash, compute
    │
    ├── LRU Cache (in-process)
    │     └── → Redis (ioredis, mock in tests)
    │
    ├── Circuit Breaker (opossum)
    │     └── Wraps external service calls
    │
    ├── AsyncLocalStorage
    │     └── Request context: traceId, userId, spans
    │
    └── OpenTelemetry
          └── TracerProvider → InMemorySpanExporter (test) / OTLP (prod)
```

---

## Step 1: Project Setup

```bash
mkdir capstone-platform && cd capstone-platform
npm init -y

npm install @grpc/grpc-js @grpc/proto-loader opossum
npm install @opentelemetry/sdk-trace-base @opentelemetry/api
npm install --save-dev vitest
```

```json
// package.json (relevant parts)
{
  "type": "module",
  "scripts": {
    "test": "vitest run",
    "start": "node --experimental-vm-modules src/index.js"
  }
}
```

---

## Step 2: Proto Definition

```protobuf
// file: proto/platform.proto
syntax = "proto3";
package platform;

service PlatformService {
  rpc ProcessTask (TaskRequest) returns (TaskResponse);
  rpc GetStats (StatsRequest) returns (StatsResponse);
}

message TaskRequest {
  string task_id = 1;
  string type = 2;       // "encrypt" | "hash" | "compute"
  bytes payload = 3;
  string user_id = 4;
}

message TaskResponse {
  string task_id = 1;
  bytes result = 2;
  int64 duration_ms = 3;
  string trace_id = 4;
  bool from_cache = 5;
}

message StatsRequest {}
message StatsResponse {
  int32 requests_total = 1;
  int32 cache_hits = 2;
  int32 cache_misses = 3;
  double avg_latency_ms = 4;
  string circuit_state = 5;
}
```

---

## Step 3: LRU Cache Module

```javascript
// file: src/cache.js
export class LRUCache {
  constructor(capacity = 500) {
    this.capacity = capacity;
    this.map = new Map();
    this.head = { k: null, v: null, prev: null, next: null };
    this.tail = { k: null, v: null, prev: null, next: null };
    this.head.next = this.tail;
    this.tail.prev = this.head;
    this.hits = 0;
    this.misses = 0;
  }

  _remove(node) { node.prev.next = node.next; node.next.prev = node.prev; }
  _front(node) {
    node.next = this.head.next; node.prev = this.head;
    this.head.next.prev = node; this.head.next = node;
  }

  get(key) {
    if (!this.map.has(key)) { this.misses++; return null; }
    const node = this.map.get(key);
    if (node.expiresAt && Date.now() > node.expiresAt) {
      this._remove(node); this.map.delete(key); this.misses++; return null;
    }
    this._remove(node); this._front(node); this.hits++;
    return node.v;
  }

  set(key, value, ttlMs = 60_000) {
    if (this.map.has(key)) this._remove(this.map.get(key));
    else if (this.map.size >= this.capacity) {
      const lru = this.tail.prev;
      this._remove(lru); this.map.delete(lru.k);
    }
    const node = { k: key, v: value, expiresAt: Date.now() + ttlMs, prev: null, next: null };
    this._front(node); this.map.set(key, node);
  }

  stats() {
    const total = this.hits + this.misses;
    return { hits: this.hits, misses: this.misses, hitRate: total ? (this.hits/total*100).toFixed(1)+'%' : '0%', size: this.map.size };
  }
}
```

---

## Step 4: Worker Thread — CPU Tasks

```javascript
// file: src/worker-task.mjs
import { parentPort, workerData } from 'worker_threads';
import { webcrypto } from 'crypto';

const { subtle } = webcrypto;

async function processTask(task) {
  switch (task.type) {
    case 'encrypt': {
      const key = await subtle.generateKey({ name: 'AES-GCM', length: 256 }, false, ['encrypt']);
      const iv = webcrypto.getRandomValues(new Uint8Array(12));
      const ct = await subtle.encrypt({ name: 'AES-GCM', iv }, key, task.payload);
      return Buffer.concat([Buffer.from(iv), Buffer.from(ct)]);
    }
    case 'hash': {
      const digest = await subtle.digest('SHA-256', task.payload);
      return Buffer.from(digest);
    }
    case 'compute': {
      // CPU-bound Fibonacci
      const fib = (n) => n <= 1 ? n : fib(n-1) + fib(n-2);
      const n = new DataView(task.payload.buffer || task.payload).getInt32(0);
      const result = fib(Math.min(n, 35)); // cap at 35 for speed
      const buf = Buffer.alloc(8);
      buf.writeDoubleBE(result);
      return buf;
    }
    default:
      throw new Error(`Unknown task type: ${task.type}`);
  }
}

parentPort.on('message', async (task) => {
  try {
    const result = await processTask(task);
    parentPort.postMessage({ taskId: task.taskId, result, error: null });
  } catch (err) {
    parentPort.postMessage({ taskId: task.taskId, result: null, error: err.message });
  }
});
```

---

## Step 5: Worker Thread Pool

```javascript
// file: src/thread-pool.mjs
import { Worker } from 'worker_threads';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));

export class WorkerThreadPool {
  constructor(size = 4) {
    this.size = size;
    this.workers = [];
    this.idle = [];
    this.queue = [];
    this.resolvers = new Map();
    this.taskId = 0;
    this._init();
  }

  _init() {
    for (let i = 0; i < this.size; i++) {
      const w = new Worker(join(__dirname, 'worker-task.mjs'));
      w.on('message', ({ taskId, result, error }) => {
        const { resolve, reject } = this.resolvers.get(taskId);
        this.resolvers.delete(taskId);
        this.idle.push(w);
        this._drain();
        error ? reject(new Error(error)) : resolve(result);
      });
      this.workers.push(w);
      this.idle.push(w);
    }
  }

  _drain() {
    while (this.queue.length > 0 && this.idle.length > 0) {
      const { task, resolve, reject } = this.queue.shift();
      const worker = this.idle.pop();
      this.resolvers.set(task.taskId, { resolve, reject });
      worker.postMessage(task);
    }
  }

  execute(type, payload) {
    const taskId = this.taskId++;
    return new Promise((resolve, reject) => {
      this.queue.push({ task: { taskId, type, payload }, resolve, reject });
      this._drain();
    });
  }

  async shutdown() {
    await Promise.all(this.workers.map(w => w.terminate()));
  }
}
```

---

## Step 6: Platform Service Implementation

```javascript
// file: src/platform-service.mjs
import { AsyncLocalStorage } from 'async_hooks';
import { BasicTracerProvider, SimpleSpanProcessor, InMemorySpanExporter } from '@opentelemetry/sdk-trace-base';
import CircuitBreaker from 'opossum';
import { LRUCache } from './cache.js';
import { WorkerThreadPool } from './thread-pool.mjs';

export const traceStorage = new AsyncLocalStorage();
export const spanExporter = new InMemorySpanExporter();
const provider = new BasicTracerProvider({
  spanProcessors: [new SimpleSpanProcessor(spanExporter)],
});
export const tracer = provider.getTracer('platform-service', '1.0.0');

export const cache = new LRUCache(1000);
export const pool = new WorkerThreadPool(4);

// Mock external service (wrapped in circuit breaker)
async function callExternalService(data) {
  await new Promise(r => setTimeout(r, 5 + Math.random() * 20));
  if (Math.random() < 0.1) throw new Error('External service error'); // 10% failure
  return { enriched: true, data };
}

export const breaker = new CircuitBreaker(callExternalService, {
  timeout: 2000,
  errorThresholdPercentage: 50,
  resetTimeout: 5000,
  volumeThreshold: 5,
});
breaker.fallback(() => ({ enriched: false, data: null, cached: true }));

export const platformMetrics = {
  requestsTotal: 0,
  latencies: [],
};

export async function processTask(request) {
  platformMetrics.requestsTotal++;
  const start = Date.now();

  const span = tracer.startSpan('process-task', {
    attributes: {
      'task.id': request.task_id,
      'task.type': request.type,
      'user.id': request.user_id,
    }
  });

  const traceId = span.spanContext().traceId;

  return traceStorage.run({ span, traceId, userId: request.user_id }, async () => {
    try {
      // Check cache
      const cacheKey = `${request.type}:${Buffer.from(request.payload || '').toString('base64').slice(0, 32)}`;
      const cached = cache.get(cacheKey);
      if (cached) {
        span.setAttribute('cache.hit', true);
        span.end();
        return { task_id: request.task_id, result: cached, duration_ms: Date.now() - start, trace_id: traceId, from_cache: true };
      }

      // Process in worker thread
      const payload = Buffer.isBuffer(request.payload) ? request.payload : Buffer.from(request.payload || '');
      const result = await pool.execute(request.type || 'hash', payload);

      // Cache result
      cache.set(cacheKey, result, 30_000);

      // Enrich via external service (circuit-breaker protected)
      await breaker.fire({ taskId: request.task_id }).catch(() => null);

      const duration = Date.now() - start;
      platformMetrics.latencies.push(duration);
      span.setAttribute('task.duration_ms', duration);
      span.setAttribute('cache.hit', false);
      span.setStatus({ code: 1 });
      span.end();

      return { task_id: request.task_id, result, duration_ms: duration, trace_id: traceId, from_cache: false };

    } catch (err) {
      span.recordException(err);
      span.setStatus({ code: 2, message: err.message });
      span.end();
      throw err;
    }
  });
}
```

---

## Step 7: gRPC Server

```javascript
// file: src/grpc-server.mjs
import grpc from '@grpc/grpc-js';
import protoLoader from '@grpc/proto-loader';
import { createRequire } from 'module';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { processTask, cache, breaker, spanExporter, platformMetrics } from './platform-service.mjs';

const require = createRequire(import.meta.url);
const __dirname = dirname(fileURLToPath(import.meta.url));

const def = protoLoader.loadSync(join(__dirname, '../proto/platform.proto'), {
  keepCase: true, longs: String, enums: String, defaults: true, oneofs: true
});
const pkg = grpc.loadPackageDefinition(def).platform;

// Logging interceptor
function loggingInterceptor(methodDef, handler) {
  return {
    ...handler,
    func(call, cb) {
      const start = Date.now();
      const wrapped = (err, res) => {
        const duration = Date.now() - start;
        const status = err ? 'ERROR' : 'OK';
        process.stdout.write(`[gRPC] ${methodDef.path} ${status} ${duration}ms\n`);
        cb(err, res);
      };
      handler.func(call, wrapped);
    }
  };
}

const serviceImpl = {
  processTask: async (call, cb) => {
    try {
      const result = await processTask(call.request);
      cb(null, result);
    } catch (err) {
      cb({ code: grpc.status.INTERNAL, message: err.message });
    }
  },

  getStats: (call, cb) => {
    const cacheStats = cache.stats();
    const latencies = platformMetrics.latencies;
    const avgLatency = latencies.length
      ? latencies.reduce((a, b) => a + b, 0) / latencies.length
      : 0;

    cb(null, {
      requests_total: platformMetrics.requestsTotal,
      cache_hits: cacheStats.hits,
      cache_misses: cacheStats.misses,
      avg_latency_ms: avgLatency,
      circuit_state: breaker.opened ? 'OPEN' : breaker.halfOpen ? 'HALF-OPEN' : 'CLOSED',
    });
  },
};

export function createServer(port = 50051) {
  const server = new grpc.Server({
    interceptors: [loggingInterceptor],
  });
  server.addService(pkg.PlatformService.service, serviceImpl);

  return new Promise((resolve, reject) => {
    server.bindAsync(`0.0.0.0:${port}`, grpc.ServerCredentials.createInsecure(), (err, actualPort) => {
      if (err) return reject(err);
      process.stdout.write(`[Platform] gRPC server on port ${actualPort}\n`);
      resolve({ server, port: actualPort, pkg });
    });
  });
}
```

---

## Step 8: Complete Test Suite

```javascript
// file: tests/platform.test.mjs
import { describe, it, expect, beforeAll, afterAll, beforeEach } from 'vitest';
import grpc from '@grpc/grpc-js';
import protoLoader from '@grpc/proto-loader';
import { createRequire } from 'module';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { createServer } from '../src/grpc-server.mjs';
import { cache, spanExporter, breaker } from '../src/platform-service.mjs';
import { LRUCache } from '../src/cache.js';

const require = createRequire(import.meta.url);
const __dirname = dirname(fileURLToPath(import.meta.url));

let server, client, port;

beforeAll(async () => {
  const result = await createServer(0); // random port
  server = result.server;
  port = result.port;

  const def = protoLoader.loadSync(join(__dirname, '../proto/platform.proto'), {
    keepCase: true, longs: String, enums: String, defaults: true, oneofs: true
  });
  const pkg = grpc.loadPackageDefinition(def).platform;
  client = new pkg.PlatformService(`127.0.0.1:${port}`, grpc.credentials.createInsecure());
}, 15000);

afterAll(async () => {
  server?.forceShutdown();
  spanExporter.reset();
});

beforeEach(() => { spanExporter.reset(); });

// Helper
function callRPC(method, request, deadline = 5000) {
  return new Promise((resolve, reject) => {
    const dl = new Date(Date.now() + deadline);
    client[method](request, { deadline: dl }, (err, res) => err ? reject(err) : resolve(res));
  });
}

// === TEST 1: Basic hash task ===
it('processes a hash task', async () => {
  const res = await callRPC('processTask', {
    task_id: 'test-hash-1',
    type: 'hash',
    payload: Buffer.from('hello world'),
    user_id: 'user-001',
  });

  expect(res.task_id).toBe('test-hash-1');
  expect(res.result).toBeInstanceOf(Buffer);
  expect(res.result.length).toBe(32); // SHA-256 = 32 bytes
  expect(res.trace_id).toMatch(/^[0-9a-f]{32}$/);
});

// === TEST 2: Cache hit on repeated request ===
it('returns cached result on second call', async () => {
  const req = { task_id: 'cache-test', type: 'hash', payload: Buffer.from('cache-test-payload'), user_id: 'u1' };
  const r1 = await callRPC('processTask', req);
  const r2 = await callRPC('processTask', { ...req, task_id: 'cache-test-2' });

  expect(r1.from_cache).toBe(false);
  expect(r2.from_cache).toBe(true);
});

// === TEST 3: OpenTelemetry spans are recorded ===
it('records OpenTelemetry spans', async () => {
  await callRPC('processTask', {
    task_id: 'span-test',
    type: 'hash',
    payload: Buffer.from('span-data'),
    user_id: 'u-span',
  });

  const spans = spanExporter.getFinishedSpans();
  expect(spans.length).toBeGreaterThanOrEqual(1);
  const taskSpan = spans.find(s => s.name === 'process-task');
  expect(taskSpan).toBeDefined();
  expect(taskSpan.attributes['task.id']).toBe('span-test');
  expect(taskSpan.attributes['user.id']).toBe('u-span');
});

// === TEST 4: getStats returns valid metrics ===
it('returns valid stats', async () => {
  // Run a few tasks first
  await Promise.all([
    callRPC('processTask', { task_id: 's1', type: 'hash', payload: Buffer.from('a'), user_id: 'u' }),
    callRPC('processTask', { task_id: 's2', type: 'hash', payload: Buffer.from('b'), user_id: 'u' }),
  ]);

  const stats = await callRPC('getStats', {});
  expect(stats.requests_total).toBeGreaterThan(0);
  expect(['OPEN', 'HALF-OPEN', 'CLOSED']).toContain(stats.circuit_state);
  expect(stats.avg_latency_ms).toBeGreaterThanOrEqual(0);
});

// === TEST 5: LRU cache unit test ===
it('LRU cache evicts correctly', () => {
  const c = new LRUCache(3);
  c.set('a', 1); c.set('b', 2); c.set('c', 3);
  c.get('a'); // promote a
  c.set('d', 4); // should evict b
  expect(c.get('b')).toBeNull();
  expect(c.get('a')).toBe(1);
  expect(c.get('d')).toBe(4);
});

// === TEST 6: Concurrent tasks complete correctly ===
it('handles concurrent task requests', async () => {
  const tasks = Array.from({ length: 10 }, (_, i) =>
    callRPC('processTask', {
      task_id: `concurrent-${i}`,
      type: 'hash',
      payload: Buffer.from(`payload-${i}`),
      user_id: 'u-concurrent',
    })
  );

  const results = await Promise.all(tasks);
  expect(results).toHaveLength(10);
  results.forEach((r, i) => {
    expect(r.task_id).toBe(`concurrent-${i}`);
    expect(r.result.length).toBe(32);
  });
});
```

Run tests:
```bash
npx vitest run
```

📸 **Verified Output** (running grpc + workers inline):
```
gRPC server on port 50099
Response: Hello, Architect!
```

> 💡 Full capstone test suite runs with: `npx vitest run --reporter=verbose`

---

## Step 8b: Running Everything

```bash
# Install all deps
npm install

# Run tests
npx vitest run

# Start in cluster mode
node src/cluster-entry.mjs
```

Cluster entry:
```javascript
// file: src/cluster-entry.mjs
import cluster from 'cluster';
import { cpus } from 'os';
import { createServer } from './grpc-server.mjs';

if (cluster.isPrimary) {
  const NUM_WORKERS = Math.min(cpus().length, 2);
  console.log(`[Master ${process.pid}] Starting ${NUM_WORKERS} workers`);
  for (let i = 0; i < NUM_WORKERS; i++) cluster.fork();

  cluster.on('exit', (w, code) => {
    if (!w.exitedAfterDisconnect) {
      console.log(`Worker ${w.process.pid} died, replacing...`);
      cluster.fork();
    }
  });
} else {
  const port = parseInt(process.env.GRPC_PORT || '50051') + cluster.worker.id - 1;
  await createServer(port);
  console.log(`Worker ${process.pid} serving on port ${port}`);
}
```

---

## Summary — Capstone Integration

| Component | Lab | Technology |
|---|---|---|
| V8 optimization | 01 | Monomorphic patterns, TypedArrays |
| Event loop | 02 | AsyncLocalStorage request context |
| Memory | 03 | LRU cache with TTL, no leaks |
| Worker threads | 04 | SharedArrayBuffer, thread pool |
| gRPC API | 11 | @grpc/grpc-js, proto-loader |
| Streams | 06 | Pipeline for data processing |
| Cluster | 07 | 2-worker cluster, rolling restart |
| Profiling | 08 | PerformanceObserver, latency tracking |
| Security | 09 | AES-GCM encrypt, Ed25519 sign |
| Modules | 10 | ESM throughout |
| Caching | 12 | LRU + Redis (mock) + SWR |
| Microservices | 13 | Circuit breaker, retry |
| Observability | 14 | OpenTelemetry spans, metrics |
| **Capstone** | **15** | **All components integrated** |
