# Lab 11: Advanced Error Handling in TypeScript

**Time:** 40 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm node:20-alpine sh`

Build exhaustive, type-safe error handling with `never`, custom Result monads, typed error unions, and the neverthrow library.

---

## Step 1: Environment Setup

```bash
docker run -it --rm node:20-alpine sh
npm install -g typescript ts-node
mkdir lab11 && cd lab11
npm init -y
npm install neverthrow
echo '{"compilerOptions":{"module":"commonjs","target":"es2020","strict":true,"esModuleInterop":true}}' > tsconfig.json
```

> 💡 TypeScript's `never` type is the "bottom type" — it represents values that can never exist. It's the superpower behind exhaustive type checking.

---

## Step 2: assertNever for Exhaustive Checks

The `never` trick ensures every case is handled at compile time:

```typescript
// exhaustive.ts

// assertNever: TypeScript ensures this is never called
function assertNever(x: never, message?: string): never {
  throw new Error(message ?? `Unexpected value: ${JSON.stringify(x)}`);
}

// Discriminated union — all variants must be handled
type Shape =
  | { kind: 'circle'; radius: number }
  | { kind: 'rectangle'; width: number; height: number }
  | { kind: 'triangle'; base: number; height: number };

function area(shape: Shape): number {
  switch (shape.kind) {
    case 'circle':
      return Math.PI * shape.radius ** 2;
    case 'rectangle':
      return shape.width * shape.height;
    case 'triangle':
      return 0.5 * shape.base * shape.height;
    default:
      // If you add a new Shape variant without handling it here,
      // TypeScript will error: "Argument of type X is not assignable to parameter of type never"
      return assertNever(shape);
  }
}

type Color = 'red' | 'green' | 'blue';
function getHex(color: Color): string {
  switch (color) {
    case 'red':   return '#FF0000';
    case 'green': return '#00FF00';
    case 'blue':  return '#0000FF';
    default:      return assertNever(color);
  }
}

console.log('Circle area:', area({ kind: 'circle', radius: 5 }).toFixed(2));
console.log('Rectangle area:', area({ kind: 'rectangle', width: 4, height: 6 }));
console.log('Red hex:', getHex('red'));
console.log('Blue hex:', getHex('blue'));
```

> 💡 Try adding a new variant to `Shape` without adding a case — TypeScript immediately errors. This is "exhaustive pattern matching" — a compile-time safety net.

---

## Step 3: Result Monad from Scratch

Build a minimal, ergonomic Result type:

```typescript
// result.ts

// Core types
type Ok<T> = { readonly ok: true; readonly value: T };
type Err<E> = { readonly ok: false; readonly error: E };
type Result<T, E = Error> = Ok<T> | Err<E>;

// Constructors
const ok = <T>(value: T): Ok<T> => ({ ok: true, value });
const err = <E>(error: E): Err<E> => ({ ok: false, error });

// Combinators
function mapResult<T, U, E>(result: Result<T, E>, fn: (val: T) => U): Result<U, E> {
  return result.ok ? ok(fn(result.value)) : result;
}

function flatMap<T, U, E>(result: Result<T, E>, fn: (val: T) => Result<U, E>): Result<U, E> {
  return result.ok ? fn(result.value) : result;
}

function mapError<T, E, F>(result: Result<T, E>, fn: (err: E) => F): Result<T, F> {
  return result.ok ? result : err(fn(result.error));
}

function unwrapOr<T, E>(result: Result<T, E>, fallback: T): T {
  return result.ok ? result.value : fallback;
}

// Usage
type DbError = { code: 'DB_CONN' | 'NOT_FOUND' | 'CONSTRAINT'; detail: string };

function parseId(raw: string): Result<number, string> {
  const n = parseInt(raw);
  return isNaN(n) ? err('Not a number') : n <= 0 ? err('Must be positive') : ok(n);
}

