# Lab 06: Iterators & Generators

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Master the iterator protocol, build custom iterables, use generator functions (`function*`), `yield`/`yield*`, infinite sequences, async generators, and `for...of` loops.

---

## Step 1: Iterator Protocol

```javascript
// An iterator is any object with a next() method
const manualIterator = {
  items: ['a', 'b', 'c'],
  index: 0,
  next() {
    if (this.index < this.items.length) {
      return { value: this.items[this.index++], done: false };
    }
    return { value: undefined, done: true };
  }
};

console.log(manualIterator.next()); // { value: 'a', done: false }
console.log(manualIterator.next()); // { value: 'b', done: false }
console.log(manualIterator.next()); // { value: 'c', done: false }
console.log(manualIterator.next()); // { value: undefined, done: true }

// Built-in iterables
const arr = [1, 2, 3];
const iter = arr[Symbol.iterator]();
console.log(iter.next()); // { value: 1, done: false }
console.log(iter.next()); // { value: 2, done: false }

// String is iterable
for (const char of 'hello') {
  process.stdout.write(char + ' ');
}
console.log(); // h e l l o
```

> 💡 An **iterable** has `[Symbol.iterator]()`. An **iterator** has `next()`. They can be the same object.

---

## Step 2: Custom Iterable

```javascript
// Make any object iterable with [Symbol.iterator]
class LinkedList {
  constructor() {
    this.head = null;
    this.size = 0;
  }

  push(value) {
    this.head = { value, next: this.head };
    this.size++;
    return this;
  }

  [Symbol.iterator]() {
    let current = this.head;
    const items = [];
    while (current) {
      items.unshift(current.value);
      current = current.next;
    }
    let index = 0;
    return {
      next() {
        if (index < items.length) return { value: items[index++], done: false };
        return { value: undefined, done: true };
      },
      [Symbol.iterator]() { return this; } // Make iterator itself iterable
    };
  }
}

const list = new LinkedList();
list.push(1).push(2).push(3);

for (const item of list) {
  console.log(item); // 1, 2, 3
}

const [first, ...rest] = list;
console.log(first, rest); // 1 [2, 3]
console.log([...list]);   // [1, 2, 3]
```

---

## Step 3: Generator Functions (function*)

```javascript
// function* creates a generator function
function* simpleGenerator() {
  console.log('Step 1');
  yield 1;
  console.log('Step 2');
  yield 2;
  console.log('Step 3');
  yield 3;
  console.log('Done');
}

const gen = simpleGenerator();
console.log(gen.next()); // Step 1 / { value: 1, done: false }
console.log(gen.next()); // Step 2 / { value: 2, done: false }
console.log(gen.next()); // Step 3 / { value: 3, done: false }
console.log(gen.next()); // Done   / { value: undefined, done: true }

// Generators are iterables
function* range(start, end, step = 1) {
  for (let i = start; i < end; i += step) {
    yield i;
  }
}

console.log([...range(0, 10, 2)]); // [0, 2, 4, 6, 8]

for (const n of range(1, 5)) {
  process.stdout.write(n + ' ');
}
console.log(); // 1 2 3 4
```

---

## Step 4: yield* and Delegation

```javascript
function* innerGen() {
  yield 'a';
  yield 'b';
  yield 'c';
}

function* outerGen() {
  yield 1;
  yield* innerGen(); // Delegate to another iterable
  yield 2;
  yield* [3, 4, 5]; // Delegate to array
}

console.log([...outerGen()]); // [1, 'a', 'b', 'c', 2, 3, 4, 5]

// yield* with trees (recursive)
function* walkTree(node) {
  if (!node) return;
  yield node.value;
  yield* walkTree(node.left);
  yield* walkTree(node.right);
}

const tree = {
  value: 1,
  left: {
    value: 2,
    left: { value: 4, left: null, right: null },
    right: { value: 5, left: null, right: null }
  },
  right: {
    value: 3,
    left: null,
    right: { value: 6, left: null, right: null }
  }
};

console.log([...walkTree(tree)]); // [1, 2, 4, 5, 3, 6] (preorder)
```

---

## Step 5: Infinite Sequences

```javascript
// Generators can model infinite sequences safely
function* fibonacci() {
  let [prev, curr] = [0, 1];
  while (true) {
    yield curr;
    [prev, curr] = [curr, prev + curr];
  }
}

function* naturals(start = 1) {
  while (true) yield start++;
}

// Take first N items from a generator
function take(n, gen) {
  const result = [];
  for (const value of gen) {
    result.push(value);
    if (result.length >= n) break;
  }
  return result;
}

// Lazy filter/map for generators
function* filter(pred, iter) {
  for (const item of iter) {
    if (pred(item)) yield item;
  }
}

function* map(fn, iter) {
  for (const item of iter) {
    yield fn(item);
  }
}

const fib = fibonacci();
console.log(take(8, fibonacci())); // [1, 1, 2, 3, 5, 8, 13, 21]

// First 5 even fibonacci numbers
const evenFibs = take(5, filter(n => n % 2 === 0, fibonacci()));
console.log(evenFibs); // [2, 8, 34, 144, 610]
```

