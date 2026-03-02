# Lab 12: Iterators & Generators

## Objective
Understand the JavaScript iteration protocol, create custom iterables, use generator functions to produce sequences lazily, and apply generators to real-world patterns like infinite sequences, async iteration, and pipelines.

## Background
Iterators are the protocol behind `for...of`, spread `[...arr]`, destructuring, and `Array.from()`. Generators are functions that can pause execution (`yield`) and resume later — enabling lazy evaluation, infinite sequences, and cooperative async control flow. Understanding these unlocks deeper JavaScript patterns used in libraries like Redux-Saga, RxJS, and async stream processing.

## Time
40 minutes

## Prerequisites
- Lab 05 (Classes & OOP)
- Lab 06 (Promises & Async/Await)

## Tools
- Node.js 20 LTS
- Docker image: `innozverse-js:latest`

---

## Lab Instructions

### Step 1: The Iterator Protocol

Any object with a `[Symbol.iterator]()` method returning `{ next() { return { value, done } } }` is iterable.

```javascript
// step1-iterator.js

// Manual iterator
function rangeIterator(start, end, step = 1) {
  let current = start;
  return {
    [Symbol.iterator]() { return this; },
    next() {
      if (current <= end) {
        const value = current;
        current += step;
        return { value, done: false };
      }
      return { value: undefined, done: true };
    }
  };
}

const range = rangeIterator(1, 10, 2);

// Use with for...of
for (const n of range) {
  process.stdout.write(n + ' ');
}
console.log();

// Spread operator works on iterables
const evens = [...rangeIterator(2, 10, 2)];
console.log('Evens:', evens);

// Destructuring
const [a, b, c] = rangeIterator(10, 50, 10);
console.log('First three tens:', a, b, c);
```

> 💡 **`Symbol.iterator`** is a well-known Symbol — a unique key that JavaScript uses to identify the iteration protocol. By defining it, your object plugs into the entire iteration ecosystem: `for...of`, spread, `Array.from`, `Map`, `Set`, destructuring.

**📸 Verified Output:**
```
1 3 5 7 9
Evens: [ 2, 4, 6, 8, 10 ]
First three tens: 10 20 30
```

---

### Step 2: Generator Functions

Generator functions use `function*` and `yield` to pause and resume, returning a generator object.

```javascript
// step2-generators.js

function* count(start = 1, step = 1) {
  let n = start;
  while (true) {
    yield n;
    n += step;
  }
}

// Generators are lazy — only compute when asked
const counter = count(0, 5);
console.log(counter.next()); // { value: 0, done: false }
console.log(counter.next()); // { value: 5, done: false }
console.log(counter.next()); // { value: 10, done: false }

// Take first N values from an infinite generator
function take(gen, n) {
  const result = [];
  for (const val of gen) {
    result.push(val);
    if (result.length >= n) break;
  }
  return result;
}

console.log('\nFirst 5 multiples of 3:', take(count(3, 3), 5));
console.log('First 5 squares:', take(
  (function* () {
    let i = 1;
    while (true) yield i++ ** 2;
  })(),
  5
));
```

> 💡 **Generators are lazy by nature** — they compute the next value only when `.next()` is called. This makes infinite sequences possible without infinite memory. The `while(true)` loop never runs away because `yield` pauses execution.

**📸 Verified Output:**
```
{ value: 0, done: false }
{ value: 5, done: false }
{ value: 10, done: false }

First 5 multiples of 3: [ 3, 6, 9, 12, 15 ]
First 5 squares: [ 1, 4, 9, 16, 25 ]
```

---

### Step 3: yield* — Delegating to Other Generators

`yield*` delegates to another iterable, letting you compose generators.

```javascript
// step3-yield-star.js

function* range(start, end) {
  for (let i = start; i <= end; i++) yield i;
}

function* concat(...iterables) {
  for (const iterable of iterables) {
    yield* iterable;
  }
}

// Flatten nested arrays
function* flatten(arr) {
  for (const item of arr) {
    if (Array.isArray(item)) yield* flatten(item);
    else yield item;
  }
}

console.log([...concat(range(1, 3), range(7, 9), [20, 21])]);
// [1, 2, 3, 7, 8, 9, 20, 21]

const nested = [1, [2, [3, [4]], 5], 6];
console.log([...flatten(nested)]);
// [1, 2, 3, 4, 5, 6]

// Tree traversal
function* inorder(node) {
  if (!node) return;
  yield* inorder(node.left);
  yield node.value;
  yield* inorder(node.right);
}

const tree = {
  value: 4,
  left: { value: 2, left: { value: 1, left: null, right: null }, right: { value: 3, left: null, right: null } },
  right: { value: 6, left: { value: 5, left: null, right: null }, right: { value: 7, left: null, right: null } }
};

console.log('BST in-order:', [...inorder(tree)]);
// [1, 2, 3, 4, 5, 6, 7]
```

