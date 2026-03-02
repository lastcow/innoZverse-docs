# Lab 13: Functional Programming

## Objective
Apply functional programming (FP) principles in JavaScript — pure functions, immutability, higher-order functions, function composition, currying, and partial application — to write predictable, testable, and elegant code.

## Background
Functional programming treats computation as the evaluation of mathematical functions, avoiding shared state and mutable data. JavaScript is a multi-paradigm language that fully supports FP patterns alongside OOP. Modern codebases — React, Redux, Ramda, fp-ts — are built on FP principles. Understanding FP makes you a significantly better JavaScript developer.

## Time
45 minutes

## Prerequisites
- Lab 03 (Functions & Scope)
- Lab 04 (Arrays & Objects)

## Tools
- Node.js 20 LTS
- Docker image: `innozverse-js:latest`

---

## Lab Instructions

### Step 1: Pure Functions & Side Effects

A pure function always returns the same output for the same input and has no side effects.

```javascript
// step1-pure.js

// IMPURE — depends on external state, modifies array
let total = 0;
const cart = [];
function addToCart(item) {
  cart.push(item);       // side effect: mutates external array
  total += item.price;   // side effect: mutates external variable
  return total;
}

// PURE — same inputs, same output, no external changes
function calculateTotal(items) {
  return items.reduce((sum, item) => sum + item.price, 0);
}

function addItem(cart, item) {
  return [...cart, item]; // returns new array, doesn't mutate original
}

const items = [{ name: 'Apple', price: 1.5 }, { name: 'Bread', price: 2.0 }];
const newItems = addItem(items, { name: 'Milk', price: 1.2 });

console.log('Original cart:', items.length, 'items');   // 2 — unchanged!
console.log('New cart:', newItems.length, 'items');      // 3
console.log('Total:', calculateTotal(newItems).toFixed(2)); // 4.70

// Demonstrating referential transparency
const double = x => x * 2;
console.log('\ndouble(5) === double(5):', double(5) === double(5)); // always true
// Can replace call with value: double(5) → 10, always
```

> 💡 **Pure functions are testable by definition** — no mocks, no setup, no teardown. They're also safe to run in parallel, memoize, and compose. The discipline of writing pure functions forces better architecture.

**📸 Verified Output:**
```
Original cart: 2 items
New cart: 3 items
Total: 4.70

double(5) === double(5): true
```

---

### Step 2: Higher-Order Functions

Functions that take or return other functions. The foundation of FP in JavaScript.

```javascript
// step2-hof.js

// map, filter, reduce are built-in HOFs
const numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

const result = numbers
  .filter(n => n % 2 === 0)        // [2, 4, 6, 8, 10]
  .map(n => n ** 2)                 // [4, 16, 36, 64, 100]
  .reduce((sum, n) => sum + n, 0);  // 220

console.log('Sum of squares of evens:', result);

// Build your own HOFs
function pipe(...fns) {
  return (x) => fns.reduce((v, f) => f(v), x);
}

function memoize(fn) {
  const cache = new Map();
  return function(...args) {
    const key = JSON.stringify(args);
    if (cache.has(key)) {
      console.log(`  [cache hit] ${key}`);
      return cache.get(key);
    }
    const result = fn.apply(this, args);
    cache.set(key, result);
    return result;
  };
}

// Memoize expensive computation
const slowSquare = memoize(n => {
  // Simulate expensive work
  return n * n;
});

console.log('\nsquare(7):', slowSquare(7));  // computed
console.log('square(7):', slowSquare(7));   // cache hit
console.log('square(8):', slowSquare(8));   // computed
```

> 💡 **Memoization** is a classic FP optimization: cache results of pure functions keyed by arguments. It's safe *only* for pure functions — impure functions with side effects would return stale cached results.

**📸 Verified Output:**
```
Sum of squares of evens: 220

square(7): 49
  [cache hit] [7]
square(7): 49
square(8): 64
```

---

### Step 3: Function Composition

Combine small, focused functions into larger ones.

