# Lab 06: Microservices Patterns

**Time:** 30 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Implement microservice patterns in Node.js: API Gateway, Circuit Breaker state machine, Bulkhead, Service Discovery, health checks, graceful shutdown, and structured logging.

---

## Step 1: Circuit Breaker

```javascript
// Circuit Breaker: CLOSED -> OPEN -> HALF_OPEN -> CLOSED/OPEN
class CircuitBreaker {
  static STATES = { CLOSED: 'CLOSED', OPEN: 'OPEN', HALF_OPEN: 'HALF_OPEN' };

  #fn; #state; #failures; #successes; #nextAttempt;
  #threshold; #successThreshold; #timeout; #onStateChange;

  constructor(fn, options = {}) {
    this.#fn = fn;
    this.#state = CircuitBreaker.STATES.CLOSED;
    this.#failures = 0;
    this.#successes = 0;
    this.#threshold = options.threshold ?? 5;
    this.#successThreshold = options.successThreshold ?? 2;
    this.#timeout = options.timeout ?? 30000;
    this.#onStateChange = options.onStateChange ?? (() => {});
    this.#nextAttempt = Date.now();
  }

  get state() { return this.#state; }
  get metrics() { return { state: this.#state, failures: this.#failures, successes: this.#successes }; }

  #transition(newState) {
    if (this.#state !== newState) {
      this.#onStateChange(this.#state, newState);
      this.#state = newState;
    }
  }

  async call(...args) {
    if (this.#state === CircuitBreaker.STATES.OPEN) {
      if (Date.now() < this.#nextAttempt) {
        throw new Error(`Circuit breaker OPEN. Retry after ${new Date(this.#nextAttempt).toISOString()}`);
      }
      this.#transition(CircuitBreaker.STATES.HALF_OPEN);
      this.#successes = 0;
    }

    try {
      const result = await this.#fn(...args);
      this.#onSuccess();
      return result;
    } catch (err) {
      this.#onFailure();
      throw err;
    }
  }

  #onSuccess() {
    this.#failures = 0;
    if (this.#state === CircuitBreaker.STATES.HALF_OPEN) {
      this.#successes++;
      if (this.#successes >= this.#successThreshold) {
        this.#transition(CircuitBreaker.STATES.CLOSED);
      }
    }
  }

  #onFailure() {
    this.#failures++;
    if (this.#failures >= this.#threshold || this.#state === CircuitBreaker.STATES.HALF_OPEN) {
      this.#nextAttempt = Date.now() + this.#timeout;
      this.#transition(CircuitBreaker.STATES.OPEN);
    }
  }
}

// Demo
let callCount = 0;
const unstableService = async () => {
  callCount++;
  if (callCount <= 3) throw new Error('Service down');
  return 'Success';
};

const cb = new CircuitBreaker(unstableService, {
  threshold: 3,
  onStateChange: (from, to) => console.log(`Circuit: ${from} -> ${to}`)
});

(async () => {
  for (let i = 0; i < 5; i++) {
    try {
      const r = await cb.call();
      console.log(`Call ${i+1}: ${r} [${cb.state}]`);
    } catch (e) {
      console.log(`Call ${i+1}: ${e.message.slice(0,30)}... [${cb.state}]`);
    }
  }
})();
```

---

## Step 2: Bulkhead Pattern

```javascript
// Bulkhead: limit concurrent requests to prevent cascading failures
class Bulkhead {
  #maxConcurrent;
  #maxQueue;
  #active = 0;
  #queue = [];

  constructor({ maxConcurrent = 10, maxQueue = 100 } = {}) {
    this.#maxConcurrent = maxConcurrent;
    this.#maxQueue = maxQueue;
  }

  async execute(fn) {
    if (this.#active >= this.#maxConcurrent) {
      if (this.#queue.length >= this.#maxQueue) {
        throw new Error('Bulkhead queue full — request rejected');
      }
      await new Promise((resolve, reject) => {
        this.#queue.push({ resolve, reject });
      });
    }

    this.#active++;
    try {
      return await fn();
    } finally {
      this.#active--;
      this.#processQueue();
    }
  }

  #processQueue() {
    const next = this.#queue.shift();
    if (next) next.resolve();
  }

  get stats() {
    return { active: this.#active, queued: this.#queue.length };
  }
}

// Usage
const dbBulkhead = new Bulkhead({ maxConcurrent: 5, maxQueue: 20 });

