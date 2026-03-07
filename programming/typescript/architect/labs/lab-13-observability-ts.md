# Lab 13: Typed Observability

**Time:** 60 minutes | **Level:** Architect | **Docker:** `node:20-alpine`

## Overview

Typed observability stack: OpenTelemetry TypeScript SDK (typed spans/attributes/metrics), pino structured logging with type-safe bindings, `AsyncLocalStorage<T>` typed context propagation, and distributed tracing type patterns.

---

## Step 1: OpenTelemetry TypeScript Setup

```typescript
// src/telemetry/sdk.ts
import { NodeSDK }           from '@opentelemetry/sdk-node';
import { Resource }           from '@opentelemetry/resources';
import { ATTR_SERVICE_NAME, ATTR_SERVICE_VERSION } from '@opentelemetry/semantic-conventions';
import { OTLPTraceExporter }  from '@opentelemetry/exporter-trace-otlp-http';
import { OTLPMetricExporter } from '@opentelemetry/exporter-metrics-otlp-http';
import { PeriodicExportingMetricReader } from '@opentelemetry/sdk-metrics';

const sdk = new NodeSDK({
  resource: new Resource({
    [ATTR_SERVICE_NAME]:    'my-service',
    [ATTR_SERVICE_VERSION]: '1.0.0',
    'deployment.environment': process.env.NODE_ENV,
  }),
  traceExporter: new OTLPTraceExporter({
    url: 'http://otel-collector:4318/v1/traces',
  }),
  metricReader: new PeriodicExportingMetricReader({
    exporter: new OTLPMetricExporter({
      url: 'http://otel-collector:4318/v1/metrics',
    }),
    exportIntervalMillis: 30_000,
  }),
});

sdk.start();
process.on('SIGTERM', () => sdk.shutdown());
```

---

## Step 2: Typed Spans

```typescript
import { trace, SpanStatusCode, SpanKind, Attributes } from '@opentelemetry/api';

const tracer = trace.getTracer('my-service', '1.0.0');

// Type-safe span attribute keys (semantic conventions)
const SpanAttributes = {
  HTTP_METHOD:      'http.request.method',
  HTTP_URL:         'url.full',
  HTTP_STATUS_CODE: 'http.response.status_code',
  DB_SYSTEM:        'db.system',
  DB_OPERATION:     'db.operation.name',
  USER_ID:          'app.user.id',
  ORDER_ID:         'app.order.id',
} as const;

type SpanAttributeKey = typeof SpanAttributes[keyof typeof SpanAttributes];

// Typed span wrapper
async function withSpan<T>(
  name: string,
  attributes: Partial<Record<SpanAttributeKey, string | number | boolean>>,
  fn: () => Promise<T>
): Promise<T> {
  return tracer.startActiveSpan(name, { attributes, kind: SpanKind.INTERNAL }, async (span) => {
    try {
      const result = await fn();
      span.setStatus({ code: SpanStatusCode.OK });
      return result;
    } catch (error) {
      span.recordException(error as Error);
      span.setStatus({ code: SpanStatusCode.ERROR, message: (error as Error).message });
      throw error;
    } finally {
      span.end();
    }
  });
}

// Usage — attribute keys are autocompleted and type-checked
const user = await withSpan(
  'db.findUser',
  {
    [SpanAttributes.DB_SYSTEM]: 'sqlite',
    [SpanAttributes.DB_OPERATION]: 'SELECT',
    [SpanAttributes.USER_ID]: userId,
  },
  () => db.users.findById(userId)
);
```

---

## Step 3: AsyncLocalStorage for Request Context

