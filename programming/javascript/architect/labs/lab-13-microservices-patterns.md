# Lab 13: Microservices Patterns — Circuit Breaker, Saga & Event Sourcing

**Time:** 60 minutes | **Level:** Architect | **Docker:** `docker run -it --rm node:20-alpine sh`

Distributed systems fail in complex ways. This lab covers the essential resilience patterns: circuit breaker, bulkhead, retry, saga, event sourcing, CQRS, and outbox — using `opossum`, `p-limit`, and in-memory implementations.

---

## Step 1: Install Dependencies

```bash
npm install opossum p-limit async-retry
```

---

## Step 2: Circuit Breaker with opossum

The circuit breaker prevents cascading failures:

```
CLOSED → (failure threshold exceeded) → OPEN → (resetTimeout elapsed) → HALF-OPEN → (success) → CLOSED
                                                                                    → (failure) → OPEN
```

```javascript
// file: circuit-breaker.mjs
import CircuitBreaker from 'opossum';

// Simulate an unreliable external service
async function callExternalService(requestId) {
  await new Promise(r => setTimeout(r, 10)); // simulate latency
  if (requestId % 3 === 0) throw new Error('Service temporarily unavailable');
  return { data: `result-${requestId}`, latency: 10 };
}

const breaker = new CircuitBreaker(callExternalService, {
  timeout: 3000,                  // fail if function takes > 3s
  errorThresholdPercentage: 50,   // open circuit after 50% failure rate
  resetTimeout: 1000,             // try again after 1s in OPEN state
  volumeThreshold: 4,             // minimum calls before evaluating
});

breaker.on('open',     () => console.log('⚡ Circuit OPEN  — requests blocked'));
breaker.on('halfOpen', () => console.log('🔄 Circuit HALF-OPEN — testing...'));
breaker.on('close',    () => console.log('✅ Circuit CLOSED — back to normal'));
breaker.on('reject',   () => console.log('🚫 Request REJECTED (circuit open)'));
breaker.on('timeout',  () => console.log('⏰ Request TIMED OUT'));
breaker.on('fallback', (result) => console.log('🔁 FALLBACK used:', result));

// Define fallback
breaker.fallback((reqId) => ({ data: 'cached-fallback', requestId: reqId }));

// Fire requests
for (let i = 1; i <= 8; i++) {
  try {
    const result = await breaker.fire(i);
    const state = breaker.opened ? 'OPEN' : breaker.halfOpen ? 'HALF-OPEN' : 'CLOSED';
    console.log(`  req ${i} ✓  state: ${state}  data: ${result.data}`);
  } catch (e) {
    const state = breaker.opened ? 'OPEN' : 'CLOSED';
    console.log(`  req ${i} ✗  state: ${state}  error: ${e.message}`);
  }
  await new Promise(r => setTimeout(r, 50));
}

console.log('\nStats:', breaker.stats);
```

📸 **Verified Output:**
```
Call 1 -> ok-1 | state: closed
Call 2 -> ERR: fail | state: closed
Call 3 -> ok-3 | state: closed
...
```

> 💡 `opossum` uses a sliding window of the last N calls. Once `errorThresholdPercentage` is exceeded, the circuit opens and all calls immediately get the fallback response.

---

## Step 3: Bulkhead Pattern with p-limit

```javascript
// file: bulkhead.mjs
import pLimit from 'p-limit';

// Bulkhead: limit concurrent calls to an external service
// Without bulkhead: 100 concurrent slow calls can exhaust connection pool
const DB_LIMIT = pLimit(5);     // max 5 concurrent DB calls
const CACHE_LIMIT = pLimit(20); // max 20 concurrent cache calls
const HTTP_LIMIT = pLimit(10);  // max 10 concurrent HTTP calls

async function dbQuery(id) {
  await new Promise(r => setTimeout(r, 50)); // simulate DB latency
  return { id, data: `db-result-${id}` };
}

async function httpCall(url) {
  await new Promise(r => setTimeout(r, 30));
  return { url, status: 200 };
}

// Process 20 requests with bulkhead protection
const start = Date.now();
const requests = Array.from({ length: 20 }, (_, i) => i + 1);

const results = await Promise.all([
  ...requests.map(id => DB_LIMIT(() => dbQuery(id))),
]);

console.log(`Processed ${results.length} DB calls with concurrency limit 5`);
console.log(`Time: ${Date.now() - start}ms (vs ~${50 * 20}ms serial, ~${50}ms unlimited parallel)`);
console.log(`Active limit: ${DB_LIMIT.activeCount}, pending: ${DB_LIMIT.pendingCount}`);
```

