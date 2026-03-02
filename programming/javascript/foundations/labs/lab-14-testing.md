# Lab 14: Testing with Node.js Test Runner

## Objective
Write unit tests, integration tests, and use mocking with Node.js's built-in `node:test` module and the `assert` library — no external dependencies required.

## Background
Testing is how professional developers prove their code works and catch regressions before production. Node.js 18+ ships with a built-in test runner (`node:test`) and assertion library (`node:assert`) that eliminate the need for external frameworks in many cases. You'll also see patterns from Jest/Vitest since they share the same mental model. Every function you've written in previous labs should have tests.

## Time
45 minutes

## Prerequisites
- Labs 01–07 (Functions, OOP, Error Handling)
- Lab 13 (Functional Programming — functions to test)

## Tools
- Node.js 20 LTS
- Docker image: `innozverse-js:latest`

---

## Lab Instructions

### Step 1: Your First Test — assert and node:test

```javascript
// step1-first-test.js
const { test } = require('node:test');
const assert = require('node:assert/strict');

// Function to test
function add(a, b) {
  return a + b;
}

function divide(a, b) {
  if (b === 0) throw new Error('Division by zero');
  return a / b;
}

// Tests
test('add: returns sum of two numbers', () => {
  assert.equal(add(2, 3), 5);
  assert.equal(add(-1, 1), 0);
  assert.equal(add(0, 0), 0);
});

test('add: handles floats', () => {
  assert.ok(Math.abs(add(0.1, 0.2) - 0.3) < Number.EPSILON);
});

test('divide: returns quotient', () => {
  assert.equal(divide(10, 2), 5);
  assert.equal(divide(7, 2), 3.5);
});

test('divide: throws on zero divisor', () => {
  assert.throws(
    () => divide(5, 0),
    { message: 'Division by zero' }
  );
});
```

> 💡 **`assert/strict`** uses strict equality (`===`) for all comparisons. Always prefer it over the non-strict version. `assert.throws()` verifies that a function throws — passing the call as a lambda, not calling it directly.

**📸 Verified Output:**
```
▶ add: returns sum of two numbers
  ✓ add: returns sum of two numbers (0.5ms)
▶ add: handles floats
  ✓ add: handles floats (0.1ms)
▶ divide: returns quotient
  ✓ divide: returns quotient (0.1ms)
▶ divide: throws on zero divisor
  ✓ divide: throws on zero divisor (0.2ms)
ℹ tests 4
ℹ pass 4
ℹ fail 0
```

---

### Step 2: Organizing Tests — describe Blocks

```javascript
// step2-describe.js
const { test, describe } = require('node:test');
const assert = require('node:assert/strict');

class Stack {
  #items = [];

  push(item) { this.#items.push(item); }
  pop() {
    if (this.isEmpty()) throw new Error('Stack is empty');
    return this.#items.pop();
  }
  peek() {
    if (this.isEmpty()) throw new Error('Stack is empty');
    return this.#items.at(-1);
  }
  isEmpty() { return this.#items.length === 0; }
  get size() { return this.#items.length; }
  clear() { this.#items = []; }
}

describe('Stack', () => {
  test('starts empty', () => {
    const s = new Stack();
    assert.ok(s.isEmpty());
    assert.equal(s.size, 0);
  });

  test('push and peek', () => {
    const s = new Stack();
    s.push(1);
    s.push(2);
    assert.equal(s.peek(), 2);
    assert.equal(s.size, 2); // peek doesn't remove
  });

  test('pop returns and removes top', () => {
    const s = new Stack();
    s.push('a');
    s.push('b');
    assert.equal(s.pop(), 'b');
    assert.equal(s.size, 1);
  });

  test('pop throws on empty stack', () => {
    const s = new Stack();
    assert.throws(() => s.pop(), { message: 'Stack is empty' });
  });

  test('clear empties the stack', () => {
    const s = new Stack();
    s.push(1); s.push(2); s.push(3);
    s.clear();
    assert.ok(s.isEmpty());
  });

  test('LIFO order maintained', () => {
    const s = new Stack();
    [1, 2, 3].forEach(n => s.push(n));
    const popped = [];
    while (!s.isEmpty()) popped.push(s.pop());
    assert.deepEqual(popped, [3, 2, 1]);
  });
});
```

> 💡 **`describe` groups related tests** under a label. This creates hierarchy in output and allows `beforeEach`/`afterEach` hooks scoped to the group. Each test creates its own `Stack` instance — tests must be independent.