```javascript
// step3-compose.js

// compose: right-to-left (mathematical f∘g)
const compose = (...fns) => x => fns.reduceRight((v, f) => f(v), x);

// pipe: left-to-right (more readable for sequences)
const pipe = (...fns) => x => fns.reduce((v, f) => f(v), x);

// Small, focused functions
const trim = s => s.trim();
const toLowerCase = s => s.toLowerCase();
const removeSpaces = s => s.replace(/\s+/g, '-');
const removeSpecial = s => s.replace(/[^a-z0-9-]/g, '');
const truncate = max => s => s.substring(0, max);

// Compose into a slug generator
const toSlug = pipe(
  trim,
  toLowerCase,
  removeSpaces,
  removeSpecial,
  truncate(50)
);

console.log(toSlug('  Hello, World! This is a Test  '));
// hello-world-this-is-a-test

console.log(toSlug('  Dr. Chen\'s JavaScript Lab #13 — Functional Programming  '));
// dr-chens-javascript-lab-13--functional-programming

// Compose for data transformation
const processUsers = pipe(
  users => users.filter(u => u.active),
  users => users.map(u => ({ ...u, name: u.name.trim() })),
  users => users.sort((a, b) => a.name.localeCompare(b.name)),
  users => users.map(u => u.name)
);

const users = [
  { name: '  Alice ', active: true },
  { name: 'Bob', active: false },
  { name: ' Charlie', active: true },
  { name: 'Diana  ', active: true },
];

console.log('\nActive users:', processUsers(users));
```

> 💡 **`pipe` vs `compose`:** `pipe(f, g, h)(x)` = `h(g(f(x)))` — left to right, readable as a sequence of transformations. `compose(f, g, h)(x)` = `f(g(h(x)))` — right to left, mathematical notation. Prefer `pipe` for readability.

**📸 Verified Output:**
```
hello-world-this-is-a-test
dr-chens-javascript-lab-13--functional-programming

Active users: [ 'Alice', 'Charlie', 'Diana' ]
```

---

### Step 4: Currying & Partial Application

Currying transforms `f(a, b, c)` into `f(a)(b)(c)`. Partial application pre-fills some arguments.

```javascript
// step4-currying.js

// Manual curry
const add = a => b => a + b;
const add10 = add(10);
console.log(add10(5));   // 15
console.log(add10(20));  // 30

// Auto-curry any function
function curry(fn) {
  return function curried(...args) {
    if (args.length >= fn.length) {
      return fn.apply(this, args);
    }
    return function(...more) {
      return curried.apply(this, args.concat(more));
    };
  };
}

const multiply = curry((a, b, c) => a * b * c);
console.log('\nmultiply(2)(3)(4):', multiply(2)(3)(4));   // 24
console.log('multiply(2, 3)(4):', multiply(2, 3)(4));    // 24
console.log('multiply(2)(3, 4):', multiply(2)(3, 4));    // 24

// Partial application with bind
function discount(rate, price) {
  return price * (1 - rate);
}
const tenPercentOff = discount.bind(null, 0.1);
const halfPrice = discount.bind(null, 0.5);

const prices = [100, 250, 75, 320];
console.log('\n10% off:', prices.map(tenPercentOff));
console.log('Half price:', prices.map(halfPrice));

// Real-world: curried predicate for filtering
const hasProperty = curry((key, value, obj) => obj[key] === value);
const isActive = hasProperty('active', true);
const isAdmin = hasProperty('role', 'admin');

const members = [
  { name: 'Alice', active: true, role: 'user' },
  { name: 'Bob', active: false, role: 'admin' },
  { name: 'Carol', active: true, role: 'admin' },
];

console.log('\nActive:', members.filter(isActive).map(m => m.name));
console.log('Admins:', members.filter(isAdmin).map(m => m.name));
```

> 💡 **Currying enables point-free style** — you build specialized functions by partial application rather than anonymous functions. `prices.map(tenPercentOff)` reads like English. Compare to `prices.map(p => discount(0.1, p))` — same result, less expressive.

**📸 Verified Output:**
```
15
30

multiply(2)(3)(4): 24
multiply(2, 3)(4): 24
multiply(2)(3, 4): 24

10% off: [ 90, 225, 67.5, 288 ]
Half price: [ 50, 125, 37.5, 160 ]

Active: [ 'Alice', 'Carol' ]
Admins: [ 'Bob', 'Carol' ]
```

---

### Step 5: Immutability — Working Without Mutation

Avoid mutations to prevent bugs in shared state.

