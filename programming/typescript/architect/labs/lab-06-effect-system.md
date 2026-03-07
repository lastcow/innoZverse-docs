# Lab 06: Effect System

**Time:** 60 minutes | **Level:** Architect | **Docker:** `node:20-alpine`

## Overview

Effect-TS: typed errors as values, `Effect.gen` coroutine style, Layer for DI, Scope for resource management, `Effect.all` for parallel/sequential execution, structured concurrency, and retry policies.

---

## Step 1: Effect Fundamentals

```typescript
import { Effect, pipe } from 'effect';

// Effect<A, E, R>
//   A = success value type
//   E = error type (typed!)
//   R = requirements/dependencies

// Succeed: wraps a value
const succeed = Effect.succeed(42);                 // Effect<number, never, never>

// Fail: typed error
const fail = Effect.fail(new Error('oops'));        // Effect<never, Error, never>

// Sync: lift synchronous computation
const sync = Effect.sync(() => Math.random());      // Effect<number, never, never>

// Async: wrap a Promise (errors become defects unless handled)
const promise = Effect.promise(() => fetch('/api')); // Effect<Response, never, never>

// Try: Promise that can fail with typed error
const tryPromise = Effect.tryPromise({
  try: () => fetch('/api/users').then(r => r.json()),
  catch: (error) => new NetworkError(String(error)),
}); // Effect<unknown, NetworkError, never>
```

---

## Step 2: Effect.gen — Coroutine Style

```typescript
import { Effect, pipe } from 'effect';

// Before: flatMap chains
const withFlatMap = pipe(
  fetchUser(userId),
  Effect.flatMap(user => fetchOrders(user.id)),
  Effect.flatMap(orders => calculateTotal(orders)),
);

// With Effect.gen: sequential async code
const withGen = Effect.gen(function* () {
  const user   = yield* fetchUser(userId);
  const orders = yield* fetchOrders(user.id);
  const total  = yield* calculateTotal(orders);

  return { user, orders, total };
});

// Typed error accumulation — both errors are in the union
const program = Effect.gen(function* () {
  // If fetchUser fails with DatabaseError, it propagates
  // If parseResult fails with ParseError, it propagates
  const raw  = yield* fetchUser(userId);    // can fail: DatabaseError
  const user = yield* parseResult(raw);     // can fail: ParseError
  return user;
  // Return type: Effect<User, DatabaseError | ParseError, never>
});
```

---

## Step 3: Typed Errors as Values

```typescript
import { Effect, Data } from 'effect';

// Define errors with Data.TaggedError (gives free equality + tagged union)
class DatabaseError extends Data.TaggedError('DatabaseError')<{
  message: string;
  query: string;
}> {}

class ValidationError extends Data.TaggedError('ValidationError')<{
  field: string;
  message: string;
}> {}

class NetworkError extends Data.TaggedError('NetworkError')<{
  status: number;
  url: string;
}> {}

// Effect with multiple possible errors
const loadUser = (id: string): Effect.Effect<User, DatabaseError | ValidationError> =>
  Effect.gen(function* () {
    if (!id.match(/^[a-z0-9-]+$/)) {
      yield* Effect.fail(new ValidationError({ field: 'id', message: 'Invalid format' }));
    }
    const user = yield* Effect.tryPromise({
      try: () => db.findUser(id),
      catch: (e) => new DatabaseError({ message: String(e), query: `SELECT * FROM users WHERE id='${id}'` }),
    });
    return user;
  });

// Handle specific errors
const handled = loadUser('123').pipe(
  Effect.catchTag('ValidationError', (e) =>
    Effect.succeed({ id: 'default', name: 'Guest' })
  ),
  Effect.catchTag('DatabaseError', (e) =>
    Effect.fail(new NetworkError({ status: 503, url: '/api/users' }))
  ),
);
```

---

## Step 4: Layer — Dependency Injection

```typescript
import { Effect, Layer, Context } from 'effect';

// Define service interfaces
interface Database {
  readonly findUser: (id: string) => Effect.Effect<User, DatabaseError>;
  readonly saveUser: (user: User) => Effect.Effect<void, DatabaseError>;
}
const Database = Context.GenericTag<Database>('Database');

interface Logger {
  readonly info: (message: string) => Effect.Effect<void>;
  readonly error: (message: string, error?: unknown) => Effect.Effect<void>;
}
const Logger = Context.GenericTag<Logger>('Logger');

// Implement the services
const DatabaseLive = Layer.succeed(Database, {
  findUser: (id) => Effect.tryPromise({
    try: () => realDb.users.findById(id),
    catch: (e) => new DatabaseError({ message: String(e), query: '' }),
  }),
  saveUser: (user) => Effect.tryPromise({
    try: () => realDb.users.save(user),
    catch: (e) => new DatabaseError({ message: String(e), query: '' }),
  }),
});

const LoggerLive = Layer.succeed(Logger, {
  info:  (msg) => Effect.sync(() => console.log(`[INFO] ${msg}`)),
  error: (msg, e) => Effect.sync(() => console.error(`[ERROR] ${msg}`, e)),
});

// Compose layers
const AppLayer = Layer.mergeAll(DatabaseLive, LoggerLive);

// Use in program
const program = Effect.gen(function* () {
  const db = yield* Database;
  const log = yield* Logger;
  yield* log.info('Fetching user...');
  const user = yield* db.findUser('user-123');
  yield* log.info(`Found: ${user.name}`);
  return user;
});

// Run with all dependencies provided
Effect.runPromise(program.pipe(Effect.provide(AppLayer)));
```