> 💡 **`yield*` recursion** is the generator equivalent of recursive function calls. It's how you traverse trees, flatten structures, or chain sequences without building intermediate arrays.

**📸 Verified Output:**
```
[
  1, 2, 3, 7,
  8, 9, 20, 21
]
[ 1, 2, 3, 4, 5, 6 ]
BST in-order: [
  1, 2, 3, 4,
  5, 6, 7
]
```

---

### Step 4: Two-way Communication — Sending Values into Generators

`.next(value)` sends a value back into the generator at the last `yield` point.

```javascript
// step4-two-way.js

function* calculator() {
  let result = 0;
  while (true) {
    const input = yield result;
    if (input === null) break;
    const [op, num] = input;
    if (op === '+') result += num;
    else if (op === '-') result -= num;
    else if (op === '*') result *= num;
    else if (op === '/') result /= num;
  }
  return result;
}

const calc = calculator();
calc.next();            // Initialize (run to first yield)
console.log(calc.next(['+', 10]).value);  // 10
console.log(calc.next(['+', 5]).value);   // 15
console.log(calc.next(['*', 2]).value);   // 30
console.log(calc.next(['-', 8]).value);   // 22
console.log(calc.next(null));             // { value: 22, done: true }
```

> 💡 **The first `.next()` call always passes `undefined`** because there's no previous `yield` to receive it. Think of it as "start the generator". Subsequent `.next(value)` calls resume from the `yield` and the expression `yield result` evaluates to `value`.

**📸 Verified Output:**
```
10
15
30
22
{ value: 22, done: true }
```

---

### Step 5: Async Generators — Streaming Data

`async function*` yields Promises, enabling streaming over async sources.

```javascript
// step5-async-generator.js

// Simulate paginated API
async function* fetchPages(baseUrl, maxPages = 3) {
  for (let page = 1; page <= maxPages; page++) {
    // Simulate API call delay
    await new Promise(r => setTimeout(r, 50));

    // Simulate response
    yield {
      page,
      data: Array.from({ length: 3 }, (_, i) => ({
        id: (page - 1) * 3 + i + 1,
        name: `Item ${(page - 1) * 3 + i + 1}`
      })),
      hasMore: page < maxPages
    };
  }
}

async function main() {
  let total = 0;

  // for-await-of for async iterables
  for await (const response of fetchPages('https://api.example.com/items')) {
    console.log(`Page ${response.page}:`, response.data.map(d => d.name).join(', '));
    total += response.data.length;
  }

  console.log(`\nTotal items fetched: ${total}`);
}

main();
```

> 💡 **`for await...of`** is the async equivalent of `for...of` — it `await`s each yielded value. This is perfect for processing large datasets page-by-page, reading streams line-by-line, or polling APIs without loading everything into memory.

**📸 Verified Output:**
```
Page 1: Item 1, Item 2, Item 3
Page 2: Item 4, Item 5, Item 6
Page 3: Item 7, Item 8, Item 9

Total items fetched: 9
```

---

### Step 6: Generator Pipeline — Lazy Data Processing

Chain generators to process data lazily without intermediate arrays.

```javascript
// step6-pipeline.js

function* map(iterable, fn) {
  for (const item of iterable) yield fn(item);
}

function* filter(iterable, predicate) {
  for (const item of iterable) {
    if (predicate(item)) yield item;
  }
}

function* take(iterable, n) {
  let count = 0;
  for (const item of iterable) {
    if (count++ >= n) break;
    yield item;
  }
}

function* naturals(start = 1) {
  while (true) yield start++;
}

// Pipeline: infinite naturals → filter primes → take 10
function* sieve(numbers) {
  for (const n of numbers) {
    if (n < 2) continue;
    let prime = true;
    for (let i = 2; i <= Math.sqrt(n); i++) {
      if (n % i === 0) { prime = false; break; }
    }
    if (prime) yield n;
  }
}

const first10Primes = [...take(sieve(naturals()), 10)];
console.log('First 10 primes:', first10Primes);

// Practical: process log entries lazily
const logs = [
  'INFO: Server started',
  'ERROR: DB connection failed',
  'INFO: Retry attempt 1',
  'ERROR: Timeout after 3000ms',
  'INFO: Connected successfully',
  'WARN: Memory at 85%',
  'ERROR: Rate limit exceeded',
];

const pipeline = take(
  map(
    filter(logs, line => line.startsWith('ERROR')),
    line => line.replace('ERROR: ', '').toUpperCase()
  ),
  2
);

console.log('\nFirst 2 errors:');
for (const err of pipeline) console.log(' -', err);
```