async function queryDB(id) {
  return dbBulkhead.execute(async () => {
    await new Promise(r => setTimeout(r, 10)); // Simulate DB query
    return { id, data: 'result' };
  });
}
```

---

## Step 3: Retry Pattern

```javascript
async function withRetry(fn, options = {}) {
  const {
    maxAttempts = 3,
    baseDelay = 100,
    maxDelay = 10000,
    backoff = 'exponential', // 'linear', 'exponential', 'fixed'
    shouldRetry = (err) => true,
    onRetry = (err, attempt) => {}
  } = options;

  let lastError;
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (err) {
      lastError = err;
      if (attempt === maxAttempts || !shouldRetry(err)) throw err;

      const delay = backoff === 'exponential'
        ? Math.min(baseDelay * 2 ** (attempt - 1), maxDelay)
        : backoff === 'linear'
        ? Math.min(baseDelay * attempt, maxDelay)
        : baseDelay;

      const jitter = delay * 0.2 * Math.random(); // Add jitter
      onRetry(err, attempt);
      await new Promise(r => setTimeout(r, delay + jitter));
    }
  }
  throw lastError;
}
```

---

## Step 4: Structured Logging

```javascript
// Structured logging (pino-like without dependencies)
const levels = { trace: 10, debug: 20, info: 30, warn: 40, error: 50, fatal: 60 };

function createLogger(options = {}) {
  const {
    level = 'info',
    name = 'app',
    serializers = {},
    context = {}
  } = options;

  const minLevel = levels[level] ?? levels.info;

  function log(levelName, message, extra = {}) {
    if (levels[levelName] < minLevel) return;

    const entry = {
      time: Date.now(),
      level: levels[levelName],
      levelName,
      name,
      msg: message,
      ...context,
      ...extra,
      pid: process.pid,
      hostname: require('node:os').hostname()
    };

    // Apply serializers
    for (const [key, serializer] of Object.entries(serializers)) {
      if (entry[key] !== undefined) entry[key] = serializer(entry[key]);
    }

    process.stdout.write(JSON.stringify(entry) + '\n');
  }

  const logger = {
    child(bindings) {
      return createLogger({ ...options, context: { ...context, ...bindings } });
    }
  };

  for (const levelName of Object.keys(levels)) {
    logger[levelName] = (msg, extra) => log(levelName, msg, extra);
  }

  return logger;
}

const logger = createLogger({ level: 'info', name: 'api-gateway' });
const reqLogger = logger.child({ requestId: 'req-123', userId: 'user-456' });

reqLogger.info('Request received', { method: 'GET', path: '/users' });
reqLogger.error('Database error', { error: 'Connection timeout', retrying: true });
```

---

## Step 5: Health Checks

```javascript
// Health check endpoint
class HealthChecker {
  #checks = new Map();

  register(name, checkFn, options = {}) {
    this.#checks.set(name, { checkFn, critical: options.critical ?? true });
    return this;
  }

  async check() {
    const results = {};
    let healthy = true;

    await Promise.allSettled(
      [...this.#checks.entries()].map(async ([name, { checkFn, critical }]) => {
        const start = Date.now();
        try {
          const result = await Promise.race([
            checkFn(),
            new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout')), 5000))
          ]);
          results[name] = { status: 'healthy', latencyMs: Date.now() - start, ...result };
        } catch (err) {
          results[name] = { status: 'unhealthy', error: err.message, latencyMs: Date.now() - start };
          if (critical) healthy = false;
        }
      })
    );

    return {
      status: healthy ? 'healthy' : 'unhealthy',
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
      checks: results
    };
  }
}

const health = new HealthChecker()
  .register('database', async () => {
    // Simulate DB ping
    await new Promise(r => setTimeout(r, 5));
    return { connections: 5 };
  })
  .register('memory', () => {
    const { heapUsed, heapTotal } = process.memoryUsage();
    return { heapUsed, heapTotal, percent: (heapUsed / heapTotal * 100).toFixed(1) };
  });

health.check().then(result => console.log(JSON.stringify(result, null, 2)));
```

---

## Step 6: Graceful Shutdown

```javascript
class GracefulShutdown {
  #isShuttingDown = false;
  #handlers = [];
  #server;

  constructor(server) {
    this.#server = server;
    this.#setupSignals();
  }

  #setupSignals() {
    ['SIGTERM', 'SIGINT', 'SIGUSR2'].forEach(signal => {
      process.once(signal, async () => {
        await this.shutdown(signal);
      });
    });

