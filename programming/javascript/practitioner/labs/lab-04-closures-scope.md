# Lab 04: Closures & Scope

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Deep dive into JavaScript's lexical scope, closures, IIFE pattern, module pattern, factory functions, closure pitfalls, and WeakRef for memory-safe closures.

---

## Step 1: Lexical Scope

```javascript
const globalVar = 'global';

function outer() {
  const outerVar = 'outer';

  function inner() {
    const innerVar = 'inner';
    // inner has access to outer and global scope
    console.log(globalVar); // 'global'
    console.log(outerVar);  // 'outer'
    console.log(innerVar);  // 'inner'
  }

  inner();
  // console.log(innerVar); // ReferenceError — not accessible here
}

outer();

// Block scope (let/const)
{
  let blockScoped = 'block';
  const alsoBlock = 'also block';
  console.log(blockScoped); // 'block'
}
// console.log(blockScoped); // ReferenceError
```

> 💡 JavaScript uses **lexical (static) scope** — a function's scope is determined by where it's *defined*, not where it's *called*.

---

## Step 2: Closures

```javascript
// A closure is a function that "remembers" its lexical environment
function makeCounter(start = 0, step = 1) {
  let count = start; // Closed over by the returned functions

  return {
    increment: () => { count += step; return count; },
    decrement: () => { count -= step; return count; },
    reset: () => { count = start; return count; },
    value: () => count
  };
}

const counter1 = makeCounter(0, 1);
const counter2 = makeCounter(100, 10);

console.log(counter1.increment()); // 1
console.log(counter1.increment()); // 2
console.log(counter2.increment()); // 110
console.log(counter1.value());     // 2  (independent from counter2)
console.log(counter2.value());     // 110

// Closures capture the variable reference, not the value
function makeAdder(x) {
  return function(y) {
    return x + y; // x is closed over
  };
}

const add5 = makeAdder(5);
const add10 = makeAdder(10);
console.log(add5(3));  // 8
console.log(add10(3)); // 13
```

---

## Step 3: IIFE (Immediately Invoked Function Expression)

```javascript
// Classic IIFE — creates isolated scope
const result = (function() {
  const privateData = 'secret';
  return { getData: () => privateData };
})();

console.log(result.getData()); // 'secret'
// console.log(privateData);   // ReferenceError

// Arrow IIFE
const config = (() => {
  const ENV = 'production';
  return { env: ENV, debug: ENV !== 'production' };
})();
console.log(config); // { env: 'production', debug: false }

// Async IIFE (useful in non-module contexts)
(async () => {
  const data = await Promise.resolve('async data');
  console.log('Async IIFE result:', data);
})();

// Named IIFE (better stack traces)
(function initApp() {
  console.log('App initialized');
  // ... setup code
}());
```

> 💡 IIFE was the primary way to create private scope before ES modules. Still useful for async initialization.

---

## Step 4: Module Pattern

```javascript
// Revealing Module Pattern — expose only what's needed
const UserStore = (() => {
  const users = new Map(); // Private
  let nextId = 1;          // Private

  function create(data) {
    const id = nextId++;
    const user = { id, ...data, createdAt: new Date().toISOString() };
    users.set(id, user);
    return user;
  }

  function findById(id) {
    return users.get(id) ?? null;
  }

  function findAll() {
    return [...users.values()];
  }

  function remove(id) {
    return users.delete(id);
  }

  return { create, findById, findAll, remove }; // Public API
})();

const alice = UserStore.create({ name: 'Alice', email: 'alice@example.com' });
const bob = UserStore.create({ name: 'Bob', email: 'bob@example.com' });

console.log(alice);               // { id: 1, name: 'Alice', ... }
console.log(UserStore.findAll().length); // 2
UserStore.remove(1);
console.log(UserStore.findAll().length); // 1
```

---

## Step 5: Factory Functions

```javascript
// Factory functions with closures for encapsulation
function createBankAccount(initialBalance = 0) {
  let balance = initialBalance;
  const transactions = [];

  function recordTransaction(type, amount) {
    transactions.push({ type, amount, balance, timestamp: Date.now() });
  }

  return {
    deposit(amount) {
      if (amount <= 0) throw new RangeError('Amount must be positive');
      balance += amount;
      recordTransaction('deposit', amount);
      return this;
    },
    withdraw(amount) {
      if (amount <= 0) throw new RangeError('Amount must be positive');
      if (amount > balance) throw new Error('Insufficient funds');
      balance -= amount;
      recordTransaction('withdrawal', amount);
      return this;
    },
    getBalance: () => balance,
    getHistory: () => [...transactions] // Return copy, not reference
  };
}

const account = createBankAccount(1000);
account.deposit(500).withdraw(200); // Fluent interface
console.log('Balance:', account.getBalance()); // 1300
console.log('Transactions:', account.getHistory().length); // 2
```

---

## Step 6: Closure Pitfalls & Fixes

