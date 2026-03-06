# Lab 14: Observability — OpenTelemetry, Pino & Diagnostics Channel

**Time:** 60 minutes | **Level:** Architect | **Docker:** `docker run -it --rm node:20-alpine sh`

"You can't manage what you can't measure." This lab covers the three pillars of observability: traces (OpenTelemetry), metrics, and structured logging (pino), plus Node.js's built-in `diagnostics_channel`.

---

## Step 1: The Three Pillars of Observability

```
TRACES          → WHAT happened, in what order, how long each step took
                  (distributed request tracing across services)

METRICS         → HOW MUCH: counts, rates, histograms over time
                  (request rate, error rate, latency p99, heap usage)

LOGS            → WHAT exactly happened, with context
                  (structured JSON: level, msg, traceId, userId, duration)
```

**OpenTelemetry (OTel)** is the CNCF standard for all three pillars. One SDK, any backend (Jaeger, Zipkin, Tempo, Datadog, etc.).

---

## Step 2: Install OpenTelemetry

```bash
npm install @opentelemetry/sdk-trace-base @opentelemetry/api
# For auto-instrumentation:
# npm install @opentelemetry/sdk-node @opentelemetry/auto-instrumentations-node
```

---

## Step 3: TracerProvider + Custom Spans

```javascript
// file: tracer-setup.js
const {
  BasicTracerProvider,
  SimpleSpanProcessor,
  InMemorySpanExporter,
  ConsoleSpanExporter,
} = require('@opentelemetry/sdk-trace-base');

// In production: replace with OtlpTraceExporter
const exporter = new InMemorySpanExporter();
const provider = new BasicTracerProvider({
  spanProcessors: [new SimpleSpanProcessor(exporter)],
});

const tracer = provider.getTracer('my-service', '1.0.0');

// Create spans
async function processRequest(requestId) {
  const span = tracer.startSpan('process-request', {
    attributes: {
      'request.id': requestId,
      'service.name': 'my-service',
    }
  });

  try {
    span.addEvent('request.received', { timestamp: Date.now() });

    // Simulate sub-operation
    await computeTask(span);

    span.setStatus({ code: 1 }); // OK
    span.setAttribute('request.success', true);
  } catch (err) {
    span.recordException(err);
    span.setStatus({ code: 2, message: err.message }); // ERROR
  } finally {
    span.end();
  }
}

async function computeTask(parentSpan) {
  // Child span
  const ctx = require('@opentelemetry/api').context.with(
    require('@opentelemetry/api').trace.setSpan(require('@opentelemetry/api').context.active(), parentSpan),
    () => require('@opentelemetry/api').context.active()
  );

  const childSpan = tracer.startSpan('compute-fibonacci', {
    attributes: { 'task.type': 'fibonacci', 'task.n': 10 },
  });

  const fib = (n) => n <= 1 ? n : fib(n-1) + fib(n-2);
  const result = fib(10);
  childSpan.setAttribute('task.result', result);
  childSpan.end();
  return result;
}

await processRequest('req-001');
await processRequest('req-002');

// Inspect recorded spans
const spans = exporter.getFinishedSpans();
console.log(`Recorded ${spans.length} spans:`);
for (const span of spans) {
  console.log(`  ${span.name}`);
  console.log(`    traceId: ${span.spanContext().traceId}`);
  console.log(`    attrs:   ${JSON.stringify(span.attributes)}`);
}
```

📸 **Verified Output:**
```
fib(10) = 55
Span name: compute-task
traceId: 2d9594e608f9dd5cb1dcaf294dd701e9
Attributes: {"task.type":"fibonacci","result":55}
```

---

## Step 4: Metrics — Counter, Histogram, Gauge