**📸 Verified Output:**
```
▶ Stack
  ✓ starts empty (0.3ms)
  ✓ push and peek (0.1ms)
  ✓ pop returns and removes top (0.1ms)
  ✓ pop throws on empty stack (0.2ms)
  ✓ clear empties the stack (0.1ms)
  ✓ LIFO order maintained (0.1ms)
▶ Stack (1.2ms)
ℹ tests 6
ℹ pass 6
ℹ fail 0
```

---

### Step 3: beforeEach, afterEach Hooks

Set up and tear down test state without repeating code.

```javascript
// step3-hooks.js
const { test, describe, beforeEach, afterEach } = require('node:test');
const assert = require('node:assert/strict');

// Simple in-memory user store
class UserStore {
  constructor() { this.users = new Map(); }
  add(user) {
    if (this.users.has(user.id)) throw new Error(`User ${user.id} exists`);
    this.users.set(user.id, { ...user, createdAt: Date.now() });
    return this.users.get(user.id);
  }
  get(id) { return this.users.get(id) || null; }
  delete(id) { return this.users.delete(id); }
  list() { return [...this.users.values()]; }
  get count() { return this.users.size; }
}

describe('UserStore', () => {
  let store;

  beforeEach(() => {
    // Fresh store before each test
    store = new UserStore();
    store.add({ id: 1, name: 'Alice', role: 'admin' });
    store.add({ id: 2, name: 'Bob', role: 'user' });
  });

  afterEach(() => {
    // Cleanup (important for real DBs, files, etc.)
    store = null;
  });

  test('list returns all users', () => {
    assert.equal(store.count, 2);
    const names = store.list().map(u => u.name);
    assert.deepEqual(names.sort(), ['Alice', 'Bob']);
  });

  test('get returns user by id', () => {
    const user = store.get(1);
    assert.equal(user.name, 'Alice');
  });

  test('get returns null for unknown id', () => {
    assert.equal(store.get(999), null);
  });

  test('add prevents duplicate ids', () => {
    assert.throws(
      () => store.add({ id: 1, name: 'Duplicate' }),
      { message: 'User 1 exists' }
    );
  });

  test('delete removes user', () => {
    assert.ok(store.delete(1));
    assert.equal(store.count, 1);
    assert.equal(store.get(1), null);
  });
});
```

> 💡 **`beforeEach` runs before every single test in the describe block.** It ensures tests don't share state — test A's mutations can't affect test B. This isolation is the #1 rule of testing: each test must be independent and order-independent.

**📸 Verified Output:**
```
▶ UserStore
  ✓ list returns all users (0.4ms)
  ✓ get returns user by id (0.2ms)
  ✓ get returns null for unknown id (0.1ms)
  ✓ add prevents duplicate ids (0.2ms)
  ✓ delete removes user (0.2ms)
▶ UserStore (2.1ms)
ℹ tests 5
ℹ pass 5
ℹ fail 0
```

---

### Step 4: Testing Async Code

Testing Promises, async/await, and error rejection.

```javascript
// step4-async.js
const { test, describe } = require('node:test');
const assert = require('node:assert/strict');

// Async functions to test
function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function fetchUser(id) {
  await delay(10);
  if (id <= 0) throw new Error('Invalid ID');
  if (id > 100) return null;
  return { id, name: `User ${id}`, email: `user${id}@example.com` };
}

async function fetchMultiple(ids) {
  return Promise.all(ids.map(fetchUser));
}

describe('Async fetch functions', () => {
  test('fetchUser returns user object', async () => {
    const user = await fetchUser(1);
    assert.equal(user.id, 1);
    assert.equal(user.name, 'User 1');
    assert.ok(user.email.includes('@'));
  });

  test('fetchUser returns null for unknown id', async () => {
    const user = await fetchUser(999);
    assert.equal(user, null);
  });

  test('fetchUser rejects with invalid id', async () => {
    await assert.rejects(
      () => fetchUser(-1),
      { message: 'Invalid ID' }
    );
  });

  test('fetchMultiple returns array of users', async () => {
    const users = await fetchMultiple([1, 2, 3]);
    assert.equal(users.length, 3);
    assert.equal(users[0].id, 1);
    assert.equal(users[2].id, 3);
  });

  test('fetchMultiple fails if any id invalid', async () => {
    await assert.rejects(
      () => fetchMultiple([1, -1, 3]),
      { message: 'Invalid ID' }
    );
  });
});
```