```javascript
// PITFALL: var in loops — all closures share same variable
const badFunctions = [];
for (var i = 0; i < 5; i++) {
  badFunctions.push(() => i); // All capture the same `i`
}
console.log(badFunctions.map(f => f())); // [5, 5, 5, 5, 5] — WRONG!

// FIX 1: Use let (block scope)
const goodFunctions = [];
for (let i = 0; i < 5; i++) {
  goodFunctions.push(() => i); // Each iteration has its own `i`
}
console.log(goodFunctions.map(f => f())); // [0, 1, 2, 3, 4] — CORRECT!

// FIX 2: IIFE to capture current value
const iifeFunctions = [];
for (var j = 0; j < 5; j++) {
  iifeFunctions.push(((captured) => () => captured)(j));
}
console.log(iifeFunctions.map(f => f())); // [0, 1, 2, 3, 4] — CORRECT!

// FIX 3: Array.from
const arrayFromFunctions = Array.from({ length: 5 }, (_, i) => () => i);
console.log(arrayFromFunctions.map(f => f())); // [0, 1, 2, 3, 4]

// Memory leak: closure preventing GC
function leakExample() {
  const bigData = new Array(1000000).fill('data');
  return function() {
    return bigData[0]; // bigData can't be GC'd while this fn exists
  };
}
// Fix: Don't hold unnecessary references in closures
```

> 💡 `let` and `const` are block-scoped, so each loop iteration creates a new binding.

---

## Step 7: WeakRef for Memory-Safe Closures

```javascript
// WeakRef — holds reference without preventing garbage collection
class Cache {
  #store = new Map();

  set(key, value) {
    this.#store.set(key, new WeakRef(value));
  }

  get(key) {
    const ref = this.#store.get(key);
    if (!ref) return undefined;
    const value = ref.deref();
    if (value === undefined) {
      this.#store.delete(key); // Clean up dead ref
      return undefined;
    }
    return value;
  }
}

// FinalizationRegistry — callback when object is GC'd
const registry = new FinalizationRegistry((key) => {
  console.log(`Object with key "${key}" was garbage collected`);
});

const cache = new Cache();
let obj = { data: 'important' };
registry.register(obj, 'myKey');
cache.set('myKey', obj);

console.log(cache.get('myKey')); // { data: 'important' }

// If obj is no longer referenced elsewhere and GC runs,
// the WeakRef will return undefined
// obj = null; // Allow GC
```

---

## Step 8: Capstone — Memoization with Closures

```javascript
function memoize(fn, options = {}) {
  const { maxSize = 100, ttl = Infinity } = options;
  const cache = new Map();
  const timestamps = new Map();

  return function memoized(...args) {
    const key = JSON.stringify(args);
    const now = Date.now();

    if (cache.has(key)) {
      const age = now - (timestamps.get(key) || 0);
      if (age < ttl) {
        return cache.get(key);
      }
      cache.delete(key);
      timestamps.delete(key);
    }

    if (cache.size >= maxSize) {
      const firstKey = cache.keys().next().value;
      cache.delete(firstKey);
      timestamps.delete(firstKey);
    }

    const result = fn.apply(this, args);
    cache.set(key, result);
    timestamps.set(key, now);
    return result;
  };
}

// Test memoization
let computeCount = 0;
function expensiveCalc(n) {
  computeCount++;
  let result = 0;
  for (let i = 0; i <= n; i++) result += i;
  return result;
}

const memoCalc = memoize(expensiveCalc, { maxSize: 10, ttl: 60000 });

console.log(memoCalc(100));  // 5050 (computed)
console.log(memoCalc(100));  // 5050 (from cache)
console.log(memoCalc(200));  // 20100 (computed)
console.log('Actual computations:', computeCount); // 2 (not 3)

// Verify with Docker
```

**Run verification:**
```bash
docker run --rm node:20-alpine sh -c "node -e '
function makeCounter(start = 0) {
  let count = start;
  return {
    increment: () => ++count,
    decrement: () => --count,
    value: () => count
  };
}
const c = makeCounter(10);
console.log(c.increment(), c.increment(), c.decrement(), c.value());
const result = (function() { return 42; })();
console.log(result);
const fns = Array.from({length: 3}, (_, i) => () => i);
console.log(fns.map(f => f()));
'"
```

📸 **Verified Output:**
```
11 12 11 11
42
[ 0, 1, 2 ]
```

---

## Summary

| Concept | Description | Example |
|---------|-------------|---------|
| Lexical scope | Scope determined by code position | Nested functions access outer vars |
| Closure | Function + its lexical environment | Counter, memoize, factory |
| IIFE | Function called immediately | `(() => {})()` |
| Module pattern | IIFE returning public API | Private state + public methods |
| Factory function | Function returning objects | `createCounter()`, `createAccount()` |
| `var` pitfall | `var` leaks from blocks/loops | Use `let`/`const` instead |
| WeakRef | Reference without preventing GC | Caches that auto-expire |