```typescript
import { AsyncLocalStorage } from 'node:async_hooks';

interface RequestContext {
  requestId:  string;
  userId:     string | null;
  traceId:    string;
  startTime:  number;
  path:       string;
  method:     string;
}

// Typed singleton context store
const requestContext = new AsyncLocalStorage<RequestContext>();

// Middleware: set context for each request
function contextMiddleware(req: Request, res: Response, next: NextFunction): void {
  const traceId = trace.getActiveSpan()?.spanContext().traceId ?? generateId();

  requestContext.run(
    {
      requestId: req.headers['x-request-id'] as string ?? generateId(),
      userId:    req.user?.id ?? null,
      traceId,
      startTime: performance.now(),
      path:      req.path,
      method:    req.method,
    },
    next
  );
}

// Anywhere in the call stack: get typed context
function getCurrentContext(): RequestContext {
  const ctx = requestContext.getStore();
  if (!ctx) throw new Error('No request context — called outside request handler');
  return ctx;
}

// Usage in deep function
function logAction(action: string): void {
  const ctx = getCurrentContext();
  logger.info({ action, userId: ctx.userId, traceId: ctx.traceId }, 'Action performed');
}
```

---

## Step 4: Pino — Type-Safe Structured Logging

```typescript
import pino, { Logger } from 'pino';

// Type-safe log bindings
interface LogBindings {
  service:    string;
  version:    string;
  environment: string;
}

interface RequestBindings {
  requestId: string;
  userId:    string | null;
  method:    string;
  path:      string;
}

// Create typed logger
const logger = pino<keyof (LogBindings & RequestBindings)>({
  level: process.env.LOG_LEVEL ?? 'info',
  transport: process.env.NODE_ENV === 'development'
    ? { target: 'pino-pretty' }
    : undefined,
  base: {
    service: 'my-service',
    version: process.env.npm_package_version,
  },
  serializers: {
    error: pino.stdSerializers.err,
    req:   pino.stdSerializers.req,
    res:   pino.stdSerializers.res,
  },
});

// Per-request logger with bindings
function createRequestLogger(req: Request): Logger {
  const { requestId, userId, traceId } = getCurrentContext();
  return logger.child({
    requestId,
    userId,
    traceId,
    method: req.method,
    path:   req.path,
  });
}

// Type-safe log calls
logger.info({ userId: 'u-123', action: 'login' }, 'User logged in');
logger.warn({ userId: 'u-123', attempts: 3 }, 'Multiple failed login attempts');
logger.error({ error: new Error('DB timeout'), query: 'SELECT...' }, 'Database error');
```

---

## Step 5: Typed Metrics

```typescript
import { metrics, ObservableGauge, Counter, Histogram } from '@opentelemetry/api';

const meter = metrics.getMeter('my-service', '1.0.0');

// Typed metric instruments
interface AppMetrics {
  httpRequestDuration: Histogram;
  httpRequestCount:    Counter;
  activeConnections:   ObservableGauge;
  cacheHitRate:        ObservableGauge;
}

const appMetrics: AppMetrics = {
  httpRequestDuration: meter.createHistogram('http.request.duration', {
    description: 'HTTP request duration in milliseconds',
    unit: 'ms',
    advice: { explicitBucketBoundaries: [5, 10, 25, 50, 100, 250, 500, 1000] },
  }),

  httpRequestCount: meter.createCounter('http.request.count', {
    description: 'Total HTTP request count',
  }),

  activeConnections: meter.createObservableGauge('db.active_connections', {
    description: 'Number of active database connections',
  }),

  cacheHitRate: meter.createObservableGauge('cache.hit_rate', {
    description: 'Cache hit rate (0-1)',
  }),
};

// Record metrics with typed attributes
function recordHttpRequest(
  method: string,
  path: string,
  statusCode: number,
  durationMs: number
): void {
  const attrs = { 'http.request.method': method, 'url.path': path, 'http.response.status_code': statusCode };
  appMetrics.httpRequestDuration.record(durationMs, attrs);
  appMetrics.httpRequestCount.add(1, attrs);
}
```

---

## Step 6: Distributed Tracing — Context Propagation