> 💡 **Generator pipelines are memory-efficient.** When you chain `filter → map → take` over 1 million log lines, only one item flows through at a time. Arrays would allocate millions of entries. This is how Node.js streams and RxJS observables work under the hood.

**📸 Verified Output:**
```
First 10 primes: [
   2,  3,  5,  7,
  11, 13, 17, 19,
  23, 29
]

First 2 errors:
 - DB CONNECTION FAILED
 - TIMEOUT AFTER 3000MS
```

---

### Step 7: Return and Throw — Generator Control Flow

Generators can be terminated early with `.return()` or have errors injected with `.throw()`.

```javascript
// step7-control.js

function* resilientGen() {
  try {
    let i = 0;
    while (true) {
      try {
        yield i++;
      } catch (e) {
        console.log('  Caught inside generator:', e.message);
        yield -1; // yield error sentinel
      }
    }
  } finally {
    console.log('  Generator cleaned up');
  }
}

const gen = resilientGen();
console.log(gen.next().value);          // 0
console.log(gen.next().value);          // 1
console.log(gen.throw(new Error('oops')).value);  // -1
console.log(gen.next().value);          // 2
console.log(gen.return('done'));        // { value: 'done', done: true }
// Note: finally runs when return() is called
```

> 💡 **`.throw(err)` injects an error at the yield point**, letting the generator handle it with try/catch. `.return(value)` forces completion and triggers `finally` blocks — critical for cleanup (closing files, releasing connections).

**📸 Verified Output:**
```
0
1
  Caught inside generator: oops
-1
2
  Generator cleaned up
{ value: 'done', done: true }
```

---

### Step 8: Real-World — Paginated Data Collector

Build a practical async generator that collects all pages from a paginated API.

```javascript
// step8-paginator.js

// Simulate paginated data store
const DATA_STORE = Array.from({ length: 25 }, (_, i) => ({
  id: i + 1,
  name: `Product ${i + 1}`,
  price: parseFloat((Math.random() * 100 + 10).toFixed(2))
}));

async function* paginate(fetchFn, pageSize = 5) {
  let page = 1;
  let hasMore = true;

  while (hasMore) {
    const { items, total } = await fetchFn(page, pageSize);
    yield* items;
    hasMore = page * pageSize < total;
    page++;
  }
}

// Simulated API call
async function fetchProducts(page, limit) {
  await new Promise(r => setTimeout(r, 10)); // simulate latency
  const start = (page - 1) * limit;
  return {
    items: DATA_STORE.slice(start, start + limit),
    total: DATA_STORE.length
  };
}

async function main() {
  let count = 0;
  let totalValue = 0;
  let expensive = [];

  for await (const product of paginate(fetchProducts, 5)) {
    count++;
    totalValue += product.price;
    if (product.price > 80) expensive.push(product.name);
  }

  console.log(`Products fetched: ${count}`);
  console.log(`Total catalog value: $${totalValue.toFixed(2)}`);
  console.log(`Premium products (>$80): ${expensive.length}`);
}

main();
```

> 💡 **This pattern is production-ready.** Replace `fetchProducts` with an actual API call and you have a generic paginator that works with GitHub's API, Stripe's cursors, or any offset-based pagination — all without loading all pages into memory first.

**📸 Verified Output:**
```
Products fetched: 25
Total catalog value: $1389.47
Premium products (>$80): 5
```
*(prices are randomized — values will differ)*

---

## Verification

```bash
node step8-paginator.js
```

Expected: All 25 products fetched across 5 pages, total value and premium count printed.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Calling `next()` on exhausted generator | Check `done` before calling `next()` again |
| Forgetting first `.next()` initializes | First call runs to first `yield`, can't pass values |
| Using `return` inside generator loop | `return` ends the generator; use `yield` to continue |
| Forgetting `*` in `function*` | Without `*`, it's a regular function |
| Using `for...of` with async generator | Use `for await...of` for async generators |

## Summary

You now understand the iterator protocol, generator functions, `yield*` delegation, two-way communication via `.next(value)`, async generators with `for await...of`, lazy pipelines, and early termination with `.return()`/`.throw()`. Generators are a superpower for elegant, memory-efficient data processing.

## Further Reading
- [MDN: Iterators and Generators](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Iterators_and_generators)
- [MDN: async function*](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/async_function*)
- [You Don't Know JS: Async & Performance — Generators](https://github.com/getify/You-Dont-Know-JS)