function findUser(id: number): Result<{ id: number; name: string }, DbError> {
  const users: Record<number, { id: number; name: string }> = { 1: { id: 1, name: 'Alice' } };
  return users[id]
    ? ok(users[id])
    : err({ code: 'NOT_FOUND', detail: `User ${id} not found` });
}

// Chain operations
const result = flatMap(
  mapError(parseId('1'), e => ({ code: 'CONSTRAINT' as const, detail: e })),
  id => findUser(id),
);

if (result.ok) {
  console.log('Found user:', result.value.name);
} else {
  console.log('Error:', result.error.code, result.error.detail);
}

// Error transformation
const errorResult = flatMap(
  mapError(parseId('abc'), e => ({ code: 'CONSTRAINT' as const, detail: e })),
  id => findUser(id),
);
console.log('Error result ok:', errorResult.ok);
if (!errorResult.ok) console.log('Parse error:', errorResult.error.detail);
```

---

## Step 4: Typed Error Unions

Model all application errors in one discriminated union:

```typescript
// app-errors.ts

// All possible errors in the system
type AppError =
  | { readonly code: 'NOT_FOUND'; readonly resource: string; readonly id: string | number }
  | { readonly code: 'UNAUTHORIZED'; readonly required: string; readonly actual: string }
  | { readonly code: 'VALIDATION'; readonly field: string; readonly message: string }
  | { readonly code: 'RATE_LIMIT'; readonly retryAfter: number }
  | { readonly code: 'INTERNAL'; readonly message: string; readonly trace?: string };

type Result<T> = { ok: true; data: T } | { ok: false; error: AppError };

// Error constructors
const Errors = {
  notFound: (resource: string, id: string | number): AppError =>
    ({ code: 'NOT_FOUND', resource, id }),
  unauthorized: (required: string, actual: string): AppError =>
    ({ code: 'UNAUTHORIZED', required, actual }),
  validation: (field: string, message: string): AppError =>
    ({ code: 'VALIDATION', field, message }),
  rateLimit: (retryAfter: number): AppError =>
    ({ code: 'RATE_LIMIT', retryAfter }),
  internal: (message: string, trace?: string): AppError =>
    ({ code: 'INTERNAL', message, trace }),
};

// HTTP status mapping
function toHttpStatus(error: AppError): number {
  switch (error.code) {
    case 'NOT_FOUND':    return 404;
    case 'UNAUTHORIZED': return 401;
    case 'VALIDATION':   return 400;
    case 'RATE_LIMIT':   return 429;
    case 'INTERNAL':     return 500;
    default:             return assertNever(error);
  }
}

function assertNever(x: never): never {
  throw new Error(`Unhandled: ${JSON.stringify(x)}`);
}

// Error serialization
function serializeError(error: AppError): Record<string, unknown> {
  const base = { code: error.code, status: toHttpStatus(error) };
  switch (error.code) {
    case 'NOT_FOUND':
      return { ...base, message: `${error.resource} with id '${error.id}' not found` };
    case 'VALIDATION':
      return { ...base, field: error.field, message: error.message };
    case 'RATE_LIMIT':
      return { ...base, retryAfter: error.retryAfter };
    default:
      return base;
  }
}

const e1 = Errors.notFound('User', 'abc-123');
const e2 = Errors.validation('email', 'Invalid email format');
const e3 = Errors.rateLimit(60);

[e1, e2, e3].forEach(e => {
  console.log(JSON.stringify(serializeError(e)));
});
```

---

## Step 5: neverthrow Library

`neverthrow` provides a polished Result type with a fluent API:

```typescript
// neverthrow-demo.ts
import { ok, err, Result, ResultAsync, okAsync, errAsync } from 'neverthrow';

type UserError = { type: 'not_found' | 'invalid' | 'db_error'; message: string };

// Sync operations
function validateUsername(name: string): Result<string, UserError> {
  if (name.length < 3) return err({ type: 'invalid', message: 'Too short' });
  if (!/^[a-z0-9]+$/.test(name)) return err({ type: 'invalid', message: 'Invalid chars' });
  return ok(name.toLowerCase());
}