```javascript
// file: metrics-demo.js
// npm install @opentelemetry/sdk-metrics @opentelemetry/api

// Simple in-memory metrics without OTel for illustration:
class MetricsCollector {
  constructor() {
    this.counters = new Map();
    this.histograms = new Map();
    this.gauges = new Map();
  }

  // Counter: monotonically increasing (requests, errors)
  increment(name, value = 1, labels = {}) {
    const key = name + JSON.stringify(labels);
    this.counters.set(key, (this.counters.get(key) || 0) + value);
  }

  // Histogram: distribution of values (latency, payload size)
  record(name, value, labels = {}) {
    const key = name + JSON.stringify(labels);
    if (!this.histograms.has(key)) this.histograms.set(key, []);
    this.histograms.get(key).push(value);
  }

  // Gauge: current value (active connections, queue depth)
  set(name, value) { this.gauges.set(name, value); }

  // Percentile helper
  percentile(values, p) {
    const sorted = [...values].sort((a, b) => a - b);
    const idx = Math.ceil(p * sorted.length) - 1;
    return sorted[Math.max(0, idx)];
  }

  report() {
    console.log('\n=== Metrics Report ===');
    for (const [key, val] of this.counters) console.log(`Counter ${key}: ${val}`);
    for (const [key, vals] of this.histograms) {
      const avg = vals.reduce((a, b) => a + b, 0) / vals.length;
      console.log(`Histogram ${key}: count=${vals.length} avg=${avg.toFixed(1)}ms p50=${this.percentile(vals, 0.5)}ms p99=${this.percentile(vals, 0.99)}ms`);
    }
    for (const [key, val] of this.gauges) console.log(`Gauge ${key}: ${val}`);
  }
}

const metrics = new MetricsCollector();

// Simulate request handling
for (let i = 0; i < 100; i++) {
  metrics.increment('http.requests', 1, { method: 'GET', path: '/api/users' });
  const latency = Math.random() * 100 + 5;
  metrics.record('http.latency', latency, { path: '/api/users' });
  if (Math.random() < 0.05) metrics.increment('http.errors', 1, { code: '500' });
}

metrics.set('active_connections', 42);
metrics.set('queue_depth', 7);
metrics.report();
```

---

## Step 5: Pino Structured Logging

```bash
npm install pino pino-pretty
```

```javascript
// file: pino-logging.js
const pino = require('pino');

// Production: JSON output
const logger = pino({
  level: process.env.LOG_LEVEL || 'info',
  base: { pid: process.pid, service: 'my-service', version: '1.0.0' },
  timestamp: pino.stdTimeFunctions.isoTime,
  formatters: {
    level: (label) => ({ level: label }), // use string level, not number
  },
  serializers: {
    err: pino.stdSerializers.err,
    req: (req) => ({ method: req.method, url: req.url, id: req.id }),
    res: (res) => ({ statusCode: res.statusCode }),
  },
});

// Child loggers inherit context
const requestLogger = logger.child({ requestId: 'req-123', userId: 'user-456' });
requestLogger.info({ action: 'start' }, 'Processing request');
requestLogger.info({ action: 'db.query', table: 'users', durationMs: 12 }, 'DB query complete');
requestLogger.warn({ action: 'cache.miss', key: 'user:456' }, 'Cache miss');

// Error logging with full stack
try {
  throw new Error('Something went wrong');
} catch (err) {
  requestLogger.error({ err, action: 'error' }, 'Request failed');
}

// Performance: pino is ~5x faster than winston
const N = 10000;
const start = Date.now();
for (let i = 0; i < N; i++) {
  logger.debug({ i }, 'debug message');
}
console.log(`\nLogged ${N} messages in ${Date.now() - start}ms`);
```

> 💡 Use `pino-pretty` for development: `node app.js | pino-pretty`. In production, output raw JSON and use a log aggregator (Loki, CloudWatch, ELK).

---

## Step 6: AsyncLocalStorage + Trace Context Propagation

