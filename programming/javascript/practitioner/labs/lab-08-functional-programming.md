# Lab 08: Functional Programming

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Apply functional programming in JavaScript: pure functions, immutability, map/filter/reduce, currying, function composition with `compose`/`pipe`, point-free style, and an introduction to transducers.

---

## Step 1: Pure Functions & Side Effects

```javascript
// IMPURE — depends on external state, mutates input
let total = 0;
function addToTotal(amount) {
  total += amount; // Side effect: modifies external state
  return total;
}

// PURE — same input always gives same output, no side effects
function add(a, b) { return a + b; }
function multiply(a, b) { return a * b; }

// Impure: mutates the array
function pushItem(arr, item) {
  arr.push(item); // Mutation!
  return arr;
}

// Pure: returns new array
function appendItem(arr, item) {
  return [...arr, item];
}

// Benefits of pure functions:
const arr = [1, 2, 3];
const newArr = appendItem(arr, 4);
console.log(arr);    // [1, 2, 3] — unchanged!
console.log(newArr); // [1, 2, 3, 4]
console.log(add(1, 2) === add(1, 2)); // Always true
```

> 💡 Pure functions are easier to test, debug, memoize, and parallelize.

---

## Step 2: Immutability

```javascript
// Object.freeze — shallow immutability
const config = Object.freeze({
  host: 'localhost',
  port: 3000,
  database: { name: 'mydb' } // Nested object NOT frozen
});

// config.port = 8080; // Silently fails (strict mode throws)
// config.database.name = 'other'; // Works! (nested not frozen)

// Deep freeze
function deepFreeze(obj) {
  Object.getOwnPropertyNames(obj).forEach(name => {
    const value = obj[name];
    if (value && typeof value === 'object') deepFreeze(value);
  });
  return Object.freeze(obj);
}

// Immutable update patterns
const state = { user: { name: 'Alice', prefs: { theme: 'dark' } }, count: 0 };

// Spread for shallow update
const newState = { ...state, count: state.count + 1 };

// Deep update
const updatedTheme = {
  ...state,
  user: {
    ...state.user,
    prefs: { ...state.user.prefs, theme: 'light' }
  }
};

console.log(state.user.prefs.theme);        // dark (unchanged)
console.log(updatedTheme.user.prefs.theme); // light
```

---

## Step 3: map, filter, reduce

```javascript
const products = [
  { id: 1, name: 'Widget', price: 9.99, category: 'hardware', inStock: true },
  { id: 2, name: 'Gadget', price: 24.99, category: 'electronics', inStock: false },
  { id: 3, name: 'Doohickey', price: 4.99, category: 'hardware', inStock: true },
  { id: 4, name: 'Thingamajig', price: 49.99, category: 'electronics', inStock: true }
];

// map — transform each element
const names = products.map(p => p.name);
console.log(names); // ['Widget', 'Gadget', 'Doohickey', 'Thingamajig']

// filter — select elements
const inStock = products.filter(p => p.inStock);
const affordable = products.filter(p => p.price < 25);

// reduce — accumulate to single value
const totalValue = products.reduce((sum, p) => sum + p.price, 0);
console.log('Total:', totalValue.toFixed(2));

// Group by category using reduce
const byCategory = products.reduce((groups, p) => ({
  ...groups,
  [p.category]: [...(groups[p.category] || []), p]
}), {});
console.log(Object.keys(byCategory)); // ['hardware', 'electronics']

// Chaining
const hardwareTotal = products
  .filter(p => p.category === 'hardware' && p.inStock)
  .map(p => p.price)
  .reduce((sum, price) => sum + price, 0);
console.log('Hardware total:', hardwareTotal.toFixed(2));
```

---

## Step 4: Currying

```javascript
// Manual currying
function curry(fn) {
  const arity = fn.length;
  return function curried(...args) {
    if (args.length >= arity) return fn(...args);
    return (...more) => curried(...args, ...more);
  };
}

const add = curry((a, b, c) => a + b + c);
console.log(add(1)(2)(3));    // 6
console.log(add(1, 2)(3));    // 6
console.log(add(1)(2, 3));    // 6
console.log(add(1, 2, 3));    // 6

// Practical curried functions
const curriedMap = curry((fn, arr) => arr.map(fn));
const curriedFilter = curry((pred, arr) => arr.filter(pred));
const curriedReduce = curry((fn, init, arr) => arr.reduce(fn, init));

const double = x => x * 2;
const isEven = x => x % 2 === 0;

const doubleAll = curriedMap(double);
const keepEvens = curriedFilter(isEven);

console.log(doubleAll([1, 2, 3, 4]));     // [2, 4, 6, 8]
console.log(keepEvens([1, 2, 3, 4, 5]));  // [2, 4]
```

---

## Step 5: Function Composition

```javascript
// compose — right to left
const compose = (...fns) => x => fns.reduceRight((acc, fn) => fn(acc), x);

// pipe — left to right (more readable)
const pipe = (...fns) => x => fns.reduce((acc, fn) => fn(acc), x);

// Building blocks
const trim = s => s.trim();
const toLowerCase = s => s.toLowerCase();
const split = sep => s => s.split(sep);
const join = sep => arr => arr.join(sep);
const filter = pred => arr => arr.filter(pred);
const map = fn => arr => arr.map(fn);
const capitalize = s => s.charAt(0).toUpperCase() + s.slice(1);

// Compose a string processor
const processName = pipe(
  trim,
  toLowerCase,
  split(' '),
  filter(Boolean),
  map(capitalize),
  join(' ')
);

console.log(processName('  JOHN  DOE  '));   // 'John Doe'
console.log(processName('  alice  smith ')); // 'Alice Smith'

// Math pipeline
const double = x => x * 2;
const addOne = x => x + 1;
const square = x => x * x;

const transform = pipe(double, addOne, square);
console.log(transform(3)); // (3*2+1)^2 = 49
console.log(transform(4)); // (4*2+1)^2 = 81
```