> 💡 Generators are lazy — values are computed on demand. Perfect for infinite sequences and large datasets.

---

## Step 6: Two-way Communication

```javascript
// Generators can receive values via next(value)
function* stateMachine() {
  let state = 'idle';
  while (true) {
    const event = yield state;
    switch (state) {
      case 'idle':
        if (event === 'START') state = 'running';
        break;
      case 'running':
        if (event === 'PAUSE') state = 'paused';
        if (event === 'STOP') state = 'idle';
        break;
      case 'paused':
        if (event === 'RESUME') state = 'running';
        if (event === 'STOP') state = 'idle';
        break;
    }
  }
}

const machine = stateMachine();
console.log(machine.next().value);         // 'idle' (initial state)
console.log(machine.next('START').value);  // 'running'
console.log(machine.next('PAUSE').value);  // 'paused'
console.log(machine.next('RESUME').value); // 'running'
console.log(machine.next('STOP').value);   // 'idle'
```

---

## Step 7: Async Generators

```javascript
// async function* — combines generators with async/await
async function* paginatedFetch(endpoint, pageSize = 10) {
  let page = 1;
  let hasMore = true;

  while (hasMore) {
    // Simulate API call
    const data = await new Promise(resolve =>
      setTimeout(() => {
        const items = Array.from({ length: pageSize },
          (_, i) => ({ id: (page - 1) * pageSize + i + 1, page }));
        resolve({ items, hasMore: page < 3 }); // 3 pages total
      }, 50)
    );

    yield* data.items;
    hasMore = data.hasMore;
    page++;
  }
}

// Consume with for await...of
(async () => {
  const items = [];
  for await (const item of paginatedFetch('/api/items')) {
    items.push(item.id);
    if (items.length >= 15) break; // Stop early
  }
  console.log('Fetched items:', items);
})();
```

---

## Step 8: Capstone — Lazy Pipeline

```javascript
// Full lazy evaluation pipeline using generators
function* range(start, end, step = 1) {
  for (let i = start; i < end; i += step) yield i;
}
function* fibonacci() {
  let [a, b] = [0, 1];
  while (true) { yield a; [a, b] = [b, a + b]; }
}
async function* asyncRange(n) {
  for (let i = 0; i < n; i++) {
    await new Promise(r => setTimeout(r, 1));
    yield i;
  }
}
(async () => {
  const vals = [];
  for await (const v of asyncRange(5)) vals.push(v);
  console.log(vals);
})();
console.log([...range(0, 10, 2)]);
const fib = fibonacci();
console.log(Array.from({length: 8}, () => fib.next().value));
```

**Run verification:**
```bash
docker run --rm node:20-alpine sh -c "node -e '
function* range(start, end, step = 1) {
  for (let i = start; i < end; i += step) yield i;
}
console.log([...range(0, 10, 2)]);
function* fibonacci() {
  let [a, b] = [0, 1];
  while (true) { yield a; [a, b] = [b, a + b]; }
}
const fib = fibonacci();
console.log(Array.from({length: 8}, () => fib.next().value));
async function* asyncRange(n) {
  for (let i = 0; i < n; i++) {
    await new Promise(r => setTimeout(r, 1));
    yield i;
  }
}
(async () => {
  const vals = [];
  for await (const v of asyncRange(5)) vals.push(v);
  console.log(vals);
})();
'"
```

📸 **Verified Output:**
```
[ 0, 2, 4, 6, 8 ]
[
  0, 1, 1,  2,
  3, 5, 8, 13
]
[ 0, 1, 2, 3, 4 ]
```

---

## Summary

| Concept | Syntax | Use Case |
|---------|--------|----------|
| Iterator protocol | `{ next() { return {value, done} } }` | Custom iteration logic |
| Iterable | `[Symbol.iterator]() { return iterator }` | `for...of`, spread, destructure |
| Generator | `function* gen() { yield v; }` | Lazy sequences, coroutines |
| yield* | `yield* iterable` | Delegate to another iterable |
| Infinite sequence | `while(true) { yield n++; }` | Math sequences, IDs |
| Two-way | `const v = yield expr` | State machines, coroutines |
| Async generator | `async function* gen()` | Paginated APIs, streams |
| for await...of | `for await (const x of asyncIter)` | Consume async iterables |