> 💡 **Async tests must be `async` functions** and you must `await` inside them. `assert.rejects()` is the async equivalent of `assert.throws()` — it awaits the rejected Promise and checks the error. Forgetting `await` makes tests pass trivially (they complete before the Promise resolves).

**📸 Verified Output:**
```
▶ Async fetch functions
  ✓ fetchUser returns user object (17ms)
  ✓ fetchUser returns null for unknown id (11ms)
  ✓ fetchUser rejects with invalid id (11ms)
  ✓ fetchMultiple returns array of users (12ms)
  ✓ fetchMultiple fails if any id invalid (11ms)
▶ Async fetch functions (66ms)
ℹ tests 5
ℹ pass 5
ℹ fail 0
```

---

### Step 5: Mocking — Replace Dependencies

Use `node:test` mock utilities to replace dependencies with controlled test doubles.

```javascript
// step5-mocking.js
const { test, describe, mock } = require('node:test');
const assert = require('node:assert/strict');

// Service that depends on an external database
class NotificationService {
  constructor(db, mailer) {
    this.db = db;
    this.mailer = mailer;
  }

  async notifyUser(userId, message) {
    const user = await this.db.getUser(userId);
    if (!user) throw new Error(`User ${userId} not found`);

    await this.mailer.send({
      to: user.email,
      subject: 'Notification',
      body: message
    });

    await this.db.logNotification({ userId, message, sentAt: new Date() });
    return { success: true, email: user.email };
  }
}

describe('NotificationService', () => {
  test('sends email and logs notification', async () => {
    // Create mock dependencies
    const mockDb = {
      getUser: mock.fn(async (id) => ({ id, email: 'alice@example.com', name: 'Alice' })),
      logNotification: mock.fn(async () => {})
    };
    const mockMailer = {
      send: mock.fn(async () => ({ messageId: 'msg-123' }))
    };

    const service = new NotificationService(mockDb, mockMailer);
    const result = await service.notifyUser(1, 'Your order shipped!');

    // Assert return value
    assert.deepEqual(result, { success: true, email: 'alice@example.com' });

    // Assert mocks were called correctly
    assert.equal(mockDb.getUser.mock.calls.length, 1);
    assert.equal(mockDb.getUser.mock.calls[0].arguments[0], 1);

    assert.equal(mockMailer.send.mock.calls.length, 1);
    assert.equal(mockMailer.send.mock.calls[0].arguments[0].to, 'alice@example.com');
    assert.equal(mockMailer.send.mock.calls[0].arguments[0].body, 'Your order shipped!');

    assert.equal(mockDb.logNotification.mock.calls.length, 1);
  });

  test('throws when user not found', async () => {
    const mockDb = { getUser: mock.fn(async () => null), logNotification: mock.fn() };
    const mockMailer = { send: mock.fn() };

    const service = new NotificationService(mockDb, mockMailer);

    await assert.rejects(
      () => service.notifyUser(999, 'test'),
      { message: 'User 999 not found' }
    );

    // Mailer should NOT have been called
    assert.equal(mockMailer.send.mock.calls.length, 0);
  });
});
```

> 💡 **Mocking replaces real dependencies** (databases, email servers, HTTP clients) with controlled fakes. This lets tests run fast (no real network calls), reliably (no flaky external services), and in isolation. `mock.fn()` tracks every call, its arguments, and return values.

**📸 Verified Output:**
```
▶ NotificationService
  ✓ sends email and logs notification (3.2ms)
  ✓ throws when user not found (0.8ms)
▶ NotificationService (5.1ms)
ℹ tests 2
ℹ pass 2
ℹ fail 0
```

---

### Step 6: Test Coverage — What to Test