    process.on('uncaughtException', async (err) => {
      console.error('Uncaught exception:', err);
      await this.shutdown('uncaughtException');
    });
  }

  addCleanup(name, fn) {
    this.#handlers.push({ name, fn });
    return this;
  }

  async shutdown(signal) {
    if (this.#isShuttingDown) return;
    this.#isShuttingDown = true;
    console.log(`\nShutdown signal: ${signal}`);

    // Stop accepting new connections
    await new Promise((resolve, reject) => {
      this.#server.close(err => err ? reject(err) : resolve());
    });

    // Run cleanup handlers in reverse order
    for (const { name, fn } of this.#handlers.reverse()) {
      try {
        await fn();
        console.log(`  ✓ ${name} closed`);
      } catch (e) {
        console.error(`  ✗ ${name} failed: ${e.message}`);
      }
    }

    process.exit(0);
  }
}
```

---

## Step 7: Service Discovery (Simple)

```javascript
// Simple in-process service registry
class ServiceRegistry {
  #services = new Map();

  register(name, instance) {
    if (!this.#services.has(name)) this.#services.set(name, []);
    const service = {
      id: Math.random().toString(36).slice(2),
      name,
      instance,
      registeredAt: Date.now(),
      healthy: true
    };
    this.#services.get(name).push(service);
    console.log(`Registered service: ${name}#${service.id}`);
    return service.id;
  }

  discover(name) {
    const instances = this.#services.get(name)?.filter(s => s.healthy) ?? [];
    if (!instances.length) throw new Error(`No healthy instances of '${name}'`);
    // Round-robin load balancing
    const idx = (this._counters = this._counters ?? {});
    idx[name] = ((idx[name] ?? -1) + 1) % instances.length;
    return instances[idx[name]].instance;
  }

  deregister(name, id) {
    const instances = this.#services.get(name);
    const idx = instances?.findIndex(s => s.id === id);
    if (idx >= 0) instances.splice(idx, 1);
  }
}
```

---

## Step 8: Capstone — Circuit Breaker State Machine

```javascript
let callCount = 0;
const unstableService = async () => {
  callCount++;
  if (callCount <= 3) throw new Error('Service down');
  return 'Success';
};

const cb = new CircuitBreaker(unstableService, { threshold: 3 });

(async () => {
  for (let i = 0; i < 5; i++) {
    try {
      const r = await cb.call();
      console.log(`Call ${i+1}:`, r, 'State:', cb.state);
    } catch (e) {
      console.log(`Call ${i+1}:`, e.message, 'State:', cb.state);
    }
  }
})();
```

**Run verification:**
```bash
docker run --rm node:20-alpine sh -c "node -e '
class CircuitBreaker {
  constructor(fn, { threshold = 3, timeout = 5000, resetTimeout = 10000 } = {}) {
    this.fn = fn; this.threshold = threshold; this.timeout = timeout;
    this.resetTimeout = resetTimeout; this.failures = 0;
    this.state = \"CLOSED\"; this.nextAttempt = Date.now();
  }
  async call(...args) {
    if (this.state === \"OPEN\") {
      if (Date.now() < this.nextAttempt) throw new Error(\"Circuit OPEN\");
      this.state = \"HALF_OPEN\";
    }
    try { const result = await this.fn(...args); this.onSuccess(); return result; }
    catch (e) { this.onFailure(); throw e; }
  }
  onSuccess() { this.failures = 0; this.state = \"CLOSED\"; }
  onFailure() {
    this.failures++;
    if (this.failures >= this.threshold) { this.state = \"OPEN\"; this.nextAttempt = Date.now() + this.resetTimeout; }
  }
}
let callCount = 0;
const unstableService = async () => {
  callCount++;
  if (callCount <= 3) throw new Error(\"Service down\");
  return \"Success\";
};
const cb = new CircuitBreaker(unstableService, { threshold: 3 });
(async () => {
  for (let i = 0; i < 5; i++) {
    try { const r = await cb.call(); console.log(\"Call\", i+1, \":\", r, \"State:\", cb.state); }
    catch (e) { console.log(\"Call\", i+1, \":\", e.message, \"State:\", cb.state); }
  }
})();
'"
```

📸 **Verified Output:**
```
Call 1 : Service down State: CLOSED
Call 2 : Service down State: CLOSED
Call 3 : Service down State: OPEN
Call 4 : Circuit OPEN State: OPEN
Call 5 : Circuit OPEN State: OPEN
```

---

## Summary

| Pattern | Problem Solved | Implementation |
|---------|---------------|----------------|
| Circuit Breaker | Prevent cascading failures | State machine: CLOSED/OPEN/HALF_OPEN |
| Bulkhead | Isolate resources | Semaphore + queue |
| Retry + Backoff | Transient failures | Exponential backoff + jitter |
| Structured logging | Observability | JSON log lines |
| Health check | Service monitoring | `/health` endpoint |
| Graceful shutdown | Clean termination | SIGTERM handler + cleanup |
| Service registry | Service discovery | Register/discover pattern |