```typescript
import { context, propagation, trace } from '@opentelemetry/api';

// Extract trace context from incoming request (W3C TraceContext)
function extractTraceContext(headers: Record<string, string>): void {
  const carrier = { traceparent: headers['traceparent'], tracestate: headers['tracestate'] };
  const ctx = propagation.extract(context.active(), carrier);
  context.with(ctx, () => {
    // All spans created here are children of the incoming trace
  });
}

// Inject trace context into outgoing request
async function httpRequest(url: string, opts: RequestInit = {}): Promise<Response> {
  const headers: Record<string, string> = { ...(opts.headers as Record<string, string>) };

  // Inject current trace context
  propagation.inject(context.active(), headers);
  // Now headers contains 'traceparent' and 'tracestate'

  return fetch(url, { ...opts, headers });
}
```

---

## Step 7: Error Tracking with Types

```typescript
// Typed error categories for structured error tracking
const ErrorCategories = {
  VALIDATION:    'validation',
  DATABASE:      'database',
  NETWORK:       'network',
  AUTHORIZATION: 'authorization',
  RATE_LIMIT:    'rate_limit',
  UNKNOWN:       'unknown',
} as const;
type ErrorCategory = typeof ErrorCategories[keyof typeof ErrorCategories];

interface AppError {
  category:  ErrorCategory;
  code:      string;
  message:   string;
  context:   Record<string, unknown>;
}

function captureError(error: AppError): void {
  const span = trace.getActiveSpan();
  if (span) {
    span.setAttributes({
      'error.category': error.category,
      'error.code':     error.code,
    });
    span.recordException(new Error(error.message));
    span.setStatus({ code: SpanStatusCode.ERROR, message: error.message });
  }

  logger.error({ ...error }, error.message);
}
```

---

## Step 8: Capstone — OpenTelemetry Typed Spans

```bash
docker run --rm node:20-alpine sh -c "
  mkdir -p /work && cd /work && npm init -y > /dev/null 2>&1
  npm install @opentelemetry/sdk-trace-base @opentelemetry/api 2>&1 | tail -1
  node -e \"
const { BasicTracerProvider, SimpleSpanProcessor, InMemorySpanExporter } = require('@opentelemetry/sdk-trace-base');
const api = require('@opentelemetry/api');
const exporter = new InMemorySpanExporter();
const provider = new BasicTracerProvider({ spanProcessors: [new SimpleSpanProcessor(exporter)] });
api.trace.setGlobalTracerProvider(provider);
const tracer = provider.getTracer('my-service', '1.0.0');
const span = tracer.startSpan('processOrder');
span.setAttribute('order.id', 'ORD-123');
span.setAttribute('order.value', 99.99);
span.setStatus({ code: api.SpanStatusCode.OK });
span.end();
const spans = exporter.getFinishedSpans();
console.log('=== OpenTelemetry Typed Spans ===');
spans.forEach(s => {
  console.log('Span:', s.name);
  console.log('  TraceId:', s.spanContext().traceId);
  console.log('  Attrs:', JSON.stringify(s.attributes));
  console.log('  Status:', s.status.code === api.SpanStatusCode.OK ? 'OK' : 'UNSET');
});
  \"
"
```

📸 **Verified Output:**
```
=== OpenTelemetry Typed Spans ===
Span: processOrder
  TraceId: 3089959a23406ce9648002ee7b6eec79
  Attrs: {"order.id":"ORD-123","order.value":99.99}
  Status: OK
```

---

## Summary

| Tool | Type Feature | Benefit |
|------|-------------|---------|
| OpenTelemetry | `Attributes` type | Type-checked span attrs |
| `AsyncLocalStorage<T>` | Generic type param | Type-safe request context |
| pino | `Logger<K>` | Typed log bindings |
| Semantic conventions | `ATTR_*` constants | Standard attribute names |
| Custom metrics | `Histogram/Counter` | Typed instrument API |
| W3C propagation | `propagation.inject` | Distributed trace context |