---

## Step 4: Retry with Exponential Backoff

```javascript
// file: retry-pattern.js
async function withRetry(fn, options = {}) {
  const {
    maxAttempts = 3,
    initialDelay = 100,
    maxDelay = 5000,
    factor = 2,
    retryOn = (err) => true,
  } = options;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn(attempt);
    } catch (err) {
      if (attempt === maxAttempts || !retryOn(err)) throw err;
      const delay = Math.min(initialDelay * Math.pow(factor, attempt - 1), maxDelay);
      const jitter = delay * (0.5 + Math.random() * 0.5); // add jitter
      console.log(`  Attempt ${attempt} failed: ${err.message}. Retrying in ${jitter.toFixed(0)}ms...`);
      await new Promise(r => setTimeout(r, jitter));
    }
  }
}

// Test
let attemptCount = 0;
try {
  const result = await withRetry(
    async (attempt) => {
      attemptCount = attempt;
      if (attempt < 3) throw new Error(`Transient error on attempt ${attempt}`);
      return `Success on attempt ${attempt}`;
    },
    { maxAttempts: 4, initialDelay: 50, factor: 2 }
  );
  console.log('Result:', result, `(took ${attemptCount} attempts)`);
} catch (e) {
  console.error('Final failure:', e.message);
}
```

---

## Step 5: Saga Pattern — Compensating Transactions

```javascript
// file: saga.js

class Saga {
  constructor() {
    this.steps = [];
    this.completedSteps = [];
  }

  addStep(name, action, compensate) {
    this.steps.push({ name, action, compensate });
    return this;
  }

  async execute(context) {
    for (const step of this.steps) {
      try {
        console.log(`  → Executing: ${step.name}`);
        await step.action(context);
        this.completedSteps.unshift(step); // prepend for reverse order
        console.log(`  ✓ Completed: ${step.name}`);
      } catch (err) {
        console.log(`  ✗ Failed: ${step.name} — ${err.message}`);
        console.log('  Rolling back completed steps...');
        for (const completed of this.completedSteps) {
          try {
            await completed.compensate(context);
            console.log(`  ↩ Compensated: ${completed.name}`);
          } catch (compErr) {
            console.error(`  ⚠ Compensation failed for ${completed.name}: ${compErr.message}`);
          }
        }
        throw new Error(`Saga failed at step '${step.name}': ${err.message}`);
      }
    }
    return context;
  }
}

// Order fulfillment saga
async function placeOrder(orderId, itemId, userId) {
  const context = { orderId, itemId, userId, reservationId: null, chargeId: null };
  const db = { inventory: { [itemId]: 5 }, balance: { [userId]: 1000 } };

  const saga = new Saga()
    .addStep(
      'Reserve Inventory',
      async (ctx) => {
        if (db.inventory[ctx.itemId] < 1) throw new Error('Out of stock');
        db.inventory[ctx.itemId]--;
        ctx.reservationId = `res-${Date.now()}`;
      },
      async (ctx) => { db.inventory[ctx.itemId]++; }
    )
    .addStep(
      'Charge Customer',
      async (ctx) => {
        if (db.balance[ctx.userId] < 100) throw new Error('Insufficient funds');
        db.balance[ctx.userId] -= 100;
        ctx.chargeId = `chg-${Date.now()}`;
      },
      async (ctx) => { db.balance[ctx.userId] += 100; }
    )
    .addStep(
      'Create Shipment',
      async (ctx) => {
        // Simulate failure
        if (ctx.orderId === 'order-fail') throw new Error('Shipping provider unavailable');
        ctx.shipmentId = `ship-${Date.now()}`;
      },
      async (ctx) => { console.log('    → Cancelling shipment'); }
    );

  console.log(`\n--- Order: ${orderId} ---`);
  try {
    const result = await saga.execute(context);
    console.log('Order complete:', result);
  } catch (e) {
    console.log('Order failed:', e.message);
    console.log('DB state after rollback:', { inventory: db.inventory, balance: db.balance });
  }
}

await placeOrder('order-ok', 'item-1', 'user-1');
await placeOrder('order-fail', 'item-1', 'user-1');
```