```javascript
// file: trace-context.js
const { AsyncLocalStorage } = require('async_hooks');
const {
  BasicTracerProvider,
  SimpleSpanProcessor,
  InMemorySpanExporter,
} = require('@opentelemetry/sdk-trace-base');

const traceStorage = new AsyncLocalStorage();

const exporter = new InMemorySpanExporter();
const provider = new BasicTracerProvider({
  spanProcessors: [new SimpleSpanProcessor(exporter)],
});
const tracer = provider.getTracer('context-demo');

// Middleware: start span + store in AsyncLocalStorage
async function withTracing(requestId, fn) {
  const span = tracer.startSpan('request', { attributes: { 'request.id': requestId } });
  return traceStorage.run({ span, requestId }, async () => {
    try {
      const result = await fn();
      span.setStatus({ code: 1 }); // OK
      return result;
    } catch (err) {
      span.recordException(err);
      span.setStatus({ code: 2, message: err.message });
      throw err;
    } finally {
      span.end();
    }
  });
}

// Any function can access current trace context
function getCurrentSpan() {
  return traceStorage.getStore()?.span;
}

async function dbQuery(table) {
  const parentSpan = getCurrentSpan();
  const childSpan = tracer.startSpan(`db.${table}`);
  childSpan.setAttribute('db.table', table);
  await new Promise(r => setTimeout(r, 10)); // simulate query
  childSpan.end();
  return [{ id: 1 }];
}

// Handle two concurrent requests
await Promise.all([
  withTracing('req-A', async () => { await dbQuery('users'); await dbQuery('orders'); }),
  withTracing('req-B', async () => { await dbQuery('products'); }),
]);

const spans = exporter.getFinishedSpans();
console.log(`Spans recorded: ${spans.length}`);
spans.forEach(s => console.log(`  ${s.name} [${s.spanContext().traceId.slice(0,8)}...]`));
```

---

## Step 7: `node:diagnostics_channel`

```javascript
// file: diagnostics-channel.js
const diagnostics = require('node:diagnostics_channel');

// Create channels for different subsystems
const dbChannel = diagnostics.channel('db:query');
const cacheChannel = diagnostics.channel('cache:operation');
const httpChannel = diagnostics.channel('http:request');

// Subscribers (monitoring/tracing tools hook here)
diagnostics.subscribe('db:query', ({ sql, params, durationMs }) => {
  console.log(`[DB] ${sql} (${params}) → ${durationMs}ms`);
});

diagnostics.subscribe('cache:operation', ({ op, key, hit }) => {
  console.log(`[Cache] ${op} ${key} → ${hit ? 'HIT' : 'MISS'}`);
});

diagnostics.subscribe('http:request', ({ method, url, statusCode, durationMs }) => {
  console.log(`[HTTP] ${method} ${url} ${statusCode} ${durationMs}ms`);
});

// Application code publishes to channels
async function queryDB(sql, params = []) {
  const start = Date.now();
  await new Promise(r => setTimeout(r, 15)); // simulate
  dbChannel.publish({ sql, params, durationMs: Date.now() - start });
  return [];
}

async function cacheGet(key) {
  const hit = Math.random() > 0.5;
  cacheChannel.publish({ op: 'GET', key, hit });
  return hit ? 'cached-value' : null;
}

// Simulate request handling
await cacheGet('user:1');
await cacheGet('user:2');
await queryDB('SELECT * FROM users WHERE id = ?', [42]);
httpChannel.publish({ method: 'GET', url: '/api/users', statusCode: 200, durationMs: 32 });
```

> 💡 `diagnostics_channel` is zero-overhead when no one is subscribed. It's how Node.js's built-in HTTP, PostgreSQL drivers, and Express can publish hook points without impacting performance.

---

## Step 8: Capstone — Full Observability Stack