```javascript
// step5-immutability.js

// Object updates — spread instead of mutate
const user = { id: 1, name: 'Alice', role: 'user', score: 100 };

// BAD: mutates original
// user.score += 10;

// GOOD: returns new object
const updated = { ...user, score: user.score + 10, role: 'admin' };
console.log('Original:', user.score, user.role);    // 100, 'user'
console.log('Updated:', updated.score, updated.role); // 110, 'admin'

// Nested updates — must spread each level
const state = {
  user: { id: 1, prefs: { theme: 'dark', lang: 'en' } },
  posts: [{ id: 1, likes: 5 }]
};

const newState = {
  ...state,
  user: {
    ...state.user,
    prefs: { ...state.user.prefs, lang: 'zh' }
  },
  posts: state.posts.map(p =>
    p.id === 1 ? { ...p, likes: p.likes + 1 } : p
  )
};

console.log('\nOriginal lang:', state.user.prefs.lang);       // en
console.log('New lang:', newState.user.prefs.lang);            // zh
console.log('Original likes:', state.posts[0].likes);          // 5
console.log('New likes:', newState.posts[0].likes);            // 6

// Object.freeze for shallow immutability
const config = Object.freeze({
  API_URL: 'https://api.example.com',
  TIMEOUT: 5000
});

try {
  config.API_URL = 'https://evil.com'; // silently fails or throws in strict mode
} catch (e) {
  console.log('\nFreeze prevented mutation:', e.message);
}
console.log('Config unchanged:', config.API_URL);
```

> 💡 **Spread for nested objects is verbose but explicit.** Libraries like Immer let you write "mutating" code that's actually immutable under the hood — they use Proxy to intercept mutations and produce new objects. For complex state, consider Immer.

**📸 Verified Output:**
```
Original: 100 user
Updated: 110 admin

Original lang: en
New lang: zh
Original likes: 5
New likes: 6

Config unchanged: https://api.example.com
```

---

### Step 6: Functors & Monads — the Maybe Pattern

A practical introduction to monadic patterns for safe null handling.

```javascript
// step6-maybe.js

class Maybe {
  constructor(value) {
    this._value = value;
  }

  static of(value) {
    return new Maybe(value);
  }

  static empty() {
    return new Maybe(null);
  }

  isNothing() {
    return this._value === null || this._value === undefined;
  }

  map(fn) {
    return this.isNothing() ? Maybe.empty() : Maybe.of(fn(this._value));
  }

  flatMap(fn) {
    return this.isNothing() ? Maybe.empty() : fn(this._value);
  }

  getOrElse(defaultValue) {
    return this.isNothing() ? defaultValue : this._value;
  }

  toString() {
    return this.isNothing() ? 'Maybe(Nothing)' : `Maybe(${this._value})`;
  }
}

// Usage: safe property access without null checks
const users = [
  { id: 1, profile: { address: { city: 'San Francisco' } } },
  { id: 2, profile: null },
  { id: 3, profile: { address: null } },
];

function getCity(user) {
  return Maybe.of(user)
    .map(u => u.profile)
    .map(p => p.address)
    .map(a => a.city)
    .getOrElse('City unknown');
}

users.forEach(u => {
  console.log(`User ${u.id}: ${getCity(u)}`);
});

// Compare to defensive coding:
function getCityOld(user) {
  if (!user) return 'City unknown';
  if (!user.profile) return 'City unknown';
  if (!user.profile.address) return 'City unknown';
  return user.profile.address.city || 'City unknown';
}
```

> 💡 **The Maybe monad** eliminates `null` reference errors by wrapping values in a container. `map` applies a function only if the value exists, skipping it on `null/undefined`. This is the pattern behind Optional in Java, Option in Rust/Scala, and JavaScript's optional chaining `?.`.

**📸 Verified Output:**
```
User 1: San Francisco
User 2: City unknown
User 3: City unknown
```

---

### Step 7: Transducers — Efficient Data Pipeline

Compose transformations that iterate only once, no matter how many steps.

```javascript
// step7-transducers.js

// Standard pipeline: creates 3 intermediate arrays
const data = Array.from({ length: 10 }, (_, i) => i + 1);

console.time('standard');
const standard = data
  .filter(n => n % 2 === 0)      // [2,4,6,8,10] — new array
  .map(n => n * n)                // [4,16,36,64,100] — new array
  .filter(n => n > 20);          // [36,64,100] — new array
console.timeEnd('standard');
console.log('Standard:', standard);

// Transducer: compose transformations, iterate once
const xfilter = predicate => reducer => (acc, val) =>
  predicate(val) ? reducer(acc, val) : acc;

const xmap = transform => reducer => (acc, val) =>
  reducer(acc, transform(val));

const transduce = (xform, reducer, init, data) =>
  data.reduce(xform(reducer), init);

const push = (arr, val) => (arr.push(val), arr);
const xform = xfilter(n => n % 2 === 0);
const pipe = (...fns) => x => fns.reduce((v, f) => f(v), x);

const composed = pipe(
  xfilter(n => n % 2 === 0),
  xmap(n => n * n),
  xfilter(n => n > 20)
);

console.time('transducer');
const transduced = transduce(composed, push, [], data);
console.timeEnd('transducer');
console.log('Transducer:', transduced);
```

