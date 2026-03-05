# Lab 07: Error Handling Patterns

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Master error handling: built-in error types, custom errors, try/catch/finally, error chaining with `cause`, Promise rejection handling, `unhandledRejection`, and the Result/Either pattern.

---

## Step 1: Error Types

```javascript
// Built-in Error types
try { null.property; }
catch (e) {
  console.log(e instanceof TypeError);   // true
  console.log(e.name);                   // 'TypeError'
  console.log(e.message);
  console.log(e.stack.split('\n')[0]);   // Error location
}

// RangeError
try { new Array(-1); }
catch (e) { console.log(e instanceof RangeError, e.message); }

// SyntaxError (usually from eval/JSON.parse)
try { JSON.parse('not json'); }
catch (e) { console.log(e instanceof SyntaxError, e.message.slice(0, 30)); }

// URIError
try { decodeURIComponent('%'); }
catch (e) { console.log(e instanceof URIError, e.name); }

// ReferenceError
try { undeclaredVariable; }
catch (e) { console.log(e instanceof ReferenceError); }
```

---

## Step 2: Custom Error Classes

```javascript
// Base custom error
class AppError extends Error {
  constructor(message, options = {}) {
    super(message, options);
    this.name = this.constructor.name;
    this.timestamp = new Date().toISOString();
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, this.constructor);
    }
  }
}

// Domain-specific errors
class ValidationError extends AppError {
  constructor(message, field, value) {
    super(message);
    this.field = field;
    this.value = value;
    this.code = 'VALIDATION_ERROR';
  }
}

class NotFoundError extends AppError {
  constructor(resource, id) {
    super(`${resource} with id '${id}' not found`);
    this.resource = resource;
    this.id = id;
    this.code = 'NOT_FOUND';
    this.statusCode = 404;
  }
}

class NetworkError extends AppError {
  constructor(message, statusCode) {
    super(message);
    this.statusCode = statusCode;
    this.code = 'NETWORK_ERROR';
    this.retryable = statusCode >= 500;
  }
}

// Usage
try {
  throw new ValidationError('Invalid email format', 'email', 'not-an-email');
} catch (e) {
  if (e instanceof ValidationError) {
    console.log(`Validation failed on field '${e.field}': ${e.message}`);
  }
}
```

---

## Step 3: try/catch/finally

```javascript
function parseAndProcess(jsonString) {
  let data;
  try {
    data = JSON.parse(jsonString); // May throw SyntaxError
    if (!data.name) throw new ValidationError('name is required', 'name');
    return { success: true, name: data.name.toUpperCase() };
  } catch (e) {
    if (e instanceof SyntaxError) {
      return { success: false, error: 'Invalid JSON format' };
    }
    if (e instanceof ValidationError) {
      return { success: false, error: e.message, field: e.field };
    }
    throw e; // Re-throw unexpected errors
  } finally {
    // Always runs, even if we return or throw
    console.log('parseAndProcess completed');
  }
}

console.log(parseAndProcess('{"name":"Alice"}'));
console.log(parseAndProcess('not json'));
console.log(parseAndProcess('{"age":30}'));
```

> 💡 `finally` always runs even if you `return` inside `try` or `catch`. The return value from `finally` overrides others.

---

## Step 4: Error Chaining (cause)

```javascript
// Error chaining preserves context
async function fetchUserProfile(userId) {
  try {
    const response = await fetch(`/api/users/${userId}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
  } catch (e) {
    throw new NetworkError(`Failed to fetch user ${userId}`, 503, { cause: e });
  }
}

async function buildDashboard(userId) {
  try {
    const profile = await fetchUserProfile(userId);
    return { profile, loaded: true };
  } catch (e) {
    throw new AppError(`Dashboard failed for user ${userId}`, { cause: e });
  }
}

// Chain inspection
function printErrorChain(err, depth = 0) {
  const indent = '  '.repeat(depth);
  console.log(`${indent}${err.name}: ${err.message}`);
  if (err.cause) printErrorChain(err.cause, depth + 1);
}

// Demonstrate error chain
try {
  const original = new Error('Connection refused');
  const wrapped = new NetworkError('API unavailable', 503, { cause: original });
  const topLevel = new AppError('Operation failed', { cause: wrapped });
  throw topLevel;
} catch (e) {
  printErrorChain(e);
}
```

---

## Step 5: Promise Rejection Handling

```javascript
// Always handle rejections!

// 1. .catch()
fetch('/api/data')
  .then(r => r.json())
  .catch(err => console.error('Fetch failed:', err.message));

// 2. async/await try/catch
async function loadData() {
  try {
    const data = await fetch('/api/data').then(r => r.json());
    return data;
  } catch (err) {
    console.error('Failed:', err.message);
    return null;
  }
}

// 3. Handling in Promise.all
async function loadAll() {
  const [users, posts] = await Promise.all([
    fetch('/api/users').then(r => r.json()).catch(() => []),
    fetch('/api/posts').then(r => r.json()).catch(() => [])
  ]);
  return { users, posts };
}

// 4. Unhandled rejection listener (Node.js)
process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled rejection at:', promise);
  console.error('Reason:', reason);
  process.exit(1); // Recommended in production
});