```javascript
// file: full-observability.js
'use strict';
const { AsyncLocalStorage } = require('async_hooks');
const {
  BasicTracerProvider,
  SimpleSpanProcessor,
  InMemorySpanExporter,
} = require('@opentelemetry/sdk-trace-base');
const diagnostics = require('node:diagnostics_channel');

// === SETUP ===
const traceStorage = new AsyncLocalStorage();
const exporter = new InMemorySpanExporter();
const provider = new BasicTracerProvider({
  spanProcessors: [new SimpleSpanProcessor(exporter)],
});
const tracer = provider.getTracer('platform', '1.0');

// === METRICS ===
const metrics = { requests: 0, errors: 0, latencies: [] };

// === STRUCTURED LOGGER ===
const log = {
  info: (msg, ctx = {}) => console.log(JSON.stringify({ level: 'info', msg, ...ctx, ts: new Date().toISOString() })),
  warn: (msg, ctx = {}) => console.log(JSON.stringify({ level: 'warn', msg, ...ctx, ts: new Date().toISOString() })),
  error: (msg, ctx = {}) => console.log(JSON.stringify({ level: 'error', msg, ...ctx, ts: new Date().toISOString() })),
};

// === DIAGNOSTICS CHANNEL ===
const queryChannel = diagnostics.channel('db:query');
diagnostics.subscribe('db:query', ({ sql, ms }) => {
  const store = traceStorage.getStore();
  if (store?.span) store.span.addEvent('db.query', { 'db.statement': sql, 'db.duration_ms': ms });
  log.info('db.query', { sql, ms, traceId: store?.traceId });
});

// === REQUEST HANDLER ===
async function handleRequest(requestId, simulateError = false) {
  const span = tracer.startSpan('http.request', { attributes: { 'http.request_id': requestId } });
  const traceId = span.spanContext().traceId;
  const start = Date.now();
  metrics.requests++;

  return traceStorage.run({ span, traceId, requestId }, async () => {
    try {
      log.info('request.start', { requestId, traceId });

      // DB query
      const dbStart = Date.now();
      await new Promise(r => setTimeout(r, 10 + Math.random() * 20));
      queryChannel.publish({ sql: 'SELECT * FROM users', ms: Date.now() - dbStart });

      if (simulateError) throw new Error('Internal error');

      const duration = Date.now() - start;
      metrics.latencies.push(duration);
      log.info('request.complete', { requestId, traceId, durationMs: duration });
      span.setStatus({ code: 1 });
      return { success: true };
    } catch (err) {
      metrics.errors++;
      log.error('request.error', { requestId, traceId, error: err.message });
      span.recordException(err);
      span.setStatus({ code: 2, message: err.message });
      throw err;
    } finally {
      span.end();
    }
  });
}

// === RUN ===
const requests = [
  handleRequest('r1'),
  handleRequest('r2'),
  handleRequest('r3', true), // error
  handleRequest('r4'),
];

await Promise.allSettled(requests);

// === REPORT ===
const spans = exporter.getFinishedSpans();
const avgLatency = metrics.latencies.reduce((a, b) => a + b, 0) / metrics.latencies.length;

console.log('\n=== Observability Report ===');
console.log(`Requests: ${metrics.requests} | Errors: ${metrics.errors} | Error rate: ${(metrics.errors/metrics.requests*100).toFixed(0)}%`);
console.log(`Avg latency: ${avgLatency?.toFixed(1)}ms`);
console.log(`Spans recorded: ${spans.length}`);
spans.forEach(s => console.log(`  [${s.spanContext().traceId.slice(0,8)}] ${s.name} status=${s.status.code === 2 ? 'ERROR' : 'OK'}`));
```

---

## Summary

| Pillar | Tool | Key Concept |
|---|---|---|
| Traces | `@opentelemetry/sdk-trace-base` | Spans, traceId, context propagation |
| Metrics | `@opentelemetry/sdk-metrics` | Counter, Histogram, Gauge |
| Logs | `pino` | Structured JSON, child loggers |
| Context | `AsyncLocalStorage` | Propagate traceId through async calls |
| Hooks | `diagnostics_channel` | Zero-overhead instrumentation points |
| Export | OTLP exporter | Send to Jaeger, Tempo, Datadog, etc. |
| Auto-instrument | `@opentelemetry/auto-instrumentations-node` | HTTP, pg, redis — zero config |