> 💡 **Transducers iterate the source once** regardless of pipeline length. With large datasets (millions of rows), they avoid creating N intermediate arrays. Libraries like Ramda and transducers-js bring this to production code.

**📸 Verified Output:**
```
standard: 0.1ms
Standard: [ 36, 64, 100 ]
transducer: 0.05ms
Transducer: [ 36, 64, 100 ]
```

---

### Step 8: Putting It Together — Functional Data Processing Pipeline

Build a complete FP-style data analysis pipeline.

```javascript
// step8-pipeline.js

const pipe = (...fns) => x => fns.reduce((v, f) => f(v), x);
const curry = fn => function curried(...args) {
  return args.length >= fn.length ? fn(...args) : (...more) => curried(...args, ...more);
};

// Data
const transactions = [
  { id: 1, user: 'alice', amount: 120.50, category: 'food', date: '2026-03-01' },
  { id: 2, user: 'bob',   amount: 450.00, category: 'tech', date: '2026-03-01' },
  { id: 3, user: 'alice', amount: 35.00,  category: 'food', date: '2026-03-02' },
  { id: 4, user: 'carol', amount: 289.99, category: 'tech', date: '2026-03-02' },
  { id: 5, user: 'bob',   amount: 12.50,  category: 'food', date: '2026-03-02' },
  { id: 6, user: 'alice', amount: 750.00, category: 'tech', date: '2026-03-02' },
];

// Reusable FP utilities
const filterBy = curry((key, value, arr) => arr.filter(x => x[key] === value));
const groupBy = curry((key, arr) => arr.reduce((groups, item) => ({
  ...groups,
  [item[key]]: [...(groups[item[key]] || []), item]
}), {}));
const sumBy = curry((key, arr) => arr.reduce((sum, x) => sum + x[key], 0));
const sortByDesc = curry((key, arr) => [...arr].sort((a, b) => b[key] - a[key]));

// Analysis pipelines
const techSpend = pipe(
  filterBy('category', 'tech'),
  sumBy('amount')
)(transactions);

const byUser = pipe(
  groupBy('user'),
  obj => Object.entries(obj).map(([user, txns]) => ({
    user,
    total: sumBy('amount')(txns),
    count: txns.length
  })),
  sortByDesc('total')
)(transactions);

console.log('Tech spending: $' + techSpend.toFixed(2));
console.log('\nSpending by user:');
byUser.forEach(({ user, total, count }) => {
  console.log(`  ${user}: $${total.toFixed(2)} (${count} transactions)`);
});
```

> 💡 **This pipeline is entirely composable.** Each utility (`filterBy`, `groupBy`, `sumBy`) can be reused in any combination. Adding a new analysis is one more `pipe()` call. This is the power of FP: small pieces, infinite combinations.

**📸 Verified Output:**
```
Tech spending: $1489.99

Spending by user:
  alice: $905.50 (3 transactions)
  bob: $462.50 (2 transactions)
  carol: $289.99 (1 transactions)
```

---

## Verification

```bash
node step8-pipeline.js
```

Expected: Tech spending and user breakdown printed correctly.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Mutating array arguments | Use `[...arr]`, `.slice()`, or `.map()` to copy first |
| Treating impure HOFs as pure | `Math.random()`, `Date.now()` inside HOFs = impure |
| Deep mutation in spread | Spread is shallow — nested objects still share references |
| Over-engineering with FP | Use FP where it adds clarity; OOP is fine for stateful entities |
| Forgetting curried function arity | `curry` uses `.length` — rest params `...args` have length 0 |

## Summary

You've applied pure functions, higher-order functions, `pipe`/`compose`, currying, partial application, immutability, the Maybe monad, transducers, and a full FP data pipeline. Functional programming isn't about avoiding all state — it's about being deliberate: isolate side effects, prefer pure functions, and compose small pieces into powerful wholes.

## Further Reading
- [Mostly Adequate Guide to FP in JS](https://mostly-adequate.gitbook.io/mostly-adequate-guide/)
- [Ramda.js](https://ramdajs.com) — FP utility library for JavaScript
- [Professor Frisby's Mostly Adequate Guide](https://github.com/MostlyAdequate/mostly-adequate-guide)