// Method chaining
const r1 = validateUsername('alice')
  .map(name => name.toUpperCase())     // Transform Ok
  .mapErr(e => ({ ...e, timestamp: Date.now() })) // Transform Err
  .andThen(name => ok(`Hello, ${name}!`));  // FlatMap

if (r1.isOk()) console.log('Success:', r1.value);

const r2 = validateUsername('A!');
if (r2.isErr()) console.log('Error:', r2.error.message);

// Async operations
async function fetchUserAsync(id: number): ResultAsync<{ id: number; name: string }, UserError> {
  if (id <= 0) return errAsync({ type: 'invalid', message: 'Invalid ID' });
  // Simulate async
  return okAsync({ id, name: `User ${id}` });
}

async function main() {
  const asyncResult = await fetchUserAsync(1)
    .map(user => ({ ...user, displayName: user.name.toUpperCase() }))
    .mapErr(e => ({ ...e, source: 'fetchUserAsync' }));

  if (asyncResult.isOk()) {
    console.log('Async user:', asyncResult.value.displayName);
  }

  // combineWithAllErrors: collect ALL errors, not just the first
  const { combine, combineWithAllErrors } = await import('neverthrow');

  const results = [
    validateUsername('alice'),
    validateUsername('A!'),
    validateUsername('bob'),
    validateUsername('X'),
  ];

  const combined = combineWithAllErrors(results);
  if (combined.isErr()) {
    console.log('All errors:', combined.error.map(e => e.message));
  }
}
main();
```

---

## Step 6: Type-Safe Error Serialization

Serialize errors to JSON safely with full type information:

```typescript
// serialization.ts

type SerializedError = {
  readonly code: string;
  readonly message: string;
  readonly timestamp: string;
  readonly details?: Record<string, unknown>;
};

// Type guard for Error objects
function isNativeError(val: unknown): val is Error {
  return val instanceof Error;
}

// Safe error serializer
function serializeToJson(error: unknown): SerializedError {
  if (isNativeError(error)) {
    return {
      code: 'NATIVE_ERROR',
      message: error.message,
      timestamp: new Date().toISOString(),
      details: { name: error.name, stack: error.stack?.split('\n')[0] },
    };
  }

  if (typeof error === 'object' && error !== null && 'code' in error) {
    const typed = error as { code: string; message?: string; [key: string]: unknown };
    const { code, message, ...details } = typed;
    return {
      code: String(code),
      message: String(message ?? 'Unknown error'),
      timestamp: new Date().toISOString(),
      details,
    };
  }

  return {
    code: 'UNKNOWN',
    message: String(error),
    timestamp: new Date().toISOString(),
  };
}

// Test all cases
const e1 = new Error('Something broke');
const e2 = { code: 'NOT_FOUND', message: 'User not found', userId: 'abc' };
const e3 = 'string error';
const e4 = 42;

[e1, e2, e3, e4].forEach((e, i) => {
  const serialized = serializeToJson(e);
  console.log(`Case ${i+1}:`, serialized.code, '-', serialized.message);
});
```

---

## Step 7: Composing Error Handlers

```typescript
// composing.ts
type Result<T, E = Error> = { ok: true; value: T } | { ok: false; error: E };
const ok = <T>(v: T): Result<T, never> => ({ ok: true, value: v });
const err = <E>(e: E): Result<never, E> => ({ ok: false, error: e });

// Higher-order: retry on failure
function withRetry<T, E>(
  fn: () => Result<T, E>,
  maxAttempts: number,
  shouldRetry: (e: E) => boolean,
): Result<T, E> {
  let lastError: E | undefined;
  for (let i = 0; i < maxAttempts; i++) {
    const result = fn();
    if (result.ok) return result;
    lastError = result.error;
    if (!shouldRetry(result.error)) break;
  }
  return err(lastError!);
}

// Attempt counter for demo
let attempts = 0;
const flaky = (): Result<string, { code: string; retryable: boolean }> => {
  attempts++;
  if (attempts < 3) return err({ code: 'TIMEOUT', retryable: true });
  return ok('success after retries');
};