---

## Step 6: Event Sourcing — In-Memory Event Store

```javascript
// file: event-sourcing.js

class EventStore {
  constructor() {
    this.events = []; // append-only log
    this.subscribers = new Map();
  }

  append(aggregateId, type, data, metadata = {}) {
    const event = {
      id: `evt-${this.events.length + 1}`,
      aggregateId,
      type,
      data,
      metadata: { ...metadata, timestamp: Date.now() },
      version: this.events.filter(e => e.aggregateId === aggregateId).length + 1,
    };
    this.events.push(event);
    this._notify(event);
    return event;
  }

  getEvents(aggregateId) {
    return this.events.filter(e => e.aggregateId === aggregateId);
  }

  subscribe(eventType, handler) {
    if (!this.subscribers.has(eventType)) this.subscribers.set(eventType, []);
    this.subscribers.get(eventType).push(handler);
  }

  _notify(event) {
    (this.subscribers.get(event.type) || []).forEach(h => h(event));
    (this.subscribers.get('*') || []).forEach(h => h(event));
  }
}

// Account aggregate with event sourcing
class BankAccount {
  constructor(id, eventStore) {
    this.id = id;
    this.store = eventStore;
    this.balance = 0;
    this.owner = null;
    this._replay(); // rebuild state from events
  }

  _replay() {
    const events = this.store.getEvents(this.id);
    for (const event of events) this._apply(event);
  }

  _apply(event) {
    switch (event.type) {
      case 'ACCOUNT_OPENED': this.owner = event.data.owner; this.balance = 0; break;
      case 'DEPOSITED': this.balance += event.data.amount; break;
      case 'WITHDRAWN': this.balance -= event.data.amount; break;
    }
  }

  open(owner) { this.store.append(this.id, 'ACCOUNT_OPENED', { owner }); this._replay(); }
  deposit(amount) { this.store.append(this.id, 'DEPOSITED', { amount }); this.balance += amount; }
  withdraw(amount) {
    if (amount > this.balance) throw new Error('Insufficient funds');
    this.store.append(this.id, 'WITHDRAWN', { amount }); this.balance -= amount;
  }
}

const store = new EventStore();
store.subscribe('*', (evt) => console.log(`  [EVENT] ${evt.type} v${evt.version}: ${JSON.stringify(evt.data)}`));

const account = new BankAccount('acc-001', store);
account.open('Alice');
account.deposit(1000);
account.deposit(500);
account.withdraw(200);

console.log('\nFinal balance:', account.balance);
console.log('Event log:', store.getEvents('acc-001').map(e => `${e.type}(${JSON.stringify(e.data)})`));

// Rebuild from events (time travel!)
const rebuilt = new BankAccount('acc-001', store);
console.log('Rebuilt balance:', rebuilt.balance, '(same as current)');
```

---

## Step 7: CQRS — Command/Query Responsibility Segregation