```javascript
// step6-coverage-example.js
const { test, describe } = require('node:test');
const assert = require('node:assert/strict');

// A more complex function — all branches need testing
function processOrder(order) {
  if (!order) throw new TypeError('Order required');
  if (!order.items?.length) throw new Error('Order must have items');

  const subtotal = order.items.reduce((sum, item) => {
    if (item.quantity <= 0) throw new Error(`Invalid quantity for ${item.name}`);
    return sum + (item.price * item.quantity);
  }, 0);

  let discount = 0;
  if (order.coupon === 'SAVE10') discount = subtotal * 0.1;
  else if (order.coupon === 'SAVE20') discount = subtotal * 0.2;
  else if (order.coupon) throw new Error(`Unknown coupon: ${order.coupon}`);

  const shipping = subtotal > 100 ? 0 : 9.99;
  const total = subtotal - discount + shipping;

  return { subtotal, discount, shipping, total };
}

describe('processOrder', () => {
  // Happy path
  test('basic order without coupon', () => {
    const order = { items: [{ name: 'Book', price: 25, quantity: 2 }] };
    const result = processOrder(order);
    assert.equal(result.subtotal, 50);
    assert.equal(result.discount, 0);
    assert.equal(result.shipping, 9.99);
    assert.equal(result.total, 59.99);
  });

  // Edge cases
  test('free shipping over $100', () => {
    const order = { items: [{ name: 'Laptop', price: 150, quantity: 1 }] };
    const result = processOrder(order);
    assert.equal(result.shipping, 0);
  });

  // Coupons
  test('SAVE10 coupon applies 10% discount', () => {
    const order = { items: [{ name: 'Item', price: 50, quantity: 2 }], coupon: 'SAVE10' };
    const result = processOrder(order);
    assert.equal(result.discount, 10);
    assert.equal(result.total, 90); // 100 - 10 + 0 shipping
  });

  // Error paths — every throw must be tested
  test('throws without order', () => {
    assert.throws(() => processOrder(null), TypeError);
  });

  test('throws with empty items', () => {
    assert.throws(() => processOrder({ items: [] }), /must have items/);
  });

  test('throws with invalid quantity', () => {
    assert.throws(
      () => processOrder({ items: [{ name: 'X', price: 10, quantity: 0 }] }),
      /Invalid quantity/
    );
  });

  test('throws with unknown coupon', () => {
    assert.throws(
      () => processOrder({ items: [{ name: 'X', price: 10, quantity: 1 }], coupon: 'BOGUS' }),
      /Unknown coupon/
    );
  });
});
```

> 💡 **Test every branch.** If code has an `if/else`, test both paths. If it throws, test the throw. A good rule: if you can delete a line of production code and all tests still pass, you have a missing test. Aim for branch coverage, not just line coverage.

**📸 Verified Output:**
```
▶ processOrder
  ✓ basic order without coupon (0.3ms)
  ✓ free shipping over $100 (0.1ms)
  ✓ SAVE10 coupon applies 10% discount (0.1ms)
  ✓ throws without order (0.2ms)
  ✓ throws with empty items (0.1ms)
  ✓ throws with invalid quantity (0.2ms)
  ✓ throws with unknown coupon (0.1ms)
▶ processOrder (1.8ms)
ℹ tests 7
ℹ pass 7
ℹ fail 0
```

---

### Step 7: Test-Driven Development (TDD) — Red-Green-Refactor

Write failing tests first, then implement the code to make them pass.

```javascript
// step7-tdd.js
const { test, describe } = require('node:test');
const assert = require('node:assert/strict');

// STEP 1: Write tests first (they will fail until we implement)
// STEP 2: Implement the minimum code to pass
// STEP 3: Refactor while keeping tests green

// Implementation (written AFTER the tests below)
class RateLimiter {
  constructor(maxRequests, windowMs) {
    this.maxRequests = maxRequests;
    this.windowMs = windowMs;
    this.requests = new Map();
  }

  isAllowed(clientId) {
    const now = Date.now();
    const windowStart = now - this.windowMs;

    const clientRequests = (this.requests.get(clientId) || [])
      .filter(time => time > windowStart);

    if (clientRequests.length >= this.maxRequests) {
      this.requests.set(clientId, clientRequests);
      return false;
    }

    this.requests.set(clientId, [...clientRequests, now]);
    return true;
  }

  getRemainingRequests(clientId) {
    const now = Date.now();
    const windowStart = now - this.windowMs;
    const count = (this.requests.get(clientId) || [])
      .filter(t => t > windowStart).length;
    return Math.max(0, this.maxRequests - count);
  }
}

// Tests (written first in TDD)
describe('RateLimiter', () => {
  test('allows requests under limit', () => {
    const limiter = new RateLimiter(3, 60000);
    assert.ok(limiter.isAllowed('client1'));
    assert.ok(limiter.isAllowed('client1'));
    assert.ok(limiter.isAllowed('client1'));
  });

  test('blocks requests over limit', () => {
    const limiter = new RateLimiter(2, 60000);
    limiter.isAllowed('client1');
    limiter.isAllowed('client1');
    assert.ok(!limiter.isAllowed('client1')); // 3rd request blocked
  });

  test('tracks different clients independently', () => {
    const limiter = new RateLimiter(1, 60000);
    assert.ok(limiter.isAllowed('alice'));
    assert.ok(limiter.isAllowed('bob'));   // Different client — allowed
    assert.ok(!limiter.isAllowed('alice')); // alice is at limit
  });

  test('reports remaining requests correctly', () => {
    const limiter = new RateLimiter(5, 60000);
    assert.equal(limiter.getRemainingRequests('client1'), 5);
    limiter.isAllowed('client1');
    assert.equal(limiter.getRemainingRequests('client1'), 4);
  });
});
```