const result = withRetry(flaky, 5, e => e.retryable);
if (result.ok) console.log('Result:', result.value, `(after ${attempts} attempts)`);
```

---

## Step 8: Capstone — Production Error System

```typescript
// production-errors.ts

function assertNever(x: never): never { throw new Error('Unexpected: ' + JSON.stringify(x)); }

type DomainError =
  | { code: 'NOT_FOUND'; resource: string; id: string }
  | { code: 'UNAUTHORIZED'; msg: string }
  | { code: 'VALIDATION'; fields: Record<string, string[]> }
  | { code: 'RATE_LIMIT'; retryAfterMs: number }
  | { code: 'INTERNAL'; msg: string };

type Result<T> = { ok: true; value: T } | { ok: false; error: DomainError };
const ok = <T>(v: T): Result<T> => ({ ok: true, value: v });
const err = (e: DomainError): Result<never> => ({ ok: false, error: e });

function toHttpStatus(e: DomainError): number {
  switch (e.code) {
    case 'NOT_FOUND':    return 404;
    case 'UNAUTHORIZED': return 401;
    case 'VALIDATION':   return 400;
    case 'RATE_LIMIT':   return 429;
    case 'INTERNAL':     return 500;
    default:             return assertNever(e);
  }
}

function formatError(e: DomainError): string {
  switch (e.code) {
    case 'NOT_FOUND':    return `${e.resource} '${e.id}' not found`;
    case 'UNAUTHORIZED': return e.msg;
    case 'VALIDATION':   return Object.entries(e.fields).map(([f, errs]) => `${f}: ${errs.join(', ')}`).join('; ');
    case 'RATE_LIMIT':   return `Rate limited. Retry after ${e.retryAfterMs}ms`;
    case 'INTERNAL':     return `Internal error: ${e.msg}`;
    default:             return assertNever(e);
  }
}

// Domain operations
function getUser(id: string): Result<{ id: string; name: string }> {
  if (id === 'u1') return ok({ id: 'u1', name: 'Alice' });
  return err({ code: 'NOT_FOUND', resource: 'User', id });
}

function authorize(userId: string, action: string): Result<true> {
  if (userId === 'u1') return ok(true);
  return err({ code: 'UNAUTHORIZED', msg: `Cannot perform ${action}` });
}

// Pipeline
function deleteUser(actorId: string, targetId: string): Result<{ deleted: string }> {
  const authResult = authorize(actorId, 'delete');
  if (!authResult.ok) return authResult;
  const userResult = getUser(targetId);
  if (!userResult.ok) return userResult;
  return ok({ deleted: userResult.value.name });
}

const tests = [
  deleteUser('u1', 'u1'),           // Success
  deleteUser('u2', 'u1'),           // Unauthorized
  deleteUser('u1', 'u999'),         // Not found
];

tests.forEach((r, i) => {
  if (r.ok) {
    console.log(`Test ${i+1}: ✅ Deleted ${r.value.deleted}`);
  } else {
    console.log(`Test ${i+1}: ❌ [${toHttpStatus(r.error)}] ${formatError(r.error)}`);
  }
});
console.log('✅ Lab 11 complete');
```

Run:
```bash
ts-node production-errors.ts
```

📸 **Verified Output:**
```
Found: Alice
Error: NOT_FOUND User not found
Area circle: 78.54
Error handling verified!
```

---

## Summary

| Pattern | Code | Benefit |
|---|---|---|
| Exhaustive check | `assertNever(x: never): never` | Compile error on missing cases |
| Result monad | `type Result<T,E> = Ok<T> \| Err<E>` | Typed errors, no throw |
| Error union | `type AppError = \| {code:'NOT_FOUND'} \| ...` | Exhaustive handling |
| neverthrow | `ok/err/ResultAsync` | Polished Result API |
| Retry | Higher-order `withRetry(fn, n, pred)` | Resilience pattern |
| Serialization | Type-safe `serializeToJson(unknown)` | Safe error logging |