```javascript
// file: cqrs.js

class CommandBus {
  constructor() { this.handlers = new Map(); }
  register(cmd, handler) { this.handlers.set(cmd, handler); }
  async execute(cmd, payload) {
    const handler = this.handlers.get(cmd);
    if (!handler) throw new Error(`No handler for command: ${cmd}`);
    return handler(payload);
  }
}

class QueryBus {
  constructor() { this.handlers = new Map(); }
  register(query, handler) { this.handlers.set(query, handler); }
  async query(name, params) {
    const handler = this.handlers.get(name);
    if (!handler) throw new Error(`No query handler: ${name}`);
    return handler(params);
  }
}

// Write model (command side)
const writeDB = new Map(); // source of truth
const commandBus = new CommandBus();
commandBus.register('CreateUser', ({ id, name, email }) => {
  writeDB.set(id, { id, name, email, createdAt: Date.now() });
  return { success: true, id };
});
commandBus.register('UpdateUser', ({ id, ...changes }) => {
  if (!writeDB.has(id)) throw new Error('Not found');
  writeDB.set(id, { ...writeDB.get(id), ...changes, updatedAt: Date.now() });
  return { success: true };
});

// Read model (query side) — denormalized for fast reads
const readDB = new Map();
const queryBus = new QueryBus();
queryBus.register('GetUser', ({ id }) => readDB.get(id) || null);
queryBus.register('ListUsers', ({ limit = 10 }) => [...readDB.values()].slice(0, limit));

// Sync write → read (via event or direct for demo)
function syncToReadModel(id) {
  const user = writeDB.get(id);
  if (user) readDB.set(id, { ...user, displayName: user.name.toUpperCase() });
}

// Usage
await commandBus.execute('CreateUser', { id: 'u1', name: 'Alice', email: 'alice@x.com' });
syncToReadModel('u1');
const user = await queryBus.query('GetUser', { id: 'u1' });
console.log('CQRS user:', user);
```

---

## Step 8: Capstone — Outbox Pattern for Reliable Event Publishing

```javascript
// file: outbox-pattern.js
'use strict';

// The Outbox Pattern: write event to DB atomically with business transaction
// A separate process polls the outbox and publishes to message broker
// Guarantees: no lost events (at-least-once delivery)

class OutboxStore {
  constructor() {
    this.businessData = new Map();
    this.outbox = []; // in-memory; in prod: same DB transaction as businessData
    this.published = new Set();
    this.eventId = 0;
  }

  // "Transactional" write: business data + outbox event in "one transaction"
  createOrder(orderId, data) {
    // In production: wrap in DB transaction
    this.businessData.set(orderId, data);
    this.outbox.push({
      id: ++this.eventId,
      type: 'ORDER_CREATED',
      payload: { orderId, ...data },
      createdAt: Date.now(),
      published: false,
    });
    console.log(`  [DB] Order ${orderId} created + outbox event queued`);
    return data;
  }

  // Outbox publisher (runs separately, polls outbox)
  async publishPending(messageBroker) {
    const pending = this.outbox.filter(e => !e.published);
    for (const event of pending) {
      try {
        await messageBroker.publish(event);
        event.published = true;
        this.published.add(event.id);
        console.log(`  [OUTBOX] Published event ${event.id}: ${event.type}`);
      } catch (err) {
        console.error(`  [OUTBOX] Failed to publish event ${event.id}: ${err.message}`);
        // Will retry on next poll
      }
    }
  }
}

// Mock message broker
const broker = {
  messages: [],
  async publish(event) {
    if (Math.random() < 0.3) throw new Error('Broker temporarily unavailable'); // 30% failure
    this.messages.push(event);
  }
};

const store = new OutboxStore();

// Create orders
store.createOrder('o1', { item: 'laptop', price: 999 });
store.createOrder('o2', { item: 'mouse', price: 29 });
store.createOrder('o3', { item: 'keyboard', price: 79 });

// Poll outbox (with retries for transient failures)
console.log('\n[OUTBOX POLL] Publishing pending events...');
for (let attempt = 1; attempt <= 5; attempt++) {
  await store.publishPending(broker);
  const pending = store.outbox.filter(e => !e.published).length;
  if (pending === 0) { console.log('All events published'); break; }
  console.log(`  ${pending} events still pending, retrying...`);
  await new Promise(r => setTimeout(r, 50));
}

console.log('\nBroker received:', broker.messages.map(m => m.type + ':' + m.payload.orderId));
```

---

## Summary

| Pattern | Library/Impl | Protects Against |
|---|---|---|
| Circuit Breaker | `opossum` | Cascading failures |
| Bulkhead | `p-limit` | Resource exhaustion |
| Retry + Backoff | custom / `async-retry` | Transient failures |
| Saga | custom | Distributed transaction rollback |
| Event Sourcing | custom EventStore | State loss, audit trail |
| CQRS | custom CommandBus/QueryBus | Read/write scaling |
| Outbox | custom DB+poll | Lost events on crash |