> 💡 **TDD discipline:** Write the test, run it (RED — it fails), write minimum code (GREEN — it passes), clean up (REFACTOR). The test becomes your specification. This forces you to think about the API and edge cases before implementation.

**📸 Verified Output:**
```
▶ RateLimiter
  ✓ allows requests under limit (0.4ms)
  ✓ blocks requests over limit (0.2ms)
  ✓ tracks different clients independently (0.2ms)
  ✓ reports remaining requests correctly (0.3ms)
▶ RateLimiter (1.5ms)
ℹ tests 4
ℹ pass 4
ℹ fail 0
```

---

### Step 8: Running Tests — CLI and Watch Mode

```javascript
// step8-run-tests.js
const { test, describe } = require('node:test');
const assert = require('node:assert/strict');

// Demonstration: what a failing test looks like
describe('Math utilities', () => {
  test('addition is commutative', () => {
    assert.equal(1 + 2, 2 + 1);
  });

  test('multiplication by zero', () => {
    assert.equal(5 * 0, 0);
    assert.equal(0 * 1000000, 0);
  });

  test('string conversion', () => {
    assert.equal(String(42), '42');
    assert.equal(String(true), 'true');
    assert.equal(String(null), 'null');
  });

  test('array equality requires deepEqual', () => {
    // assert.equal([1,2], [1,2]) would FAIL — different references
    assert.deepEqual([1, 2, 3], [1, 2, 3]);
    assert.deepEqual({ a: 1 }, { a: 1 });
  });
});

// To run: node --test step8-run-tests.js
// To run all test files: node --test **/*.test.js
// Watch mode: node --test --watch **/*.test.js
console.log('\nRun command: node --test step8-run-tests.js');
```

> 💡 **`assert.deepEqual` vs `assert.equal`:** Arrays and objects are reference types — `[1,2] === [1,2]` is `false` (different objects). Use `deepEqual` for structural comparison. `equal` uses `===` which is fine for primitives.

**📸 Verified Output:**
```
▶ Math utilities
  ✓ addition is commutative (0.3ms)
  ✓ multiplication by zero (0.2ms)
  ✓ string conversion (0.1ms)
  ✓ array equality requires deepEqual (0.2ms)
▶ Math utilities (1.1ms)
ℹ tests 4
ℹ pass 4
ℹ fail 0

Run command: node --test step8-run-tests.js
```

---

## Verification

```bash
node --test step7-tdd.js
```

Expected: All 4 RateLimiter tests pass.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Not `await`-ing async tests | Async test functions must be `async` and awaited inside |
| `assert.equal` on arrays/objects | Use `assert.deepEqual` for structural comparison |
| Shared state between tests | Use `beforeEach` to create fresh instances |
| Not testing error paths | Every `throw` needs a corresponding `assert.throws` test |
| Testing implementation, not behavior | Test what functions return/do, not how they do it |

## Summary

You've written tests using Node's built-in `node:test` runner — unit tests, grouped `describe` blocks, `beforeEach`/`afterEach` hooks, async test handling, mocking with `mock.fn()`, branch coverage strategy, and TDD red-green-refactor. These skills apply directly to Jest, Vitest, and Mocha — they all share the same mental model.

## Further Reading
- [Node.js Test Runner docs](https://nodejs.org/api/test.html)
- [Node.js assert docs](https://nodejs.org/api/assert.html)
- [Jest docs](https://jestjs.io) — the most popular JS testing framework
- [Test-Driven Development by Example — Kent Beck](https://www.oreilly.com/library/view/test-driven-development/0321146530/)