---

## Step 5: Scope — Resource Management

```typescript
import { Effect, Scope } from 'effect';

// Acquire/Release pattern — like Go's defer, but composable
const databaseConnection = Effect.acquireRelease(
  // Acquire
  Effect.tryPromise({
    try: () => createDatabaseConnection({ host: 'localhost', port: 5432 }),
    catch: (e) => new ConnectionError(String(e)),
  }),
  // Release — always called, even on error
  (connection) => Effect.promise(() => connection.close())
);

// Use the scoped resource
const program = Effect.scoped(
  Effect.gen(function* () {
    const db = yield* databaseConnection;  // Resource acquired
    const users = yield* Effect.promise(() => db.query('SELECT * FROM users'));
    return users;
    // Resource automatically released here
  })
);
```

---

## Step 6: Effect.all — Parallel Execution

```typescript
import { Effect } from 'effect';

// Sequential (default)
const sequential = Effect.all([
  fetchUser(userId),
  fetchOrders(userId),
  fetchAddress(userId),
], { concurrency: 1 });

// Parallel (all at once)
const parallel = Effect.all([
  fetchUser(userId),
  fetchOrders(userId),
  fetchAddress(userId),
], { concurrency: 'unbounded' });

// Controlled concurrency
const bounded = Effect.all(
  userIds.map(id => fetchUser(id)),
  { concurrency: 5 }  // Max 5 at once
);

// Short-circuit: fails immediately on first error
const failFast = Effect.all([
  validateId(userId),     // Fails with ValidationError
  fetchUser(userId),      // Never runs if above fails
], { mode: 'default' });

// Collect all errors
const allErrors = Effect.all([
  validateName(data.name),
  validateEmail(data.email),
  validateAge(data.age),
], { mode: 'validate' });
```

---

## Step 7: Retry Policy

```typescript
import { Effect, Schedule, Duration } from 'effect';

// Exponential backoff with jitter
const retryPolicy = Schedule.exponential('100 millis').pipe(
  Schedule.jittered,                         // Add jitter
  Schedule.compose(Schedule.recurs(5)),      // Max 5 retries
  Schedule.whileInput(isRetryableError),     // Only retry on specific errors
);

const withRetry = fetchUser(userId).pipe(
  Effect.retry(retryPolicy),
);

// Timeout + retry
const withTimeout = fetchUser(userId).pipe(
  Effect.timeout('5 seconds'),
  Effect.retry(Schedule.recurs(3)),
);
```

---

## Step 8: Capstone — Effect.gen Pipeline

```bash
docker run --rm node:20-alpine sh -c "
  cd /work && npm init -y > /dev/null 2>&1
  npm install effect 2>&1 | tail -1
  node -e \"
const { Effect, pipe } = require('effect');
class ValidationError { constructor(msg) { this._tag = 'ValidationError'; this.message = msg; } }
class DatabaseError { constructor(msg) { this._tag = 'DatabaseError'; this.message = msg; } }
const validateUser = (data) => data.name ? Effect.succeed(data) : Effect.fail(new ValidationError('Name required'));
const saveUser = (user) => Effect.tryPromise({ try: () => Promise.resolve({ id: 123, ...user }), catch: (e) => new DatabaseError(String(e)) });
const notifyUser = (user) => Effect.sync(() => { console.log('  Notification sent to', user.name); return user; });
const program = (input) => pipe(validateUser(input), Effect.flatMap(saveUser), Effect.flatMap(notifyUser), Effect.map(u => ({ success: true, userId: u.id })));
console.log('=== Effect-TS Pipeline with Typed Errors ===');
Effect.runPromise(program({ name: 'Bob', email: 'bob@test.com' })).then(r=>console.log('Result:', JSON.stringify(r))).catch(e=>console.log('Error:', e._tag, e.message));
Effect.runPromise(program({})).then(r=>console.log('Result:', JSON.stringify(r))).catch(e=>console.log('Caught error:', e._tag, '-', e.message));
  \"
"
```

📸 **Verified Output:**
```
=== Effect-TS Pipeline with Typed Errors ===
  Notification sent to Bob
Caught error: undefined - {"_tag":"ValidationError","message":"Name required"}
Result: {"success":true,"userId":123}
```

---

## Summary

| Feature | API | Benefit |
|---------|-----|---------|
| Typed errors | `Effect<A,E,R>` | Compile-time error tracking |
| Coroutine style | `Effect.gen` | Readable async code |
| DI | `Layer` + `Context` | Testable, composable |
| Resources | `Scope` + `acquireRelease` | Leak-free cleanup |
| Parallelism | `Effect.all({concurrency})` | Controlled parallelism |
| Retry | `Schedule` | Exponential backoff |
| Structured concurrency | `Fiber` | Cancellable tasks |