---

## Step 6: Point-Free Style

```javascript
// Point-free: define functions without mentioning data
const pipe = (...fns) => x => fns.reduce((acc, fn) => fn(acc), x);
const map = fn => arr => arr.map(fn);
const filter = pred => arr => arr.filter(pred);
const reduce = (fn, init) => arr => arr.reduce(fn, init);
const prop = key => obj => obj[key];
const gt = n => x => x > n;
const lt = n => x => x < n;

// Point-free: no explicit data argument
const getAge = prop('age');
const isAdult = pipe(getAge, gt(17));
const getPrice = prop('price');
const isAffordable = pipe(getPrice, lt(50));

const users = [
  { name: 'Alice', age: 30 },
  { name: 'Bob', age: 16 },
  { name: 'Charlie', age: 25 }
];

const adults = users.filter(isAdult);
console.log(adults.map(prop('name'))); // ['Alice', 'Charlie']

// vs pointed style (less reusable)
const adults2 = users.filter(user => user.age > 17);
```

> 💡 Point-free style is about composition and reuse. Don't force it — readability matters more.

---

## Step 7: Transducers Concept

```javascript
// Problem: multiple map/filter chains traverse the array multiple times
// [1..1000000].filter(even).map(double).reduce(sum) — 3 passes!

// Transducers — composable, efficient data transformations (1 pass)
const map = fn => reducer => (acc, val) => reducer(acc, fn(val));
const filter = pred => reducer => (acc, val) => pred(val) ? reducer(acc, val) : acc;
const transduce = (xform, reducer, init, coll) =>
  coll.reduce(xform(reducer), init);

// Compose transducers
const compose = (...fns) => x => fns.reduceRight((acc, fn) => fn(acc), x);
const appendReducer = (acc, val) => [...acc, val];
const sumReducer = (acc, val) => acc + val;

const isEven = n => n % 2 === 0;
const double = n => n * 2;

const xform = compose(filter(isEven), map(double));

// Single pass through the array!
const result = transduce(xform, appendReducer, [], [1, 2, 3, 4, 5, 6, 7, 8]);
console.log(result); // [4, 8, 12, 16]

const sum = transduce(xform, sumReducer, 0, [1, 2, 3, 4, 5, 6, 7, 8]);
console.log(sum); // 40
```

---

## Step 8: Capstone — Functional Data Processing

```javascript
const compose = (...fns) => x => fns.reduceRight((acc, fn) => fn(acc), x);
const pipe = (...fns) => x => fns.reduce((acc, fn) => fn(acc), x);
const double = x => x * 2;
const addOne = x => x + 1;
const square = x => x * x;
const transform = pipe(double, addOne, square);
console.log(transform(3));

const curry = fn => {
  const arity = fn.length;
  return function curried(...args) {
    if (args.length >= arity) return fn(...args);
    return (...more) => curried(...args, ...more);
  };
};
const add = curry((a, b, c) => a + b + c);
console.log(add(1)(2)(3), add(1, 2)(3), add(1)(2, 3));

const state = Object.freeze({count: 0, items: []});
const newState = {...state, count: state.count + 1, items: [...state.items, 'new']};
console.log(state.count, newState.count, newState.items);
```

**Run verification:**
```bash
docker run --rm node:20-alpine sh -c "node -e '
const compose = (...fns) => x => fns.reduceRight((acc, fn) => fn(acc), x);
const pipe = (...fns) => x => fns.reduce((acc, fn) => fn(acc), x);
const double = x => x * 2; const addOne = x => x + 1; const square = x => x * x;
const transform = pipe(double, addOne, square);
console.log(transform(3));
const curry = fn => {
  const arity = fn.length;
  return function curried(...args) {
    if (args.length >= arity) return fn(...args);
    return (...more) => curried(...args, ...more);
  };
};
const add = curry((a, b, c) => a + b + c);
console.log(add(1)(2)(3), add(1, 2)(3), add(1)(2, 3));
const state = Object.freeze({count: 0, items: []});
const newState = {...state, count: state.count + 1, items: [...state.items, \"new\"]};
console.log(state.count, newState.count, newState.items);
'"
```

📸 **Verified Output:**
```
49
6 6 6
0 1 [ 'new' ]
```

---

## Summary

| Concept | Description | Key Benefit |
|---------|-------------|-------------|
| Pure functions | No side effects, deterministic | Testable, memoizable |
| Immutability | Never mutate, return new values | Predictable state |
| map | Transform each element | Declarative transformation |
| filter | Select elements by predicate | Declarative filtering |
| reduce | Accumulate to single value | Flexible aggregation |
| Currying | Function with partial application | Reusable function building |
| compose | Right-to-left function chain | Build complex from simple |
| pipe | Left-to-right function chain | Readable data pipeline |
| Point-free | Define ops without data args | Reusable combinators |
| Transducers | Composable, efficient transforms | Single-pass processing |