// This would trigger unhandledRejection:
// Promise.reject(new Error('forgotten rejection'));
```

---

## Step 6: Result / Either Pattern

```javascript
// Result pattern — explicit success/failure without exceptions
class Result {
  static ok(value) { return new OkResult(value); }
  static err(error) { return new ErrResult(error); }
}

class OkResult extends Result {
  constructor(value) { super(); this.value = value; this.ok = true; }
  map(fn) { return Result.ok(fn(this.value)); }
  flatMap(fn) { return fn(this.value); }
  mapErr() { return this; }
  unwrap() { return this.value; }
  unwrapOr() { return this.value; }
  match({ ok }) { return ok(this.value); }
}

class ErrResult extends Result {
  constructor(error) { super(); this.error = error; this.ok = false; }
  map() { return this; }
  flatMap() { return this; }
  mapErr(fn) { return Result.err(fn(this.error)); }
  unwrap() { throw new Error(`Unwrap on Err: ${this.error}`); }
  unwrapOr(defaultValue) { return defaultValue; }
  match({ err }) { return err(this.error); }
}

// Usage — no try/catch needed
function divide(a, b) {
  if (b === 0) return Result.err('Division by zero');
  return Result.ok(a / b);
}

function sqrt(n) {
  if (n < 0) return Result.err('Cannot sqrt negative number');
  return Result.ok(Math.sqrt(n));
}

const result = divide(10, 2)
  .flatMap(n => sqrt(n))
  .map(n => n.toFixed(3));

result.match({
  ok: v => console.log('Result:', v),     // Result: 2.236
  err: e => console.log('Error:', e)
});

// Chain of operations
const pipeline = divide(16, 4)
  .flatMap(n => sqrt(n))
  .map(n => Math.round(n));

console.log(pipeline.unwrapOr(0)); // 2
```

---

## Step 7: Global Error Handling

```javascript
// Comprehensive global error handling for Node.js
process.on('uncaughtException', (err, origin) => {
  console.error('Uncaught exception:');
  console.error('Error:', err.message);
  console.error('Origin:', origin);
  // Log to external service
  // gracefulShutdown(1);
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Promise rejection:');
  console.error('Reason:', reason instanceof Error ? reason.message : reason);
  process.exit(1);
});

// Graceful shutdown
function createGracefulShutdown(cleanup) {
  let isShuttingDown = false;

  async function shutdown(signal) {
    if (isShuttingDown) return;
    isShuttingDown = true;
    console.log(`\nReceived ${signal}. Graceful shutdown...`);
    try {
      await cleanup();
      console.log('Cleanup complete');
      process.exit(0);
    } catch (e) {
      console.error('Cleanup failed:', e.message);
      process.exit(1);
    }
  }

  process.on('SIGTERM', () => shutdown('SIGTERM'));
  process.on('SIGINT', () => shutdown('SIGINT'));
}
```

---

## Step 8: Capstone — Error Chain Demo

```javascript
// Run verification
class ValidationError extends Error {
  constructor(message, field) {
    super(message);
    this.name = 'ValidationError';
    this.field = field;
  }
}
try {
  try { JSON.parse('bad json'); }
  catch (e) { throw new Error('Parse failed', { cause: e }); }
} catch (e) {
  console.log(e.message, '->', e.cause?.message);
}
const Result = {
  ok: (value) => ({ ok: true, value }),
  err: (error) => ({ ok: false, error })
};
function divide(a, b) {
  if (b === 0) return Result.err('Division by zero');
  return Result.ok(a / b);
}
const r1 = divide(10, 2);
const r2 = divide(10, 0);
console.log(r1.ok, r1.value);
console.log(r2.ok, r2.error);
```

**Run verification:**
```bash
docker run --rm node:20-alpine sh -c "node -e '
class ValidationError extends Error {
  constructor(message, field) {
    super(message); this.name = \"ValidationError\"; this.field = field;
  }
}
try {
  try { JSON.parse(\"bad json\"); }
  catch (e) { throw new Error(\"Parse failed\", { cause: e }); }
} catch (e) { console.log(e.message, \"->\", e.cause?.message); }
const Result = { ok: (value) => ({ ok: true, value }), err: (error) => ({ ok: false, error }) };
function divide(a, b) {
  if (b === 0) return Result.err(\"Division by zero\");
  return Result.ok(a / b);
}
const r1 = divide(10, 2); const r2 = divide(10, 0);
console.log(r1.ok, r1.value); console.log(r2.ok, r2.error);
'"
```

📸 **Verified Output:**
```
Parse failed -> Unexpected token 'b', "bad json" is not valid JSON
true 5
false Division by zero
```

---

## Summary

| Pattern | When to Use | Pros |
|---------|-------------|------|
| Custom Error class | Domain-specific errors | Rich metadata, `instanceof` checks |
| Error chaining (`cause`) | Wrapping lower-level errors | Full context preserved |
| try/catch/finally | Synchronous + async/await | Standard, familiar |
| `.catch()` | Promise chains | Inline error handling |
| `Result` pattern | When errors are expected | No exceptions, explicit flow |
| `unhandledRejection` | Global safety net | Catch forgotten rejections |
| `uncaughtException` | Last resort | Prevent silent crashes |
